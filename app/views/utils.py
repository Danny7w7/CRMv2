# Standard Python libraries
import logging
import smtplib
import ssl
from email.message import EmailMessage
from typing import Dict
import matplotlib.pyplot as plt
import numpy as np
import base64
import matplotlib.pyplot as plt
import os
import io
import uuid
from uuid import uuid4

# Django core libraries
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from io import BytesIO
from django.test.client import RequestFactory
from dateutil.relativedelta import relativedelta
from datetime import datetime

# Django utilities
from django.http import JsonResponse
from django.template.loader import render_to_string
from datetime import date, timedelta
from collections import defaultdict
from django.utils import timezone
from weasyprint import HTML, CSS
from django.db.models import Count, Case, When, Q, BooleanField, Subquery
from django.template import Engine, Context
from matplotlib.ticker import MaxNLocator

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

def send_email_with_pdf(subject, receiver_email, pdf_content):
    try:
        # ✅ Contenido como texto plano, no con template
        body = f"""
            Hello,

            Adjunto encontrarás tu reporte de ventas de las últimas 6 semanas, enviado automaticamente por el mejor equipo de IT.

            Saludos,
            Equipo IT
            """
        # Configurar mensaje
        message = EmailMessage()
        message['Subject'] = subject
        message['From'] = settings.SENDER_EMAIL_ADDRESS
        message['To'] = ', '.join(receiver_email)
        message.set_content(body)

        # Adjuntar PDF
        message.add_attachment(
            pdf_content,
            maintype='application',
            subtype='pdf',
            filename='reporte_ventas6_week.pdf'
        )

        # Enviar email
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(settings.SMTP_HOST, int(settings.SMTP_PORT), context=context) as server:
            server.login(settings.SENDER_EMAIL_ADDRESS, settings.EMAIL_PASSWORD)
            server.send_message(message)

        logger.info(f"✅ Email enviado exitosamente a {receiver_email}")
        return True

    except Exception as e:
        logger.error(f"❌ Error al enviar email: {str(e)}")
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

        totalActivos = [
            sum(vals) for vals in zip(
                data.get("Act ACA", [0] * len(x)),
                data.get("Act Supp", [0] * len(x)),
            )
        ]

        ax1.plot(x, totalActivos, color="black", marker="o", linestyle="--", linewidth=2, label="Total Activos")
        for i, val in enumerate(totalActivos):
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
    HTML(string=html).write_pdf(buffer, stylesheets=[
        CSS(string='@page { size: A4 landscape; margin: 1cm; }')
    ])
    buffer.seek(0)

    return buffer.getvalue()

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
    excluded_obama_ids = CustomerRedFlag.objects.filter(date_completed__isnull=True).values('obamacare')
    obamacare_qs = ObamaCare.objects.filter(
        is_active=True,
        company_id=company_id,
        client__isnull=False,
        created_at__gte=fecha_corte
    ).select_related("client", "agent").exclude(id__in=Subquery(excluded_obama_ids))

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

# SMS automatico de reporte de customer enviado con telnyx de gestion semanal
def weekRange():
    today = date.today()
    startDateDateField = today - timedelta(days=today.weekday())
    endDateDateField = startDateDateField + timedelta(days=6)
    startDatedatetime = timezone.make_aware(timezone.datetime(startDateDateField.year, startDateDateField.month, startDateDateField.day, 0, 0, 0))
    endDatedatetime = timezone.make_aware(timezone.datetime(endDateDateField.year, endDateDateField.month, endDateDateField.day, 23, 59, 59, 999999))
    return startDateDateField, endDateDateField, startDatedatetime, endDatedatetime

def observationCustomer(startDatedatetime, endDatedatetime):
    data = ObservationCustomer.objects.filter(
        created_at__range=(startDatedatetime, endDatedatetime)
    ).values(
        'agent__first_name', 'agent__last_name'
    ).annotate(
        total_observations=Count('id'),
        total_effective_management=Count(
            Case(When(typification__icontains='EFFECTIVE MANAGEMENT', then=1), output_field=BooleanField())
        ),
        total_others=Count(
            Case(When(~Q(typification__icontains='EFFECTIVE MANAGEMENT'), then=1), output_field=BooleanField())
        )
    ).order_by('agent__first_name', 'agent__last_name')

    nombres = []
    efectivas = []
    no_efectivas = []

    for item in data:
        nombre = f"{item['agent__first_name']} {item['agent__last_name']}"
        nombres.append(nombre)
        efectivas.append(item['total_effective_management'])
        no_efectivas.append(item['total_others'])

    # Gráfico de barras: 2 barras por agente
    x = range(len(nombres))
    width = 0.35  # Ancho de cada barra

    fig, ax = plt.subplots(figsize=(8, 4))
    x_effectivas = [i - width/2 for i in x]
    x_no_efectivas = [i + width/2 for i in x]

    bars1 = ax.bar(x_effectivas, efectivas, width=width, label='Efectivas', color='green')
    bars2 = ax.bar(x_no_efectivas, no_efectivas, width=width, label='No Efectivas', color='red')

    # Etiquetas
    ax.set_xticks(x)
    ax.set_xticklabels(nombres, rotation=45, ha='right')
    ax.set_ylabel('Cantidad')
    ax.set_title('Llamadas por Agente - Semana')
    ax.legend()

    # Mostrar valores sobre las barras
    def agregar_valores(barras):
        for barra in barras:
            altura = barra.get_height()
            ax.annotate(f'{int(altura)}',
                        xy=(barra.get_x() + barra.get_width() / 2, altura),
                        xytext=(0, 3),  # 3 puntos arriba
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=8)

    agregar_valores(bars1)
    agregar_valores(bars2)

    plt.tight_layout()

    # Guardar imagen
    output_dir = os.path.join('temp')
    os.makedirs(output_dir, exist_ok=True)
    filename = f"grafico_llamadas_{uuid4().hex}.png"
    image_path = os.path.join(output_dir, filename)
    plt.savefig(image_path)
    plt.close()

    return image_path

