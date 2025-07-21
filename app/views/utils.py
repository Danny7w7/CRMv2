# Standard Python libraries
import logging
import smtplib
import ssl
from email.message import EmailMessage
from typing import Dict
import boto3
import matplotlib.pyplot as plt
import numpy as np
import base64


# Django core libraries
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from io import BytesIO
from django.test.client import RequestFactory

# Django utilities
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from datetime import date, timedelta
from collections import defaultdict
from django.utils import timezone
from weasyprint import HTML, CSS
from django.db.models import Count

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

# SMS automatico de reporte de customer enviado con telnyx
from django.db.models import Count, Case, When, Q, BooleanField
from datetime import date, timedelta
from django.utils import timezone
from django.http import HttpResponse

# def dataQuery():

#     # ✅ Cálculo del rango de fechas de la semana anterior
#     def get_previous_week_date_range():
#         today = date.today()
#         start_of_current_week = today - timedelta(days=today.weekday())
#         start_of_last_week = start_of_current_week - timedelta(days=7)
#         end_of_last_week = start_of_last_week + timedelta(days=6)
#         return start_of_last_week, end_of_last_week


#     # # ✅ Cálculo del rango de fechas de la semana actual
#     # def get_current_week_date_range():
#     #     today = date.today()
#     #     start_of_week = today - timedelta(days=today.weekday())
#     #     end_of_week = start_of_week + timedelta(days=6)
#     #     return start_of_week, end_of_week

#     start_date_week, end_date_week = get_previous_week_date_range()

#     # ✅ Fechas aware para campos DateTimeField
#     start_datetime = timezone.make_aware(
#         timezone.datetime(start_date_week.year, start_date_week.month, start_date_week.day, 0, 0, 0)
#     )
#     end_datetime = timezone.make_aware(
#         timezone.datetime(end_date_week.year, end_date_week.month, end_date_week.day, 23, 59, 59, 999999)
#     )

#     # ✅ Consulta: ObservationCustomer (agrupado por agente)
#     effectiveManager = ObservationCustomer.objects.filter(
#         created_at__range=(start_datetime, end_datetime)
#     ).values(
#         'agent__first_name',
#         'agent__last_name'
#     ).annotate(
#         total_observations=Count('id'),
#         total_effective_management=Count(
#             Case(When(typification__icontains='EFFECTIVE MANAGEMENT', then=1), output_field=BooleanField())
#         ),
#         total_others=Count(
#             Case(When(~Q(typification__icontains='EFFECTIVE MANAGEMENT'), then=1), output_field=BooleanField())
#         )
#     ).order_by('agent__first_name', 'agent__last_name')

#     sms_text = ("--- Resultados de effectiveManager ---")
#     for item in effectiveManager:
#         sms_text += (f"Agente: {item['agent__first_name']} {item['agent__last_name']}, "
#               f"Total: {item['total_observations']}, "
#               f"Effective Management: {item['total_effective_management']}, "
#               f"Otros: {item['total_others']}")
#     sms_text += ("---------------------------------------------------------------")

#     # ✅ Consulta: UserCarrier (por fechas DATE, no datetime)
#     userCarrier = UserCarrier.objects.filter(
#         dateUserCarrier__range=(start_date_week, end_date_week)
#     ).values(
#         'agent_create__first_name',
#         'agent_create__last_name'
#     ).annotate(
#         total_observationss=Count('id')
#     ).order_by('agent_create__first_name', 'agent_create__last_name')

#     sms_text += ("--- Resultados de userCarrier ---")
#     for item in userCarrier:
#         sms_text += (f"Agente2: {item['agent_create__first_name']} {item['agent_create__last_name']}, "
#               f"Total2: {item['total_observationss']}, ")
#     sms_text += ("---------------------------------------------------------------")

