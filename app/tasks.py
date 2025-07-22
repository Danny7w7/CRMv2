import logging
from django.conf import settings
import requests
import telnyx
from django.core.files.base import ContentFile

from celery import shared_task
from datetime import datetime, date
from celery.utils.log import get_task_logger

from app.models import *
from app.views.consents import getCompanyPerAgent
from app.views.reports.table import table6Week
from app.views.sms import sendIndividualsSms, comprobate_company, SendMessageWebsocketChannel, discountRemainingBalance
from app.utils import generateWeeklyPdf, uploadTempUrl
from app.views.utils import *

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
    payments = PaymentDate.objects.select_related('obamacare__client__agent', 'supp__client__agent').filter(
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
    recipient = ['+13052199932','+13052190572']
    for item in recipient:
        telnyx.Message.create(
            from_='+17869848427',
            to=item,
            text='Reporte de la semana actual generado automáticamente.',
            subject='Reporte PDF',
            media_urls=[url_temporal]
        )
   
@shared_task
def saveImageFromUrlTask(messageId, payload, contactId, companyId):
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

@shared_task
def enviar_pdf_por_email():
    user = Users.objects.filter(id=56).first()
    if not user:
        return

    request = create_request(user)
    finalSummary, weekRanges = table6Week(request)
    finalSummary = completar_summary_con_assure_medicare_life(finalSummary, request.company_id)
    detalles_clientes = get_customer_details(request.company_id)

    # ✅ Generar el PDF
    pdf_bytes = sale6Week(finalSummary, weekRanges, detalles_clientes)

    # ✅ Enviar el email
    send_email_with_pdf(
        subject="Reporte de Ventas - Últimas 6 Semanas",
        receiver_email=['luis4007@gmail.com','ginapao2310@hotmail.com'], # ✅ solo para el texto del cuerpo
        pdf_content=pdf_bytes  # ✅ nombre del parámetro como te lo dejé
    )

# @shared_task
# def test():

#     smsAll = dataQuery()

#     # 3. Enviar por Telnyx MMS
#     telnyx.api_key = settings.TELNYX_API_KEY

#     for sms in smsAll:
#         telnyx.Message.create(
#             from_='+17869848427',
#             to='+17863034781',
#             text=sms
#         )

from celery import shared_task
from django.conf import settings
from reportlab.pdfgen import canvas
import telnyx
import os
from datetime import datetime
import boto3

from celery import shared_task
from django.conf import settings
from reportlab.pdfgen import canvas
import telnyx
import boto3
from io import BytesIO
from datetime import datetime

@shared_task
def test():
    # 1. Obtener datos
    mensajes = dataQuery()
    contenido = "\n\n".join(mensajes)

    # 2. Crear PDF en memoria
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer)
    text = c.beginText(40, 800)
    text.setFont("Helvetica", 10)

    for linea in contenido.split('\n'):
        text.textLine(linea)

    c.drawText(text)
    c.showPage()
    c.save()
    pdf_buffer.seek(0)

    # 3. Subir a S3 (sin ACL)
    nombre_archivo = f"mms_reports/reporte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME
    )

    s3.upload_fileobj(
        pdf_buffer,
        settings.AWS_STORAGE_BUCKET_NAME,
        nombre_archivo,
        ExtraArgs={
            'ContentType': 'application/pdf'
            # ⚠️ NO INCLUIMOS 'ACL': 'public-read'
        }
    )

    # 4. Generar URL pública (debes asegurarte que el bucket lo permita)
    url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{nombre_archivo}"

    # 5. Enviar el MMS
    telnyx.api_key = settings.TELNYX_API_KEY

    telnyx.Message.create(
        from_='+17869848427',  # Tu número Telnyx
        to='+17863034781',     # Número destino
        text='📄 Reporte semanal adjunto.',
        media_urls=[url]
    )