def userCarrier(startDateDateField, endDateDateField):
    agentes_crm = Users.objects.prefetch_related('usaAgents').all()

    nombres = []
    llenados_semana = []
    faltan = []
    acumulado = []

    status = ['ACTIVE','ENROLLED','SELF-ENROLMENT','IN PROGRESS']

    for agente in agentes_crm:
        usa_names = list(agente.usaAgents.values_list("name", flat=True))
        if not usa_names:
            continue

        # Total clientes activos del agente USA
        total_clients = ObamaCare.objects.filter(
            is_active=True,
            agent_usa__in=usa_names,
            company = 2,
            status__in = status
        ).count()

        # Total con username y password (sin importar fecha)
        total_filled = UserCarrier.objects.filter(
            obamacare__is_active=True,
            obamacare__agent_usa__in=usa_names,
            username_carrier__isnull=False,
            password_carrier__isnull=False,
            obamacare__status__in = status,
            obamacare__company = 2
        ).exclude(username_carrier='', password_carrier='').count()

        # Solo los de esta semana
        total_week = UserCarrier.objects.filter(
            obamacare__is_active=True,
            obamacare__agent_usa__in=usa_names,
            dateUserCarrier__range=(startDateDateField, endDateDateField),
            username_carrier__isnull=False,
            password_carrier__isnull=False,
            obamacare__status__in = status,
            obamacare__company = 2
        ).exclude(username_carrier='', password_carrier='').count()

        faltan_count = total_clients - total_filled

        nombres.append(f"{agente.first_name} {agente.last_name}")
        llenados_semana.append(total_week)
        faltan.append(faltan_count)
        acumulado.append(total_filled)

    # Gráfico
    x = range(len(nombres))
    width = 0.25
    fig, ax = plt.subplots(figsize=(10, 7))

    x1 = [i - width for i in x]
    x2 = [i for i in x]
    x3 = [i + width for i in x]

    bars1 = ax.bar(x1, llenados_semana, width, label='Semana Actual', color='green')
    bars2 = ax.bar(x2, faltan, width, label='Faltan por llenar', color='red')
    bars3 = ax.bar(x3, acumulado, width, label='Acumulado Total', color='blue')

    ax.set_xticks(x)
    ax.set_xticklabels(nombres, rotation=45, ha='right')
    ax.set_ylabel('Cantidad')
    ax.set_title('Formularios Carrier por Agente (Semana, Faltan y Acumulado)')
    ax.legend()

    def agregar_valores(barras):
        for barra in barras:
            height = barra.get_height()
            ax.annotate(f'{int(height)}',
                        xy=(barra.get_x() + barra.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=8)

    agregar_valores(bars1)
    agregar_valores(bars2)
    agregar_valores(bars3)

    plt.tight_layout()

    output_dir = os.path.join('temp')
    os.makedirs(output_dir, exist_ok=True)
    filename = f"user_carrier_{uuid4().hex}.png"
    image_path = os.path.join(output_dir, filename)
    plt.savefig(image_path)
    plt.close()

    return image_path

def paymentDate(startDatedatetime, endDatedatetime):
    agentes_crm = Users.objects.prefetch_related('usaAgents').all()

    nombres = []
    llenados_semana = []
    faltantes = []
    acumulados = []

    status = ['ACTIVE','ENROLLED','SELF-ENROLMENT','IN PROGRESS']

    for agente in agentes_crm:
        usa_names = list(agente.usaAgents.values_list("name", flat=True))
        if not usa_names:
            continue

        full_name = f"{agente.first_name} {agente.last_name}"

        # Clientes activos con premium > 0
        total_clients = ObamaCare.objects.filter(
            is_active=True,
            premium__gt=0,
            agent_usa__in=usa_names,
            company = 2,
            status__in = status
        ).count()

        esta_semana = PaymentDate.objects.filter(
            agent_create=agente,
            created_at__range=(startDatedatetime, endDatedatetime),
            obamacare__isnull=False,
            obamacare__is_active=True,
            obamacare__premium__gt=0,
            obamacare__agent_usa__in=usa_names,
            obamacare__company = 2,
            obamacare__status__in = status
        ).count()

        # Acumulado total histórico
        acumulado_total = PaymentDate.objects.filter(
            agent_create=agente,
            obamacare__isnull=False,
            obamacare__is_active=True,
            obamacare__premium__gt=0,
            obamacare__agent_usa__in=usa_names,
            obamacare__company=2,
            obamacare__status__in = status
        ).count()

        faltan = total_clients - acumulado_total

        nombres.append(full_name)
        llenados_semana.append(esta_semana)
        faltantes.append(faltan)
        acumulados.append(acumulado_total)

    # Crear gráfico
    x = range(len(nombres))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 7))

    x1 = [i - width for i in x]
    x2 = [i for i in x]
    x3 = [i + width for i in x]

    bars1 = ax.bar(x1, llenados_semana, width, label='Semana Actual', color='green')
    bars2 = ax.bar(x2, faltantes, width, label='Faltan por llenar', color='red')
    bars3 = ax.bar(x3, acumulados, width, label='Acumulado Total', color='blue')

    ax.set_xticks(x)
    ax.set_xticklabels(nombres, rotation=45, ha='right')
    ax.set_ylabel('Cantidad')
    ax.set_title('Pagos: semana actual, faltantes y acumulado total por agente')
    ax.legend()

    def agregar_valores(barras):
        for barra in barras:
            height = barra.get_height()
            ax.annotate(f'{int(height)}',
                        xy=(barra.get_x() + barra.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=8)

    agregar_valores(bars1)
    agregar_valores(bars2)
    agregar_valores(bars3)

    plt.tight_layout()

    output_dir = os.path.join('temp')
    os.makedirs(output_dir, exist_ok=True)
    filename = f"payment_date_{uuid4().hex}.png"
    image_path = os.path.join(output_dir, filename)
    plt.savefig(image_path)
    plt.close()

    return image_path

def obamacareStatus(startDateDateField, endDateDateField):
    agentes_crm = Users.objects.prefetch_related('usaAgents').all()

    nombres_agentes = []
    activos = []
    con_poliza = []
    sin_poliza = []
    no_activos = []

    for agente in agentes_crm:
        usa_agents_names = list(agente.usaAgents.values_list("name", flat=True))
        if not usa_agents_names:
            continue

        full_name = f"{agente.first_name} {agente.last_name}"
        nombres_agentes.append(full_name)

        clientes = ObamaCare.objects.filter(agent_usa__in=usa_agents_names, is_active=True, company = 2)

        total_activos = clientes.filter(status__iexact='ACTIVE').count()
        total_con_poliza = clientes.filter(status__iexact='ACTIVE').exclude(policyNumber__isnull=True).exclude(policyNumber='').count()
        total_total = clientes.count()

        activos.append(total_activos)
        con_poliza.append(total_con_poliza)
        sin_poliza.append(total_activos - total_con_poliza)
        no_activos.append(total_total - total_activos)

    # 📊 Crear gráfica
    x = np.arange(len(nombres_agentes))
    width = 0.2

    fig, ax = plt.subplots(figsize=(10, 7))

    bars1 = ax.bar(x - 1.5 * width, activos, width, label='Clientes Activos', color='green')
    bars2 = ax.bar(x - 0.5 * width, con_poliza, width, label='Clientes Activos con # Póliza', color='blue')
    bars3 = ax.bar(x + 0.5 * width, sin_poliza, width, label='Clientes Activos sin # Póliza', color='orange')
    bars4 = ax.bar(x + 1.5 * width, no_activos, width, label='Clientes NO Activos', color='red')
    

    # ✅ Etiquetas
    def add_labels(bars):
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.annotate(f'{height}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=8)

    for bars in [bars1, bars2, bars3, bars4]:
        add_labels(bars)

    ax.set_xlabel('Agentes')
    ax.set_ylabel('Cantidad de Clientes')
    ax.set_title('Estado de Clientes ObamaCare por Agente')
    ax.set_xticks(x)
    ax.set_xticklabels(nombres_agentes, rotation=45, ha='right')
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.6)

    plt.tight_layout()

    # 🖼️ Imagen como base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    buffer.close()
    plt.close()

    return f"data:image/png;base64,{image_base64}"

def appointmentClients(startDatedatetime, endDatedatetime):
    agentes_crm = Users.objects.prefetch_related('usaAgents').all()

    agentes = []
    acumuladas = []
    esta_semana = []
    faltan = []

    status = ['ACTIVE','ENROLLED','SELF-ENROLMENT','IN PROGRESS']

    for agente in agentes_crm:
        usa_agents_names = list(agente.usaAgents.values_list("name", flat=True))
        if not usa_agents_names:
            continue

        full_name = f"{agente.first_name} {agente.last_name}"
        total_clients = ObamaCare.objects.filter(
            is_active=True,
            agent_usa__in=usa_agents_names,
            company = 2,
            status__in = status
        ).count()

        acumulado = AppointmentClient.objects.filter(
            agent_create=agente,
            obamacare__isnull=False,
            obamacare__is_active=True,
            obamacare__agent_usa__in=usa_agents_names,
            obamacare__company = 2,
            obamacare__status__in = status
        ).count()

        esta_semana_count = AppointmentClient.objects.filter(
            agent_create=agente,
            created_at__range=(startDatedatetime, endDatedatetime),
            obamacare__isnull=False,
            obamacare__is_active=True,
            obamacare__agent_usa__in=usa_agents_names,
            obamacare__company = 2,
            obamacare__status__in = status
        ).count()

        faltan_count = total_clients - acumulado

        agentes.append(full_name)
        acumuladas.append(acumulado)
        esta_semana.append(esta_semana_count)
        faltan.append(faltan_count)

    if not agentes:
        return None  # No hay datos

    # Crear gráfico
    x = np.arange(len(agentes))
    width = 0.25

    fig, ax = plt.subplots(figsize=(10, 7))
    bars1 = ax.bar(x - width, acumuladas, width, label='Acumuladas Total', color='blue')
    bars2 = ax.bar(x, esta_semana, width, label='Esta semana', color='green')
    bars3 = ax.bar(x + width, faltan, width, label='Faltanes por llenar', color='red')

    # Mostrar valores encima de cada barra
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),  # 3 puntos hacia arriba
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=8)

    ax.set_ylabel('Cantidad de Citas')
    ax.set_title('Citas por Agente')
    ax.set_xticks(x)
    ax.set_xticklabels(agentes, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, axis='y', linestyle='--', alpha=0.7)

    # Guardar imagen
    output_dir = 'temp'
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{uuid.uuid4().hex}_citas.png"
    img_path = os.path.join(output_dir, filename)
    plt.tight_layout()
    plt.savefig(img_path)
    plt.close()

    return img_path

