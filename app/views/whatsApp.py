# Standard Python libraries
from datetime import datetime, timedelta
from decimal import Decimal
import json
import requests
import re
import logging
import pandas as pd
import io
import stripe
import os

# Third-party libraries
from weasyprint import HTML
from requests.auth import HTTPBasicAuth

# Django utilities
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt

# Django core libraries
from django.utils import timezone
from django.utils.timezone import timedelta, now
import unicodedata

# Third-party imports
from twilio.rest import Client

# Application-specific imports
from app.modelsWhatsapp import *
from ..forms import *
from .utils import *
from .decoratorsCompany import *
from ..contextProcessors import validateSms
from .sms import disableAllUserCompany , paymend_recording, deactivatecontact, activatecontact, discountRemainingBalance


@login_required(login_url='/login')
def index(request):

    if request.user.is_superuser:
        chats = Chat_whatsapp.objects.all()
    elif request.user.is_staff:
        chats = Chat_whatsapp.objects.select_related('contact').filter(company=request.user.company).order_by('-last_message')
    else:
        chats = Chat_whatsapp.objects.select_related('contact').filter(agent_id=request.user.id).order_by('-last_message')

    chats = get_last_message_for_chats(chats)

    if request.method == 'POST':
        phoneNumber = request.POST.get('phoneNumber')
        name = request.POST.get('name', None)
        contact, created = createOrUpdatecontact(phoneNumber, request.user.company, name)
        chat = createOrUpdateChat(contact, request.user.company, request.user)
        return redirect('chatWatsapp', chat.id)
    return render(request, 'whatsapp/indexWhatsapp.html', {'chats': chats})

