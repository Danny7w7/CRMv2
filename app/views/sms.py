# Standard Python libraries
import time
import json
import requests
import re
import logging
import pandas as pd
import io
import os
import boto3
import threading

# Third-party libraries
from weasyprint import HTML
from io import BytesIO

# Django utilities
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.core.signing import BadSignature, Signer
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.files.storage import FileSystemStorage
from PIL import Image
from threading import Timer
from datetime import datetime, timedelta
from decimal import Decimal

# Django core libraries
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.timezone import timedelta
from django.utils.translation import activate, gettext as _

# Third-party imports
import telnyx
import stripe
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

# Application-specific imports
from app.modelsSMS import *
from ..forms import *
from .utils import *
from .consents import getCompanyPerAgent
from ..alertWebsocket import websocketAlertGeneric
from .decoratorsCompany import *
from ..contextProcessors import validateSms

# Create your views here.
logger = logging.getLogger('django')

@csrf_exempt
def sendMessage(request):
    if comprobate_company(request.user.company):
        return JsonResponse({'message': 'No money'}, status=402)

    telnyx.api_key = settings.TELNYX_API_KEY

    phone_number = request.POST.get('phoneNumber')
    message_content = request.POST.get('messageContent', '')

    assigned_phone = getattr(request.user, "assigned_phone", None)

    if not assigned_phone or not getattr(assigned_phone, "phone_number", None):
        return JsonResponse({
            'error': 'You do not have an assigned phone number. Please contact the website administrators.'
        }, status=400)
    
    # Telnyx SMS limit (single part, GSM-7)
    MAX_SMS_LENGTH = 1530
    if len(message_content) > MAX_SMS_LENGTH:
        return JsonResponse({
            'error': f'Message too long. Max allowed is {MAX_SMS_LENGTH} characters.',
            'currentLength': len(message_content)
        }, status=400)

    try:
        telnyx.Message.create(
            from_=f"+{request.user.assigned_phone.phone_number}",
            to=f'+{phone_number}',
            text=message_content
        )

        contact, created = createOrUpdatecontact(phone_number, request.user.company)
        if request.user.role == 'Customer':
            chat = createOrUpdateChat(contact, request.user.company)
        else:
            chat = createOrUpdateChat(contact, request.user.company, request.user)

        saveMessageInDb('Agent', message_content, chat, request.user)

        return JsonResponse({'message': 'ok'})

    except telnyx.error.InvalidRequestError as e:
        return JsonResponse({'error': f'Telnyx error: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Unexpected error: {str(e)}'}, status=500)


@csrf_exempt
@require_POST
def sms(request, company_id):
    try:
        body = json.loads(request.body)
        company = Companies.objects.get(id=company_id)
        
        # Imprimir el cuerpo completo
        # print("Cuerpo completo de la solicitud:")
        # print(json.dumps(body, indent=2))
        
        # Acceder a datos específicos
        if 'data' in body and 'payload' in body['data']:
            payload = body['data']['payload']
            if body['data'].get('event_type') == 'message.received':
                contact, created = createOrUpdatecontact(int(payload.get('from', {}).get('phone_number')), company)
                chat = createOrUpdateChat(contact, company)
                message = saveMessageInDb('Client', payload.get('text'), chat)
                
                if not contact.is_active:
                    activatecontact(contact, payload.get('text'))

                if contact.is_active:
                    deactivatecontact(contact, payload.get('text'))

                if payload.get('type') == 'MMS':
                    try:
                        from app.tasks import saveImageFromUrlTask
                        saveImageFromUrlTask(message.id, payload, contact.id, company.id)
                    except:
                        message.message_content = 'Error receiving image, contact an administrator'
                        message.save()
                else:
                    SendMessageWebsocketChannel('SMS', payload, contact, company.id)
                    if company.id not in [1,2]:
                        discountRemainingBalance(company, '0.025')
                sendAlertToAgent(request, chat, contact)

            return HttpResponse("Webhook recibido correctamente", status=200)
    except json.JSONDecodeError:
        return HttpResponse("Error en el formato JSON", status=400)
    except Exception as e:
        return HttpResponse(f"Error interno del servidor {str(e)}", status=500)

def sendAlertToAgent(request, chat, contact):
    #Obtener al agente asociado
    agent = Users.objects.get(id=chat.agent_id)
    websocketAlertGeneric(
        request,
        'send_alert',
        'newMessage',
        'info',
        'New Message',
        f'{contact.name} sent a message.',
        'Go to chat with Client',
        f'/chatSms/{chat.id}/',
        agent.id,
        agent.username
    )