def lettersCardStatus(startDateDateField, endDateDateField):
    agentes_crm = Users.objects.prefetch_related('usaAgents').all()

    nombres_agentes = []
    cartas_semana = []
    tarjetas_semana = []
    faltan_cartas = []
    faltan_tarjetas = []

    status = ['ACTIVE','ENROLLED','SELF-ENROLMENT','IN PROGRESS']

    for agente in agentes_crm:
        usa_agents_names = list(agente.usaAgents.values_list("name", flat=True))
        if not usa_agents_names:
            continue

        full_name = f"{agente.first_name} {agente.last_name}"

        c_semana = LettersCard.objects.filter(
            agent_create=agente,
            dateCard__range=(startDateDateField, endDateDateField),
            letters=True,
            obamacare__isnull=False,
            obamacare__is_active=True,
            obamacare__agent_usa__in=usa_agents_names,
            obamacare__company = 2,
            obamacare__status__in = status  
        ).count()

        t_semana = LettersCard.objects.filter(
            agent_create=agente,
            dateLetters__range=(startDateDateField, endDateDateField),
            card=True,
            obamacare__isnull=False,
            obamacare__is_active=True,
            obamacare__agent_usa__in=usa_agents_names,
            obamacare__company = 2,
            obamacare__status__in = status   
        ).count()

        # Clientes sin cartas
        faltan_c = ObamaCare.objects.filter(
            is_active=True,
            company=2,
            agent_usa__in=usa_agents_names,
            status__in = status,
            letterscard__letters = False    
        ).count()

        # Clientes sin tarjetas
        faltan_t = ObamaCare.objects.filter(
            is_active=True,
            company=2,
            agent_usa__in=usa_agents_names,
            status__in = status,
            letterscard__card = False                      
        ).count()

        nombres_agentes.append(full_name)
        cartas_semana.append(c_semana)
        tarjetas_semana.append(t_semana)
        faltan_cartas.append(faltan_c)
        faltan_tarjetas.append(faltan_t)

    # 📊 GRAFICAR
    x = range(len(nombres_agentes))
    width = 0.2

    fig, ax = plt.subplots(figsize=(10, 7))

    b1 = ax.bar([i - 1.5*width for i in x], cartas_semana, width, label='Cartas Semana', color='green')
    b2 = ax.bar([i - 0.5*width for i in x], tarjetas_semana, width, label='Tarjetas Semana', color='blue')
    b3 = ax.bar([i + 0.5*width for i in x], faltan_cartas, width, label='# Cartas faltantes', color='orange')
    b4 = ax.bar([i + 1.5*width for i in x], faltan_tarjetas, width, label='# Tarjetas faltantes', color='red')

    # Etiquetas de cantidad
    for bars in [b1, b2, b3, b4]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height + 0.5, str(height), ha='center', va='bottom', fontsize=8)

    ax.set_ylabel('Cantidad')
    ax.set_title('Cartas y Tarjetas por Agente')
    ax.set_xticks(list(x))
    ax.set_xticklabels(nombres_agentes, rotation=45, ha='right')
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    # Guardar imagen como base64
    buffer = BytesIO()
    plt.tight_layout()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close()

    return f"data:image/png;base64,{img_base64}"

