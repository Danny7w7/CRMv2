from django.conf import settings
import requests
import telnyx
from django.core.files.base import ContentFile

from celery import shared_task
from datetime import datetime, date
from celery.utils.log import get_task_logger

from app.models import *
from app.views.consents import getCompanyPerAgent
from app.views.sms import sendIndividualsSms, comprobate_company
from app.utils import generateWeeklyPdf, uploadTempUrl

logger = get_task_logger(__name__)

@shared_task
def my_daily_task():
    now = datetime.now().date()
    # Filtramos los clientes que cumplen años hoy, ignorando el año
    birthdayClients = Clients.objects.filter(
        date_birth__month=now.month,
        date_birth__day=now.day
    )

    for clientBlue in birthdayClients:
        lines = clientBlue.agent_usa.split("\n")
        agentFirstName = lines[0].split()[0] 
        clientSms = Clients.objects.filter(phone_number=clientBlue.phone_number).first()

        if clientSms:
            chat = Chat.objects.select_related('agent').filter(contact_id=clientSms.id).first()

            sendIndividualsSms(
                chat.agent.assigned_phone.phone_number,
                clientBlue.phone_number,
                Users.objects.get(id=1),
                clientSms.company,
                f'¡Feliz cumpleaños, {clientBlue.first_name} {clientBlue.last_name}! 🎉 \nTodo el equipo de {getCompanyPerAgent(agentFirstName)} le desea un año lleno de salud, éxitos y bienestar. \nRecuerde que su agente de seguros, {clientBlue.agent_usa}, está siempre disponible para apoyarle con su póliza. \n¡Que tenga un día maravilloso! 🌟'
            )

@shared_task
def smsPayment():
    now = datetime.now().date()
    payments = paymentDate.objects.select_related('obamacare__client__agent', 'supp__client__agent').filter(
        payment_date__month=now.month,
        payment_date__day=now.day,
    )

    for payment in payments:
        if payment.obamacare or payment.supp:
            plan = payment.supp or payment.obamacare

        if not plan:  # Si no hay plan, continuar con el siguiente plan
            break

        lines = plan.agent_usa.split("\n")
        agentFirstName = lines[0].split()[0]

        if plan.client:
            company = plan.client.company  # Obtén la empresa asociada al cliente

            if not comprobate_company(company):
                message =f'Hola {plan.client.first_name} {plan.client.last_name} 👋,{getCompanyPerAgent(agentFirstName)} le recuerda que su pago de ${plan.premium} de su póliza de {plan.carrier} se vence en 2 días. 💚'

                sendIndividualsSms(
                    plan.client.agent.assigned_phone.phone_number,
                    plan.client.phone_number,
                    Users.objects.get(id=1),
                    plan.client.company,
                    message
                )

# @shared_task
# def reportBoosLapeira():

#     now = timezone.now()
#     yesterday = now - timedelta(days=1)

#     # Establecer rangos: inicio y fin del día de ayer
#     start_date = timezone.make_aware(datetime(yesterday.year, yesterday.month, yesterday.day, 0, 0, 0))
#     end_date = timezone.make_aware(datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59, 999999))

#     #consulta base
#     obama = ObamaCare.objects.select_related('agent').filter(created_at__range=(start_date, end_date),company = 2)
#     supp = Supp.objects.select_related('agent').filter(created_at__range=(start_date, end_date),company = 2)
#     medicare = Medicare.objects.filter(created_at__range=(start_date, end_date),company = 2)
#     assure = ClientsAssure.objects.filter(created_at__range=(start_date, end_date),company = 2)
#     lifeInsurance = ClientsLifeInsurance.objects.filter(created_at__range=(start_date, end_date),company = 2)

#     telnyx.api_key = settings.TELNYX_API_KEY    

#     if obama.exists():
#         mensageObama = '📄 ObamaCare\n'
#         for index, policy in enumerate(obama, start=1):
#             mensageObama += (
#                 f'Póliza #{index}:\n'
#                 f'Agente: {policy.agent.first_name}\n'
#                 f'Estado: {policy.status}\n'
#                 f'Fecha: {policy.created_at.strftime("%d de %B")}\n\n'
#             )      
        
#         telnyx.Message.create(
#             from_=f'+17869848427', # Your Telnyx number
#             to=f'+13052199932', # numero del jefe
#             text= mensageObama
#         )

