# Standard Python libraries
import datetime
from datetime import timedelta, date

# Django utilities
from django.utils.timezone import make_aware

# Django core libraries
from django.contrib.auth.decorators import login_required
from django.db.models import Count, F, Q, Subquery
from django.db.models.functions import Substr
from django.shortcuts import render
from django.utils.text import Truncator

# Application-specific imports
from app.models import *
from ..utils import format_decimal
from ..reports.charts import chart6WeekSale
from ..decoratorsCompany import *

@login_required(login_url='/login') 
@company_ownership_required_sinURL
def sale(request):

    company_id = request.company_id  # Obtener company_id desde request
    start_date = None
    end_date = None

    if request.method == 'POST':
        # Obtener los parámetros de fecha del request
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

    # Llamar a la función que procesa los datos de ventas y obtiene la información agrupada
    saleACA =  saleObamaAgent (request, company_id, start_date, end_date)
    saleACAUsa = saleObamaAgentUsa(request, company_id, start_date, end_date)
    saleSupp = saleSuppAgent(request, company_id, start_date, end_date)
    saleSuppUsa = saleSuppAgentUsa(request, company_id, start_date, end_date)
    ventasAgentes = salesBonusAgent(request, company_id, start_date, end_date)

    registered, proccessing, profiling, canceled, countRegistered,countProccsing,countProfiling,countCanceled = saleClientStatusObama(request, company_id, start_date, end_date)
    registeredSupp, proccessingSupp, activeSupp, canceledSupp,countRegisteredSupp,countProccsingSupp,countActiveSupp,countCanceledSupp,registeredAssure,proccessingAssure,activeAssure,canceledAssure = saleClientStatusSupp(request, company_id, start_date, end_date)

    context = {
        'saleACA': saleACA,
        'saleACAUsa': saleACAUsa,
        'saleSupp': saleSupp,
        'saleSuppUsa': saleSuppUsa,
        'registered':registered,
        'proccessing' : proccessing,
        'profiling':profiling,
        'canceled':canceled,
        'registeredSupp': registeredSupp, 
        'proccessingSupp':proccessingSupp,
        'activeSupp':activeSupp,
        'canceledSupp':canceledSupp,
        'countRegistered':countRegistered,
        'countProccsing': countProccsing,
        'countProfiling':countProfiling,
        'countCanceled':countCanceled,
        'countRegisteredSupp':countRegisteredSupp,
        'countProccsingSupp': countProccsingSupp,
        'countActiveSupp':countActiveSupp,
        'countCanceledSupp':countCanceledSupp,
        'start_date' : start_date,
        'end_date': end_date,
        'registeredAssure':registeredAssure,
        'proccessingAssure':proccessingAssure,
        'activeAssure': activeAssure,
        'canceledAssure' : canceledAssure,
        'ventasAgentes': ventasAgentes,
    }

    return render (request, 'saleReports/sale.html', context)

def saleObamaAgent(request, company_id, start_date=None, end_date=None):

    # Obtener los IDs de ObamaCare que están en CustomerRedFlag
    excluded_obama_ids = CustomerRedFlag.objects.values('obamacare_id')

    if request.user.is_superuser:
        # Definir la consulta base para Supp, utilizando `select_related` para obtener el nombre completo del agente (User)
        sales_query = ObamaCare.objects.select_related('agent').filter(is_active=True).exclude( id__in=Subquery(excluded_obama_ids)) \
            .values('agent__username', 'agent__first_name', 'agent__last_name', 'status_color') \
            .annotate(total_sales=Count('id')) \
            .order_by('agent', 'status_color')
    else:
        # Definir la consulta base para Supp, utilizando `select_related` para obtener el nombre completo del agente (User)
        sales_query = ObamaCare.objects.select_related('agent').filter(is_active=True, company = company_id).exclude( id__in=Subquery(excluded_obama_ids)) \
            .values('agent__username', 'agent__first_name', 'agent__last_name', 'status_color') \
            .annotate(total_sales=Count('id')) \
            .order_by('agent', 'status_color')


    # Si no se proporcionan fechas, filtrar por el mes actual
    if not start_date and not end_date:
        today = timezone.now()
        first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        if today.month == 12:
            last_day_of_month = today.replace(day=31, hour=23, minute=59, second=59, microsecond=999999)
        else:
            last_day_of_month = (first_day_of_month.replace(month=first_day_of_month.month + 1) - timezone.timedelta(seconds=1))

        sales_query = sales_query.filter(created_at__range=[first_day_of_month, last_day_of_month])

    # Si se proporcionan fechas, filtrar por el rango de fechas
    elif start_date and end_date:
        start_date = timezone.make_aware(
            datetime.datetime.strptime(start_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
        )
        end_date = timezone.make_aware(
            datetime.datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)
        )

        sales_query = sales_query.filter(created_at__range=[start_date, end_date])

    # Crear un diccionario para almacenar los resultados por agente y status color
    agents_sales = {}
    status_colors = [1, 2, 3, 4]

    # Procesar los resultados y organizar los totales por agente
    for entry in sales_query:
        agent_username = entry['agent__username']
        first_name = entry['agent__first_name']
        last_name = entry['agent__last_name']
        agent_full_name = f"{first_name} {last_name} "
        status_color = entry['status_color']
        total_sales = entry['total_sales']

        if agent_full_name not in agents_sales:
            agents_sales[agent_full_name] = {'status_color_1': 0, 'status_color_2': 0, 'status_color_3': 0, 'status_color_4': 0, 'total_sales': 0}

        if status_color == 1:
            agents_sales[agent_full_name]['status_color_1'] = total_sales
        elif status_color == 2:
            agents_sales[agent_full_name]['status_color_2'] = total_sales
        elif status_color == 3:
            agents_sales[agent_full_name]['status_color_3'] = total_sales
        elif status_color == 4:
            agents_sales[agent_full_name]['status_color_4'] = total_sales

        agents_sales[agent_full_name]['total_sales'] += total_sales

    return agents_sales

def saleObamaAgentUsa(request, company_id, start_date=None, end_date=None):
    excluded_obama_ids = CustomerRedFlag.objects.values('obamacare_id')

    base_queryset = ObamaCare.objects.visible_for_user(request.user).filter(is_active=True).exclude(
        id__in=Subquery(excluded_obama_ids)
    )

    # Filtrado por fechas
    if not start_date and not end_date:
        today = timezone.now()
        first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if today.month == 12:
            last_day_of_month = today.replace(day=31, hour=23, minute=59, second=59, microsecond=999999)
        else:
            last_day_of_month = (first_day_of_month.replace(month=first_day_of_month.month + 1) - timezone.timedelta(seconds=1))
        base_queryset = base_queryset.filter(created_at__range=[first_day_of_month, last_day_of_month])

    elif start_date and end_date:
        start_date = timezone.make_aware(
            datetime.datetime.strptime(start_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
        )
        end_date = timezone.make_aware(
            datetime.datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)
        )
        base_queryset = base_queryset.filter(created_at__range=[start_date, end_date])

    # Agrupar y contar
    sales_query = base_queryset.values('agent_usa', 'status_color').annotate(
        total_sales=Count('id')
    ).order_by('agent_usa', 'status_color')

    # Armar estructura por agente
    agents_sales = {}
    for entry in sales_query:
        agent_name = entry['agent_usa'] or "Sin nombre"
        short_name = Truncator(agent_name).chars(8)
        status_color = entry['status_color']
        total_sales = entry['total_sales']

        if short_name not in agents_sales:
            agents_sales[short_name] = {
                'status_color_1': 0, 'status_color_2': 0,
                'status_color_3': 0, 'status_color_4': 0,
                'total_sales': 0
            }

        if status_color == 1:
            agents_sales[short_name]['status_color_1'] = total_sales
        elif status_color == 2:
            agents_sales[short_name]['status_color_2'] = total_sales
        elif status_color == 3:
            agents_sales[short_name]['status_color_3'] = total_sales
        elif status_color == 4:
            agents_sales[short_name]['status_color_4'] = total_sales

        agents_sales[short_name]['total_sales'] += total_sales

    return agents_sales

