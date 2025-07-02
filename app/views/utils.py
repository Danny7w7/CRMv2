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

from weasyprint import HTML
import boto3
from io import BytesIO
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
import matplotlib.pyplot as plt
import base64
import tempfile
import os
from weasyprint import HTML, CSS

def generar_grafico_base64(nombre, semanas, data):
    import matplotlib.pyplot as plt
    import numpy as np
    from io import BytesIO
    import base64

    fig, ax1 = plt.subplots(figsize=(13, 7))  # 📏 Más grande

    x = np.arange(len(semanas))
    bar_width = 0.18

    # Barras
    bars_aca = ax1.bar(x - 1.5 * bar_width, data["ACA"], width=bar_width, label="ACA", color="#3498db")
    bars_act_aca = ax1.bar(x - 0.5 * bar_width, data["Act ACA"], width=bar_width, label="Act ACA", color="#2ecc71")
    bars_supp = ax1.bar(x + 0.5 * bar_width, data["Supp"], width=bar_width, label="Supp", color="#f1c40f")
    bars_act_supp = ax1.bar(x + 1.5 * bar_width, data["Act Supp"], width=bar_width, label="Act Supp", color="#e67e22")

    # Línea Total
    ax1.plot(x, data["Total"], color="black", marker="o", linestyle="--", linewidth=2, label="Total")

    # Etiquetas de barras
    def label_bars(bars):
        for bar in bars:
            height = bar.get_height()
            ax1.annotate(f'{height}',
                         xy=(bar.get_x() + bar.get_width() / 2, height),
                         xytext=(0, 4),
                         textcoords="offset points",
                         ha='center', va='bottom', fontsize=9)

    for bars in [bars_aca, bars_act_aca, bars_supp, bars_act_supp]:
        label_bars(bars)

    # 🔼 Etiquetas para puntos de la línea (por encima del punto)
    for i, val in enumerate(data["Total"]):
        ax1.annotate(f'{val}',
                     xy=(x[i], val),
                     xytext=(0, 10),  # ➕ está ahora por encima
                     textcoords="offset points",
                     ha='center', va='bottom',
                     fontsize=9, color='black', weight='bold')

    ax1.set_xticks(x)
    ax1.set_xticklabels(semanas)
    ax1.set_title(f"Ventas de {nombre}", fontsize=15, weight='bold')
    ax1.set_ylabel("Cantidad", fontsize=12)
    ax1.set_xlabel("Semanas", fontsize=12)
    ax1.legend(loc='upper left')
    ax1.grid(axis='y', linestyle='--', linewidth=0.5, alpha=0.7)

    fig.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format="png", dpi=160)
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode("utf-8")
    plt.close(fig)
    return img_base64


def transformar_summary(finalSummary, weekRanges):
    resultado = []
    for name, data in finalSummary.items():
        aca, act_aca, supp, act_supp, total = [], [], [], [], []

        for i in range(1, 7):
            semana = data.get(f"Week{i}", {
                "obama": 0, "activeObama": 0, "supp": 0, "activeSupp": 0, "total": 0
            })
            aca.append(semana["obama"])
            act_aca.append(semana["activeObama"])
            supp.append(semana["supp"])
            act_supp.append(semana["activeSupp"])
            total.append(semana["total"])

        img = generar_grafico_base64(name, weekRanges, {
            "ACA": aca,
            "Act ACA": act_aca,
            "Supp": supp,
            "Act Supp": act_supp,
            "Total": total,
        })

        resultado.append({"name": name, "grafico": img})
    return resultado

def sale6Week(finalSummary, weekRanges):
    summary_transformado = transformar_summary(finalSummary, weekRanges)

    html = render_to_string("reporte_6_semanas.html", {
        'summary': summary_transformado,
        'weekRanges': weekRanges,
    })

    buffer = BytesIO()
    HTML(string=html).write_pdf(buffer, stylesheets=[
        CSS(string='@page { size: A4 landscape; margin: 1cm; }')
    ])
    buffer.seek(0)

    filename = f"reporte_ventas_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    key = f"reports/{filename}"

    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME
    )

    s3.upload_fileobj(
        buffer,
        settings.AWS_STORAGE_BUCKET_NAME,
        key,
        ExtraArgs={'ContentType': 'application/pdf'}
    )

    url_firmado = s3.generate_presigned_url(
        ClientMethod='get_object',
        Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': key},
        ExpiresIn=3600
    )

    return url_firmado