#     # ✅ Consulta: PaymentDate (usa created_at datetime)
#     paymentReminder = PaymentDate.objects.filter(
#         created_at__range=(start_datetime, end_datetime)
#     ).values(
#         'agent_create__first_name',
#         'agent_create__last_name'
#     ).annotate(
#         total_observationss=Count('id')
#     ).order_by('agent_create__first_name', 'agent_create__last_name')

#     sms_text += ("--- Resultados de paymentReminder ---")
#     for item in paymentReminder:
#         sms_text += (f"Agente3: {item['agent_create__first_name']} {item['agent_create__last_name']}, "
#               f"Total3: {item['total_observationss']}, ")
#     sms_text += ("---------------------------------------------------------------")

#     # ✅ Consulta: ObamaCare agrupado por profiling
#     statusPolicyClients = ObamaCare.objects.filter(created_at__range=(start_datetime, end_datetime))

#     resultados = statusPolicyClients.values('profiling').annotate(
#         total_registros=Count('id'),
#         total_activos=Count(
#             Case(When(status__iexact='ACTIVO', then=1), output_field=BooleanField())
#         ),
#         total_policy_lleno=Count(
#             Case(When(~Q(policyNumber='') & ~Q(policyNumber__isnull=True), then=1), output_field=BooleanField())
#         )
#     ).order_by('profiling')

#     sms_text += ("--- Resultados de ObamaCare agrupado por profiling ---")
#     for item in resultados:
#         sms_text += (f"Profiling: {item['profiling']}, "
#               f"Total: {item['total_registros']}, "
#               f"Activos: {item['total_activos']}, "
#               f"Con Policy: {item['total_policy_lleno']}")
#     sms_text += ("---------------------------------------------------------------")

#     # ✅ Consulta: AppointmentClient
#     appointmentClients = AppointmentClient.objects.filter(
#         created_at__range=(start_datetime, end_datetime)
#     ).values(
#         'agent_create__first_name',
#         'agent_create__last_name'
#     ).annotate(
#         total_observationss=Count('id')
#     ).order_by('agent_create__first_name', 'agent_create__last_name')

#     sms_text += ("--- Resultados de appointmentClients ---")
#     for item in appointmentClients:
#         sms_text += (f"Agente6: {item['agent_create__first_name']} {item['agent_create__last_name']}, "
#               f"Total6: {item['total_observationss']}, ")
#     sms_text += ("---------------------------------------------------------------")

#     print(sms_text)

#     return sms_text


#     # return HttpResponse("OK")

from datetime import date, timedelta
from django.utils import timezone
from django.db.models import Count, Case, When, Q, BooleanField
from app.models import ObservationCustomer, UserCarrier, PaymentDate, ObamaCare, AppointmentClient

# 👉 Rango de fechas de la semana anterior
def weekRange():
    today = date.today()
    startDateDateField = today - timedelta(days=today.weekday() + 7)
    endDateDateField = startDateDateField + timedelta(days=6)
    startDatedatetime = timezone.make_aware(timezone.datetime(startDateDateField.year, startDateDateField.month, startDateDateField.day, 0, 0, 0))
    endDatedatetime = timezone.make_aware(timezone.datetime(endDateDateField.year, endDateDateField.month, endDateDateField.day, 23, 59, 59, 999999))
    return startDateDateField, endDateDateField, startDatedatetime, endDatedatetime

def observationCustomer(startDatedatetime, endDatedatetime):
    
    # 🔢 Total acumulado histórico por agente
    acumulado = ObservationCustomer.objects.values(
        'agent__first_name', 'agent__last_name'
    ).annotate(
        total_acumulado=Count('id')
    )

    # 🔄 Diccionario: nombre -> total_acumulado
    acumulado_dict = {
        f"{a['agent__first_name']} {a['agent__last_name']}": a['total_acumulado']
        for a in acumulado
    }

    # 📆 Observaciones solo de esta semana
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

    # 📨 Mensaje SMS
    sms = "--- RESULTADO DE LLAMADAS EFECTIVAS ---\n"
    for item in data:
        nombre = f"{item['agent__first_name']} {item['agent__last_name']}"
        esta_semana = item['total_observations']
        acumulado_total = acumulado_dict.get(nombre, 0)

        sms += (
            f"AGENTE: 🧑‍💼 {nombre}, Semana: {esta_semana}, "
            f"LLAMADAS EFECTIVAS: {item['total_effective_management']}, "
            f"LLAMADAS NO EFECTIVAS: {item['total_others']}, "
            f"ACULADO DE LLAMADAS: {acumulado_total}, "
        )

    return sms