def saleSuppAgent(request, company_id, start_date=None, end_date=None):

    if request.user.is_superuser:
        # Definir la consulta base para Supp, utilizando `select_related` para obtener el nombre completo del agente (User)
        sales_query = Supp.objects.select_related('agent').filter(is_active=True) \
            .values('agent__username', 'agent__first_name', 'agent__last_name', 'status_color') \
            .annotate(total_sales=Count('id')) \
            .order_by('agent', 'status_color')
        sales_query_assure = ClientsAssure.objects.select_related('agent').filter(is_active=True) \
            .values('agent__username', 'agent__first_name', 'agent__last_name', 'status_color') \
            .annotate(total_sales=Count('id')) \
            .order_by('agent', 'status_color')
        sales_query_life = ClientsLifeInsurance.objects.select_related('agent').filter(is_active=True) \
            .values('agent__username', 'agent__first_name', 'agent__last_name', 'status_color') \
            .annotate(total_sales=Count('id')) \
            .order_by('agent', 'status_color')
    else:
        # Definir la consulta base para Supp, utilizando `select_related` para obtener el nombre completo del agente (User)
        sales_query = Supp.objects.select_related('agent').filter(is_active=True, company = company_id) \
            .values('agent__username', 'agent__first_name', 'agent__last_name', 'status_color') \
            .annotate(total_sales=Count('id')) \
            .order_by('agent', 'status_color')
        sales_query_assure = ClientsAssure.objects.select_related('agent').filter(is_active=True, company = company_id) \
            .values('agent__username', 'agent__first_name', 'agent__last_name', 'status_color') \
            .annotate(total_sales=Count('id')) \
            .order_by('agent', 'status_color')
        sales_query_life = ClientsLifeInsurance.objects.select_related('agent').filter(is_active=True, company = company_id) \
            .values('agent__username', 'agent__first_name', 'agent__last_name', 'status_color') \
            .annotate(total_sales=Count('id')) \
            .order_by('agent', 'status_color')


    # Si no se proporcionan fechas, filtrar por el mes actual
    if not start_date and not end_date:
        today = timezone.now()
        first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        if today.month == 12:
            last_day_of_month = today.replace(day=31, hour=23, minute=59, second=59, microsecond=999999)
        else:
            last_day_of_month = (first_day_of_month.replace(month=first_day_of_month.month + 1) - timezone.timedelta(seconds=1))

        sales_query = sales_query.filter(created_at__range=[first_day_of_month, last_day_of_month])
        sales_query_assure = sales_query_assure.filter(created_at__range=[first_day_of_month, last_day_of_month])
        sales_query_life = sales_query_life.filter(created_at__range=[first_day_of_month, last_day_of_month])

    # Si se proporcionan fechas, filtrar por el rango de fechas
    elif start_date and end_date:
        start_date = timezone.make_aware(
            datetime.datetime.strptime(start_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
        )
        end_date = timezone.make_aware(
            datetime.datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)
        )

        sales_query = sales_query.filter(created_at__range=[start_date, end_date])
        sales_query_assure = sales_query_assure.filter(created_at__range=[start_date, end_date])
        sales_query_life = sales_query_life.filter(created_at__range=[start_date, end_date])

    # Crear un diccionario para almacenar los resultados por agente y status color
    agents_sales = {}
    status_colors = [1, 2, 3, 4]

    # Procesar los resultados y organizar los totales por agente
    for entry in sales_query:
        agent_username = entry['agent__username']
        first_name = entry['agent__first_name']
        last_name = entry['agent__last_name']
        agent_full_name = f"{first_name} {last_name}"
        status_color = entry['status_color']
        total_sales = entry['total_sales']

        if agent_full_name not in agents_sales:
            agents_sales[agent_full_name] = {
                'status_color_1': 0,
                'status_color_2': 0,
                'status_color_3': 0,
                'status_color_4': 0,
                'total_sales': 0
            }

        if status_color == 1:
            agents_sales[agent_full_name]['status_color_1'] += total_sales
        elif status_color == 2:
            agents_sales[agent_full_name]['status_color_2'] += total_sales
        elif status_color == 3:
            agents_sales[agent_full_name]['status_color_3'] += total_sales
        elif status_color == 4:
            agents_sales[agent_full_name]['status_color_4'] += total_sales

        agents_sales[agent_full_name]['total_sales'] += total_sales

    for entry in sales_query_assure:
        agent_username = entry['agent__username']
        first_name = entry['agent__first_name']
        last_name = entry['agent__last_name']
        agent_full_name = f"{first_name} {last_name}"
        status_color = entry['status_color']
        total_sales = entry['total_sales']

        if agent_full_name not in agents_sales:
            agents_sales[agent_full_name] = {
                'status_color_1': 0,
                'status_color_2': 0,
                'status_color_3': 0,
                'status_color_4': 0,
                'total_sales': 0
            }

        if status_color == 1:
            agents_sales[agent_full_name]['status_color_1'] += total_sales
        elif status_color == 2:
            agents_sales[agent_full_name]['status_color_2'] += total_sales
        elif status_color == 3:
            agents_sales[agent_full_name]['status_color_3'] += total_sales
        elif status_color == 4:
            agents_sales[agent_full_name]['status_color_4'] += total_sales

        agents_sales[agent_full_name]['total_sales'] += total_sales

    for entry in sales_query_life:
        agent_username = entry['agent__username']
        first_name = entry['agent__first_name']
        last_name = entry['agent__last_name']
        agent_full_name = f"{first_name} {last_name}"
        status_color = entry['status_color']
        total_sales = entry['total_sales']

        if agent_full_name not in agents_sales:
            agents_sales[agent_full_name] = {
                'status_color_1': 0,
                'status_color_2': 0,
                'status_color_3': 0,
                'status_color_4': 0,
                'total_sales': 0
            }

        if status_color == 1:
            agents_sales[agent_full_name]['status_color_1'] += total_sales
        elif status_color == 2:
            agents_sales[agent_full_name]['status_color_2'] += total_sales
        elif status_color == 3:
            agents_sales[agent_full_name]['status_color_3'] += total_sales
        elif status_color == 4:
            agents_sales[agent_full_name]['status_color_4'] += total_sales

        agents_sales[agent_full_name]['total_sales'] += total_sales

    return agents_sales

