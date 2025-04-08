# Standard Python libraries
import calendar
import datetime
from collections import defaultdict
from datetime import timedelta

# Django utilities
from django.utils.timezone import make_aware

# Django core libraries
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render

# Application-specific imports
from app.models import *
from .decoratorsCompany import *

@login_required(login_url='/login')
@company_ownership_required_sinURL
def weeklyLiveView(request):

    company_id = request.company_id  # Obtener company_id desde request

    context = {
        'weeklySales': getSalesForWeekly(company_id)
    }
    if request.user.role == 'TV': return render(request, 'dashboard/weeklyLiveViewTV.html', context)
    else: return render(request, 'dashboard/weeklyLiveView.html', context)

def getSalesForWeekly(company_id):
    # Obtener la fecha de hoy y calcular el inicio de la semana (asumiendo que empieza el lunes)
    today = timezone.now()
    startOfWeek = today - timedelta(days=today.weekday())
    endOfWeek = startOfWeek + timedelta(days=6)

    # Inicializamos un diccionario por defecto para contar las instancias
    userCounts = defaultdict(lambda: {
        'lunes': {'obama': 0, 'obamaActive': 0 , 'supp': 0, 'suppActive':0},
        'martes': {'obama': 0, 'obamaActive': 0 , 'supp': 0, 'suppActive':0},
        'miercoles': {'obama': 0, 'obamaActive': 0 , 'supp': 0, 'suppActive':0},
        'jueves': {'obama': 0, 'obamaActive': 0 , 'supp': 0, 'suppActive':0},
        'viernes': {'obama': 0, 'obamaActive': 0 , 'supp': 0, 'suppActive':0},
        'sabado': {'obama': 0, 'obamaActive': 0 , 'supp': 0, 'suppActive':0},
    })

    # Mapeo de números a días de la semana
    daysOfWeek = {
        0: 'lunes',
        1: 'martes',
        2: 'miercoles',
        3: 'jueves',
        4: 'viernes',
        5: 'sabado'
    }

    # Contamos cuántos registros de ObamaCare tiene cada usuario por día
    userRole = ['A', 'C', 'S']

    #validation de lo que se va a mostrar por company o si es super user    
    if company_id == 1:
        filterCompany = ObamaCare.objects.filter(is_active = True)
    else:
        filterCompany = ObamaCare.objects.filter(company = company_id, is_active = True)

    # Filtrar por la semana actual
    obamaCounts = filterCompany.values('agent', 'created_at') \
        .filter(
            agent__role__in=userRole,
            is_active=True,
            created_at__range=[startOfWeek, endOfWeek]
        ) \
        .annotate(obamaCount=Count('id'))
        
    obamaActiveCounts = filterCompany.values('agent', 'created_at')\
        .filter(
            agent__role__in=userRole, 
            is_active=True, 
            created_at__range=[startOfWeek, endOfWeek],
            status='ACTIVE'
        )\
        .annotate(obamaProfilingCount=Count('id'))

    for obama in obamaCounts:
        # Obtener el día de la semana (0=lunes, 1=martes, ..., 6=domingo)
        dayOfWeek = obama['created_at'].weekday()
        if dayOfWeek < 6:  # Excluimos el domingo
            day = daysOfWeek[dayOfWeek]
            userCounts[obama['agent']][day]['obama'] += obama['obamaCount']

    for obamaActive in obamaActiveCounts:
        # Obtener el día de la semana (0=lunes, 1=martes, ..., 6=domingo)
        dayOfWeek = obamaActive['created_at'].weekday()
        if dayOfWeek < 6:  # Excluimos el domingo
            day = daysOfWeek[dayOfWeek]
            userCounts[obamaActive['agent']][day]['obamaActive'] += obamaActive['obamaProfilingCount']

    #validation de lo que se va a mostrar por company o si es super user    
    if company_id == 1:
        filterCompanySupp = Supp.objects.filter(is_active = True)
    else:
        filterCompanySupp = Supp.objects.filter(company = company_id, is_active = True)

    # Contamos cuántos registros de Supp tiene cada usuario por día
    suppCounts = filterCompanySupp.values('agent', 'created_at') \
        .filter(
            agent__role__in=userRole,
            is_active=True,
            created_at__range=[startOfWeek, endOfWeek]
        ) \
        .annotate(suppCount=Count('id'))

    suppActiveCounts = filterCompanySupp.values('agent', 'created_at') \
        .filter(
            agent__role__in=userRole,
            is_active=True,
            created_at__range=[startOfWeek, endOfWeek],
            status='ACTIVE'
        ) \
        .annotate(suppActiveCount=Count('id'))

    for supp in suppCounts:
        # Obtener el día de la semana (0=lunes, 1=martes, ..., 6=domingo)
        dayOfWeek = supp['created_at'].weekday()
        if dayOfWeek < 6:  # Excluimos el domingo
            day = daysOfWeek[dayOfWeek]
            userCounts[supp['agent']][day]['supp'] += supp['suppCount']

    for suppActive in suppActiveCounts:
        # Obtener el día de la semana (0=lunes, 1=martes, ..., 6=domingo)
        dayOfWeek = suppActive['created_at'].weekday()
        if dayOfWeek < 6:  # Excluimos el domingo
            day = daysOfWeek[dayOfWeek]
            userCounts[suppActive['agent']][day]['suppActive'] += suppActive['suppActiveCount']

    excludedUsernames = ['Calidad01', 'mariluz', 'MariaCaTi'] #Excluimos a gente que no debe aparecer en la vista

    #validation de lo que se va a mostrar por company o si es super user    
    if company_id == 1:
        filterCompanyUser = Users.objects.filter(role__in=userRole, is_active=True)
    else:
        filterCompanyUser = Users.objects.filter(role__in=userRole, is_active=True, company = company_id)

    # Aseguramos que todos los usuarios estén en el diccionario, incluso si no tienen registros
    for user in filterCompanyUser.exclude(username__in=excludedUsernames):
        if user.id not in userCounts:
            userCounts[user.id] = {
                'lunes': {'obama': 0, 'obamaActive': 0 , 'supp': 0, 'suppActive':0},
                'martes': {'obama': 0, 'obamaActive': 0 , 'supp': 0, 'suppActive':0},
                'miercoles': {'obama': 0, 'obamaActive': 0 , 'supp': 0, 'suppActive':0},
                'jueves': {'obama': 0, 'obamaActive': 0 , 'supp': 0, 'suppActive':0},
                'viernes': {'obama': 0, 'obamaActive': 0 , 'supp': 0, 'suppActive':0},
                'sabado': {'obama': 0, 'obamaActive': 0 , 'supp': 0, 'suppActive':0}
            }

    # Convertimos los identificadores de usuario a nombres (si necesitas los nombres de los usuarios)
    userNames = {user.id: f'{user.first_name} {user.last_name}' for user in Users.objects.all()}

    # Crear un diccionario con los nombres de los usuarios y los conteos por día
    finalCounts = {userNames[userId]: counts for userId, counts in userCounts.items()}

    return finalCounts