def SendMessageWebsocketChannel(typeMessage, payload, contact, company_id, mediaUrl=None):
    # Enviar mensaje al canal de WebSocket
    channel_layer = get_channel_layer()
    # logger.debug('UwU:Intento enviar el mensaje al websocket')
    # logger.debug(f"Intentando enviar mensaje - Tipo: {typeMessage}")
    # logger.debug(f"contacte: {contact.phone_number}")
    # logger.debug(f"Payload: {payload}")
    # logger.debug(f"MediaUrl: {mediaUrl}")
    if typeMessage == 'MMS':
        async_to_sync(channel_layer.group_send)(
            f"chat_{contact.phone_number}_company_{company_id}", # Asegúrate de que este formato coincida con tu room_group_name
            {
                'type': typeMessage,
                'message': mediaUrl,
                'username': f"contacte {contact.phone_number}",  # O como quieras identificar al contacte
                'datetime': timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S'),
                'sender_id': True  # O cualquier identificador único que uses
            }
        )
    else:
        async_to_sync(channel_layer.group_send)(
            f"chat_{contact.phone_number}_company_{company_id}", # Asegúrate de que este formato coincida con tu room_group_name
            {
                'type': 'chat_message',
                'message': payload.get('text'),
                'username': f"contacte {contact.phone_number}",  # O como quieras identificar al contacte
                'datetime': timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S'),
                'sender_id': True  # O cualquier identificador único que uses
            }
        )

def saveMessageInDb(inboundOrOutbound, message_content, chat, sender=None):
    message = Messages(
        sender_type=inboundOrOutbound,
        message_content=message_content,
        chat=chat,
    )
    if sender:
        message.sender = sender
        message.is_read = True
    else:
        message.is_read = False

    message.save()
    
    #Upload last message
    chat.last_message = timezone.localtime(timezone.now())
    chat.save()
    return message

def createOrUpdateChat(contact, company, agent=None):
    try:
        # Intenta obtener un chat existente para el contacte en la empresa especificada
        chat = Chat.objects.get(contact_id=contact.id, company_id=company.id)

        # Si se proporciona un nuevo agente, actualiza el chat
        if agent:
            chat.agent = agent
            chat.save()

    except Chat.DoesNotExist:
        # Si el chat no existe, crea uno nuevo
        if not agent:
            # Define un agente por defecto si no se proporciona (opcional)
            agent = Users.objects.get(id=1)  # ID de un agente genérico (En este caso sera el ID de Maria Carolina.)

        chat = Chat(
            agent=agent,
            contact=contact,
            company=company  # Asocia el chat con la compañía
        )
        chat.save()

    return chat

def createOrUpdatecontact(phoneNumber, company, name=None):
    # Intenta obtener o crear un contact
    contact, created = Contacts.objects.get_or_create(
        phone_number=phoneNumber,
        company=company,
        defaults={
            'name': name,
            'is_active': False
            }
    )
    if not created and name:
        # Si el contacte ya existía y se proporcionó un nombre, actualizamos el nombre
        contact.name = name
        contact.save()
        created = False  # El contacte no fue creado, solo actualizado
    return contact, created

def deleteContact(request, id):
    if request.user.is_superuser:
        contact = Contacts.objects.get(id=id)
        contact.delete()
    return redirect(index)

def activatecontact(contact, message):
    # Limpiar el mensaje eliminando espacios al principio y al final, así como cualquier puntuación extra.
    cleaned_message = re.sub(r'[^a-zA-Z]+', '', message.strip()).upper()

    # Verificar si el mensaje es 'YES' o 'SI' o 'START'
    if cleaned_message == 'YES' or cleaned_message == 'SI' or cleaned_message == 'START':
        contact.is_active = True
        contact.save()

def deactivatecontact(contact, message):
    message_upper = message.upper()
    if message_upper == 'STOP':
        contact.is_active = False
        contact.save()

