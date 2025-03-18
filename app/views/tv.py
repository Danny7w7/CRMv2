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

@login_required(login_url='/login')
def weeklyLiveView(request):
    context = {
        'weeklySales': getSalesForWeekly(),
    }
    if request.user.role == 'TV': return render(request, 'dashboard/weeklyLiveViewTV.html', context)
    else: return render(request, 'dashboard/weeklyLiveView.html', context)

def getSalesForWeekly():
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

    # Filtrar por la semana actual
    obamaCounts = ObamaCare.objects.values('agent', 'created_at') \
        .filter(
            agent__role__in=userRole,
            is_active=True,
            created_at__range=[startOfWeek, endOfWeek]
        ) \
        .annotate(obamaCount=Count('id'))
        
    obamaActiveCounts = ObamaCare.objects.values('agent', 'created_at')\
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

    # Contamos cuántos registros de Supp tiene cada usuario por día
    suppCounts = Supp.objects.values('agent', 'created_at') \
        .filter(
            agent__role__in=userRole,
            is_active=True,
            created_at__range=[startOfWeek, endOfWeek]
        ) \
        .annotate(suppCount=Count('id'))

    suppActiveCounts = Supp.objects.values('agent', 'created_at') \
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

    # Aseguramos que todos los usuarios estén en el diccionario, incluso si no tienen registros
    for user in Users.objects.filter(role__in=userRole, is_active=True).exclude(username__in=excludedUsernames):
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

def getSalesForMonth():
    # Obtener las fechas de inicio y fin del mes actual
    today = datetime.today()
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
    users = Users.objects.filter(role__in=userRoles, is_active=True).exclude(username__in=excludedUsernames)  # Lista completa de usuarios
    salesSummary = {
        user.username: {
            f"Week{i + 1}": {"obama": 0, "activeObama": 0, "supp": 0, "activeSupp": 0}
            for i in range(numWeeks)
        } for user in users
    }
    
    # Filtrar todas las ventas realizadas en el mes actual
    obamaSales = ObamaCare.objects.filter(created_at__range=[startDate, endDate])
    suppSales = Supp.objects.filter(created_at__range=[startDate, endDate])
    
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
    activeObamaPolicies = ObamaCare.objects.filter(status='Active')
    activeSuppPolicies = Supp.objects.filter(status='Active')
    
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

def monthLiveView(request):
    monthSales, weekRanges = getSalesForMonth()
    context = {
        'monthSales': monthSales,
        'weekRanges': weekRanges,
        'toggle': True
    }
    
    if request.user.role == 'TV': return render(request, 'dashboard/monthLiveViewTV.html', context)
    else: return render(request, 'dashboard/monthLiveView.html', context)
