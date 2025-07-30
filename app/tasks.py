import logging
from django.conf import settings
import requests
import telnyx
from django.core.files.base import ContentFile
from django.db.models import Q

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
                '+17869848427',
                clientBlue.phone_number,
                Users.objects.get(id=1),
                clientSms.company,
                f'¡Feliz cumpleaños, {clientBlue.first_name} {clientBlue.last_name}! 🎉 \nTodo el equipo de {getCompanyPerAgent(agentFirstName)} le desea un año lleno de salud, éxitos y bienestar. \nRecuerde que su agente de seguros, {clientBlue.agent_usa}, está siempre disponible para apoyarle con su póliza. \n¡Que tenga un día maravilloso! 🌟'
            )

@shared_task
def smsPayment():

    status = ['ACTIVE','ENROLLED','SELF-ENROLMENT']
    statusSupp = ['ACTIVE', 'PAYMENT PROCESS (PENDING)']

    now = datetime.now().date()
    payments = PaymentDate.objects.select_related(
        'obamacare__client__agent__assigned_phone',
        'supp__client__agent__assigned_phone',
        'assure__agent__assigned_phone',
        'life_insurance__agent__assigned_phone'
    ).filter(
        (
            Q(obamacare__isnull=False) |
            Q(supp__isnull=False) |
            Q(assure__isnull=False) |
            Q(life_insurance__isnull=False)
        ), 
        payment_date__month=now.month, 
        payment_date__day=now.day,
    ).exclude(

        # (Obamacare es inactivo O su estado NO está en la lista 'status')
        Q(obamacare__is_active=False) | ~Q(obamacare__status__in=status) |
        # O (Supp es inactivo)
        Q(supp__is_active=False) | ~Q(supp__status__in=statusSupp) |
        # O (Assure es inactivo)
        Q(assure__is_active=False) |
        # O (Life Insurance es inactivo)
        Q(life_insurance__is_active=False)
    )

    for payment in payments:
        plan = None
        plan_type = None # Para depuración, si quieres saber qué tipo de plan es

        if payment.obamacare:
            plan = payment.obamacare
            plan_type = 'Obamacare'
        elif payment.supp:
            plan = payment.supp
            plan_type = 'Supp'
        elif payment.assure:
            plan = payment.assure
            plan_type = 'Assure'
        elif payment.life_insurance:
            plan = payment.life_insurance
            plan_type = 'Life Insurance'

        if not plan:
            # Si un PaymentDate no está asociado a NINGÚN plan, lo saltamos.
            #print(f"DEBUG: PaymentDate ID {payment.id} para {payment.payment_date} no tiene ningún plan asociado. Saltando.")
            break

        # --- Verificaciones de existencia para la cadena de relaciones ---
        # Estas verificaciones son cruciales para evitar el AttributeError
        if not hasattr(plan, 'client') or not plan.client:
            #print(f"DEBUG: Plan {plan_type} ID {plan.id} no tiene cliente. Saltando.")
            break

        if not hasattr(plan.client, 'agent') or not plan.client.agent:
            #print(f"DEBUG: Cliente {plan.client.id} de Plan {plan_type} ID {plan.id} no tiene agente. Saltando.")
            break

        # Asegurarse de que el agente tenga un 'assigned_phone' si es un campo ForeignKey
        if not hasattr(plan.client.agent, 'assigned_phone') or not plan.client.agent.assigned_phone:
            #print(f"DEBUG: Agente {plan.client.agent.id} de Plan {plan_type} ID {plan.id} no tiene teléfono asignado. Saltando.")
            break

        # --- Si todo existe, procedemos con el envío del SMS ---
        try:
            
            client_phone_number = plan.client.phone_number


            lines = plan.agent_usa.split("\n")
            agentFirstName = lines[0].split()[0] # Esto podría fallar si lines[0] está vacío

            company = plan.client.company 

            if not comprobate_company(company):
                message = f'Hola {plan.client.first_name} {plan.client.last_name} 👋,{getCompanyPerAgent(agentFirstName)} le recuerda que su pago de ${plan.premium} de su póliza de {plan.carrier} se vence en 2 días. 💚'

                sendIndividualsSms(
                    '+17869848427',
                    client_phone_number,
                    Users.objects.get(id=1), # Asegúrate de que este usuario con ID 1 siempre exista
                    plan.client.company,
                    message
                )
                #print(f"DEBUG: SMS enviado para Plan {plan_type} ID {plan.id}, Cliente: {plan.client.first_name} {plan.client.last_name}")

        except AttributeError as e:
            print(f"ERROR: AttributeError al procesar el Plan {plan_type} ID {plan.id} (posible campo faltante): {e}")
        except IndexError as e:
            # Esto captura si lines[0] es vacío o no se puede dividir (e.g., plan.agent_usa está vacío)
            print(f"ERROR: IndexError al obtener agentFirstName para Plan {plan_type} ID {plan.id}: {e}")
        except Exception as e:
            print(f"ERROR: Error inesperado al procesar el Plan {plan_type} ID {plan.id}: {e}")

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