@login_required(login_url='/login')
def index(request):
    validSms = validateSms(request)
    if not validSms or not validSms.get('smsIsActive'):
        return render(request, "auth/404.html", {"message": "Perfil desactivado por falta de pago."})

    chats = getPageChats(request, 1)

    if request.method == 'POST':
        phoneNumber = request.POST.get('phoneNumber')
        name = request.POST.get('name', None)
        contact, created = createOrUpdatecontact(phoneNumber, request.user.company, name)
        chat = createOrUpdateChat(contact, request.user.company, request.user)
        if created:
            if request.POST.get('language') == 'english':
                message = "Reply YES to receive updates and information about your policy from Lapeira & Associates LLC. Msg & data rates may apply. Up to 5 msgs/month. Reply STOP to opt-out at any time."
            else: 
                message = "Favor de responder SI para recibir actualizaciones e información sobre su póliza de Lapeira & Associates LLC. Pueden aplicarse tarifas estándar de mensaje y datos. Hasta 5 mensajes/mes. Responder STOP para cancelar en cualquier momento."
            sendIndividualsSms(
                request.user.assigned_phone.phone_number,
                phoneNumber,
                request.user,
                request.user.company,
                message
            )
        return redirect('chatSms', chat.id)
    return render(request, 'sms/indexSms.html', {'chats': chats})

@login_required(login_url='/login')
def chat(request, chatId):
    validSms = validateSms(request)
    if not validSms or not validSms.get('smsIsActive'):
        return render(request, "auth/404.html", {"message": "Perfil desactivado por falta de pago."})
    if request.method == 'POST':
        phoneNumber = request.POST.get('phoneNumber')
        name = request.POST.get('name', None)
        contact, created = createOrUpdatecontact(phoneNumber, request.user.company, name)
        chat = createOrUpdateChat(contact, request.user.company, request.user)
        if created:
            if request.POST.get('language') == 'english':
                message = "Reply YES to receive updates and information about your policy from Lapeira & Associates LLC. Msg & data rates may apply. Up to 5 msgs/month. Reply STOP to opt-out at any time."
            else: 
                message = "Favor de responder SI para recibir actualizaciones e información sobre su póliza de Lapeira & Associates LLC. Pueden aplicarse tarifas estándar de mensaje y datos. Hasta 5 mensajes/mes. Responder STOP para cancelar en cualquier momento."
            sendIndividualsSms(
                request.user.assigned_phone.phone_number,
                phoneNumber,
                request.user,
                request.user.company,
                message
            )
        return redirect('chatSms', chat.id)
            
    if request.user.is_superuser:
        chat = Chat.objects.select_related('contact').get(id=chatId)
    else:
        chat = Chat.objects.select_related('contact').get(id=chatId, company=request.user.company)
        
    secretKey = SecretKey.objects.filter(contact=chat.contact).first()
    
    messages = Messages.objects.prefetch_related('files').filter(chat=chat.id)

    messages_with_files = []
    for message in messages:
        files = message.files.all()
        message_dict = {
            'id': message.id,
            'sender_type': message.sender_type,
            'sender': message.sender,
            'message_content': message.message_content,
            'created_at': message.created_at,
            'is_read': message.is_read,
            'files': [f.file.url for f in files] if files else []
        }
        messages_with_files.append(message_dict)        
    messages.update(is_read=True)

    chats = getPageChats(request, 1)

    context = {
        "chat_url": f"/chatSms/{chatId}/",
        'contact': chat.contact,
        'chats': chats,
        'messages': messages_with_files,
        'secretKey':secretKey
    }
    return render(request, 'sms/chat.html', context)

def getPageChats(request, page):
    queryset = Chat.objects.select_related('contact').order_by('-last_message')

    if request.user.is_superuser:
        pass
    elif request.user.is_staff:
        queryset = queryset.filter(company=request.user.company)
    else:
        queryset = queryset.filter(agent_id=request.user.id)

    paginator = Paginator(queryset, 20)
    chats = paginator.get_page(page)
    chats = get_last_message_for_chats(chats)

    return chats

@csrf_exempt
@require_POST
@login_required(login_url='/login')
def getChatsLoad(request):
    data = json.loads(request.body)
    text = data.get('text', '')

    chats = Chat.objects.select_related('contact').filter(
        Q(contact__name__icontains=text) | Q(contact__phone_number__icontains=text)
    ).order_by('-last_message')

    chats = get_last_message_for_chats(chats)

    # Serializar manualmente para incluir todos los atributos agregados
    chats_data = [
        {
            'id': chat.id,
            'contactName': chat.contact.name,
            'contactPhone': chat.contact.phone_number,
            'lastMessage': chat.last_message_content,
            'lastMessageTime': chat.last_message_time,
            'isMessageUnread': chat.is_message_unread,
            'unreadMessages': chat.unread_messages,
            'hasAttachment': chat.has_attachment,
            'createdAt': chat.created_at,
        }
        for chat in chats
    ]

    return JsonResponse({'chats': chats_data})