def documentsUploaded(startDatedatetime, endDatedatetime):
    agentes_crm = Users.objects.prefetch_related('usaAgents').all()

    nombres = []
    llenados_semana = []
    faltantes = []
    acumulado = []

    status = ['ACTIVE','ENROLLED','SELF-ENROLMENT','IN PROGRESS']

    for agente in agentes_crm:
        usa_names = list(agente.usaAgents.values_list("name", flat=True))
        if not usa_names:
            continue

        full_name = f"{agente.first_name} {agente.last_name}"

        # Total clientes activos
        total_clients = ObamaCare.objects.filter(
            is_active=True,
            agent_usa__in=usa_names,
            company=2,
            status__in = status
        ).count()

        # Documentos esta semana
        esta_semana = DocumentObamaSupp.objects.filter(
            typePlan="OBAMACARE",
            created_at__range=(startDatedatetime, endDatedatetime),
            obamacare__isnull=False,
            obamacare__agent_usa__in=usa_names,
            obamacare__is_active=True,
            obamacare__company=2,
            obamacare__status__in = status
        ).count()

        # Documentos total acumulado
        total_docs = DocumentObamaSupp.objects.filter(
            typePlan="OBAMACARE",
            obamacare__isnull=False,
            obamacare__agent_usa__in=usa_names,
            obamacare__is_active=True,
            obamacare__company=2,
            obamacare__status__in = status
        ).values('obamacare_id').distinct().count()

        faltan = max(0, total_clients - total_docs)

        nombres.append(full_name)
        llenados_semana.append(esta_semana)
        faltantes.append(faltan)
        acumulado.append(total_docs)

    # Crear gráfico
    x = range(len(nombres))
    width = 0.3

    fig, ax = plt.subplots(figsize=(11, 7))

    x1 = [i - width for i in x]
    x2 = x
    x3 = [i + width for i in x]

    bars1 = ax.bar(x1, llenados_semana, width, label='# Documentos semana actual', color='green')
    bars2 = ax.bar(x2, faltantes, width, label='Faltan', color='red')
    bars3 = ax.bar(x3, acumulado, width, label='Acumulado', color='blue')

    ax.set_xticks(x)
    ax.set_xticklabels(nombres, rotation=45, ha='right')
    ax.set_ylabel('Cantidad')
    ax.set_title('Documentos ObamaCare por Agente')
    ax.legend()

    def agregar_valores(barras):
        for barra in barras:
            height = barra.get_height()
            ax.annotate(f'{int(height)}',
                        xy=(barra.get_x() + barra.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=8)

    agregar_valores(bars1)
    agregar_valores(bars2)
    agregar_valores(bars3)

    plt.tight_layout()

    output_dir = os.path.join('temp')
    os.makedirs(output_dir, exist_ok=True)
    filename = f"documentos_obama_{uuid4().hex}.png"
    image_path = os.path.join(output_dir, filename)
    plt.savefig(image_path)
    plt.close()

    return image_path

def dataQuery():
    startDateDateField, endDateDateField, startDatedatetime, endDatedatetime = weekRange()

    return [
        observationCustomer(startDatedatetime, endDatedatetime),  
        userCarrier(startDateDateField, endDateDateField),
        paymentDate(startDatedatetime, endDatedatetime),
        obamacareStatus(startDateDateField, endDateDateField),
        appointmentClients(startDatedatetime, endDatedatetime),
        lettersCardStatus(startDateDateField, endDateDateField),
        documentsUploaded(startDatedatetime, endDatedatetime)
    ]

def generarPDFChart(datos_secciones, output_path):

    llamadas, userCarrier, pagos, obamacare , citas, cartas, documentos = datos_secciones

    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=5)

    formatted_start = start_of_week.strftime('%A %d de %B')
    formatted_end = end_of_week.strftime('%d de %B')

    dateWeek = f"La semana es del {formatted_start} al {formatted_end}"

    context = {
        'llamadas': llamadas,
        'userCarrier': userCarrier,
        'pagos': pagos,
        'obamacare': obamacare,
        'citas': citas,
        'cartas': cartas,
        'dateWeek': dateWeek,
        'documentos' : documentos
    }

    html_content = render_to_string('pdf/reportWeekCustomer.html', context)
    HTML(string=html_content, base_url='.').write_pdf(output_path)