#     if supp.exists():
#         mensageSupp = '📄 Supp\n'
#         for index, policy in enumerate(supp, start=1):
#             mensageSupp += (
#                 f'Póliza #{index}:\n'
#                 f'Agente: {policy.agent.first_name}\n'
#                 f'Estado: {policy.status}\n'
#                 f'Fecha: {policy.created_at.strftime("%d de %B")}\n\n'
#             )      
        
#         telnyx.Message.create(
#             from_=f'+17869848427', # Your Telnyx number
#             to=f'+13052199932', # numero del jefe
#             text= mensageSupp
#         )

#     if medicare.exists():

#         mensageMedicare = '📄 Medicare\n'
#         for index, policy in enumerate(medicare, start=1):
#             mensageMedicare += (
#                 f'Póliza #{index}:\n'
#                 f'Agente: {policy.agent.first_name}\n'
#                 f'Estado: {policy.status}\n'
#                 f'Fecha: {policy.created_at.strftime("%d de %B")}\n\n'
#             )      
        
#         telnyx.Message.create(
#             from_=f'+17869848427', # Your Telnyx number
#             to=f'+13052199932', # numero del jefe
#             text= mensageMedicare
#         )
    
#     if assure.exists():

#         mensageAssure = '📄 Assure\n'
#         for index, policy in enumerate(assure, start=1):
#             mensageAssure += (
#                 f'Póliza #{index}:\n'
#                 f'Agente: {policy.agent.first_name}\n'
#                 f'Estado: {policy.status}\n'
#                 f'Fecha: {policy.created_at.strftime("%d de %B")}\n\n'
#             )      
        
#         telnyx.Message.create(
#             from_=f'+17869848427', # Your Telnyx number
#             to=f'+13052199932', # numero del jefe
#             text= mensageAssure
#         )

#     if lifeInsurance.exists():

#         mensageLife = '📄 Life Insurance\n'
#         for index, policy in enumerate(lifeInsurance, start=1):
#             mensageLife += (
#                 f'Póliza #{index}:\n'
#                 f'Agente: {policy.agent.first_name}\n'
#                 f'Estado: {policy.status}\n'
#                 f'Fecha: {policy.created_at.strftime("%d de %B")}\n\n'
#             )      
        
#         telnyx.Message.create(
#             from_=f'+17869848427', # Your Telnyx number
#             to=f'+13052199932', # numero del jefe
#             text= mensageLife
#         )

@shared_task
def reportBoosLapeira():
    week_number = date.today().isocalendar()[1]

    # 1. Generar PDF
    local_path, filename = generateWeeklyPdf(week_number)

    # 2. Subir a S3 y generar link temporal
    s3_key = f'reportes/{filename}'
    url_temporal = uploadTempUrl(local_path, s3_key)

    # 3. Enviar por Telnyx MMS
    telnyx.api_key = settings.TELNYX_API_KEY
    telnyx.Message.create(
        from_='+17869848427',
        to='+13052199932',
        text='Reporte de la semana actual generado automáticamente.',
        subject='Reporte PDF',
        media_urls=[url_temporal]
    )

    

@shared_task
def saveImageFromUrlTask(messageId, payload, contactId, companyId):
    from .models import FilesSMS, Messages, Companies, Contacts
    from .views.sms import SendMessageWebsocketChannel, discountRemainingBalance
    import logging

    logger = logging.getLogger(__name__)

    try:
        message = Messages.objects.get(id=messageId)
        contact = Contacts.objects.get(id=contactId)
        company = Companies.objects.get(id=companyId)

        media = payload.get('media', [])
        if not media:
            return

        url = media[0].get('url')
        filename = url.split('/')[-1]

        response = requests.get(url)
        response.raise_for_status()

        file = FilesSMS()
        file.message = message
        file.file.save(filename, ContentFile(response.content), save=True)

        fileUrl = file.file.url

        # Enviar por WebSocket una vez se tiene la imagen
        SendMessageWebsocketChannel('MMS', payload, contact, companyId, fileUrl)

        if companyId not in [1, 2]:
            discountRemainingBalance(company, '0.027')

    except Exception as e:
        logger.error(f'Error saving MMS image or sending WebSocket: {e}')