@csrf_exempt
def startChat(request, phoneNumber):
    try:
        if request.POST.get('language') == 'english':
            message = "Reply YES to receive updates and information about your policy from Lapeira & Associates LLC. Msg & data rates may apply. Up to 5 msgs/month. Reply STOP to opt-out at any time."
        else: 
            message = "Favor de responder SI para recibir actualizaciones e información sobre su póliza de Lapeira & Associates LLC. Pueden aplicarse tarifas estándar de mensaje y datos. Hasta 5 mensajes/mes. Responder STOP para cancelar en cualquier momento."
        
        sendIndividualsSms(
            request.user.assigned_phone.phone_number,
            phoneNumber,
            request.user,
            request.user.company,
            message
        )
        return JsonResponse({'message': message})
    
    except Exception as e:
        error_response = {"error": "An error occurred while sending the message"}

        # Verifica si el error es una excepción de Telnyx
        if hasattr(e, "errors") and isinstance(e.errors, list):
            telnyx_error = e.errors[0]  # Normalmente, Telnyx devuelve una lista de errores
            error_response.update({
                "error_code": telnyx_error.get("code"),
                "error_title": telnyx_error.get("title"),
                "error_detail": telnyx_error.get("detail"),
            })

        return JsonResponse(error_response, status=500)

def sendIndividualsSms(from_number, to_number, user, company, messageContent, messageType=None):
    telnyx.api_key = settings.TELNYX_API_KEY
    telnyx.Message.create(
        from_=f"+{from_number}", # Your Telnyx number
        to=f'+{to_number}',
        text= messageContent
    )

    contact, created = createOrUpdatecontact(to_number, company)
    chat = createOrUpdateChat(contact, company)
    messageContent = validateMessageType(messageType, messageContent)
    saveMessageInDb('Agent', messageContent, chat, user)
    if company.id not in [1,2]: #No descuenta el saldo a Lapeira
        discountRemainingBalance(company, '0.035')
    
    return True

def validateMessageType(messageType, messageContent):
    messageMap = {
        'sendSecretKey': 'Secret key link successfully sent',
        'createSecretKey': 'Secret key creation link sent successfully',
    }

    return messageMap.get(messageType, messageContent)

@csrf_exempt
def sendSecretKey(request, contact_id):
    contact = Contacts.objects.get(id=contact_id)
    secretKey = SecretKey.objects.get(contact=contact)
    chat = Chat.objects.get(contact=contact)

    sendIndividualsSms(
        request.user.assigned_phone.phone_number,
        contact.phone_number,
        request.user,
        request.user.company,
        generate_temporary_url(request, contact, secretKey.secretKey),
        'sendSecretKey'
    )
    return JsonResponse({'message': 'ok'}, status=200)

@csrf_exempt
def sendCreateSecretKey(request, id):
    contact = Contacts.objects.get(id=id)
    chat = Chat.objects.get(contact=contact)

    sendIndividualsSms(
        request.user.assigned_phone.phone_number,
        contact.phone_number,
        request.user,
        request.user.company,
        generate_temporary_url(request, contact),
        'createSecretKey'
    )
    return JsonResponse({'message': 'ok'}, status=200)

def createSecretKey(request):
    result = validate_temporary_url(request)
    is_valid, note, *contact = result

    #Aqui valido si es valido el token, si no que retorne el mensaje de error
    if not is_valid:
        return HttpResponse(note)

    if request.method == 'POST':
        secret_key_request = request.POST['secret_key']

        # Verifica si existe un SecretKey para el contacte
        secret_key = SecretKey.objects.filter(contact=contact[0].id).first()
        chat = Chat.objects.select_related('agent').get(contact_id=contact[0].id)
        if not secret_key:
            secret_key = SecretKey()
            secret_key.contact = contact[0]
        secret_key.secretKey = secret_key_request
        secret_key.save()

        websocketAlertGeneric(
            request,
            'send_alert',
            'createSecretKey',
            'success',
            'Secret key successfully created.',
            f'The client {contact[0].name} successfully created his secret key.',
            'Go to chat with Client',
            f'/chatSms/{contact[0].phone_number}/',
            chat.agent.id,
            chat.agent.username
        )

        # invalidate_temporary_url(request, note) #Aqui el note equivale al Token
        return render(request, 'secret_key/create_secret_key.html', {'secret_key':secret_key_request})
    
    token = request.GET.get('token')

    signer = Signer()   
    signed_data = force_str(urlsafe_base64_decode(token))
    data = json.loads(signer.unsign(signed_data))

    secret_key = data.get('secret_key')

    return render(request, 'secret_key/create_secret_key.html', {'secret_keyG':secret_key})