#Funcione para Graficas de Ventas de los Agentes son 4 reportes
# 6SEMANAS
def chart6WeekAgent():
    
    agentes = Users.objects.filter(is_active=True, company=2, role__in=['A', 'C'])
    now = timezone.now()

    today = now.date()
    monday = today - timedelta(days=today.weekday())  # lunes de esta semana
    start_date = monday - timedelta(weeks=5)          # hace 5 semanas

    weeks = [
        (start_date + timedelta(days=7 * i), start_date + timedelta(days=7 * i + 5))
        for i in range(6)
    ]

    all_carriers = list(Supp.objects.values_list('carrier', flat=True).distinct())

    charts = []

    for week_start, week_end in weeks:
        semana_label = f"{week_start.strftime('%Y-%m-%d')} a {week_end.strftime('%Y-%m-%d')}"
        categories = []
        series_dict = defaultdict(list)

        for agente in agentes:
            nombre = agente.first_name.upper()
            categories.append(nombre)

            obamacare_count = ObamaCare.objects.filter(
                agent=agente,
                is_active=True,
                company=2,
                status='ACTIVE',
                created_at__range=(week_start, week_end)
            ).count()
            series_dict['OBAMACARE'].append(obamacare_count)

            supp_counts = {f"SUPP - {c}": 0 for c in all_carriers}
            supps = Supp.objects.filter(
                agent=agente,
                is_active=True,
                company=2,
                status='ACTIVE',
                created_at__range=(week_start, week_end)
            ).values("carrier").annotate(total=Count("id"))

            for item in supps:
                key = f"SUPP - {item['carrier']}"
                supp_counts[key] = item["total"]

            for carrier_key, count in supp_counts.items():
                series_dict[carrier_key].append(count)

        series = [{"name": key, "data": values} for key, values in series_dict.items()]
        charts.append({
            "semana": semana_label,
            "series": series,
            "categories": categories,
        })

    return charts

