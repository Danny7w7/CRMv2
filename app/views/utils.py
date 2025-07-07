# Standard Python libraries
import logging
import smtplib
import ssl
from email.message import EmailMessage
from typing import Dict
import boto3


# Django core libraries
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from io import BytesIO
from django.test.client import RequestFactory

# Django utilities
from django.http import JsonResponse
from django.template.loader import render_to_string
from datetime import timedelta
from collections import defaultdict
from django.utils import timezone
from weasyprint import HTML, CSS

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
    
# Todo esto se necesita para el envio de segundo sms con telnyx que lleva una grafica y se envia en PDF
def create_request(user):
    request = RequestFactory().get("/")
    request.user = user
    request.company_id = user.company.id
    return request

def generate_base64_chart(nombre, semanas, data):
    import matplotlib.pyplot as plt
    import numpy as np
    from io import BytesIO
    import base64

    fig, ax1 = plt.subplots(figsize=(22, 8))  # ➕ más ancho

    x = np.arange(len(semanas))
    categorias = ["ACA", "Act ACA", "Supp", "Act Supp", "Assure", "Medicare", "Life"]
    colores = {
        "ACA": "#3498db",
        "Act ACA": "#2ecc71",
        "Supp": "#f1c40f",
        "Act Supp": "#e67e22",
        "Assure": "#9b59b6",
        "Medicare": "#34495e",
        "Life": "#d35400",
    }

    total_barras = len(categorias)
    bar_width = 0.1
    offset_inicio = -(total_barras - 1) / 2 * bar_width

    for i, categoria in enumerate(categorias):
        offset = offset_inicio + i * bar_width
        valores = data.get(categoria, [0] * len(x))
        bars = ax1.bar(x + offset, valores, width=bar_width, label=categoria, color=colores.get(categoria, "#ccc"))

        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax1.annotate(f'{height}',
                             xy=(bar.get_x() + bar.get_width() / 2, height),
                             xytext=(0, 4),
                             textcoords="offset points",
                             ha='center', va='bottom', fontsize=8)

    if "Total" in data:
        ax1.plot(x, data["Total"], color="black", marker="o", linestyle="--", linewidth=2, label="Total")
        for i, val in enumerate(data["Total"]):
            ax1.annotate(f'{val}',
                         xy=(x[i], val),
                         xytext=(0, 10),
                         textcoords="offset points",
                         ha='center', va='bottom',
                         fontsize=9, color='black', weight='bold')

    ax1.set_xticks(x)
    ax1.set_xticklabels(semanas)
    ax1.set_title(f"Ventas de {nombre}", fontsize=15, weight='bold')
    ax1.set_ylabel("Cantidad", fontsize=12)
    ax1.set_xlabel("Semanas", fontsize=12)
    ax1.legend(loc='upper left', fontsize=9)
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
        aca, act_aca, supp, act_supp = [], [], [], []
        assure, medicare, life, total = [], [], [], []

        for i in range(1, 7):
            semana = data.get(f"Week{i}", {})
            semana.setdefault("obama", 0)
            semana.setdefault("activeObama", 0)
            semana.setdefault("supp", 0)
            semana.setdefault("activeSupp", 0)
            semana.setdefault("assure", 0)
            semana.setdefault("medicare", 0)
            semana.setdefault("life", 0)
            semana.setdefault("total", 0)

            aca.append(semana["obama"])
            act_aca.append(semana["activeObama"])
            supp.append(semana["supp"])
            act_supp.append(semana["activeSupp"])
            assure.append(semana["assure"])
            medicare.append(semana["medicare"])
            life.append(semana["life"])
            total.append(semana["total"])

        img = generate_base64_chart(name, weekRanges, {
            "ACA": aca,
            "Act ACA": act_aca,
            "Supp": supp,
            "Act Supp": act_supp,
            "Assure": assure,
            "Medicare": medicare,
            "Life": life,
            "Total": total,
        })

        resultado.append({
            "name": name,
            "grafico": img
        })

    return resultado

