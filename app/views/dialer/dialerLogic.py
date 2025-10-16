# Standard Python libraries
import json
import time
from datetime import datetime

# Django utilities
from django.http import HttpResponseBadRequest, JsonResponse
from django.utils import timezone

# Django core libraries
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

# Third-party imports
import telnyx
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

# Application-specific imports
from app.modelsDialer import *
from app.tasks import dial_leads_task

telnyx.api_key = settings.TELNYX_API_KEY

import logging
logger = logging.getLogger(__name__)

@csrf_exempt
def iniciateCalls(request, campaign_id):
    if request.method == 'GET':
        agentsAvailable = Agent.objects.filter(status='available')
        if not agentsAvailable:
            return JsonResponse({
                'error': 'All agents are currently busy or no agents are logged in.'
            }, status=400)

        # Inicia el proceso en segundo plano
        dial_leads_task.delay(campaign_id)
        return JsonResponse({'ok': 'Dialer started in background'})

    return HttpResponseBadRequest('Invalid request method')


@csrf_exempt
def webhooksTelnyx(request):
    body = json.loads(request.body.decode('utf-8'))
    data = body.get('data', {})
    eventType = data.get('event_type', {})
    payload = data.get('payload', {})
    callControlId = payload.get('call_control_id')
    call = Call.objects.select_related('contact', 'agent').filter(telnyx_call_control_id = callControlId).first()

    if eventType == 'call.initiated':
        if call is None:
            logger.error(f"Call {call.contact.name} not found (Initiated event)")
            return JsonResponse({'error': f'Call with call_control_id {callControlId} not found'}, status=404)
        call.status = 'Ringing'
        call.save()
        logger.info(f"Call {call.contact.name} initiated successfully.")
    elif eventType == 'call.answered':
        if call is None:
            logger.error(f"Call {call.contact.name} not found (Answered event)")
            return JsonResponse({'error': f'Call with call_control_id {callControlId} not found'}, status=404)
        call.status = 'Answered'
        call.answered_at = datetime.now()
        agent = getAvailableAgent()
        call.agent = agent
        transferCallToAgent(callControlId, agent)
        sendClientData(agent, call.contact, call)
        updateContactedLead(call.contact)
        call.save()
        logger.info(f"Call {call.contact.name} answered and transferred to agent {agent.id}.")
    elif eventType == 'call.hangup':
        if call.answered_at == None:
            tipifyCall = tipifyNoAnswerCall(call)
        call.status = 'Completed'
        call.ended_at = timezone.now()
        call.duration = secondsBetweenTimes(call.started_at, call.ended_at)
        call.save()
        logger.info(f"Call {call.contact.name} completed.")

    # Imprimir el cuerpo completo
    # print("Cuerpo completo de la solicitud:")
    # print(json.dumps(body, indent=2))
    return JsonResponse({'ok':'ok'})

def tipifyNoAnswerCall(call):
    # Lógica para tipificar la llamada como "No Contestada"
    call.outcome = CallOutcome.objects.filter(id=5).first()
    call.save()

def updateContactedLead(contact):
    contact.attempts += 1
    contact.last_contact = timezone.now()
    contact.save()

def getAvailableAgent():
    while True:
        agent = Agent.objects.filter(status='Available').order_by('-last_call').first()
        if agent:
            agent.last_call = timezone.now()
            agent.status = 'busy'
            agent.save()
            
            return agent
        else:
            time.sleep(1)  # Espera 1 segundo antes de volver a consultar

def sendClientData(agent, contact, call):
    channel_layer = get_channel_layer()

    # Traer la última llamada de ese lead
    last_call = Call.objects.filter(contact=contact).order_by('-started_at').select_related('outcome').first()
    last_outcome_name = last_call.outcome.name if last_call and last_call.outcome else None

    async_to_sync(channel_layer.group_send)(
        f"call_alert_agent_{agent.id}",
        {
            'type': 'call_answered',
            'clientName': contact.name,
            'clientPhone': contact.phone_number,
            'clientZipCode': contact.zipcode,
            'clientAddress': contact.address,
            'lastCall': contact.last_contact.strftime('%Y-%m-%d %H:%M:%S') if contact.last_contact else None,
            'attempts': contact.attempts,
            'status': last_outcome_name,   # 👈 Aquí ya no usamos contact.status
            'callId': str(call.id)
        }
    )


@require_POST
@csrf_exempt
def endpointTranferCallToAgent(request):
    body = json.loads(request.body.decode('utf-8'))
    newAgentId = body.get('newAgentId', {})
    try:
        newAgentObject = Agent.objects.get(id=newAgentId)
    except ObjectDoesNotExist:
        return JsonResponse({'error': f'Agent with id {newAgentId} not found'}, status=404)

    try:
        agent = request.user.agent
    except AttributeError:
        return JsonResponse({'error': 'Authenticated user is not linked to an agent'}, status=403)

    try:
        callObject = Call.objects.get(agent_id=agent.id)
    except ObjectDoesNotExist:
        return JsonResponse({'error': f'No active call found for agent {agent.id}'}, status=404)

    try:
        call = telnyx.Call.retrieve(callObject.telnyx_call_control_id)
        call.transfer(
            to=f"sip:{newAgentObject.sip_username}@sip.telnyx.com",
            sip_auth_username=newAgentObject.sip_username,
            sip_auth_password=newAgentObject.sip_password,
        )
        return JsonResponse({'message': f'Call transferred to agent {newAgentObject.id}'}, status=200)

    except telnyx.error.TelnyxError as e:
        # Errores específicos de Telnyx SDK/API
        return JsonResponse({'error': f'Telnyx API error: {str(e)}'}, status=502)

    except Exception as e:
        # Cualquier otro error inesperado
        return JsonResponse({'error': f'Unexpected error: {str(e)}'}, status=500)
    
def transferCallToAgent(callControlId, agent):
    call = telnyx.Call.retrieve(callControlId)
    try:
        call.transfer(
            to=f"sip:{agent.sip_username}@sip.telnyx.com",
            sip_auth_username=agent.sip_username,
            sip_auth_password=agent.sip_password,
        )
    except Exception as e:
        agent.status = 'available'
        agent.save()

        logger.error(f"Error al transferir la llamada: {str(e)}")

def secondsBetweenTimes(startTime, endTime):
    difference = endTime - startTime
    return int(difference.total_seconds())