def generatePDFChart6Week():
    charts = chart6WeekAgent()
    image_paths = []

    os.makedirs("temp", exist_ok=True)

    for chart in charts:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.set_title(f"Clientes por Agente: Semana {chart['semana']}", fontsize=14)

        categories = chart["categories"]
        width = 0.15
        x = list(range(len(categories)))
        series_list = chart["series"]

        for i, serie in enumerate(series_list):
            data = serie["data"]
            label = serie["name"]
            positions = [pos + width * i for pos in x]
            bars = ax.bar(positions, data, width, label=label)

            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.annotate(f'{int(height)}', xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3), textcoords="offset points", ha='center', fontsize=8)

        ax.set_xticks([pos + width * (len(series_list) / 2 - 0.5) for pos in x])
        ax.set_xticklabels(categories, rotation=45, ha='right')
        ax.legend(loc='upper right')
        ax.grid(True, linestyle='--', linewidth=0.5)

        filename = f"temp/chart_{uuid.uuid4().hex}.png"
        plt.tight_layout()
        plt.savefig(filename)
        image_paths.append(os.path.abspath(filename))
        plt.close()

    return image_paths

#semana actual VS Anterior
def chartWeekPrevius():
    now = timezone.now().date()

    # Calcular los lunes de esta semana y la anterior
    monday_this_week = now - timedelta(days=now.weekday())
    monday_last_week = monday_this_week - timedelta(weeks=1)

    # Rango de semanas
    weeks = [
        (monday_last_week, monday_last_week + timedelta(days=6)),
        (monday_this_week, monday_this_week + timedelta(days=6)),
    ]

    # Obtener TODOS los agentes con rol A y C (activos)
    agentes = Users.objects.filter(is_active=True, company=2, role__in=['A', 'C']).order_by('first_name', 'last_name')

    charts = []

    for week_start, week_end in weeks:
        semana_label = f"{week_start.strftime('%Y-%m-%d')} a {week_end.strftime('%Y-%m-%d')}"

        # Totales generales para gráfica
        obamacare_total = ObamaCare.objects.filter(
            is_active=True,
            company=2,
            status='ACTIVE',
            created_at__range=(week_start, week_end)
        ).count()

        supp_total = Supp.objects.filter(
            is_active=True,
            company=2,
            status='ACTIVE',
            created_at__range=(week_start, week_end)
        ).count()

        # Tabla detallada por agente - TODOS los agentes
        tabla = []
        for agente in agentes:
            obamacare_count = ObamaCare.objects.filter(
                is_active=True,
                company=2,
                status='ACTIVE',
                agent=agente,
                created_at__range=(week_start, week_end)
            ).count()

            supp_count = Supp.objects.filter(
                is_active=True,
                company=2,
                status='ACTIVE',
                agent=agente,
                created_at__range=(week_start, week_end)
            ).count()

            # Agregar TODOS los agentes, tengan ventas o no
            tabla.append({
                "agente": f"{agente.first_name.upper()} {agente.last_name.upper()}",
                "obamacare": obamacare_count,
                "supp": supp_count,
                "total": obamacare_count + supp_count,  # Total para ordenamiento opcional
                "tiene_ventas": obamacare_count > 0 or supp_count > 0  # Flag para estilos CSS
            })

        # Opcional: Ordenar por total de ventas (descendente) y luego por nombre
        tabla.sort(key=lambda x: (-x['total'], x['agente']))

        charts.append({
            "semana": semana_label,
            "series": [
                {"name": "OBAMACARE", "data": [obamacare_total]},
                {"name": "SUPP", "data": [supp_total]},
            ],
            "categories": ["TOTAL"],
            "tabla": tabla
        })

    return charts