def userCarrier(startDateDateField,endDateDateField):

    sms = "--- RESULTADO DE USARIOS DE COMPANIES CREADOS ---\n"

    # 🔹 Todos los agentes con agentes USA asignados
    agentes_crm = Users.objects.prefetch_related('usaAgents').all()

    # 🔹 Acumulado histórico (filtrado)
    historical_qs = UserCarrier.objects.filter(
        obamacare__is_active=True,
        username_carrier__isnull=False,
        password_carrier__isnull=False
    ).exclude(username_carrier='', password_carrier='')

    historical_map = historical_qs.values('agent_create').annotate(total=Count('id'))
    historical_dict = {item['agent_create']: item['total'] for item in historical_map}

    # 🔹 Formularios esta semana (mismos filtros)
    weekly_qs = UserCarrier.objects.filter(
        obamacare__is_active=True,
        dateUserCarrier__range=(startDateDateField, endDateDateField),
        username_carrier__isnull=False,
        password_carrier__isnull=False
    ).exclude(username_carrier='', password_carrier='')

    weekly_map = weekly_qs.values('agent_create').annotate(total=Count('id'))
    weekly_dict = {item['agent_create']: item['total'] for item in weekly_map}

    for agente in agentes_crm:
        usa_names = list(agente.usaAgents.values_list("name", flat=True))
        if not usa_names:
            continue  # Ignorar agentes sin usaAgents

        total_clients = ObamaCare.objects.filter(
            is_active=True,
            agent_usa__in=usa_names
        ).count()

        total_all_time = historical_dict.get(agente.id, 0)
        total_week = weekly_dict.get(agente.id, 0)
        faltan = total_clients - total_all_time
        faltan_pct = (faltan / total_clients * 100) if total_clients > 0 else 0

        sms += (
            f"AGENTE: 🧑‍💼 {agente.first_name} {agente.last_name}, "
            f"CLIENTES TOTALES: {total_clients}, "
            f"CLIENTES LLENADOS EN LA SEMANA: {total_week}, "
            f"ACUMULADO TOTAL: {total_all_time}, "
            f"FALTAN: {faltan}, "
            f"FALTAN %: {faltan_pct:.1f}%\n"
        )

    return sms

def paymentDate(startDatedatetime, endDatedatetime):

    sms = "--- RESULTADO DE PROGRAMAR PAGOS (SMS) ---\n"

    agentes_crm = Users.objects.prefetch_related('usaAgents').all()

    for agente in agentes_crm:
        usa_names = list(agente.usaAgents.values_list("name", flat=True))
        if not usa_names:
            continue  # Ignorar si no tiene agentes USA

        full_name = f"{agente.first_name} {agente.last_name}"

        # Total de clientes activos con premium > 0
        total_clients = ObamaCare.objects.filter(
            is_active=True,
            premium__gt=0,
            agent_usa__in=usa_names
        ).count()

        # Total acumulado de formularios válidos
        acumulado = PaymentDate.objects.filter(
            agent_create=agente,
            obamacare__isnull=False,
            obamacare__is_active=True,
            obamacare__premium__gt=0,
            obamacare__agent_usa__in=usa_names
        ).count()

        # Total esta semana con mismos filtros
        esta_semana = PaymentDate.objects.filter(
            agent_create=agente,
            created_at__range=(startDatedatetime, endDatedatetime),
            obamacare__isnull=False,
            obamacare__is_active=True,
            obamacare__premium__gt=0,
            obamacare__agent_usa__in=usa_names
        ).count()

        faltan = total_clients - acumulado
        porcentaje_faltante = (faltan / total_clients * 100) if total_clients > 0 else 0

        sms += (
            f"AGENTE: 🧑‍💼 {full_name}, "
            f"CLIENTES TOTALES: {total_clients}, "
            f"CLIENTES LLENADO EN LA SEMANA: {esta_semana}, "
            f"ACUMULADO: {acumulado}, "
            f"FALTAN: {faltan}, "
            f"FALTAN %: {porcentaje_faltante:.1f}%\n"
        )

    return sms