def getSalesForMonth(company_id):
    # Obtener las fechas de inicio y fin del mes actual
    today = datetime.datetime.today()
    startDate = today.replace(day=1)  # Primer día del mes actual
    _, lastDay = calendar.monthrange(today.year, today.month)
    endDate = today.replace(day=lastDay)  # Último día del mes actual

    excludedUsernames = ['Calidad01', 'mariluz', 'MariaCaTi']  # Excluimos a gente que no debe aparecer en la vista
    userRoles = ['A', 'C', 'S']
    
    # Convertir startDate y endDate en fechas "offset-aware"
    startDate = make_aware(startDate)
    endDate = make_aware(endDate)
    
    # Número total de semanas en el mes actual
    numWeeks = (lastDay + 6) // 7  # Aproximación para incluir semanas parciales

    # Calcular los rangos de las semanas
    weekRanges = []
    for i in range(numWeeks):
        weekStart = startDate + timedelta(weeks=i)
        weekEnd = weekStart + timedelta(days=6)
        
        # Asegurarse de que la fecha final no sea después del último día del mes
        if weekEnd > endDate:
            weekEnd = endDate
        
        # Formatear las fechas en "dd/mm"
        weekRange = f"{weekStart.strftime('%d/%m')} - {weekEnd.strftime('%d/%m')}"
        weekRanges.append(weekRange)
    
    # Inicializar diccionario de ventas con todos los usuarios
    #validation de lo que se va a mostrar por company o si es super user    
    if company_id == 1:
        users = Users.objects.filter(role__in=userRoles, is_active=True).exclude(username__in=excludedUsernames)  # Lista completa de usuarios
    else:
        users = Users.objects.filter(role__in=userRoles, is_active=True, company = company_id).exclude(username__in=excludedUsernames)  # Lista completa de usuarios
    salesSummary = {
        user.username: {
            f"Week{i + 1}": {"obama": 0, "activeObama": 0, "supp": 0, "activeSupp": 0}
            for i in range(numWeeks)
        } for user in users
    }
    
    # Filtrar todas las ventas realizadas en el mes actual
    if company_id == 1:
        obamaSales = ObamaCare.objects.filter(created_at__range=[startDate, endDate])
        suppSales = Supp.objects.filter(created_at__range=[startDate, endDate])
    else:
        obamaSales = ObamaCare.objects.filter(created_at__range=[startDate, endDate], company = company_id)
        suppSales = Supp.objects.filter(created_at__range=[startDate, endDate], company = company_id)
    
    # Iterar sobre las ventas de Obamacare y organizarlas por semanas
    for sale in obamaSales:
        agentName = sale.agent.username  # Nombre del agente
        saleWeek = (sale.created_at - startDate).days // 7 + 1
        if 1 <= saleWeek <= numWeeks:
            try:
                salesSummary[agentName][f"Week{saleWeek}"]["obama"] += 1
            except KeyError:
                pass  # Ignorar ventas de agentes que no están en el filtro de usuarios
    
    # Iterar sobre las ventas de Supp y organizarlas por semanas
    for sale in suppSales:
        agentName = sale.agent.username  # Nombre del agente
        saleWeek = (sale.created_at - startDate).days // 7 + 1
        if 1 <= saleWeek <= numWeeks:
            try:
                salesSummary[agentName][f"Week{saleWeek}"]["supp"] += 1
            except KeyError:
                pass

    # Agregar el conteo de pólizas activas por agente para Obamacare y Supp
    if company_id == 1:
        activeObamaPolicies = ObamaCare.objects.filter(status='Active')
        activeSuppPolicies = Supp.objects.filter(status='Active')
    else:
        activeObamaPolicies = ObamaCare.objects.filter(status='Active',company = company_id)
        activeSuppPolicies = Supp.objects.filter(status='Active',company = company_id)
    
    for policy in activeObamaPolicies:
        agentName = policy.agent.username
        policyWeek = (policy.created_at - startDate).days // 7 + 1
        if 1 <= policyWeek <= numWeeks:
            try:
                salesSummary[agentName][f"Week{policyWeek}"]["activeObama"] += 1
            except KeyError:
                pass

    for policy in activeSuppPolicies:
        agentName = policy.agent.username
        policyWeek = (policy.created_at - startDate).days // 7 + 1
        if 1 <= policyWeek <= numWeeks:
            try:
                salesSummary[agentName][f"Week{policyWeek}"]["activeSupp"] += 1
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
def monthLiveView(request):

    company_id = request.company_id  # Obtener company_id desde request

    monthSales, weekRanges = getSalesForMonth(company_id)
    
    context = {
        'monthSales': monthSales,
        'weekRanges': weekRanges,
        'toggle': True
    }
    
    if request.user.role == 'TV': return render(request, 'dashboard/monthLiveViewTV.html', context)
    else: return render(request, 'dashboard/monthLiveView.html', context)