def generatePDFChartWeekPrevius():
    charts = chartWeekPrevius()
    output_dir = "temp"
    os.makedirs(output_dir, exist_ok=True)

    # Generar una sola imagen general
    fig, ax = plt.subplots(figsize=(6, 4))

    width = 0.35
    x = [0, 1]
    labels = [chart['semana'] for chart in charts]

    obamacare_totals = [chart['series'][0]['data'][0] for chart in charts]
    supp_totals = [chart['series'][1]['data'][0] for chart in charts]

    ax.bar([pos - width / 2 for pos in x], obamacare_totals, width=width, label="ObamaCare", color='blue')
    ax.bar([pos + width / 2 for pos in x], supp_totals, width=width, label="Supp", color='green')

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20)
    ax.set_ylabel("Cantidad de ventas")
    ax.set_title("Totales Generales - Últimas 2 semanas")
    ax.legend()
    ax.grid(True)

    filename = f"{output_dir}/chart_{uuid.uuid4().hex}.png"
    fig.tight_layout()
    plt.savefig(filename)
    plt.close()

    resumen_chart_path = os.path.abspath(filename)

    # Armar datos semanales sin imagen
    semanas = []
    for chart in charts:
        semanas.append({
            "semana": chart["semana"],
            "tabla": chart["tabla"]
        })

    return resumen_chart_path, semanas

#Unificacion de los 2 reportes antereiores en el PDF
def generarPDFCompleto(output_pdf_path):
    charts6Weekly = generatePDFChart6Week()
    resumenChartWeek, charts_two_week = generatePDFChartWeekPrevius()

    template_path = os.path.join(settings.BASE_DIR, 'app', 'templates', 'pdf','reporteCompletoAgents.html')

    with open(template_path, encoding='utf-8') as f:
        template_code = f.read()

    template = Engine().from_string(template_code)

    context = {
        'charts_weekly': charts6Weekly,
        'resumen_chart_path': resumenChartWeek,
        'charts_two_week': charts_two_week         
    }

    rendered_html = template.render(Context(context))
    HTML(string=rendered_html).write_pdf(output_pdf_path)

#Ultimos 6 mese
def chartSixMonths():
    
    now = timezone.now().date()
    
    # Calcular los últimos 6 meses
    months = []
    for i in range(6):
        # Empezar desde el mes actual y retroceder
        month_date = now.replace(day=1) - relativedelta(months=i)
        # Calcular el último día del mes
        next_month = month_date + relativedelta(months=1)
        last_day = next_month - timedelta(days=1)
        
        months.append((month_date, last_day))
    
    # Invertir para tener orden cronológico (más antiguo primero)
    months.reverse()
    
    agentes = Users.objects.filter(is_active=True, company=2, role__in=['A', 'C'])
    
    charts = []
    
    for month_start, month_end in months:
        mes_label = month_start.strftime('%B %Y')  # Ejemplo: "January 2025"
        # Si prefieres en español: mes_label = month_start.strftime('%m/%Y')
        
        # Totales generales para gráfica
        obamacare_total = ObamaCare.objects.filter(
            is_active=True,
            company=2,
            status='ACTIVE',
            created_at__range=(month_start, month_end)
        ).count()
        
        supp_total = Supp.objects.filter(
            is_active=True,
            company=2,
            status='ACTIVE',
            created_at__range=(month_start, month_end)
        ).count()
        
        charts.append({
            "mes": mes_label,
            "series": [
                {"name": "OBAMACARE", "data": [obamacare_total]},
                {"name": "SUPP", "data": [supp_total]},
            ],
            "categories": ["TOTAL"]
        })
    
    return charts