def obamacareStatus(startDateDateField,endDateDateField):

    sms = "--- RESULTADOS DE OBAMACARE ---\n"

    agentes_crm = Users.objects.prefetch_related('usaAgents').all()

    for agente in agentes_crm:
        usa_agents_names = list(agente.usaAgents.values_list("name", flat=True))

        if not usa_agents_names:
            continue

        full_name = f"{agente.first_name} {agente.last_name}"

        # Total clientes activos
        total_clientes = ObamaCare.objects.filter(
            is_active=True,
            agent_usa__in=usa_agents_names
        )

        total_clientes_count = total_clientes.count()

        # Total clientes perfilados en la semana
        clientes_semanales = ObamaCare.objects.filter(
            profiling_date__range=(startDateDateField, endDateDateField),
            agent_usa__in=usa_agents_names
        ).count()

        # Total con status ACTIVO
        total_activos = ObamaCare.objects.filter(
            agent_usa__in=usa_agents_names,
            status__iexact='ACTIVO'
        ).count()

        # Total con policyNumber lleno
        total_policy = ObamaCare.objects.filter(
            agent_usa__in=usa_agents_names
        ).exclude(
            policyNumber__isnull=True
        ).exclude(
            policyNumber=''
        ).count()

        sms += (
            f"AGENTE: 🧑‍💼 {full_name}, "
            f"CLIENTES TOTALES: {total_clientes_count}, "
            f"PERFILADOS ESTA SEMANA: {clientes_semanales}, "
            f"CLIENTES ACTIVOS: {total_activos}, "
            f"CLIENTES CON # POLIZA: {total_policy}\n"
        )

    return sms

def appointmentClients(startDatedatetime, endDatedatetime):

    sms = "--- RESULTADOS DE CITAS AGENDADAS PARA EL CLIENTE ---\n"

    agentes_crm = Users.objects.prefetch_related('usaAgents').all()

    for agente in agentes_crm:
        usa_agents_names = list(agente.usaAgents.values_list("name", flat=True))

        if not usa_agents_names:
            continue  # Ignorar agentes sin relación USA

        full_name = f"{agente.first_name} {agente.last_name}"

        # Clientes activos del agente USA
        total_clients = ObamaCare.objects.filter(
            is_active=True,
            agent_usa__in=usa_agents_names
        ).count()

        # Total acumulado de citas con obamacare activo
        acumulado = AppointmentClient.objects.filter(
            agent_create=agente,
            obamacare__isnull=False,
            obamacare__is_active=True,
            obamacare__agent_usa__in=usa_agents_names
        ).count()

        # Citas esta semana
        esta_semana = AppointmentClient.objects.filter(
            agent_create=agente,
            created_at__range=(startDatedatetime, endDatedatetime),
            obamacare__isnull=False,
            obamacare__is_active=True,
            obamacare__agent_usa__in=usa_agents_names
        ).count()

        faltan = total_clients - acumulado
        porcentaje_faltante = (faltan / total_clients * 100) if total_clients > 0 else 0

        sms += (
            f"AGENTE: 🧑‍💼 {full_name}, "
            f"CLIENTES TOTALES: {total_clients}, "
            f"CITAS ESTA SEMENA: {esta_semana}, "
            f"CITAS ACUMULADAS: {acumulado}, "
            f"FALTAN: {faltan}, "
            f"FALTAN %: {porcentaje_faltante:.1f}%\n"
        )

    return sms