def saleSuppAgentUsa(request, company_id, start_date=None, end_date=None):
    # Base query para los tres modelos con filtros de visibilidad aplicados
    base_query_supp = Supp.objects.visible_for_user(request.user).filter(is_active=True)
    base_query_assure = ClientsAssure.objects.visible_for_user(request.user).filter(is_active=True)
    base_query_life = ClientsLifeInsurance.objects.visible_for_user(request.user).filter(is_active=True)

    # Aplicar filtro por fechas si es necesario
    if not start_date and not end_date:
        today = timezone.now()
        first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if today.month == 12:
            last_day_of_month = today.replace(day=31, hour=23, minute=59, second=59, microsecond=999999)
        else:
            last_day_of_month = (first_day_of_month.replace(month=first_day_of_month.month + 1) - timezone.timedelta(seconds=1))

        base_query_supp = base_query_supp.filter(created_at__range=[first_day_of_month, last_day_of_month])
        base_query_assure = base_query_assure.filter(created_at__range=[first_day_of_month, last_day_of_month])
        base_query_life = base_query_life.filter(created_at__range=[first_day_of_month, last_day_of_month])
    elif start_date and end_date:
        start_date = timezone.make_aware(datetime.datetime.strptime(start_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0))
        end_date = timezone.make_aware(datetime.datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999))

        base_query_supp = base_query_supp.filter(created_at__range=[start_date, end_date])
        base_query_assure = base_query_assure.filter(created_at__range=[start_date, end_date])
        base_query_life = base_query_life.filter(created_at__range=[start_date, end_date])

    # Agrupar resultados por agent_usa y status_color
    sales_query = base_query_supp.values('agent_usa', 'status_color').annotate(total_sales=Count('id')).order_by('agent_usa', 'status_color')
    sales_query_assure = base_query_assure.values('agent_usa', 'status_color').annotate(total_sales=Count('id')).order_by('agent_usa', 'status_color')
    sales_query_life = base_query_life.values('agent_usa', 'status_color').annotate(total_sales=Count('id')).order_by('agent_usa', 'status_color')

    agents_sales = {}
    status_colors = [1, 2, 3, 4]

    def procesar_entry(entry):
        agent_name = entry['agent_usa']
        status_color = entry['status_color']
        total_sales = entry['total_sales']
        short_name = Truncator(agent_name).chars(8)

        if short_name not in agents_sales:
            agents_sales[short_name] = {f'status_color_{i}': 0 for i in status_colors}
            agents_sales[short_name]['total_sales'] = 0

        agents_sales[short_name][f'status_color_{status_color}'] += total_sales
        agents_sales[short_name]['total_sales'] += total_sales

    for entry in sales_query:
        procesar_entry(entry)
    for entry in sales_query_assure:
        procesar_entry(entry)
    for entry in sales_query_life:
        procesar_entry(entry)

    return agents_sales

def salesBonusAgent(request, company_id, start_date=None, end_date=None):
    
    if not start_date and not end_date:
        today = timezone.now()
        first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if today.month == 12:
            last_day_of_month = today.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
        else:
            next_month = today.replace(day=28) + timedelta(days=4)  # siempre cae en el mes siguiente
            last_day_of_month = next_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(seconds=1)
    else:
        start_date = timezone.make_aware(
            datetime.datetime.strptime(start_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
        )
        end_date = timezone.make_aware(
            datetime.datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)
        )

        first_day_of_month = start_date
        last_day_of_month = end_date

    filtro_fecha = Q(created_at__range=(first_day_of_month, last_day_of_month))
    filtro_company = Q(company_id=company_id) if not request.user.is_superuser else Q()

    agents = Users.objects.filter(filtro_company)
    ventasAgentes = []

    for agente in agents:
        row = {
            'id': agente.id,  # Agregar el id del agente aquí
            'nombre': agente.get_full_name() if hasattr(agente, 'get_full_name') else agente.username,
            'obamacare': ObamaCare.objects.filter(Q(agent=agente) & Q(status_color=3) & filtro_fecha & filtro_company).count(),
            'obamacarePendiente': ObamaCare.objects.filter(Q(agent=agente), Q(status_color__in = [1,2]),filtro_fecha, filtro_company).count(),
            'supp': Supp.objects.filter(Q(agent=agente), Q(status_color=3), filtro_fecha, filtro_company).count(),
            'suppPendiente': Supp.objects.filter(Q(agent=agente), Q(status_color__in = [1,2]), filtro_fecha, filtro_company).count(),
            'medicare': Medicare.objects.filter(Q(agent=agente), Q(status_color=3), filtro_fecha, filtro_company).count(),
            'medicarePendiente': Medicare.objects.filter(Q(agent=agente), Q(status_color__in = [1,2]), filtro_fecha, filtro_company).count(),
            'assure': ClientsAssure.objects.filter(Q(agent=agente), Q(status_color=3), filtro_fecha, filtro_company).count(),
            'assurePendiente': ClientsAssure.objects.filter(Q(agent=agente), Q(status_color__in = [1,2]), filtro_fecha, filtro_company).count(),
            'life_insurance': ClientsLifeInsurance.objects.filter(Q(agent=agente), Q(status_color=3), filtro_fecha, filtro_company).count(),
            'life_insurancePendiente': ClientsLifeInsurance.objects.filter(Q(agent=agente), Q(status_color__in = [1,2]), filtro_fecha, filtro_company).count(),
        }

        # Calcular el total horizontal por agente
        row['total'] = sum([
            row['obamacare'], row['obamacarePendiente'],
            row['supp'], row['suppPendiente'],
            row['medicare'], row['medicarePendiente'],
            row['assure'], row['assurePendiente'],
            row['life_insurance'], row['life_insurancePendiente']
        ])

        if any([
            row['obamacare'], row['obamacarePendiente'],
            row['supp'], row['suppPendiente'],
            row['medicare'], row['medicarePendiente'],
            row['assure'], row['assurePendiente'],
            row['life_insurance'], row['life_insurancePendiente']
        ]):
            ventasAgentes.append(row)

    return ventasAgentes

