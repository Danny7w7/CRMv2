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
from datetime import datetime
import os
import telnyx


# CORRECCIONES NECESARIAS EN TUS FUNCIONES:

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

    # 📨 Crear lista de resultados en lugar de sobrescribir sms
    resultados = []
    for item in data:
        nombre = f"{item['agent__first_name']} {item['agent__last_name']}"
        esta_semana = item['total_observations']
        acumulado_total = acumulado_dict.get(nombre, 0)

        linea = (
            f"AGENTE: 🧑 {nombre}, "
            f"Semana: {esta_semana}, "
            f"LLAMADAS EFECTIVAS: {item['total_effective_management']}, "
            f"LLAMADAS NO EFECTIVAS: {item['total_others']}, "
            f"ACUMULADO DE LLAMADAS: {acumulado_total}"
        )
        resultados.append(linea)

    return resultados  # Devolver lista, no string

def userCarrier(startDateDateField, endDateDateField):
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

    resultados = []
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

        linea = (
            f"AGENTE: 🧑 {agente.first_name} {agente.last_name}, "
            f"CLIENTES TOTALES: {total_clients}, "
            f"CLIENTES LLENADOS EN LA SEMANA: {total_week}, "
            f"ACUMULADO TOTAL: {total_all_time}, "
            f"FALTAN: {faltan}, "
            f"FALTAN %: {faltan_pct:.1f}%"
        )
        resultados.append(linea)

    return resultados

def paymentDate(startDatedatetime, endDatedatetime):
    agentes_crm = Users.objects.prefetch_related('usaAgents').all()

    resultados = []
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

        linea = (
            f"AGENTE: 🧑 {full_name}, "
            f"CLIENTES TOTALES: {total_clients}, "
            f"CLIENTES LLENADO EN LA SEMANA: {esta_semana}, "
            f"ACUMULADO: {acumulado}, "
            f"FALTAN: {faltan}, "
            f"FALTAN %: {porcentaje_faltante:.1f}%"
        )
        resultados.append(linea)

    return resultados

def obamacareStatus(startDateDateField, endDateDateField):
    agentes_crm = Users.objects.prefetch_related('usaAgents').all()

    resultados = []
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

        linea = (
            f"AGENTE: 🧑 {full_name}, "
            f"CLIENTES TOTALES: {total_clientes_count}, "
            f"PERFILADOS ESTA SEMANA: {clientes_semanales}, "
            f"CLIENTES ACTIVOS: {total_activos}, "
            f"CLIENTES CON # POLIZA: {total_policy}"
        )
        resultados.append(linea)

    return resultados

def appointmentClients(startDatedatetime, endDatedatetime):
    agentes_crm = Users.objects.prefetch_related('usaAgents').all()

    resultados = []
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

        linea = (
            f"AGENTE: 🧑 {full_name}, "
            f"CLIENTES TOTALES: {total_clients}, "
            f"CITAS ESTA SEMANA: {esta_semana}, "  # Corregido typo "SEMENA"
            f"CITAS ACUMULADAS: {acumulado}, "
            f"FALTAN: {faltan}, "
            f"FALTAN %: {porcentaje_faltante:.1f}%"
        )
        resultados.append(linea)

    return resultados

def lettersCardStatus(startDateDateField, endDateDateField):
    agentes_crm = Users.objects.prefetch_related('usaAgents').all()

    resultados = []
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

        linea = (
            f"AGENTE: 🧑 {full_name}, "
            f"CLIENTES TOTALES: {total_clients}, "
            f"CARTAS ESTA SEMANA: {cartas_semana}, "
            f"ACUMULADO CARTAS: {acumulado_cartas}, "
            f"FALTAN CARTAS: {faltan_cartas} ({porcentaje_faltante_cartas:.1f}%), "
            f"TARJETAS ESTA SEMANA: {tarjetas_semana}, "
            f"ACUMULADO TARJETAS: {acumulado_tarjetas}, "
            f"FALTAN TARJETAS: {faltan_tarjetas} ({porcentaje_faltante_tarjetas:.1f}%)"
        )
        resultados.append(linea)

    return resultados


# FUNCIÓN MODIFICADA PARA GENERAR PDF
from django.template.loader import render_to_string
from weasyprint import HTML

def generar_pdf_bonito(datos_secciones, output_path):
    # datos_secciones es una lista de listas de strings
    # Necesitamos convertirlo al formato que espera el template
    
    llamadas, carriers, pagos, obamacare, citas, cartas = datos_secciones
    
    context = {
        'llamadas': llamadas,
        'carriers': carriers, 
        'pagos': pagos,
        'obamacare': obamacare,
        'citas': citas,
        'cartas': cartas
    }
    
    html_content = render_to_string('pdf/reportWeekCustomer.html', context)
    HTML(string=html_content).write_pdf(output_path)


# TASK CORREGIDO
@shared_task
def test():
    # 1. Obtener los datos (ahora cada función devuelve una lista)
    partes_sms = dataQuery()  # Devuelve lista de listas
    
    # 2. Generar PDF con los datos correctos
    now = datetime.now()
    filename = f"reporte_test_{now.strftime('%Y%m%d_%H%M%S')}.pdf"
    local_path = f"/tmp/{filename}"
    generar_pdf_bonito(partes_sms, local_path)

    # 3. Subir a S3
    s3_key = f"reportes/{filename}"
    s3_url = uploadTempUrl(local_path, s3_key)

    # 4. Crear mensaje de texto resumido para SMS
    # Contar totales por sección
    totales_sms = []
    secciones_nombres = [
        "📞 Llamadas Efectivas",
        "💼 Usuarios Companies", 
        "💰 Programar Pagos",
        "🩺 Obamacare Status",
        "📅 Citas del Cliente",
        "✉️ Letters y Cards"
    ]
    
    for i, (nombre, datos) in enumerate(zip(secciones_nombres, partes_sms)):
        total_agentes = len(datos)
        totales_sms.append(f"{nombre}: {total_agentes} agentes")
    
    mensaje_sms = (
        f"📄 Reporte Semanal Generado\n"
        f"📅 {now.strftime('%d/%m/%Y %H:%M')}\n\n" +
        "\n".join(totales_sms) +
        f"\n\n📎 PDF completo adjunto"
    )

    # 5. Enviar por Telnyx
    telnyx.api_key = settings.TELNYX_API_KEY
    telnyx.Message.create(
        from_='+17869848427',
        to='+17863034781',
        text=mensaje_sms,
        subject='Reporte PDF Semanal',
        media_urls=[s3_url]
    )

    # 6. Limpiar
    if os.path.exists(local_path):
        os.remove(local_path)


