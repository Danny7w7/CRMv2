# Standard Python libraries
import json
from datetime import timedelta
from collections import defaultdict

# Django utilities
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.utils.timezone import now

# Django core libraries
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Avg

# Third-party imports

# Application-specific imports
from app.modelsDialer import *

@login_required(login_url='/login') 
def agentDashboard(request):
    try:
        agent = request.user.agent
        campaign = Campaign.objects.filter(is_active = True).first()
        tipifications = CallOutcome.objects.all()

        context = {
            'agent': agent,
            'campaign': campaign,
            'tipifications': tipifications
        }
    except AttributeError:
        return HttpResponseBadRequest("You are not an agent.", status=403)
    return render(request, 'dialer/agentDashboard.html', context)

@csrf_exempt
@require_POST
def changeStatus(request, agent_id):
    data = json.loads(request.body)
    newStatus = data.get('status')

    try:
        agent = Agent.objects.get(id=agent_id)
    except Agent.DoesNotExist:
        return JsonResponse({'message': 'Agent not found'}, status=404)
    
    agent.status = newStatus
    agent.save()

    return JsonResponse({'message': 'Status updated'})

@csrf_exempt
@require_GET
def getStats(request):
    agent = request.user

    today = now().date()
    tomorrow = today + timedelta(days=1)
    
    call = Call.objects.filter(
        agent_id=agent.id,
        status='Completed',
        started_at__gte=today,
        started_at__lt=tomorrow
    ).values('id', 'status', 'duration')

    callCompleted = call.filter(status='Completed')

    averageSeconds = callCompleted.aggregate(
        avgDuration=Avg('duration')
    )['avgDuration'] or 0
    # Convertir a MM:SS
    minutes = int(averageSeconds // 60)
    seconds = int(averageSeconds % 60)
    averageFormatted = f"{minutes}:{seconds:02d}"


    return JsonResponse({
        'callToday': call.count(),
        'callCompleted': callCompleted.count(),
        'averageDuration': averageFormatted
    })

@csrf_exempt
@require_POST
def typifyCall(request):
    data = json.loads(request.body)
    controlCallId = data.get('controlCallId')
    agent_id = data.get('agent_id')
    typificationId = data.get('typification')

    try:
        call = Call.objects.get(id=controlCallId, agent_id=agent_id)
        agent = Agent.objects.get(id=agent_id)
        typification = CallOutcome.objects.get(id=typificationId)
    except Call.DoesNotExist:
        return JsonResponse({'message': 'Call not found'}, status=404)


    call.outcome = typification
    call.save()
    agent.status = 'Available'
    agent.save()

    return JsonResponse({'message': 'Call typified successfully'})