@login_required(login_url='/login')
def chat_messages(request, phone_number):
    chat = Chat.objects.get(contact__phone_number=phone_number, agent=request.user)
    messages = Messages.objects.filter(chat=chat).order_by('created_at')
    return JsonResponse([{
        'message': msg.message_content,
        'sender_type': msg.sender_type,
        'timestamp': msg.created_at.isoformat()
    } for msg in messages], safe=False)

def payment_type(request, type, company_id):
    if type == 'Thank-You-Page':
        return render(request, 'sms/thank_you_page.html')
    elif type == 'Payment-Error':
        context = {
            'retry_payment_url': create_stripe_checkout_session(company_id)
        }
        return render(request, 'sms/payment_error.html', context)

stripe.api_key = settings.STRIPE_SECRET_KEY
def create_stripe_checkout_session(company_id):
    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    'price': 'price_1QSSDDHakpVhxYcD1d0EM7XV',
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=f"{settings.DOMAIN}/payment/Thank-You-Page/{company_id}/",
            cancel_url=f"{settings.DOMAIN}/payment/Payment-Error/{company_id}/",
            automatic_tax={'enabled': True},
            metadata={
                'company_id': company_id
            }
        )
        return checkout_session.url
    except stripe.error.StripeError as e:
        raise Exception(f"Stripe error: {str(e)}")
    except Exception as e:
        raise Exception(f"Unexpected error: {str(e)}")

@csrf_exempt
def readAllMessages(request, chat_id, company_id):
    contact = Contacts.objects.get(phone_number=chat_id, company_id=company_id)
    chat = Chat.objects.get(contact_id=contact.id)
    messages = Messages.objects.filter(chat=chat.id).select_related('filessms')
    messages.update(is_read=True)
    return JsonResponse({'message':'ok'})

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET  # Configura esto en tu cuenta de Stripe

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return JsonResponse({'error': 'Invalid signature'}, status=400)

    # Manejar el evento
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']  # Sesión completada
        company_id = session['metadata']['company_id']
        amount = format_number(session['amount_total'])

        company = Companies.objects.get(id=company_id)
        company.remaining_balance += amount
        company.notified_at_10 = False
        company.notified_at_5 = False
        company.notified_at_1 = False
        company.save()

        invoice(company_id, amount)

        send_email(
            subject=f"✅ Confirmación de Pago en SMS Blue - {company.company_name}",
            receiver_email=company.company_email,
            template_name="emailTemplates/payment_confirmation",
            context_data={
                "Owner_name": company.owner,
                "company": company.company_name,
                "payment_amount":amount,
                "current_balance": f'{company.remaining_balance:.2f}',
                "payment_date": timezone.now().strftime('%d/%m/%Y %H:%M:%S')
            }
        )

        # Aquí puedes actualizar tu base de datos, enviar correos, etc.

    return JsonResponse({'status': 'success'})

def invoice(company_id, amount):

    current_date = datetime.datetime.now().strftime("%A, %B %d, %Y %I:%M")
    company = Companies.objects.filter(id = company_id).first()

    id_formateado = f"{company.id:08d}"

    invoceHtml = Invoice(company=company)

    context = {
        'company' : company,
        'amount' : amount,
        'current_date':current_date,
        'id_formateado' : id_formateado
    } 

    # Renderiza la plantilla HTML a un string
    html_content = render_to_string('companies/invoice.html', context)

    # Genera el PDF
    pdf_file = HTML(string=html_content).write_pdf()

    # Usa BytesIO para convertir el PDF en un archivo
    pdf_io = io.BytesIO(pdf_file)
    pdf_io.seek(0)  # Asegúrate de que el cursor esté al principio del archivo

    # Guarda el PDF en el modelo usando un ContentFile
    pdf_name = f'Invoice_{company.company_name}_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'

    invoceHtml.pdf.save(pdf_name, ContentFile(pdf_io.read()), save=True)