def lettersCardStatus(startDateDateField, endDateDateField):

    sms = "--- RESULTADOS DE LETTERS AND CARD ---\n"

    agentes_crm = Users.objects.prefetch_related('usaAgents').all()

    for agente in agentes_crm:
        usa_agents_names = list(agente.usaAgents.values_list("name", flat=True))
        if not usa_agents_names:
            continue

        full_name = f"{agente.first_name} {agente.last_name}"

        # 🔹 Total de clientes activos asociados al agente USA
        total_clients = ObamaCare.objects.filter(
            is_active=True,
            agent_usa__in=usa_agents_names
        ).count()

        # 🔹 Acumulado de cartas
        acumulado_cartas = LettersCard.objects.filter(
            agent_create=agente,
            letters=True,
            obamacare__isnull=False,
            obamacare__is_active=True,
            obamacare__agent_usa__in=usa_agents_names
        ).count()

        # 🔹 Acumulado de tarjetas
        acumulado_tarjetas = LettersCard.objects.filter(
            agent_create=agente,
            card=True,
            obamacare__isnull=False,
            obamacare__is_active=True,
            obamacare__agent_usa__in=usa_agents_names
        ).count()

        # 🔹 Esta semana: cartas
        cartas_semana = LettersCard.objects.filter(
            agent_create=agente,
            dateCard__range=(startDateDateField, endDateDateField),
            letters=True,
            obamacare__isnull=False,
            obamacare__is_active=True,
            obamacare__agent_usa__in=usa_agents_names
        ).count()

        # 🔹 Esta semana: tarjetas
        tarjetas_semana = LettersCard.objects.filter(
            agent_create=agente,
            dateLetters__range=(startDateDateField, endDateDateField),
            card=True,
            obamacare__isnull=False,
            obamacare__is_active=True,
            obamacare__agent_usa__in=usa_agents_names
        ).count()

        # 🔹 Porcentajes faltantes
        faltan_cartas = total_clients - acumulado_cartas
        faltan_tarjetas = total_clients - acumulado_tarjetas

        porcentaje_faltante_cartas = (faltan_cartas / total_clients * 100) if total_clients > 0 else 0
        porcentaje_faltante_tarjetas = (faltan_tarjetas / total_clients * 100) if total_clients > 0 else 0

        sms += (
            f"AGENTE: 🧑‍💼 {full_name}, CLIENTES TOTALES: {total_clients}\n"
            f"   📩 CARTAS ESTA SEMANA: {cartas_semana}, ACUMULADO: {acumulado_cartas}, "
            f"FALTAN: {faltan_cartas}, AVANCE FALTANTE: {porcentaje_faltante_cartas:.1f}%\n"
            f"   💳 Tarjetas esta semana: {tarjetas_semana}, ACUMULADO: {acumulado_tarjetas}, "
            f"FALTAN: {faltan_tarjetas}, AVANCE FALTANTE: {porcentaje_faltante_tarjetas:.1f}%\n"
        )

    return sms


def dataQuery():
    startDateDateField, endDateDateField , startDatedatetime, endDatedatetime = weekRange()
    
    partes_sms = [
        observationCustomer(startDatedatetime, endDatedatetime),
        userCarrier(startDateDateField, endDateDateField),
        paymentDate(startDatedatetime, endDatedatetime),
        obamacareStatus(startDateDateField, endDateDateField),
        appointmentClients(startDatedatetime, endDatedatetime),
        lettersCardStatus(startDateDateField, endDateDateField)
    ]
    
    return partes_sms  # una lista de strings