@shared_task
def reportCustomerWeek():

    # 1. Obtener los datos
    partes_sms = dataQuery() 

    # 2. Generar PDF
    now = datetime.now()
    filename = f"reporte_test_{now.strftime('%Y%m%d_%H%M%S')}.pdf"
    local_path = f"/tmp/{filename}"
    generarPDFChart(partes_sms, local_path)

    # 3. Subir a S3
    s3_key = f"reportes/{filename}"
    s3_url = uploadTempUrl(local_path, s3_key)

    mensaje_sms = (
        f"📄 Reporte Semanal Generado\n"
        f"📅 {now.strftime('%d/%m/%Y %H:%M')}\n\n" +
        f"📎 PDF completo adjunto"
    )

    # 4. Enviar por Telnyx MMS
    telnyx.api_key = settings.TELNYX_API_KEY
    recipient = ['+13052199932','+13052190572']
    for item in recipient:
        telnyx.Message.create(
            from_='+17869848427',
            to=item,
            text=mensaje_sms,
            subject='Reporte PDF Semanal Customer',
            media_urls=[s3_url]
        )

    # 5. Enviar por Email - TODO INTEGRADO AQUÍ
    try:
        
        # Leer el PDF como bytes
        with open(local_path, 'rb') as pdf_file:
            pdf_content = pdf_file.read()
        
        # Configurar el mensaje del email
        email_subject = f"📄 Reporte Semanal Customer - {now.strftime('%d/%m/%Y')}"
        email_body = f"""Estimado/a,

            Se ha generado el reporte semanal correspondiente al {now.strftime('%d de %B de %Y a las %H:%M')}.

            El archivo PDF con el reporte completo del equipo de customer de la semana actual se encuentra adjunto a este correo.

            Reporte Generado por el mejor equipo de IT.

            Saludos cordiales,
            Sistema de Reportes
            """
        
        # Crear el mensaje de email
        message = EmailMessage()
        message['Subject'] = email_subject
        message['From'] = settings.SENDER_EMAIL_ADDRESS
        message['To'] = 'Jlhernandezt.88@gmail.com'
        message.set_content(email_body)

        # Adjuntar el PDF
        message.add_attachment(
            pdf_content,
            maintype='application',
            subtype='pdf',
            filename=filename
        )
        
        # Enviar el email usando SMTP_SSL
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(settings.SMTP_HOST, int(settings.SMTP_PORT), context=context) as server:
            server.login(settings.SENDER_EMAIL_ADDRESS, settings.EMAIL_PASSWORD)
            server.send_message(message)

    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Error de autenticación SMTP: {str(e)}")
        logger.error(f"Error de autenticación SMTP: {str(e)}")
    except smtplib.SMTPException as e:
        print(f"❌ Error SMTP: {str(e)}")
        logger.error(f"Error SMTP: {str(e)}")
    except Exception as e:
        print(f"❌ Error inesperado al enviar email: {str(e)}")
        logger.error(f"Error inesperado al enviar email: {str(e)}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")

    # 6. Limpiar archivos temporales
    if os.path.exists(local_path):
        os.remove(local_path)

    # Eliminar imágenes generadas
    llamadas_img_path = partes_sms[0]
    user_carrier_img_path = partes_sms[1]
    for path in [llamadas_img_path, user_carrier_img_path]:
        if os.path.exists(path):
            os.remove(path)

@shared_task
def report6Week():
    now = datetime.now()
    filename = f"reporte_graficos_{now.strftime('%Y%m%d_%H%M%S')}.pdf"
    local_pdf_path = f"/tmp/{filename}"

    # 1. Generar gráficos
    charts_paths = generate_weekly_chart_images()

    # 2. Generar PDF desde HTML
    generarPDFChart6Week(charts_paths, local_pdf_path)

    # 3. Subir a S3 y generar URL temporal
    s3_key = f"reportes/{filename}"
    s3_url = uploadTempUrl(local_pdf_path, s3_key)

    # 4. Enviar SMS vía Telnyx
    telnyx.api_key = settings.TELNYX_API_KEY
    mensaje_sms = (
        f"📄 Reporte Semanal Generado\n"
        f"📅 {now.strftime('%d/%m/%Y %H:%M')}\n\n"
        f"📎 PDF completo adjunto"
    )

    telnyx.Message.create(
        from_='+17869848427',
        to='+17863034781',
        text=mensaje_sms,
        subject='Reporte PDF Semanal Customer',
        media_urls=[s3_url]
    )

    # 5. Limpiar archivos temporales
    for path in charts_paths + [local_pdf_path]:
        if os.path.exists(path):
            os.remove(path)


@shared_task
def xxxxxxx():
    now = datetime.now()
    filename = f"reporte_graficos_{now.strftime('%Y%m%d_%H%M%S')}.pdf"
    local_pdf_path = f"/tmp/{filename}"

    # 1. Generar gráficos
    charts_paths = generate_weekly_chart_images_two()

    # 2. Generar PDF desde HTML
    generarPDFChart6Week_two(charts_paths, local_pdf_path)

    # 3. Subir a S3 y generar URL temporal
    s3_key = f"reportes/{filename}"
    s3_url = uploadTempUrl(local_pdf_path, s3_key)

    # 4. Enviar SMS vía Telnyx
    telnyx.api_key = settings.TELNYX_API_KEY
    mensaje_sms = (
        f"📄 Reporte Semanal Generado\n"
        f"📅 {now.strftime('%d/%m/%Y %H:%M')}\n\n"
        f"📎 PDF completo adjunto"
    )

    telnyx.Message.create(
        from_='+17869848427',
        to='+17863034781',
        text=mensaje_sms,
        subject='Reporte PDF Semanal Customer',
        media_urls=[s3_url]
    )

    # 5. Limpiar archivos temporales
    for path in charts_paths + [local_pdf_path]:
        if isinstance(path, str) and os.path.exists(path):
            os.remove(path)