def save_image_from_url(message, url):
    try:        
        # Descargar la imagen
        response = requests.get(url)
        response.raise_for_status()
        
        filename = url.split('/')[-1]

        file = FilesSMS()
        file.message = message
        file.file.save(filename, ContentFile(response.content), save=True)

        return file.file.url
        
    except Exception as e:
        print(f'Error {e}')

def get_last_message_for_chats(chats):
    """
    Función que enriquece los chats con información del último mensaje
    y cuenta los mensajes no leídos
    """
    for chat in chats:
        # Obtener el último mensaje del chat
        last_message = Messages.objects.filter(chat=chat).order_by('-created_at').first()
        
        # Contar mensajes no leídos
        unread_count = Messages.objects.filter(
            chat=chat,
            is_read=False,
            sender_type='Client'  # Solo mensajes del contacte
        ).count()
        
        # Si existe último mensaje, agregar atributos personalizados
        if last_message:
            # Truncar el mensaje a 27 caracteres
            content = last_message.message_content
            if len(content) > 24:
                content = content[:24] + "..."

            chat.last_message_content = content
            chat.last_message_time = last_message.created_at
            chat.has_attachment = last_message.files.exists()
            chat.is_message_unread = not last_message.is_read
        else:
            chat.last_message_content = "There are no messages."
            chat.last_message_time = None
            chat.has_attachment = False
            chat.is_message_unread = False
        
        # Agregar contador de mensajes no leídos
        chat.unread_messages = unread_count
    
    return chats

# Vista para generar el enlace temporal
def generate_temporary_url(request, contact, secret_key=None):
    signer = Signer()

    # Define una fecha de expiración (por ejemplo, 1 hora desde ahora)
    expiration_time = timezone.now() + timedelta(minutes=10)

    # Crear el token con la fecha de expiración usando JSON
    data = {
        'contact_id': contact.id,
        'phone_number': contact.phone_number,
        'expiration': expiration_time.isoformat(),
    }
    if secret_key:
        data['secret_key'] = secret_key
    signed_data = signer.sign(json.dumps(data))  # Firmar los datos serializados
    token = urlsafe_base64_encode(force_bytes(signed_data))  # Codificar seguro para URL

    # Guardar la URL temporal en la base de datos
    TemporaryToken.objects.create(
        contact=contact,
        token=token,
        expiration=expiration_time
    )
    if secret_key:
        temporary_url = f"{request.build_absolute_uri('/secret-key/')}?token={token}"
    else:
        temporary_url = f"{request.build_absolute_uri('/secret-key/')}?token={token}"

    # Crear la URL temporal

    return temporary_url

# Vista para verificar y procesar la URL temporal
def validate_temporary_url(request):
    token = request.POST.get('token') or request.GET.get('token')

    if not token:
        return False, 'Token no proporcionado. Not found token.'

    signer = Signer()
    
    try:
        signed_data = force_str(urlsafe_base64_decode(token))
        data = json.loads(signer.unsign(signed_data))

        contact_id = data.get('contact_id')
        expiration_time = timezone.datetime.fromisoformat(data['expiration'])
        # Verificar si el token está activo y no ha expirado
        temp_url = TemporaryToken.objects.select_related('contact').get(token=token, contact_id=contact_id)

        if not temp_url.is_active:
            return False, 'Enlace desactivado. Link deactivated.'

        if temp_url.is_expired():
            return False, 'Enlace ha expirado. Link expired.'

        # Procesar si la URL es válida
        contact = temp_url.contact
        
        return True, token, contact
    
    except (BadSignature, ValueError, KeyError):
        return False, 'Token inválido o alterado. Invalid token.'
        
def invalidate_temporary_url(request, token):
    try:
        temp_url = TemporaryToken.objects.get(token=token)
        temp_url.is_active = False
        temp_url.save()
    except TemporaryToken.DoesNotExist:
        return "Esta URL temporal no existe"

def comprobate_company(company):
    if company.id in [1,2]: #No descuenta el saldo a Lapeira
        return False
    if company.remaining_balance <= 0:
        disableAllUserCompany(company)
        return True
    else:
        discountRemainingBalance(company, '0.035')
        paymend_recording(company)
        return False

def discountRemainingBalance(companyObject, discount):
    companyObject.remaining_balance -= Decimal(discount)
    companyObject.save()