def get_last_message_for_chats(chats):
    """
    Función que enriquece los chats con información del último mensaje
    y cuenta los mensajes no leídos
    """
    for chat in chats:
        # Obtener el último mensaje del chat
        last_message = Messages_whatsapp.objects.filter(chat=chat).order_by('-created_at').first()
        
        # Contar mensajes no leídos
        unread_count = Messages_whatsapp.objects.filter(
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
            chat.has_attachment = hasattr(last_message, 'files')
            chat.is_message_unread = not last_message.is_read
        else:
            chat.last_message_content = "No hay mensajes"
            chat.last_message_time = None
            chat.has_attachment = False
            chat.is_message_unread = False
        
        # Agregar contador de mensajes no leídos
        chat.unread_messages = unread_count
    
    return chats

def createOrUpdatecontact(phoneNumber, company, name=None):
    # Intenta obtener o crear un contact
    contact, created = Contacts_whatsapp.objects.get_or_create(
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

def createOrUpdateChat(contact, company, agent=None):
    try:
        # Intenta obtener un chat existente para el contacte en la empresa especificada
        chat = Chat_whatsapp.objects.get(contact=contact.id, company=company)

        # Si se proporciona un nuevo agente, actualiza el chat
        if agent:
            chat.agent = agent
            chat.save()

    except Chat_whatsapp.DoesNotExist:
        # Si el chat no existe, crea uno nuevo
        if not agent:
            # Define un agente por defecto si no se proporciona (opcional)
            agent = Users.objects.get(id=1)  # ID de un agente genérico (En este caso sera el ID de Maria Carolina.)

        chat = Chat_whatsapp(
            agent=agent,
            contact=contact,
            company=company  # Asocia el chat con la compañía
        )
        chat.save()

    return chat

#verificar si se puede borrar
def verificationTemplate(chat):
    last_message = Messages_whatsapp.objects.filter(
        chat=chat,
        sender_type='C'  # C de Client
    ).order_by('-created_at').first()

    if not last_message:
        return True  # Nunca te ha escrito -> necesitas usar plantilla

    return last_message.created_at < datetime.datetime.now(timezone.utc) - timedelta(hours=24)

#verificar si esto se puede borrar
def sendTemplateWhatsapp(from_number, to_number):
    client = Client(settings.ACCOUNT_SID, settings.AUTH_TOKEN)

    try:
        message = client.messages.create(
            from_=f"whatsapp:+{from_number}",
            to=f"whatsapp:+{to_number}",
            content_sid="HX1070fc7e6dec1ce38634619b21f75d80",  # ← Reemplaza esto
            content_variables=json.dumps({
                "1": 'PRUEBA'  # Asigna la variable [first_name] (ej: "John")
            })
        )
        return True

    except Exception as e:
        return False

def sendWhatsapp(from_number, to_number, user, company, messageContent):

    client = Client(settings.ACCOUNT_SID, settings.AUTH_TOKEN)

    chat = Chat_whatsapp.objects.filter(contact__phone_number=to_number, company=company).first()

    # Enviar el mensaje
    message = client.messages.create(
        body=messageContent,
        from_=f"whatsapp:+{from_number}", #numero de what del client
        to=f"whatsapp:+{to_number}" #numero de what mio 320788
    )

    contact, created = createOrUpdatecontact(to_number, company)
    chat = createOrUpdateChat(contact, company)
    saveMessageInDb('Agent', messageContent, chat, user)

    if company.id not in [1,2]: #No descuenta el saldo a Lapeira
        discountRemainingBalance(company, '0.4')

    return True

def saveMessageInDb(inboundOrOutbound, message_content, chat, sender=None):
    message = Messages_whatsapp(
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

@login_required(login_url='/login')
def chat(request, chatId):
    validSms = validateSms(request)
   
    if not validSms or not validSms.get('whatsAppIsActive'):
        return render(request, "auth/404.html", {"message": "Perfil desactivado por falta de pago."})
    if request.method == 'POST':
        phoneNumber = request.POST.get('phoneNumber')
        name = request.POST.get('name', None)
        contact, created = createOrUpdatecontact(phoneNumber, request.user.company, name)
        chat = createOrUpdateChat(contact, request.user.company, request.user)
        return redirect('chatWatsapp', chat.id)
            
    if request.user.is_superuser:
        chat = Chat_whatsapp.objects.select_related('contact').get(id=chatId)
    else:
        chat = Chat_whatsapp.objects.select_related('contact').get(id=chatId, company=request.user.company)
        
    # Usamos select_related para optimizar las consultas
    messages = Messages_whatsapp.objects.filter(chat=chat.id).select_related('files_whatsapp')

    def normalize_text(text):
        # elimina tildes y pasa a mayúsculas
        text = unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode("utf-8")
        return text.strip().upper()


    # Traer el último mensaje del cliente en ese chat para validar su autorization
    last_msg = Messages_whatsapp.objects.filter(chat=chat, sender_type="Client").order_by("-created_at").first()
    authorization = False
    if last_msg:
        normalized = normalize_text(last_msg.message_content)
        if normalized in ["SI", "SÍ", "Si", "sI","si"]: 
            authorization = True

    #validar si el chat lleva mas de 24h para usar plantilla o no 
    limite = timezone.now() - timedelta(hours=23, minutes=59)
    validationSMS = Messages_whatsapp.objects.filter(chat=chat.id, sender__isnull=False).order_by('-created_at').first()
    result = True if not validationSMS else validationSMS.created_at < limite
    
    # Creamos una lista para almacenar los mensajes con sus archivos
    messages_with_files = []
    for message in messages:
        message_dict = {
            'id': message.id,
            'sender_type': message.sender_type,
            'sender': message.sender,
            'message_content': message.message_content,
            'created_at': message.created_at,
            'is_read': message.is_read,
            'file': None
        }

        # Intentamos obtener el archivo asociado
        try:
            message_dict['file'] = message.files_whatsapp
        except Files_whatsapp.DoesNotExist:
            pass
            
        messages_with_files.append(message_dict)
    messages.update(is_read=True)

    if request.user.is_superuser:
        chats = Chat_whatsapp.objects.all()
    elif request.user.is_staff:
        chats = Chat_whatsapp.objects.select_related('contact').filter(company=request.user.company).order_by('-last_message')
    else:
        chats = Chat_whatsapp.objects.select_related('contact').filter(agent_id=request.user.id).order_by('-last_message')
        
    chats = get_last_message_for_chats(chats)
    context = {
        "whatsapp_url": f"/chatWatsapp/{chatId}/",
        'contact': chat.contact,
        'chats': chats,
        'messages': messages_with_files,
        'authorization':authorization,
        'resultValidationTemplate':result
    }
    return render(request, 'whatsapp/chat.html', context)

@csrf_exempt
def whatsappReply(request, company_id):
    if request.method == 'POST':
        from_number = request.POST.get('From', '')
        messageBody = request.POST.get('Body', '').strip()
        numMedia = int(request.POST.get('NumMedia', 0))

        try:
            company = Companies.objects.get(id=company_id)

            # Extraer solo el número sin 'whatsapp:'
            phone_number = from_number.replace('whatsapp:', '')

            # Crear o actualizar el contacto y el chat
            contact, created = createOrUpdatecontact(int(phone_number), company)
            chat = createOrUpdateChat(contact, company)

            # Si hay medios (imágenes, por ejemplo)
            if numMedia > 0:  
                media_url = request.POST.get('MediaUrl0', '')
                media_type = request.POST.get('MediaContentType0', '')

                if media_url:
                    response = requests.get(media_url, auth=HTTPBasicAuth(settings.ACCOUNT_SID, settings.AUTH_TOKEN))

                    if response.status_code == 200:
                        file_name = os.path.basename(media_url)
                        file_content = ContentFile(response.content, name=file_name)

                        # ✅ Primero guarda el mensaje sin texto
                        message = saveMessageInDb('Client', '', chat)

                        # ✅ Luego guarda el archivo asociado al mensaje
                        media_file = Files_whatsapp(
                            file=file_content,
                            message=message
                        )
                        media_file.save()

                        # Enviar el mensaje al WebSocket como imagen
                        enviar_por_websocket(
                            tipo_mensaje='imagen',
                            datos={ 'texto': media_file.file.url  },
                            contacto=contact,
                            empresa_id=company.id,
                            url_media = media_file.file.url,
                            sender="client" 
                        )

            else:
                # Si es un mensaje de texto, guardamos el mensaje
                message = saveMessageInDb('Client', messageBody, chat)

                # Activar o desactivar el contacto según el mensaje
                if not contact.is_active:
                    activatecontact(contact, messageBody)
                else:
                    deactivatecontact(contact, messageBody)

                # Enviar el mensaje al WebSocket como texto
                enviar_por_websocket(
                    tipo_mensaje='texto',
                    datos={
                        'texto': messageBody,
                        'url_media': None
                    },
                    contacto=contact,
                    empresa_id=company.id,
                    sender="client" 
                )

                      

            # Aplica descuento si corresponde
            if company.id not in [1, 2]:
                discountRemainingBalance(company, '0.03')  # Puedes ajustar según tarifa

            return HttpResponse("ERES EL MEJOR", status=200)

        except Exception as e:
            return HttpResponse("❌ Error interno del servidor", status=500)

    elif request.method == 'GET':
        return HttpResponse("Webhook configurado correctamente", status=200)

    return HttpResponse("Método no soportado", status=405)

def enviar_por_websocket(tipo_mensaje, datos, contacto, empresa_id, url_media=None, sender='Agent'):
    capa_canal = get_channel_layer()
    nombre_sala = f"whatsapp_{contacto.phone_number}_empresa_{empresa_id}"

    if tipo_mensaje == 'imagen':
        async_to_sync(capa_canal.group_send)(
            nombre_sala,
            {
                'type': 'mensaje_media',
                'url_media': url_media,
                'usuario': f"{contacto.name}",
                'fecha': timezone.localtime().strftime('%Y-%m-%d %H:%M:%S'),
                'sender': sender  # Ahora por defecto será "agent"
            }
        )
    else:
        async_to_sync(capa_canal.group_send)(
            nombre_sala,
            {
                'type': 'mensaje_texto',
                'mensaje': datos.get('texto'),
                'usuario': f"{contacto.name}",
                'fecha': timezone.localtime().strftime('%Y-%m-%d %H:%M:%S'),
                'sender': sender  # Ahora por defecto será "agent"
            }
        )

@csrf_exempt
def sendWhatsappConversation(request):
    if comprobate_company(request.user.company):
        return JsonResponse({'message':'No money'})
    
    client = Client(settings.ACCOUNT_SID, settings.AUTH_TOKEN)

    # Enviar el mensaje
    message = client.messages.create(
        body=request.POST['messageContent'],
        from_=f"whatsapp:+{request.user.assigned_phone_whatsapp.phone_number}", #numero de what del client
        to=f"whatsapp:+{request.POST['phoneNumber']}" #numero de what mio 320788
    )
    contact, created = createOrUpdatecontact(request.POST['phoneNumber'], request.user.company)
    if request.user.role == 'Customer':
        chat = createOrUpdateChat(contact, request.user.company)
    else:
        chat = createOrUpdateChat(contact, request.user.company, request.user)
    saveMessageInDb('Agent', request.POST['messageContent'], chat, request.user)
    
    return JsonResponse({'message':'ok'})

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
    
@csrf_exempt   
def template(request, contact_id):
    try:
        contact = Contacts_whatsapp.objects.get(id=contact_id)
        chat = Chat_whatsapp.objects.get(contact = contact)

        from_number = request.user.assigned_phone_whatsapp.phone_number
        to_number = contact.phone_number

        client = Client(settings.ACCOUNT_SID, settings.AUTH_TOKEN)

        data = json.loads(request.body)
        type_param = data.get('type')  # Obtienes el valor de 'type'

        try:
            variables_dict = None
            content_sid = None
            
            if type_param == 'authorization':
                variables_dict = {
                    "1": contact.name,
                    "2": "Lapeira & Associates LLC",
                    "3": "Menos de 24 horas"
                }
                content_sid = settings.AUTHORIZATION

            elif type_param == 'activation':
                variables_dict = {
                    "1": contact.name
                }
                content_sid = settings.CUSTOMER

            if variables_dict and content_sid:
                message = client.messages.create(
                    from_=f"whatsapp:+{from_number}",
                    to=f"whatsapp:+{to_number}",
                    content_sid=content_sid,
                    content_variables=json.dumps(variables_dict)
                )

                saveMessageInDb('Agent', f"template-{type_param}", chat, request.user)

                return JsonResponse({'message': 'ok'}, status=200)

            return JsonResponse({'error': 'Datos insuficientes para enviar el mensaje.'}, status=400)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


    except Exception as e:
        return JsonResponse({'message': 'error', 'details': str(e)}, status=500)

def deleteContactWhatsApp(request, id):
    if request.user.is_superuser or request.user.role == 'Admin':
        contact = Contacts_whatsapp.objects.get(id=id)
        contact.delete()
    return redirect(index)