def saleClientStatusObama(request, company_id, start_date=None, end_date=None):

    company_filter = {'company': company_id} if not request.user.is_superuser else {}
    # Obtener los IDs de ObamaCare que están en CustomerRedFlag
    excluded_obama_ids = CustomerRedFlag.objects.values('obamacare')

    # Consulta para Registered
    sales_query_registered = ObamaCare.objects.select_related('agent','client').annotate(
        truncated_agent_usa=Substr('agent_usa', 1, 8)).filter(status_color = 1, is_active = True,  **company_filter).exclude( id__in=Subquery(excluded_obama_ids))
    
    # Consulta para Proccessing
    sales_query_proccessing = ObamaCare.objects.select_related('agent','client').annotate(
        truncated_agent_usa=Substr('agent_usa', 1, 8)).filter(status_color = 2, is_active = True,  **company_filter ).exclude( id__in=Subquery(excluded_obama_ids))

    # Consulta para Profiling
    sales_query_profiling = ObamaCare.objects.select_related('agent','client').annotate(
        truncated_agent_usa=Substr('agent_usa', 1, 8)).filter(status_color = 3, is_active = True,  **company_filter ).exclude( id__in=Subquery(excluded_obama_ids))
    
    # Consulta para Canceled
    sales_query_canceled = ObamaCare.objects.select_related('agent','client').annotate(
        truncated_agent_usa=Substr('agent_usa', 1, 8)).filter(status_color = 4, is_active = True,  **company_filter ).exclude( id__in=Subquery(excluded_obama_ids))

    # Si no se proporcionan fechas, filtrar por el mes actual
    if not start_date and not end_date:
        today = timezone.now()
        first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        if today.month == 12:
            last_day_of_month = today.replace(day=31, hour=23, minute=59, second=59, microsecond=999999)
        else:
            last_day_of_month = (first_day_of_month.replace(month=first_day_of_month.month + 1) - timezone.timedelta(seconds=1))

        sales_query_registered = sales_query_registered.filter(created_at__range=[first_day_of_month, last_day_of_month])
        sales_query_proccessing = sales_query_proccessing.filter(created_at__range=[first_day_of_month, last_day_of_month])
        sales_query_profiling = sales_query_profiling.filter(created_at__range=[first_day_of_month, last_day_of_month])
        sales_query_canceled = sales_query_canceled.filter(created_at__range=[first_day_of_month, last_day_of_month])


    # Si se proporcionan fechas, filtrar por el rango de fechas
    elif start_date and end_date:
        start_date = timezone.make_aware(
            datetime.datetime.strptime(start_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
        )
        end_date = timezone.make_aware(
            datetime.datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)
        )

        sales_query_registered = sales_query_registered.filter(created_at__range=[start_date, end_date])
        sales_query_proccessing = sales_query_proccessing.filter(created_at__range=[start_date, end_date])
        sales_query_profiling = sales_query_profiling.filter(created_at__range=[start_date, end_date])
        sales_query_canceled = sales_query_canceled.filter(created_at__range=[start_date, end_date])

    countRegistered = sales_query_registered.count()
    countProccsing = sales_query_proccessing.count()
    countProfiling = sales_query_profiling.count()
    countCanceled = sales_query_canceled.count()
    
    return sales_query_registered,sales_query_proccessing,sales_query_profiling,sales_query_canceled,countRegistered,countProccsing,countProfiling,countCanceled

def saleClientStatusSupp(request, company_id, start_date=None, end_date=None):

    company_filter = {'company': company_id} if not request.user.is_superuser else {}

    # Consulta para Registered
    registered_supp = Supp.objects.select_related('agent','client').annotate(
        truncated_agent_usa=Substr('agent_usa', 1, 8)).filter(status_color = 1, is_active = True,  **company_filter)
    registered_assure = ClientsAssure.objects.select_related('agent').annotate(
        truncated_agent_usa=Substr('agent_usa', 1, 8)).filter(status_color = 1, is_active = True,  **company_filter)
    
    # Consulta para Proccessing
    proccessing_supp = Supp.objects.select_related('agent','client').annotate(
        truncated_agent_usa=Substr('agent_usa', 1, 8)).filter(status_color = 2, is_active = True,  **company_filter ) 
    proccessing_assure = ClientsAssure.objects.select_related('agent').annotate(
        truncated_agent_usa=Substr('agent_usa', 1, 8)).filter(status_color = 2, is_active = True,  **company_filter ) 

    # Consulta para Active
    active_supp = Supp.objects.select_related('agent','client').annotate(
        truncated_agent_usa=Substr('agent_usa', 1, 8)).filter(status_color = 3, is_active = True,  **company_filter ) 
    active_assure = ClientsAssure.objects.select_related('agent').annotate(
        truncated_agent_usa=Substr('agent_usa', 1, 8)).filter(status_color = 3, is_active = True,  **company_filter ) 
    
    # Consulta para Canceled
    canceled_supp = Supp.objects.select_related('agent','client').annotate(
        truncated_agent_usa=Substr('agent_usa', 1, 8)).filter(status_color = 4, is_active = True,  **company_filter )
    canceled_assure = ClientsAssure.objects.select_related('agent').annotate(
        truncated_agent_usa=Substr('agent_usa', 1, 8)).filter(status_color = 4, is_active = True,  **company_filter )

    # Si no se proporcionan fechas, filtrar por el mes actual
    if not start_date and not end_date:
        today = timezone.now()
        first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        if today.month == 12:
            last_day_of_month = today.replace(day=31, hour=23, minute=59, second=59, microsecond=999999)
        else:
            last_day_of_month = (first_day_of_month.replace(month=first_day_of_month.month + 1) - timezone.timedelta(seconds=1))

        registered_supp = registered_supp.filter(created_at__range=[first_day_of_month, last_day_of_month])
        proccessing_supp = proccessing_supp.filter(created_at__range=[first_day_of_month, last_day_of_month])
        active_supp = active_supp.filter(created_at__range=[first_day_of_month, last_day_of_month])
        canceled_supp = canceled_supp.filter(created_at__range=[first_day_of_month, last_day_of_month])

        registered_assure = registered_assure.filter(created_at__range=[first_day_of_month, last_day_of_month])
        proccessing_assure = proccessing_assure.filter(created_at__range=[first_day_of_month, last_day_of_month])
        active_assure = active_assure.filter(created_at__range=[first_day_of_month, last_day_of_month])
        canceled_assure = canceled_assure.filter(created_at__range=[first_day_of_month, last_day_of_month])

        countRegisteredSupp = registered_assure.count() + registered_supp.count()
        countProccsingSupp = proccessing_assure.count() + proccessing_supp.count()
        countActiveSupp = active_assure.count() + active_supp.count()
        countCanceledSupp = canceled_assure.count() + canceled_supp.count()

    # Si se proporcionan fechas, filtrar por el rango de fechas
    elif start_date and end_date:
        start_date = timezone.make_aware(
            datetime.datetime.strptime(start_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
        )
        end_date = timezone.make_aware(
            datetime.datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)
        )

        registered_supp = registered_supp.filter(created_at__range=[start_date, end_date])
        proccessing_supp = proccessing_supp.filter(created_at__range=[start_date, end_date])
        active_supp = active_supp.filter(created_at__range=[start_date, end_date])
        canceled_supp = canceled_supp.filter(created_at__range=[start_date, end_date])

        registered_assure = registered_assure.filter(created_at__range=[start_date, end_date])
        proccessing_assure = proccessing_assure.filter(created_at__range=[start_date, end_date])
        active_assure = active_assure.filter(created_at__range=[start_date, end_date])
        canceled_assure = canceled_assure.filter(created_at__range=[start_date, end_date])

        countRegisteredSupp = registered_assure.count() + registered_supp.count()
        countProccsingSupp = proccessing_assure.count() + proccessing_supp.count()
        countActiveSupp = active_assure.count() + active_supp.count()
        countCanceledSupp = canceled_assure.count() + canceled_supp.count()

    
    return registered_supp,proccessing_supp,active_supp,canceled_supp,countRegisteredSupp,countProccsingSupp,countActiveSupp,countCanceledSupp,registered_assure,proccessing_assure,active_assure,canceled_assure