def disableAllUserCompany(companyObject):
    usersCompany = Users.objects.filter(company=companyObject)
    send_email(
        subject=f"Tu cuenta ha sido desactivada por saldo insuficiente",
        receiver_email=companyObject.company_email,
        template_name="emailTemplates/service_cancelled",        
        context_data={
            "Owner_name": companyObject.owner,
            "company": companyObject.company_name,
            "remaining_balance": f'{companyObject.remaining_balance:.2f}',
            "url_pay": create_stripe_checkout_session(companyObject.id)
        }
    )

    for user in usersCompany:
        if not user.is_staff:
            user.is_active = False
            user.save()

def paymend_recording(company):
    def format_mail_recording(company):
        activate(company.language_preference)
        send_email(
            subject=_("Tu saldo en SMS Blue es de {balance:.2f} USD. No te quedes sin servicio").format(balance=company.remaining_balance),
            receiver_email=company.company_email,
            template_name="emailTemplates/payment_reminder",
            context_data={
                "Owner_name": company.owner,
                "company": company.company_name,
                "remaining_balance": f'{company.remaining_balance:.2f}',
                "url_pay": create_stripe_checkout_session(company.id)
            }
        )

    if company.remaining_balance <= 10 and not company.notified_at_10:
        format_mail_recording(company)
        company.notified_at_10 = True
        company.save()
    
    if company.remaining_balance <= 5 and not company.notified_at_5:
        format_mail_recording(company)
        company.notified_at_5 = True
        company.save()
    
    if company.remaining_balance <= 1 and not company.notified_at_1:
        format_mail_recording(company)
        company.notified_at_1 = True
        company.save()

def format_number(number):
    return Decimal(number) / Decimal(100)

#vista para pagos del usuario de la company
@login_required(login_url='/login')
@company_ownership_required_sinURL
def adminSms(request):

    company_id = request.company_id  # Obtener company_id desde request
    company_filter = {'company': company_id}

    now = datetime.now()
    seven_days_ago = now - timedelta(days=6)

    # Obtener usuarios de la compañia
    company_users = Users.objects.filter(**company_filter)
    company = Companies.objects.get(id=company_id)
    numberCompanies = Numbers.objects.filter(**company_filter)

    # Filtrar mensajes de los últimos 7 días y asociados a chats de usuarios
    messages = Messages.objects.filter(
        chat__agent__in=company_users,
        created_at__gte=seven_days_ago
    )

    # Diccionario para los días de la semana
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    result = {day_name: 0 for day_name in day_names}

    # Agrupar los mensajes usando el día de la semana
    for message in messages:
        message_day = message.created_at.weekday()  # Obtiene el día de la semana (0=Monday, 6=Sunday)
        day_name = day_names[message_day]
        result[day_name] += 1

    context = {
        'day_names':json.dumps(day_names),
        'messages':json.dumps(result),
        "url_recharge": create_stripe_checkout_session(company.id),
        "company":company,
        "message_count":messages.count(),
        'numberCompanies': numberCompanies
    }

    return render(request, 'sms/adminSms.html', context)

def smstemplate(request):

    idClient = request.POST.get('idClient')
    sms = request.POST.get('sms')
    way = request.POST.get('way')
    validation = int(sms)

    obama = ObamaCare.objects.select_related('company').filter(client = idClient).first()
    client = Clients.objects.filter(id = idClient).first()

    #tomo el nombre de agente, me sirve tambien para escoger el template
    lines = obama.agent_usa.split("\n")
    agentFirstName = lines[0].split()[0] 

    template = ContentTemplate.objects.filter(id = sms).first()

    if validation == 6:
        validationSms = True
        sendTemplate(request, client.phone_number, agentFirstName, lang='es')

    if validation == 11:
        validationSms = True
        sendTemplate(request, client.phone_number, agentFirstName, lang='en')

    elif validation in (7,8,9,10):

        validationSms = True
        sendTemplateStatic(request, client.phone_number, template.identification)

    else: 

        context = {
            "name_client": client.first_name,
            "company": getCompanyPerAgent(agentFirstName),
            "agent": obama.agent_usa,
        }

        messageContent = renderMessageTemplate(template.contentTemplate, context)

        # Verificamos si ocurrió un error al renderizar
        if not messageContent.startswith("Error:"):       

            telnyx.api_key = settings.TELNYX_API_KEY
            telnyx.Message.create(
                from_='+17869848427', # Your Telnyx number
                to=f'+{client.phone_number}',
                text= messageContent
            )

        validationSms = True


    if validationSms:

        SmsTemplate.objects.create(
            contentTemplate = template,
            agent = request.user,
            obamacare = obama
        )

        if obama.company.id not in [1,2]: #No descuenta el saldo a Lapeira
            discountRemainingBalance(obama.company, '0.035')


    return redirect('editObama', obamacare_id=obama.id, way=way)

