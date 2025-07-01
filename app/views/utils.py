# Standard Python libraries
import logging
import smtplib
import ssl
from email.message import EmailMessage
from typing import Dict

# Django core libraries
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt


# Django utilities
from django.http import JsonResponse
from django.template.loader import render_to_string

# Third-party libraries
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer  

# Application-specific imports
from app.models import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def format_decimal(number):
    # Revisa si el numero es entero y lo devuelve entero
    if number.is_integer():
        return int(number)
    
    # Si es decimal lo devuelve con dos numeros despues del punto
    return round(number, 2)

#Websocket
def notify_websocket(user_id):
    """
    Función que notifica al WebSocket de un cambio, llamando a un consumidor específico.
    """
    channel_layer = get_channel_layer()

    # Llamamos al WebSocket para notificar al usuario que su plan fue agregado
    async_to_sync(channel_layer.group_send)(
        "user_updates",  # El nombre del grupo de WebSocket
        {
            "type": "user_update",  # Tipo de mensaje que enviamos
            "user_id": user_id,  # ID del usuario al que notificamos
            "message": "Nuevo plan agregado"
        }
    )

#Email
def send_email(subject: str, receiver_email: str, template_name: str, context_data: Dict) -> bool:
    """
    Envía un email usando templates de Django.
    
    Args:
        subject: Asunto del correo
        receiver_email: Email del destinatario
        template_name: Nombre del template (sin .html)
        context_data: Datos para el template
    
    Example:
        send_email(
            subject="Bienvenido",
            receiver_email="usuario@ejemplo.com",
            template_name="email_templates/welcome",
            context_data={"name": "Juan", "company": "Mi Empresa"}
        )
    """
    try:
        # Renderizar el template usando el sistema de templates de Django
        html_content = render_to_string(f'{template_name}.html', context_data)
        
        # Crear el mensaje
        message = EmailMessage()
        message['Subject'] = subject
        message['From'] = settings.SENDER_EMAIL_ADDRESS
        message['To'] = receiver_email
        message.set_content(html_content, subtype='html')
        
        # Enviar el email
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, context=context) as server:
            server.login(settings.SENDER_EMAIL_ADDRESS, settings.EMAIL_PASSWORD)
            server.send_message(message)
            logger.info(f"Email enviado exitosamente a {receiver_email}")
            return True
            
    except smtplib.SMTPAuthenticationError:
        logger.error("Error de autenticación SMTP")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"Error SMTP: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        return False
    
@csrf_exempt
def toggleDarkMode(request):
    try:
        userPreference = UserPreference.objects.get(user_id=request.user.id)
        darkMode = True if request.POST.get('theme').lower() == "true" else False
        userPreference.darkMode = darkMode
        userPreference.save()
    except:
        userPreference = UserPreference.objects.create(
            user = request.user,
            darkMode = True
        )
    return JsonResponse({'message':'success'})

def renderMessageTemplate(template_str, context):
    try:
        return template_str.format(**context)
    except KeyError as e:
        return f"Error: faltó la variable {e}"
    

from weasyprint import HTML
import boto3
from io import BytesIO
from django.test.client import RequestFactory

def crearRequest(user):
    request = RequestFactory().get("/")
    request.user = user
    request.company_id = user.company.id
    return request

def transformar_summary(finalSummary):
    resultado = []

    for name, data in finalSummary.items():
        weeks = []
        for i in range(1, 7):
            key = f"Week{i}"
            semana = data.get(key, {
                "obama": 0, "activeObama": 0, "supp": 0, "activeSupp": 0, "total": 0
            })
            weeks.append(semana)
        resultado.append({"name": name, "weeks": weeks})

    return resultado


def sale6Week(finalSummary, weekRanges):
    summary_transformado = transformar_summary(finalSummary)

    html = render_to_string("reporte_6_semanas.html", {
        'summary': summary_transformado,
        'weekRanges': weekRanges,
    })

    buffer = BytesIO()
    HTML(string=html).write_pdf(buffer)
    buffer.seek(0)

    filename = f"reporte_ventas_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME
    )

    s3.upload_fileobj(
        buffer,
        settings.AWS_STORAGE_BUCKET_NAME,
        f"reports/{filename}",
        ExtraArgs={'ContentType': 'application/pdf', 'ACL': 'public-read'}
    )

    url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/reports/{filename}"
    return url
