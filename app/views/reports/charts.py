# Standard Python libraries
import datetime
import json
from datetime import timedelta
from dateutil.relativedelta import relativedelta

# Django utilities
from django.utils.timezone import make_aware

# Django core libraries
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Subquery
from django.shortcuts import render

# Application-specific imports
from app.models import *
from app.views.utils import *
from ..decoratorsCompany import *

@company_ownership_required_sinURL
def chart6WeekSale(request):

    company_id = request.company_id  # Obtener company_id desde request
    # Definir el filtro de compañía (será un diccionario vacío si es superusuario)
    company_filter = {'company': company_id} if not request.user.is_superuser else {}

    # Obtener la fecha actual
    today = datetime.today()

    # Calcular el domingo anterior (inicio de la semana actual)
    startOfCurrentWeek = today - timedelta(days=today.weekday() + 1)

    # Calcular el inicio de las 6 semanas (domingo anterior a 6 semanas atrás)
    startDate = startOfCurrentWeek - timedelta(weeks=5)  # 5 semanas atrás desde el inicio de la semana actual

    # Convertir las fechas a "offset-aware"
    startDate = make_aware(startDate)
    endOfCurrentWeek = make_aware(startOfCurrentWeek + timedelta(days=6))

    # Número total de semanas (6 semanas, incluyendo la semana actual)
    numWeeks = 6

    # Calcular los rangos de las semanas
    weekRanges = []
    for i in range(numWeeks):
        weekStart = startDate + timedelta(weeks=i)
        weekEnd = weekStart + timedelta(days=6)
        weekRange = f"{weekStart.strftime('%d/%m')} - {weekEnd.strftime('%d/%m')}"
        weekRanges.append(weekRange)

    company_filter = {'company': company_id} if not request.user.is_superuser else {}

    # Obtener los IDs de ObamaCare que están en CustomerRedFlag
    excluded_obama_ids = CustomerRedFlag.objects.values('obamacare_id')

    # Obtener los datos de pólizas activas para las últimas 6 semanas
    activeObamaPolicies = ObamaCare.objects.filter(status='Active', created_at__range=[startDate, endOfCurrentWeek],is_active = True,  **company_filter).exclude( id__in=Subquery(excluded_obama_ids))
    activeSuppPolicies = Supp.objects.filter(status='Active', created_at__range=[startDate, endOfCurrentWeek], is_active= True,  **company_filter)
    activeAssurePolicies = ClientsAssure.objects.filter(status='Active', created_at__range=[startDate, endOfCurrentWeek], is_active= True,  **company_filter)

    # Inicializar diccionario de ventas para las últimas 6 semanas
    excludedUsernames = ['Calidad01', 'mariluz', 'MariaCaTi','StephanieMkt','CarmenR']  # Excluimos a gente que no debe aparecer en la vista

    # Inicializar diccionario para almacenar los datos de la gráfica por agente
    chart_data = {
        "labels": weekRanges,  # Etiquetas de las semanas
        "series": {}  # Diccionario para almacenar series por agente
    }

    # Procesar las pólizas activas de ObamaCare
    for policy in activeObamaPolicies:
        agentName = policy.agent.username
        if policy.agent.is_active:
            if agentName not in excludedUsernames:
                agentName = f"{policy.agent.first_name} {policy.agent.last_name}".strip()        
                policyWeek = (policy.created_at - startDate).days // 7  # Calcular la semana (0 a 5)
                if 0 <= policyWeek < numWeeks:
                    if agentName not in chart_data["series"]:
                        chart_data["series"][agentName] = {
                            "activeObama": [0] * numWeeks,
                            "activeSupp": [0] * numWeeks
                        }
                    chart_data["series"][agentName]["activeObama"][policyWeek] += 1

    # Procesar las pólizas activas de Supp
    for policy in activeSuppPolicies:
        agentName = policy.agent.username
        if policy.agent.is_active:
            if agentName not in excludedUsernames:
                agentName = f"{policy.agent.first_name} {policy.agent.last_name}".strip()        
                policyWeek = (policy.created_at - startDate).days // 7  # Calcular la semana (0 a 5)
                if 0 <= policyWeek < numWeeks:
                    if agentName not in chart_data["series"]:
                        chart_data["series"][agentName] = {
                            "activeObama": [0] * numWeeks,
                            "activeSupp": [0] * numWeeks
                        }
                    chart_data["series"][agentName]["activeSupp"][policyWeek] += 1

    for policy in activeAssurePolicies:
        agentName = policy.agent.username
        if policy.agent.is_active:
            if agentName not in excludedUsernames:
                agentName = f"{policy.agent.first_name} {policy.agent.last_name}".strip()        
                policyWeek = (policy.created_at - startDate).days // 7  # Calcular la semana (0 a 5)
                if 0 <= policyWeek < numWeeks:
                    if agentName not in chart_data["series"]:
                        chart_data["series"][agentName] = {
                            "activeObama": [0] * numWeeks,
                            "activeSupp": [0] * numWeeks
                        }
                    chart_data["series"][agentName]["activeSupp"][policyWeek] += 1

    return chart_data