def completar_summary_con_assure_medicare_life(finalSummary, company_id):
    # ✅ Calculamos rangos reales de fecha basados en las últimas 6 semanas
    today = timezone.now().date()
    weekRangesReal = []
    for _ in range(6):
        end = today
        start = end - timedelta(days=6)
        weekRangesReal.insert(0, (start, end))  # Insertamos de forma que Week1 sea la más antigua
        today = start - timedelta(days=1)

    # ✅ Querysets
    assure_qs = ClientsAssure.objects.filter(company_id=company_id, is_active=True)
    medicare_qs = Medicare.objects.filter(company_id=company_id, is_active=True)
    life_qs = ClientsLifeInsurance.objects.filter(company_id=company_id, is_active=True)

    # ✅ Función auxiliar para agregar datos
    def agregar_categoria(qs, field_name, date_field):
        for obj in qs:
            nombre_agente = f"{obj.agent.first_name} {obj.agent.last_name}"
            fecha = getattr(obj, date_field, None)
            if not fecha:
                continue
            if hasattr(fecha, 'date'):
                fecha = fecha.date()

            for idx, (start, end) in enumerate(weekRangesReal):
                if start <= fecha <= end:
                    semana_key = f"Week{idx + 1}"

                    # Si no existe el agente o la semana, inicializamos
                    if nombre_agente not in finalSummary:
                        finalSummary[nombre_agente] = {}

                    if semana_key not in finalSummary[nombre_agente]:
                        finalSummary[nombre_agente][semana_key] = {}

                    # ✅ Aseguramos que existan todas las categorías
                    for campo in ["obama", "activeObama", "supp", "activeSupp", "assure", "medicare", "life", "total"]:
                        finalSummary[nombre_agente][semana_key].setdefault(campo, 0)

                    # ✅ Sumamos el campo correspondiente
                    finalSummary[nombre_agente][semana_key][field_name] += 1
                    finalSummary[nombre_agente][semana_key]["total"] += 1
                    break  # Solo debe contar en una semana

    # ✅ Llamamos por cada modelo
    agregar_categoria(assure_qs, "assure", "date_effective_coverage")
    agregar_categoria(medicare_qs, "medicare", "dateMedicare")
    agregar_categoria(life_qs, "life", "date_effective_coverage")

    return finalSummary

def sale6Week(finalSummary, weekRanges, detalles_clientes):
    summary_transformado = transformar_summary(finalSummary, weekRanges)

    html = render_to_string("pdf/6WeekReport.html", {
        'summary': summary_transformado,
        'weekRanges': weekRanges,
        'detalles_clientes': detalles_clientes,  # ✅ agregado
    })

    buffer = BytesIO()
    doc  = HTML(string=html).write_pdf(buffer, stylesheets=[
        CSS(string='@page { size: A4 landscape; margin: 1cm; }')
    ])
    
    doc.metadata.title = "Reporte Ventas 6 Semanas"  # Aquí defines el título visible
    doc.write_pdf(buffer)
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

def get_customer_details(company_id):
    resultado = []
    fecha_corte = timezone.now() - timedelta(weeks=6)

    agentes = defaultdict(lambda: {
        "clientes_obama": [],
        "clientes_supp": [],
        "clientes_assure": [],
        "clientes_medicare": [],
        "clientes_life": [],
    })

    # ObamaCare
    obamacare_qs = ObamaCare.objects.filter(
        is_active=True,
        company_id=company_id,
        client__isnull=False,
        created_at__gte=fecha_corte
    ).select_related("client", "agent")

    for record in obamacare_qs:
        cliente = record.client
        agentes[f"{record.agent.first_name} {record.agent.last_name}"]["clientes_obama"].append({
            "nombre": f"{cliente.first_name} {cliente.last_name}",
            "fecha_poliza": record.created_at.strftime("%Y-%m-%d") if record.created_at else "N/A",
            "estatus": record.status or "N/A"
        })

    # Supp
    supp_qs = Supp.objects.filter(
        is_active=True,
        company_id=company_id,
        client__isnull=False,
        created_at__gte=fecha_corte
    ).select_related("client", "agent")

    for record in supp_qs:
        cliente = record.client
        agentes[f"{record.agent.first_name} {record.agent.last_name}"]["clientes_supp"].append({
            "nombre": f"{cliente.first_name} {cliente.last_name}",
            "fecha_poliza": record.created_at.strftime("%Y-%m-%d") if record.created_at else "N/A",
            "estatus": record.status or "N/A",
            "policy_type": record.policy_type or "N/A"
        })

    # Assure
    assure_qs = ClientsAssure.objects.filter(
        is_active=True,
        company_id=company_id,
        created_at__gte=fecha_corte
    ).select_related("agent")

    for record in assure_qs:
        agentes[f"{record.agent.first_name} {record.agent.last_name}"]["clientes_assure"].append({
            "nombre": f"{record.first_name} {record.last_name}",
            "fecha_poliza": record.created_at.strftime("%Y-%m-%d") if record.created_at else "N/A",
            "estatus": record.status or "N/A"
        })

    # Medicare
    medicare_qs = Medicare.objects.filter(
        is_active=True,
        company_id=company_id,
        created_at__gte=fecha_corte
    ).select_related("agent")

    for record in medicare_qs:
        agentes[f"{record.agent.first_name} {record.agent.last_name}"]["clientes_medicare"].append({
            "nombre": f"{record.first_name} {record.last_name}",
            "fecha_poliza": record.created_at.strftime("%Y-%m-%d") if record.created_at else "N/A",
            "estatus": record.status or "N/A"
        })

    # Life Insurance
    life_qs = ClientsLifeInsurance.objects.filter(
        is_active=True,
        company_id=company_id,
        created_at__gte=fecha_corte
    ).select_related("agent")

    for record in life_qs:
        agentes[f"{record.agent.first_name} {record.agent.last_name}"]["clientes_life"].append({
            "nombre": record.full_name,
            "fecha_poliza": record.created_at.strftime("%Y-%m-%d") if record.created_at else "N/A",
            "estatus": record.status or "N/A"
        })

    # Convertir dict → lista
    for nombre_agente, data in agentes.items():
        resultado.append({
            "nombre": nombre_agente,
            **data
        })

    return resultado