#Funcion para enviar template de bienvenida por sms
def sendTemplate(request, to_number, nameTemplate, lang='es'):
    """
    Envía una imagen personalizada al cliente por SMS (Telnyx).
    Soporta idioma español ('es') e inglés ('en').
    """

    imagen_url = None
    if request.method == 'POST' and request.FILES.get('filepond'):
        imagen_usuario_file = request.FILES['filepond']

        # Leer la imagen del usuario directamente desde memoria
        imagen_usuario = Image.open(imagen_usuario_file).convert("RGBA")

        # Cargar imagen base según el idioma
        suffix = "1" if lang == 'en' else ""
        imagen_base_path = os.path.join(
            settings.BASE_DIR, 
            'static', 'assets', 'images', 'template-images', 
            f'{nameTemplate}{suffix}.jpg'
        )
        base = Image.open(imagen_base_path).convert("RGBA")

        # Redimensionar y pegar la imagen del usuario
        imagen_usuario = imagen_usuario.resize((2000, 1000))
        base.paste(imagen_usuario, (80, 800), imagen_usuario)

        # Guardar imagen combinada en memoria
        output = BytesIO()
        base.save(output, format='PNG')
        output.seek(0)

        # Subir imagen combinada a S3
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )

        bucket = settings.AWS_STORAGE_BUCKET_NAME
        timestamp = int(time.time())
        filename = f'temp-template/combinado_{timestamp}.png'

        s3.upload_fileobj(output, bucket, filename, ExtraArgs={'ContentType': 'image/png'})

        # Generar URL prefirmada válida por 3 minutos
        imagen_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': filename},
            ExpiresIn=180
        )

        # Enviar SMS con Telnyx
        telnyx.api_key = settings.TELNYX_API_KEY
        nameCompany = getCompanyPerAgent(nameTemplate)

        if lang == 'en':
            messageContent = f'Welcome to {nameCompany}! Here is your personalized information.'
        else:
            messageContent = f'¡Bienvenido a {nameCompany}! Aquí está tu información personalizada.'

        telnyx.Message.create(
            from_='+17869848427',
            to=f'+{to_number}',
            text=messageContent,
            media_urls=[imagen_url]
        )

        # Borrar la imagen del bucket después de 3 minutos
        def eliminarImagenS3():
            try:
                s3.delete_object(Bucket=bucket, Key=filename)
                print(f"Imagen en S3 eliminada: {filename}")
            except Exception as e:
                print(f"Error al eliminar imagen en S3: {e}")

        threading.Timer(180.0, eliminarImagenS3).start()

#Funcion para enviar template static
def sendTemplateStatic(request, to_number, nameTemplate):
    imagen_url = None

    if request.method == 'POST':

        # Cargar imagen base
        imagen_base_path = os.path.join(settings.BASE_DIR, 'static', 'assets', 'images', 'template-images-static', f'{nameTemplate}.jpg')
        base = Image.open(imagen_base_path).convert("RGBA")

        # Guardar imagen combinada en memoria
        output = BytesIO()
        base.save(output, format='PNG')
        output.seek(0)

        # Subir imagen combinada a S3
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )

        bucket = settings.AWS_STORAGE_BUCKET_NAME
        timestamp = int(time.time())
        filename = f'temp-template/combinado_{timestamp}.png'

        s3.upload_fileobj(output, bucket, filename, ExtraArgs={'ContentType': 'image/png'})

        # Generar URL prefirmada válida por 3 minutos
        imagen_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': filename},
            ExpiresIn=180
        )

        # Enviar SMS con Telnyx
        telnyx.api_key = settings.TELNYX_API_KEY
        messageContent = f'¡Bienvenidos! Aquí está tu información personalizada.'

        telnyx.Message.create(
            from_='+17869848427',
            to=f'+{to_number}',
            text=messageContent,
            media_urls=[imagen_url]
        )

        # Borrar la imagen del bucket después de 3 minutos
        def eliminarImagenS3():
            try:
                s3.delete_object(Bucket=bucket, Key=filename)
                print(f"Imagen en S3 eliminada: {filename}")
            except Exception as e:
                print(f"Error al eliminar imagen en S3: {e}")

        threading.Timer(180.0, eliminarImagenS3).start()