#Ultimo año
def chartAllData():
    
    # Obtener todos los registros de ObamaCare
    obamacare_records = ObamaCare.objects.filter(
        is_active=True,
        company=2,
        status='ACTIVE',
        created_at__isnull=False
    ).values_list('created_at', flat=True)
    
    # Obtener todos los registros de Supp
    supp_records = Supp.objects.filter(
        is_active=True,
        company=2,
        status='ACTIVE',
        created_at__isnull=False
    ).values_list('created_at', flat=True)
    
    # Agrupar por mes manualmente
    obamacare_months = defaultdict(int)
    supp_months = defaultdict(int)
    
    # Procesar registros de ObamaCare
    for date in obamacare_records:
        if date:
            # Asegurar que tenemos un objeto date
            if hasattr(date, 'date'):
                date = date.date()
            
            month_key = (date.year, date.month)
            obamacare_months[month_key] += 1
    
    # Procesar registros de Supp
    for date in supp_records:
        if date:
            # Asegurar que tenemos un objeto date
            if hasattr(date, 'date'):
                date = date.date()
            
            month_key = (date.year, date.month)
            supp_months[month_key] += 1
    
    # Obtener todos los meses únicos y ordenarlos
    all_months = set()
    all_months.update(obamacare_months.keys())
    all_months.update(supp_months.keys())
    all_months = sorted(all_months)
    
    # Construir los datos para el gráfico
    charts = []
    
    for year, month in all_months:
        # Crear fecha para formateo
        date_obj = datetime(year, month, 1)
        mes_label = date_obj.strftime('%B %Y')  # Ejemplo: "January 2025"
        
        month_key = (year, month)
        obamacare_count = obamacare_months.get(month_key, 0)
        supp_count = supp_months.get(month_key, 0)
        
        charts.append({
            "mes": mes_label,
            "series": [
                {"name": "OBAMACARE", "data": [obamacare_count]},
                {"name": "SUPP", "data": [supp_count]},
            ],
            "categories": ["TOTAL"]
        })
    
    return charts

def generateSummaryCharts():
    output_dir = "temp"
    os.makedirs(output_dir, exist_ok=True)

    # Datos
    charts_6_months = chartSixMonths()
    charts_all_data = chartAllData()

    # ---------------------------
    # GRAFICA: Últimos 6 meses
    # ---------------------------
    fig1, ax1 = plt.subplots(figsize=(8, 4))
    labels_6 = [c['mes'] for c in charts_6_months]
    obama_6 = [c['series'][0]['data'][0] for c in charts_6_months]
    supp_6 = [c['series'][1]['data'][0] for c in charts_6_months]
    x_6 = range(len(labels_6))

    ax1.bar([x - 0.2 for x in x_6], obama_6, width=0.4, label='ObamaCare', color='blue')
    ax1.bar([x + 0.2 for x in x_6], supp_6, width=0.4, label='Supp', color='green')

    ax1.set_xticks(list(x_6))
    ax1.set_xticklabels(labels_6, rotation=30)
    ax1.set_title("Ventas últimos 6 meses")
    ax1.legend()
    ax1.grid(True)

    path_6_months = os.path.abspath(f"{output_dir}/chart_6m_{uuid.uuid4().hex}.png")
    fig1.tight_layout()
    plt.savefig(path_6_months)
    plt.close()

    # ---------------------------
    # GRAFICA: Todo el histórico
    # ---------------------------
    fig2, ax2 = plt.subplots(figsize=(10, 4))
    labels_all = [c['mes'] for c in charts_all_data]
    obama_all = [c['series'][0]['data'][0] for c in charts_all_data]
    supp_all = [c['series'][1]['data'][0] for c in charts_all_data]
    x_all = range(len(labels_all))

    ax2.bar([x - 0.2 for x in x_all], obama_all, width=0.4, label='ObamaCare', color='blue')
    ax2.bar([x + 0.2 for x in x_all], supp_all, width=0.4, label='Supp', color='green')

    ax2.set_xticks(list(x_all))
    ax2.set_xticklabels(labels_all, rotation=30)
    ax2.set_title("Histórico anual de ventas")
    ax2.legend()
    ax2.grid(True)

    path_all_data = os.path.abspath(f"{output_dir}/chart_all_{uuid.uuid4().hex}.png")
    fig2.tight_layout()
    plt.savefig(path_all_data)
    plt.close()

    return path_6_months, path_all_data

#Unificacion de los 2 reportes antereiores en el PDF
def generarPDFResumenMensual(output_pdf_path):

    chart_6_months, chart_all_data = generateSummaryCharts()

    template_path = os.path.join(settings.BASE_DIR, 'app', 'templates', 'pdf' ,'reporteMensual.html')
    with open(template_path, encoding='utf-8') as f:
        template_code = f.read()

    template = Engine().from_string(template_code)

    context = {
        'chart_6_months': chart_6_months,
        'chart_all_data': chart_all_data,
    }

    rendered_html = template.render(Context(context))
    HTML(string=rendered_html).write_pdf(output_pdf_path)