@login_required(login_url='/login')
@company_ownership_required_sinURL
def chart6Week(request):

    # Obtener los datos para la gráfica
    chart_data = chart6WeekSale(request)

    # Pasar los datos a la plantilla
    context = {
        'chart_data': chart_data   # Datos para la gráfica
    }

    # Renderizar la plantilla con los datos
    return render(request, 'graficsReports/chart6Week.html', context)

@login_required(login_url='/login')
def salesPerformance(request):

    # Obtener la fecha actual
    now = timezone.now()

    # Si se proporcionan fechas, filtrar por el rango de fechas
    if request.method == 'POST':
        startDatePost = request.POST['start_date']
        endDatePost = request.POST['end_date']
        startDate = timezone.make_aware(
            datetime.strptime(startDatePost, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
        )
        endDate = timezone.make_aware(
            datetime.strptime(endDatePost, '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)
        )
    else:
        startDate = timezone.make_aware(
            datetime(now.year, now.month, 1, 0, 0, 0, 0)
        )
        endDate = timezone.make_aware(
            datetime(now.year, now.month + 1, 1, 0, 0, 0, 0) - timezone.timedelta(microseconds=1)
        )


    salesData = get_agent_sales(request, startDate, endDate)

    # Preparar datos para la gráfica con nombres completos
    agents = list(salesData.keys())
    obamacareSales = [salesData[agent]['obamas'] for agent in agents]
    suppSales = [salesData[agent]['supp'] for agent in agents]

    context = {
        'agents': agents,
        'obamacareSales': obamacareSales,
        'suppSales': suppSales,
        'startDate':startDate,
        'endDate':endDate,
    }

    # Renderizar la respuesta
    return render(request, 'graficsReports/averageSales.html', context)

@company_ownership_required_sinURL
def get_weekly_counts(request, user):

    company_id = request.company_id  # Obtener company_id desde request
    # Definir el filtro de compañía (será un diccionario vacío si es superusuario)
    company_filter = {'company': company_id} if not request.user.is_superuser else {}

    # Obtener la fecha actual
    noww = timezone.now()

    # Primer día del mes anterior
    now = noww.replace(day=1) - relativedelta(months=1)
    
    # Obtener el primer día del mes actual
    first_day_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Obtener el último día del mes actual
    if now.month == 12:
        next_month = now.replace(year=now.year + 1, month=1, day=1)
    else:
        next_month = now.replace(month=now.month + 1, day=1)
    last_day_of_month = next_month - timedelta(days=1)
    
    # Calcular las fechas de inicio de cada semana
    week1_start = first_day_of_month
    week2_start = week1_start + timedelta(days=7)
    week3_start = week2_start + timedelta(days=7)
    week4_start = week3_start + timedelta(days=7)
    
    # Inicializar el diccionario de resultados
    result = {
        "week1obama": 0,
        "week2obama": 0,
        "week3obama": 0,
        "week4obama": 0,
        "week1supp": 0,
        "week2supp": 0,
        "week3supp": 0,
        "week4supp": 0,
    }
    
    # Conteo de ObamaCare
    obamacare_counts = ObamaCare.objects.filter(agent=user, created_at__range=(first_day_of_month, last_day_of_month), ** company_filter)
    for obamacare in obamacare_counts:
        if week1_start <= obamacare.created_at < week2_start:
            result["week1obama"] += 1
        elif week2_start <= obamacare.created_at < week3_start:
            result["week2obama"] += 1
        elif week3_start <= obamacare.created_at < week4_start:
            result["week3obama"] += 1
        elif week4_start <= obamacare.created_at <= last_day_of_month:
            result["week4obama"] += 1
    
    # Conteo de Supp
    supp_counts = Supp.objects.filter(agent=user, created_at__range=(first_day_of_month, last_day_of_month), **company_filter)
    for supp in supp_counts:
        if week1_start <= supp.created_at < week2_start:
            result["week1supp"] += 1
        elif week2_start <= supp.created_at < week3_start:
            result["week2supp"] += 1
        elif week3_start <= supp.created_at < week4_start:
            result["week3supp"] += 1
        elif week4_start <= supp.created_at <= last_day_of_month:
            result["week4supp"] += 1
    
    return result

@company_ownership_required_sinURL
def get_agent_sales(request, start_date, end_date):
    """
    Obtiene el conteo de ObamaCare y Supp vendidos por cada agente en un rango de fechas.
    
    Parámetros:
        start_date (date): Fecha de inicio del rango.
        end_date (date): Fecha de fin del rango.
    
    Retorna:
        dict: Un diccionario con el conteo de ventas por agente (nombre completo).
    """

    company_id = request.company_id  # Obtener company_id desde request
    # Definir el filtro de compañía (será un diccionario vacío si es superusuario)
    company_filter = {'company': company_id} if not request.user.is_superuser else {}

    # Obtener los IDs de ObamaCare que están en CustomerRedFlag
    excluded_obama_ids = CustomerRedFlag.objects.values('obamacare_id')

    userExcludes = ['CarmenR', 'MariaCaTi']

    # Obtener todos los agentes activos con roles 'A' y 'C'
    allAgents = Users.objects.filter(is_active=True, role__in=['A', 'C'], **company_filter).exclude(username__in=userExcludes).values('username', 'first_name', 'last_name')

    # Crear un diccionario para mapear username a nombre completo
    agentNameMap = {agent['username']: f"{agent['first_name']} {agent['last_name']}".strip() for agent in allAgents}

    # Obtener todos los agentes que tienen ventas
    obamaCareAgents = set(ObamaCare.objects.filter(
        created_at__range=[start_date, end_date],
        is_active=True, **company_filter
    ).exclude( id__in=Subquery(excluded_obama_ids)).values_list('agent__username', flat=True))

    suppAgents = set(Supp.objects.filter(
        created_at__range=[start_date, end_date],
        is_active=True, **company_filter
    ).values_list('agent__username', flat=True))

    assureAgents = set(ClientsAssure.objects.filter(
        created_at__range=[start_date, end_date],
        is_active=True, **company_filter
    ).values_list('agent__username', flat=True))

    # Unir todos los agentes que tienen ventas con los agentes filtrados inicialmente
    allUsernames = set(agentNameMap.keys())
    allUsernames.update(obamaCareAgents)
    allUsernames.update(suppAgents,assureAgents)

    # Obtener el conteo de ObamaCare dentro del rango de fechas
    obamaCareCount = ObamaCare.objects.filter(
        created_at__range=[start_date, end_date],
        is_active=True, **company_filter
    ).exclude( id__in=Subquery(excluded_obama_ids)).values('agent__username').annotate(obama_count=Count('id'))

    # Obtener el conteo de Supp dentro del rango de fechas
    suppCount = Supp.objects.filter(
        created_at__range=[start_date, end_date],
        is_active=True, **company_filter
    ).values('agent__username').annotate(supp_count=Count('id'))

    assureCount = ClientsAssure.objects.filter(
        created_at__range=[start_date, end_date],
        is_active=True, **company_filter
    ).values('agent__username').annotate(assure_count=Count('id'))

    # Diccionario para almacenar los resultados con nombres completos
    agentSales = {}

    # Incluir a todos los agentes de allAgents, incluso si no tienen ventas
    for agent in allAgents:
        fullName = f"{agent['first_name']} {agent['last_name']}".strip()
        agentSales[fullName] = {'obamas': 0, 'supp': 0}

    # Agregar conteos de ObamaCare
    for entry in obamaCareCount:
        username = entry['agent__username']
        if username not in agentNameMap:
            # Si el agente no está en agentNameMap, obtener su nombre completo directamente
            agent = Users.objects.filter(username=username, **company_filter).values('first_name', 'last_name').first()
            if agent:
                fullName = f"{agent['first_name']} {agent['last_name']}".strip()
            else:
                fullName = username
        else:
            fullName = agentNameMap[username]
        
        if fullName not in agentSales:
            agentSales[fullName] = {'obamas': 0, 'supp': 0}
        agentSales[fullName]['obamas'] = entry['obama_count']

    # Agregar conteos de Supp
    for entry in suppCount:
        username = entry['agent__username']
        if username not in agentNameMap:
            # Si el agente no está en agentNameMap, obtener su nombre completo directamente
            agent = Users.objects.filter(username=username, **company_filter).values('first_name', 'last_name').first()
            if agent:
                fullName = f"{agent['first_name']} {agent['last_name']}".strip()
            else:
                fullName = username
        else:
            fullName = agentNameMap[username]
        
        if fullName not in agentSales:
            agentSales[fullName] = {'obamas': 0, 'supp': 0}
        agentSales[fullName]['supp'] = entry['supp_count']

    for entry in assureCount:
        username = entry['agent__username']
        if username not in agentNameMap:
            agent = Users.objects.filter(username=username, **company_filter).values('first_name', 'last_name').first()
            fullName = f"{agent['first_name']} {agent['last_name']}".strip() if agent else username
        else:
            fullName = agentNameMap[username]
        
        if fullName not in agentSales:
            agentSales[fullName] = {'obamas': 0, 'supp': 0}
        
        agentSales[fullName]['supp'] += entry['assure_count']  # Aquí sumamos

    return agentSales

@login_required(login_url='/login')
@company_ownership_required_sinURL
def averageCustomer(request):

    company_id = request.company_id  # Obtener company_id desde request
    # Definir el filtro de compañía (será un diccionario vacío si es superusuario)
    company_filter = {'client__company': company_id} if not request.user.is_superuser else {}

    data = list(ObservationCustomer.objects.filter(
        typification__icontains="EFFECTIVE MANAGEMENT", **company_filter
    ).values('agent__first_name', 'agent__last_name').annotate(total_llamadas=Count('id')).order_by('-total_llamadas'))

    context = {
        'data': json.dumps(data)  # Convertir los datos a JSON válido
    }

    # Si se proporcionan fechas, filtrar por el rango de fechas
    if request.method == 'POST':

        # Obtener parámetros de fecha del request
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        start_date_new = timezone.make_aware(
            datetime.datetime.strptime(start_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
        )
        end_date_new = timezone.make_aware(
            datetime.datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)
        )

        data = list(ObservationCustomer.objects.filter(created_at__range=[start_date_new, end_date_new],
            typification__icontains="EFFECTIVE MANAGEMENT", **company_filter ).values('agent__first_name', 'agent__last_name')
            .annotate(total_llamadas=Count('id')).order_by('-total_llamadas'))

        context = {
            'data': json.dumps(data),  # Convertir los datos a JSON válido
            'start_date': start_date,
            'end_date': end_date
        }    

    return render(request, 'graficsReports/averageCustomer.html', context)

@login_required(login_url='/login')
@company_ownership_required_sinURL
def mixSale(request):

    charts6WeekAgent = chart6WeekAgent()
    chartsWeekPrevius = chartWeekPrevius()
    chartSixMonthsAgents = chartSixMonths()
    chartAllDataAgents = chartAllData()

    context = {
        "charts6WeekAgent": json.dumps(charts6WeekAgent),
        "chartsWeekPrevius_json": json.dumps(chartsWeekPrevius),  # 👈 para JavaScript
        "chartSixMonthsAgents_json": json.dumps(chartSixMonthsAgents),
        "chartAllDataAgents_json": json.dumps(chartAllDataAgents)
    }

    return render(request, 'graficsReports/mixSale.html', context)