@login_required(login_url='/login') 
@company_ownership_required_sinURL
def customerPerformance(request):

    company_id = request.company_id  # Obtener company_id desde request
    # Definir el filtro de compañía (será un diccionario vacío si es superusuario)
    company_filter = {'company': company_id} if not request.user.is_superuser else {}
    company_filter2 = {'obamacare__company': company_id} if not request.user.is_superuser else {}

    # Obtener los IDs de ObamaCare que están en CustomerRedFlag
    excluded_obama_ids = CustomerRedFlag.objects.filter(date_completed__isnull=True).values('obamacare')

    if request.method == 'POST':
        # Convertir fechas a objetos datetime con zona horaria
        start_date = timezone.make_aware(
            datetime.datetime.strptime(request.POST.get('start_date'), '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
        )
        end_date = timezone.make_aware(
            datetime.datetime.strptime(request.POST.get('end_date'), '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)
        )
    else:
        now = datetime.datetime.now()

        # Primer día del mes actual
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Último día del mes actual
        next_month = now.replace(day=28) + timedelta(days=4)  # Garantiza que pasamos al siguiente mes
        end_date = next_month.replace(day=1, hour=23, minute=59, second=59, microsecond=999999) - timedelta(days=1)

    obamacare = ObamaCare.objects.filter(
        created_at__range=(start_date, end_date),
        is_active=1,
        **company_filter
    ).exclude(
        status='NO CALL'
    ).exclude(
        id__in=Subquery(excluded_obama_ids)
    )
    totalEnroled = obamacare.exclude(profiling='NO')
    totalNoEnroled = obamacare.filter(profiling='NO').count()
    totalOtherParty = obamacare.filter(status='OTHER PARTY').count()
    enroledActiveCms = totalEnroled.filter(Q(status='ACTIVE') | Q(status='SELF-ENROLMENT')).count()
    totalEnroledNoActiveCms = totalEnroled.exclude(Q(status='ACTIVE') | Q(status='SELF-ENROLMENT')).count()
    totalActiveCms = obamacare.filter(Q(status='ACTIVE') | Q(status='SELF-ENROLMENT')).count()
    totalNoActiveCms = obamacare.exclude(Q(status='ACTIVE') | Q(status='SELF-ENROLMENT')).count()

    documents = DocumentObama.objects.select_related('agent_create').filter(created_at__range=(start_date, end_date), **company_filter2)
    appointments = AppointmentClient.objects.select_related('agent_create').filter(created_at__range=(start_date, end_date), **company_filter2)
    payments = Payments.objects.select_related('agent').filter(created_at__range=(start_date, end_date), **company_filter)

    # Obtener agentes Customer, excluyendo a Maria Tinoco y Carmen Rodriguez
    agents = Users.objects.prefetch_related('usaAgents').filter(role='C', is_active=1, **company_filter).exclude(username__in=('MariaCaTi', 'CarmenR'))
    agent_performance = {}


    for agent in agents:
         
        usaAgentNames = list(agent.usaAgents.values_list('name', flat=True))
        matchingObamacare = obamacare.filter(agent_usa__in=usaAgentNames)

        full_name = f"{agent.first_name} {agent.last_name}".strip()
        matchingObamacare = obamacare.filter(agent_usa__in=usaAgentNames)
        enroledActiveCmsPerAgent = matchingObamacare.filter(Q(status='ACTIVE') | Q(status='SELF-ENROLMENT'))
        enroledNoActiveCmsPerAgent = matchingObamacare.exclude(Q(status='ACTIVE') | Q(status='SELF-ENROLMENT'))
        percentageEnroledActiveCms = format_decimal(
            (enroledActiveCmsPerAgent.count() / matchingObamacare.count()) * 100
        ) if matchingObamacare.count() else 0

        # Inicializar la clave si no existe
        if full_name not in agent_performance:
            agent_performance[full_name] = {
                'totalEnroled': 0,
                'percentageEnroled': 0,
                'enroledActiveCms': 0,
                'percentageEnroledActiveCms': 0,
                'enroledNoActiveCms': 0,
                'percentageEnroledNoActiveCms': 0,
                'percentageTotalActiveCms': 0,
                'percentageTotalNoActiveCms': 0,
                'documents': 0,
                'appointments': 0,
                'payments': 0,
                'personalGoal': 0
            }

        # Asignar valores con validación de división por cero
        agent_performance[full_name]['totalEnroled'] = matchingObamacare.count()
        agent_performance[full_name]['percentageEnroled'] = format_decimal(
            (matchingObamacare.count() / obamacare.count()) * 100
        ) if obamacare.count() else 0
        agent_performance[full_name]['enroledActiveCms'] = enroledActiveCmsPerAgent
        agent_performance[full_name]['percentageEnroledActiveCms'] = percentageEnroledActiveCms
        agent_performance[full_name]['enroledNoActiveCms'] = enroledNoActiveCmsPerAgent
        agent_performance[full_name]['percentageEnroledNoActiveCms'] = format_decimal(
            (enroledNoActiveCmsPerAgent.count() / matchingObamacare.count()) * 100
        ) if matchingObamacare.count() else 0
        agent_performance[full_name]['percentageTotalActiveCms'] = format_decimal(
            (enroledActiveCmsPerAgent.count() / obamacare.count()) * 100
        ) if obamacare.count() else 0
        agent_performance[full_name]['percentageTotalNoActiveCms'] = format_decimal(
            (enroledNoActiveCmsPerAgent.count() / obamacare.count()) * 100
        ) if obamacare.count() else 0

        agent_performance[full_name]['documents'] = documents.filter(agent_create=agent).count()
        agent_performance[full_name]['appointments'] = appointments.filter(agent_create=agent).count()
        agent_performance[full_name]['payments'] = payments.filter(agent=agent).count()

        #Meta personal
        if percentageEnroledActiveCms == 100 and percentageEnroledActiveCms == 100:
            agent_performance[full_name]['personalGoal'] = 1
        elif percentageEnroledActiveCms > 89.9 and percentageEnroledActiveCms > 89.9:
            agent_performance[full_name]['personalGoal'] = 2
        elif percentageEnroledActiveCms > 79.9 and percentageEnroledActiveCms > 79.9:
            agent_performance[full_name]['personalGoal'] = 3
        else:
            agent_performance[full_name]['personalGoal'] = 4
            
    # Evitar divisiones por cero en todos los cálculos
    obamacare_count = obamacare.count() if obamacare.exists() else 1
    totalEnroled_count = totalEnroled.count() if totalEnroled.exists() else 1

    #Verificacion de bono:
    percentageEnroled = (totalEnroled.count() / obamacare_count) * 100
    percentageEnroledActiveCms = (enroledActiveCms / totalEnroled_count) * 100
    if percentageEnroled > 89.9 and percentageEnroledActiveCms > 89.9:
        groupGoal = 1
    elif percentageEnroled > 79.9 and percentageEnroledActiveCms > 79.9:
        groupGoal = 2
    else:
        groupGoal = 3

    #Diferencia entre total
    totalAgentsPayments = 0
    for agent, details in agent_performance.items():
        totalAgentsPayments += details['payments']

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'totalObamacare': obamacare.count(),
        'totalEnroled': totalEnroled.count(),
        'percentageEnroled': format_decimal(percentageEnroled),
        'totalNoEnroled': format_decimal(totalNoEnroled),
        'percentageNoEnroled': format_decimal((totalNoEnroled / obamacare_count) * 100),
        'totalOtherParty': totalOtherParty,
        'percentageOtherParty': format_decimal((totalOtherParty / obamacare_count) * 100),
        'enroledActiveCms': enroledActiveCms,
        'percentageEnroledActiveCms': format_decimal(percentageEnroledActiveCms),
        'totalEnroledNoActiveCms': totalEnroledNoActiveCms,
        'percentageNoActiveCms': format_decimal((totalEnroledNoActiveCms / totalEnroled_count) * 100),
        'totalActiveCms': totalActiveCms,
        'percentageTotalActiveCms': format_decimal((totalActiveCms / obamacare_count) * 100),
        'totalNoActiveCms': totalNoActiveCms,
        'percentageTotalNoActiveCms': format_decimal((totalNoActiveCms / obamacare_count) * 100),
        'appointmentsTotal':appointments.count(),
        'documentsTotal': documents.count(),
        'paymentsTotal':payments.count(),
        'agentPerformance': agent_performance,

        #Messages
        'totalAgentsPayments':totalAgentsPayments,
        'groupGoal':groupGoal
    }
    return render(request, 'customerReports/customerPerformance.html', context)

@company_ownership_required_sinURL
def table6Week(request):

    # Obtener la fecha actual
    today = datetime.datetime.today()

    # Calcular el domingo anterior (inicio de la semana actual)
    startOfCurrentWeek = today - timedelta(days=today.weekday() + 1)

    # Calcular el domingo siguiente (fin de la semana actual)
    endOfCurrentWeek = startOfCurrentWeek + timedelta(days=6)

    # Calcular el inicio de las 6 semanas (domingo anterior a 6 semanas atrás)
    startDate = startOfCurrentWeek - timedelta(weeks=5)  # 5 semanas atrás desde el inicio de la semana actual

    # Convertir las fechas a "offset-aware"
    startDate = make_aware(startDate)
    endOfCurrentWeek = make_aware(endOfCurrentWeek)

    # Número total de semanas (6 semanas, incluyendo la semana actual)
    numWeeks = 6

    # Calcular los rangos de las semanas
    weekRanges = []
    for i in range(numWeeks):
        weekStart = startDate + timedelta(weeks=i)
        weekEnd = weekStart + timedelta(days=6)
        weekRange = f"{weekStart.strftime('%d/%m')} - {weekEnd.strftime('%d/%m')}"
        weekRanges.append(weekRange)

    # Inicializar diccionario de ventas para las últimas 6 semanas
    excludedUsernames = ['Calidad01', 'mariluz', 'MariaCaTi','StephanieMkt','CarmenR']  # Excluimos a gente que no debe aparecer en la vista
    userRoles = ['A', 'C', 'S']

    company_id = request.company_id  # Obtener company_id desde request
    company_filter = {'company': company_id} if not request.user.is_superuser else {}

    # Obtener los IDs de ObamaCare que están en CustomerRedFlag
    excluded_obama_ids = CustomerRedFlag.objects.values('obamacare')

    users = Users.objects.filter(role__in=userRoles, is_active=True,  **company_filter).exclude(username__in=excludedUsernames)

    # Filtrar todas las ventas realizadas en las últimas 6 semanas
    obamaSales = ObamaCare.objects.filter(created_at__range=[startDate, endOfCurrentWeek],  **company_filter).exclude( id__in=Subquery(excluded_obama_ids))
    suppSales = Supp.objects.filter(created_at__range=[startDate, endOfCurrentWeek],  **company_filter)
    assureSales = ClientsAssure.objects.filter(created_at__range=[startDate, endOfCurrentWeek],  **company_filter)
        
    # Agregar el conteo de pólizas activas para las últimas 6 semanas
    activeObamaPolicies = ObamaCare.objects.filter(status='Active', created_at__range=[startDate, endOfCurrentWeek],is_active = True,  **company_filter).exclude( id__in=Subquery(excluded_obama_ids))
    activeSuppPolicies = Supp.objects.filter(status='Active', created_at__range=[startDate, endOfCurrentWeek], is_active = True,  **company_filter)
    activeAssurePolicies = ClientsAssure.objects.filter(status='Active', created_at__range=[startDate, endOfCurrentWeek], is_active = True,  **company_filter)

    salesSummary = {
        user.username: {
            f"Week{i + 1}": {
                "obama": 0, 
                "activeObama": 0, 
                "totalObama": 0,  # Total Obama = obama + activeObama
                "supp": 0, 
                "activeSupp": 0, 
                "totalSupp": 0,   # Total Supp = supp + activeSupp
                "total": 0        # Total General = totalObama + totalSupp
            }
            for i in range(numWeeks)
        } for user in users
    }

    # Procesar las ventas de Obamacare y Supp para las últimas 6 semanas
    for sale in obamaSales:
        agentName = sale.agent.username
        if sale.agent.is_active:
            if agentName not in excludedUsernames:
                saleWeek = (sale.created_at - startDate).days // 7  # Calcular la semana (0 a 5)
                if 0 <= saleWeek < numWeeks:
                    try:
                        salesSummary[agentName][f"Week{saleWeek + 1}"]["obama"] += 1
                        salesSummary[agentName][f"Week{saleWeek + 1}"]["totalObama"] += 1
                        salesSummary[agentName][f"Week{saleWeek + 1}"]["total"] += 1
                    except KeyError:
                        pass

    for sale in suppSales:
        agentName = sale.agent.username
        if sale.agent.is_active:
            if agentName not in excludedUsernames:
                saleWeek = (sale.created_at - startDate).days // 7  # Calcular la semana (0 a 5)
                if 0 <= saleWeek < numWeeks:
                    try:
                        salesSummary[agentName][f"Week{saleWeek + 1}"]["supp"] += 1
                        salesSummary[agentName][f"Week{saleWeek + 1}"]["totalSupp"] += 1
                        salesSummary[agentName][f"Week{saleWeek + 1}"]["total"] += 1
                    except KeyError:
                        pass
    
    for sale in assureSales:
        agentName = sale.agent.username
        if sale.agent.is_active:
            if agentName not in excludedUsernames:
                saleWeek = (sale.created_at - startDate).days // 7  # Calcular la semana (0 a 5)
                if 0 <= saleWeek < numWeeks:
                    try:
                        salesSummary[agentName][f"Week{saleWeek + 1}"]["supp"] += 1
                        salesSummary[agentName][f"Week{saleWeek + 1}"]["totalSupp"] += 1
                        salesSummary[agentName][f"Week{saleWeek + 1}"]["total"] += 1
                    except KeyError:
                        pass

    for policy in activeObamaPolicies:
        agentName = policy.agent.username
        if policy.agent.is_active:
            if agentName not in excludedUsernames:
                policyWeek = (policy.created_at - startDate).days // 7  # Calcular la semana (0 a 5)
                if 0 <= policyWeek < numWeeks:
                    try:
                        salesSummary[agentName][f"Week{policyWeek + 1}"]["activeObama"] += 1
                        salesSummary[agentName][f"Week{policyWeek + 1}"]["totalObama"] += 1
                        salesSummary[agentName][f"Week{policyWeek + 1}"]["total"] += 1
                    except KeyError:
                        pass

    for policy in activeSuppPolicies:
        agentName = policy.agent.username
        if policy.agent.is_active:
            if agentName not in excludedUsernames:
                policyWeek = (policy.created_at - startDate).days // 7  # Calcular la semana (0 a 5)
                if 0 <= policyWeek < numWeeks:
                    try:
                        salesSummary[agentName][f"Week{policyWeek + 1}"]["activeSupp"] += 1
                        salesSummary[agentName][f"Week{policyWeek + 1}"]["totalSupp"] += 1
                        salesSummary[agentName][f"Week{policyWeek + 1}"]["total"] += 1
                    except KeyError:
                        pass

    for policy in activeAssurePolicies:
        agentName = policy.agent.username
        if policy.agent.is_active:
            if agentName not in excludedUsernames:
                policyWeek = (policy.created_at - startDate).days // 7  # Calcular la semana (0 a 5)
                if 0 <= policyWeek < numWeeks:
                    try:
                        salesSummary[agentName][f"Week{policyWeek + 1}"]["activeSupp"] += 1
                        salesSummary[agentName][f"Week{policyWeek + 1}"]["totalSupp"] += 1
                        salesSummary[agentName][f"Week{policyWeek + 1}"]["total"] += 1
                    except KeyError:
                        pass

    # Convertir el diccionario para usar "first_name last_name" como clave
    finalSummary = {}

    for user in users:
        fullName = f"{user.first_name} {user.last_name}".strip()
        finalSummary[fullName] = salesSummary[user.username]

    return finalSummary, weekRanges

@login_required(login_url='/login')
@company_ownership_required_sinURL
def sales6WeekReport(request):

    # Obtener el resumen de ventas para las últimas 6 semanas
    finalSummary, weekRanges = table6Week(request)

    # Obtener los datos para la gráfica
    chart_data = chart6WeekSale(request)

    # Pasar los datos a la plantilla
    context = {
        'finalSummary': finalSummary,  # Resumen de ventas de las últimas 6 semanas
        'weekRanges': weekRanges,      # Rangos de fechas de las últimas 6 semanas
        'chart_data': chart_data,      # Datos para la gráfica
    }

    # Renderizar la plantilla con los datos
    return render(request, 'saleReports/sale6Week.html', context)

def weekSalesSummary(request, week_number):
    # Obtener el año actual
    current_year = datetime.datetime.today().year

    # Calcular el lunes de la semana seleccionada
    startOfWeek = datetime.datetime.fromisocalendar(current_year, week_number, 1)  # 1 = Lunes
    # Calcular el sábado de la semana seleccionada
    endOfWeek = startOfWeek + timedelta(days=5)  # Lunes + 5 días = Sábado

    # Convertir las fechas a "offset-aware" (si es necesario)
    startOfWeek = make_aware(startOfWeek)
    endOfWeek = make_aware(endOfWeek)

    # Inicializar variables de totales generales
    total_aca = 0
    total_supp = 0
    totalActiveAca = 0
    totalActiveSupp = 0

    # Inicializar diccionario de ventas para la semana seleccionada
    excludedUsernames = ['Calidad01', 'mariluz', 'MariaCaTi', 'StephanieMkt', 'CarmenR','tv','zohiraDuarte', 'vladimirDeLaHoz']  # Excluimos a gente que no debe aparecer en la vista
    userRoles = ['A', 'C', 'S','SUPP','Admin']

    company_id = request.user.company  # Obtener company_id desde request
    company_filter = {'company': company_id} if not request.user.is_superuser else {}

    # Obtener los IDs de ObamaCare que están en CustomerRedFlag
    excluded_obama_ids = CustomerRedFlag.objects.values('obamacare')

    users = Users.objects.exclude(username__in=excludedUsernames).filter(role__in=userRoles, is_active=True,  **company_filter)

    # Filtrar todas las ventas realizadas en la semana seleccionada
    obamaSales = ObamaCare.objects.filter(created_at__range=[startOfWeek, endOfWeek],  **company_filter).exclude( id__in=Subquery(excluded_obama_ids))
    suppSales = Supp.objects.filter(created_at__range=[startOfWeek, endOfWeek],  **company_filter)
    assureSales = ClientsAssure.objects.filter(created_at__range=[startOfWeek, endOfWeek],  **company_filter)

    # Agregar el conteo de pólizas activas para la semana seleccionada
    activeObamaPolicies = ObamaCare.objects.filter(status='Active', created_at__range=[startOfWeek, endOfWeek], is_active=True,  **company_filter).exclude( id__in=Subquery(excluded_obama_ids))
    activeSuppPolicies = Supp.objects.filter(status='Active', created_at__range=[startOfWeek, endOfWeek], is_active=True,  **company_filter)
    activeAssurePolicies = ClientsAssure.objects.filter(status='Active', created_at__range=[startOfWeek, endOfWeek], is_active=True,  **company_filter)

    salesSummary = {
        user.username: {
            "obama": 0,
            "activeObama": 0,
            "supp": 0,
            "activeSupp": 0,
            "total": 0,       # Total General = totalObama + totalSupp
            "clientes_obama": [],  # Lista de clientes de ObamaCare
            "clientes_supp": []    # Lista de clientes de Supp
        } for user in users
    }

    # Procesar las ventas de Obamacare para la semana seleccionada
    for sale in obamaSales:
        agentName = sale.agent.username
        if sale.agent.is_active and agentName not in excludedUsernames:
            salesSummary[agentName]["obama"] += 1
            salesSummary[agentName]["total"] += 1
            total_aca += 1  # Incrementar total general de ACA

            # Agregar detalles del cliente
            cliente_info = {
                "nombre": f"{sale.client.first_name} {sale.client.last_name}",
                "fecha_poliza": sale.created_at.strftime('%d/%m/%Y'),
                "estatus": sale.status,
                "estatus_color": sale.status_color
            }
            salesSummary[agentName]["clientes_obama"].append(cliente_info)

    # Procesar las ventas de Supp para la semana seleccionada
    for sale in suppSales:
        agentName = sale.agent.username
        if sale.agent.is_active and agentName not in excludedUsernames:
            salesSummary[agentName]["supp"] += 1
            salesSummary[agentName]["total"] += 1
            total_supp += 1  # Incrementar total general de SUPP

            # Agregar detalles del cliente
            cliente_info = {
                "nombre": f"{sale.client.first_name} {sale.client.last_name}",
                "fecha_poliza": sale.created_at.strftime('%d/%m/%Y'),
                "estatus": sale.status,
                "estatus_color": sale.status_color
            }
            salesSummary[agentName]["clientes_supp"].append(cliente_info)

    for sale in assureSales:
        agentName = sale.agent.username
        if sale.agent.is_active and agentName not in excludedUsernames:
            salesSummary[agentName]["supp"] += 1
            salesSummary[agentName]["total"] += 1
            total_supp += 1  # Incrementar total general de SUPP

            # Agregar detalles del cliente
            cliente_info = {
                "nombre": f"{sale.first_name} {sale.last_name}",
                "fecha_poliza": sale.created_at.strftime('%d/%m/%Y'),
                "estatus": sale.status,
                "estatus_color": sale.status_color
            }
            salesSummary[agentName]["clientes_supp"].append(cliente_info)

    for policy in activeObamaPolicies:
        agentName = policy.agent.username
        if policy.agent.is_active and agentName not in excludedUsernames:
            salesSummary[agentName]["activeObama"] += 1
            totalActiveAca += 1  # Incrementar total general de ACA

    for policy in activeSuppPolicies:
        agentName = policy.agent.username
        if policy.agent.is_active and agentName not in excludedUsernames:
            salesSummary[agentName]["activeSupp"] += 1
            totalActiveSupp += 1  # Incrementar total general de SUPP

    for policy in activeAssurePolicies:
        agentName = policy.agent.username
        if policy.agent.is_active and agentName not in excludedUsernames:
            salesSummary[agentName]["activeSupp"] += 1
            totalActiveSupp += 1  # Incrementar total general de SUPP

    # Convertir el diccionario para usar "first_name last_name" como clave
    finalSummary = {}
    for user in users:
        fullName = f"{user.first_name} {user.last_name}".strip()
        finalSummary[fullName] = salesSummary[user.username]

    # Agregar los totales generales al resumen
    finalSummary["TOTAL_GENERAL"] = {
        "total_aca": total_aca,
        "total_supp": total_supp,
        "totalActiveAca": totalActiveAca,
        "totalActiveSupp": totalActiveSupp,
        "total_general": total_aca + total_supp
    }

    # Rango de fechas de la semana seleccionada
    weekRange = f"{startOfWeek.strftime('%d/%m')} - {endOfWeek.strftime('%d/%m')}"

    return finalSummary, weekRange

@login_required(login_url='/login')
def weekSalesWiew(request):

    if request.method == 'POST':
        # Obtener el número de la semana del formulario
        week_number = int(request.POST.get('week_number'))

        # Llamar a la función de lógica para obtener el resumen
        resumen_semana, rango_fechas = weekSalesSummary(request, week_number)

        # Renderizar la plantilla con los resultados
        return render(request, 'saleReports/weekSalesWiew.html', {
            'resumen_semana': resumen_semana,
            'rango_fechas': rango_fechas,
            'week_number': week_number
        })

    # Si no es POST, mostrar el formulario vacío
    return render(request, 'saleReports/weekSalesWiew.html')

@login_required(login_url='/login')
@company_ownership_required_sinURL
def reports(request):

    company_id = request.company_id  # Obtener company_id desde request
    # Definir el filtro de compañía (será un diccionario vacío si es superusuario)
    company_filter = {'company': company_id} if not request.user.is_superuser else {}
    company_filter2 = {'obamacare__company': company_id} if not request.user.is_superuser else {}

    #Reports de Paymet!
    payments = Payments.objects.filter(**company_filter).values('month').annotate(total=Count('id')).order_by('month')
    # Calcular el total general de todos los meses
    total_general = Payments.objects.filter(**company_filter).aggregate(total=Count('id'))['total']

    #Reports de Action Required
    # Cantidad de registros donde agent_completed es NULL
    pending_count = CustomerRedFlag.objects.filter(agent_completed__isnull=True, **company_filter2).count()

    # Cantidad de registros donde agent_completed NO es NULL
    completed_count = CustomerRedFlag.objects.filter(agent_completed__isnull=False, **company_filter2).count()

    # Total de registros en CustomerRedFlag
    total_count = CustomerRedFlag.objects.filter(**company_filter2).count()


    context = {
        'payments' : payments, 
        'total' : total_general,
        'pending_count' : pending_count,
        'completed_count' : completed_count,
        'total_count' : total_count
        }
    
    return render(request, 'saleReports/reports.html', context)

@login_required(login_url='/login')
@company_ownership_required_sinURL
def customerTypification(request) :

    company_id = request.company_id  # Obtener company_id desde request
    # Definir el filtro de compañía (será un diccionario vacío si es superusuario)
    company_filter = {'client__company': company_id} if not request.user.is_superuser else {}

    # Obtener la fecha actual
    now = timezone.now()

    # Si se proporcionan fechas, filtrar por el rango de fechas
    if request.method == 'POST':
        startDatePost = request.POST['start_date']
        endDatePost = request.POST['end_date']
        startDate = timezone.make_aware(
            datetime.datetime.strptime(startDatePost, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
        )
        endDate = timezone.make_aware(
            datetime.datetime.strptime(endDatePost, '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)
        )
    else:
        startDate = timezone.make_aware(
            datetime.datetime(now.year, now.month, 1, 0, 0, 0, 0)
        )
        endDate = timezone.make_aware(
            datetime.datetime(now.year, now.month + 1, 1, 0, 0, 0, 0) - timezone.timedelta(microseconds=1)
        )
            
    agents = ObservationCustomer.objects.values('agent__username', 'agent__first_name', 'agent__last_name').distinct().filter(created_at__range=[startDate, endDate],is_active = True, **company_filter)
    agent_data = []

    for agent in agents:
        username = agent['agent__username']
        full_name = f"{agent['agent__first_name']} {agent['agent__last_name']}"
        
        typifications = ObservationCustomer.objects.filter(
            agent__username=username
        ).annotate(
            individual_types=F('typification')
        ).values('individual_types').filter(is_active = True, **company_filter)
        
        type_count = {}
        total = 0
        for t in typifications:
            types = [typ.strip() for typ in t['individual_types'].split(',')]
            for typ in types:
                type_count[typ] = type_count.get(typ, 0) + 1
                total += 1

        agent_data.append({
            'username': username,
            'full_name': full_name,
            'typifications': type_count,
            'total': total
        })

    context = {
        'agent_data':agent_data,
        'startDate':startDate,
        'endDate':endDate
    }       
    
    return render(request, 'customerReports/customerTypification.html', context)

@login_required(login_url='/login') 
@company_ownership_required_sinURL
def typification(request):

    company_id = request.company_id  # Obtener company_id desde request
    # Definir el filtro de compañía (será un diccionario vacío si es superusuario)
    company_filter = {'company': company_id} if not request.user.is_superuser else {}
    company_filter2 = {'client__company': company_id} if not request.user.is_superuser else {}
        
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    agent = Users.objects.filter(role__in=['SUPP', 'C'], **company_filter )
    
    # Consulta base
    typification = ObservationCustomer.objects.select_related('agent', 'client').filter(is_active = True, **company_filter2)

    # Si no se proporcionan fechas, mostrar registros del mes actual   
    # Obtener el primer día del mes actual con zona horaria
    today = timezone.now()
    first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Obtener el último día del mes actual
    if today.month == 12:
        # Si es diciembre, el último día será el 31
        last_day_of_month = today.replace(day=31, hour=23, minute=59, second=59, microsecond=999999)
    else:
        # Para otros meses, usar el día anterior al primer día del siguiente mes
        last_day_of_month = (first_day_of_month.replace(month=first_day_of_month.month+1) - timezone.timedelta(seconds=1))
    
    typification = typification.filter(created_at__range=[first_day_of_month, last_day_of_month])

    if request.method == 'POST':

        # Obtener parámetros de fecha del request
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')       
        nameAgent = request.POST.get('agent')
        nameTypification = request.POST.get('typification')

        # Consulta base
        typification = ObservationCustomer.objects.select_related('agent', 'client').filter(is_active = True, **company_filter2)   
        
     
        # Convertir fechas a objetos datetime con zona horaria
        start_date = timezone.make_aware(
            datetime.datetime.strptime(start_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
        )
        end_date = timezone.make_aware(
            datetime.datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)
        )
        
        typification = typification.filter(
            created_at__range=[start_date, end_date],
            agent = nameAgent,
            typification__contains = nameTypification
        )

        # Ordenar por fecha de creación descendente
        typification = typification.order_by('-created_at')

        return render(request, 'customerReports/typification.html', {
            'typification': typification,
            'start_date': start_date,
            'end_date': end_date,
            'agents' : agent
        })

    return render(request, 'customerReports/typification.html', {
            'typification': typification,
            'start_date': start_date,
            'end_date': end_date,
            'agents' : agent
        })
