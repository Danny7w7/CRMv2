# Standard Python libraries
import calendar
from datetime import datetime
import json

# Django core libraries
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.db.models.functions import Coalesce
from django.shortcuts import render

# Application-specific imports
from app.models import *

from django.shortcuts import render, redirect
from .decoratorsCompany import *

@login_required(login_url='/login') 
@company_ownership_required_sinURL
def index(request):

    company_id = request.company_id  # Obtener company_id desde request

    if request.user.is_superuser:  # Nota: Es is_superuser, no is_super_user
        obama = countSalesObama(request, company_id)
        supp = countSalesSupp(request, company_id)
        chartOne = chartSaleIndex(request, company_id)
        tableStatusAca = tableStatusObama(request, company_id)
        tableStatusSup = tableStatusSupp(request, company_id)
    else:
        obama = countSalesObama(request)
        supp = countSalesSupp(request)
        chartOne = chartSaleIndex(request)
        tableStatusAca = tableStatusObama(request)
        tableStatusSup = tableStatusSupp(request)


    # Asegúrate de que chartOne sea un JSON válido
    chartOne_json = json.dumps(chartOne)

    context = {
        'obama':obama,
        'supp':supp,
        'chartOne':chartOne_json,
        'tableStatusObama':tableStatusAca,
        'tableStatusSup':tableStatusSup
    }      

    return render(request, 'dashboard/index.html', context)

def chartSaleIndex(request, company_id=None):
    # Obtener la fecha y hora actual
    now = timezone.now()
    current_month = now.month
    current_year = now.year

    # Calcular inicio y fin del mes actual
    start_of_month = timezone.make_aware(datetime(current_year, current_month, 1), timezone.get_current_timezone())
    last_day_of_month = calendar.monthrange(current_year, current_month)[1]
    end_of_month = timezone.make_aware(
        datetime(current_year, current_month, last_day_of_month, 23, 59, 59), 
        timezone.get_current_timezone()
    )

    # Roles con acceso ampliado
    roleAuditar = ['S', 'Admin']
    excludeUsername = ['admin']

    # Construcción de la consulta basada en el rol del usuario
    company_filter = {} if request.user.is_superuser else {'company': company_id}

    # Construcción de la consulta basada en el rol del usuario
    if request.user.role in roleAuditar:

        # Primero filtramos los usuarios según su compañía (si no es superusuario)
        base_query = Users.objects.filter(is_active=True, **company_filter).exclude(username__in=excludeUsername)
        # Para roles con acceso ampliado: consultar datos de todos los usuarios
        users_data = base_query.annotate(
            obamacare_count=Count('agent_sale_aca', filter=Q(
                agent_sale_aca__status_color=3,
                agent_sale_aca__created_at__gte=start_of_month,
                agent_sale_aca__created_at__lt=end_of_month,
                agent_sale_aca__is_active=True,
                **{'agent_sale_aca__'+k: v for k, v in company_filter.items()} 
            ), distinct=True),
            obamacare_count_total=Count('agent_sale_aca', filter=Q(
                agent_sale_aca__created_at__gte=start_of_month,
                agent_sale_aca__created_at__lt=end_of_month,
                agent_sale_aca__is_active=True,
                **{'agent_sale_aca__'+k: v for k, v in company_filter.items()}
            ), distinct=True),
            supp_count=Coalesce(Count('agent_sale_supp', filter=Q(
                agent_sale_supp__status_color=3,
                agent_sale_supp__created_at__gte=start_of_month,
                agent_sale_supp__created_at__lt=end_of_month,
                agent_sale_supp__is_active=True,
                **{'agent_sale_supp__'+k: v for k, v in company_filter.items()}
            ), distinct=True), 0),
            supp_count_total=Coalesce(Count('agent_sale_supp', filter=Q(
                agent_sale_supp__created_at__gte=start_of_month,
                agent_sale_supp__created_at__lt=end_of_month,
                agent_sale_supp__is_active=True,
                **{'agent_sale_supp__'+k: v for k, v in company_filter.items()}
            ), distinct=True), 0)
        ).exclude(username__in=excludeUsername).values('first_name', 'obamacare_count', 'obamacare_count_total', 'supp_count', 'supp_count_total')

    elif request.user.role not in roleAuditar:
        # Para usuarios con rol 'A': consultar datos solo para el usuario actual
        users_data = Users.objects.filter(id=request.user.id, **company_filter).annotate(
            obamacare_count=Count('agent_sale_aca', filter=Q(
                agent_sale_aca__status_color=3,
                agent_sale_aca__created_at__gte=start_of_month,
                agent_sale_aca__created_at__lt=end_of_month,
                agent_sale_aca__agent=request.user.id,
                agent_sale_aca__is_active=True,
                **{'agent_sale_aca__'+k: v for k, v in company_filter.items()} 
            ), distinct=True),
            obamacare_count_total=Count('agent_sale_aca', filter=Q(
                agent_sale_aca__created_at__gte=start_of_month,
                agent_sale_aca__created_at__lt=end_of_month,
                agent_sale_aca__agent=request.user.id,
                agent_sale_aca__is_active=True,
                **{'agent_sale_aca__'+k: v for k, v in company_filter.items()}
            ), distinct=True),
            supp_count=Coalesce(Count('agent_sale_supp', filter=Q(
                agent_sale_supp__status_color=3,
                agent_sale_supp__created_at__gte=start_of_month,
                agent_sale_supp__created_at__lt=end_of_month,
                agent_sale_supp__agent=request.user.id,
                agent_sale_supp__is_active=True,
                **{'agent_sale_supp__'+k: v for k, v in company_filter.items()}
            ), distinct=True), 0),
            supp_count_total=Coalesce(Count('agent_sale_supp', filter=Q(
                agent_sale_supp__created_at__gte=start_of_month,
                agent_sale_supp__created_at__lt=end_of_month,
                agent_sale_supp__agent=request.user.id,
                agent_sale_supp__is_active=True,
                **{'agent_sale_supp__'+k: v for k, v in company_filter.items()}
            ), distinct=True), 0)
        ).values('first_name', 'obamacare_count', 'obamacare_count_total', 'supp_count', 'supp_count_total')

    # Convertir los datos a una lista de diccionarios para su uso
    combined_data = [
        {
            'username': user['first_name'],
            'obamacare_count': user['obamacare_count'],
            'obamacare_count_total': user['obamacare_count_total'],
            'supp_count': user['supp_count'],
            'supp_count_total': user['supp_count_total'],
        }
        for user in users_data
    ]

    return combined_data
 
def countSalesObama(request, company_id=None):

    # Obtener el mes y el año actuales
    now = timezone.now()

    # Calcular el primer día del mes
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Calcular el último día del mes
    last_day = calendar.monthrange(now.year, now.month)[1]  # Obtiene el último día del mes
    end_of_month = now.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)

    roleAuditar = ['S', 'C',  'AU', 'Admin']

    # Base query con filtro de compañía
    company_filter = {} if request.user.is_superuser else {'company': company_id}
    
    if request.user.role in roleAuditar:        
        all = ObamaCare.objects.filter(created_at__gte=start_of_month,created_at__lte=end_of_month,is_active = True,**company_filter).count()
        active = ObamaCare.objects.filter(status_color=3,created_at__gte=start_of_month,created_at__lte=end_of_month,is_active = True, **company_filter).count()
        process = ObamaCare.objects.filter(created_at__gte=start_of_month,created_at__lte=end_of_month,is_active = True, **company_filter).filter(Q(status_color=2) | Q(status_color=1)).count()
        cancell = ObamaCare.objects.filter(status_color=4,created_at__gte=start_of_month,created_at__lte=end_of_month,is_active = True, **company_filter).count()
    elif request.user.role in ['A','SUPP']:
        all = ObamaCare.objects.filter(created_at__gte=start_of_month,created_at__lte=end_of_month).filter(agent = request.user.id, is_active = True, **company_filter ).count()
        active = ObamaCare.objects.filter(status_color=3,created_at__gte=start_of_month,created_at__lte=end_of_month).filter(agent = request.user.id, is_active = True, **company_filter ).count()
        process = ObamaCare.objects.filter(created_at__gte=start_of_month,created_at__lte=end_of_month).filter(Q(status_color=2) | Q(status_color=1)).filter(agent = request.user.id, is_active = True, **company_filter ).count()
        cancell = ObamaCare.objects.filter(status_color=4,created_at__gte=start_of_month,created_at__lte=end_of_month).filter(agent = request.user.id, is_active = True, **company_filter ).count()
       
   
    dicts = {
        'all': all,
        'active':active,
        'process':process,
        'cancell':cancell
    }
    return dicts

def countSalesSupp(request, company_id=None):

    # Obtener el mes y el año actuales
    now = timezone.now()

    # Calcular el primer día del mes
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Calcular el último día del mes
    last_day = calendar.monthrange(now.year, now.month)[1]  # Obtiene el último día del mes
    end_of_month = now.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)

    roleAuditar = ['S', 'C',  'AU', 'Admin']

    # Base query con filtro de compañía
    company_filter = {} if request.user.is_superuser else {'company': company_id}
    
    if request.user.role in roleAuditar:
        all = Supp.objects.filter(created_at__gte=start_of_month,created_at__lte=end_of_month,is_active = True, **company_filter).count()
        active = Supp.objects.filter(status_color=3,created_at__gte=start_of_month,created_at__lte=end_of_month,is_active = True, **company_filter).count()
        process = Supp.objects.filter(created_at__gte=start_of_month,created_at__lte=end_of_month,is_active = True, **company_filter).filter(Q(status_color=2) | Q(status_color=1)).count()
        cancell = Supp.objects.filter(status_color=4,created_at__gte=start_of_month,created_at__lte=end_of_month,is_active = True, **company_filter).count()
    elif request.user.role in ['A','SUPP']:
        all = Supp.objects.filter(created_at__gte=start_of_month,created_at__lte=end_of_month).filter(agent = request.user.id, is_active = True, **company_filter ).count()
        active = Supp.objects.filter(status_color=3,created_at__gte=start_of_month,created_at__lte=end_of_month).filter(agent = request.user.id, is_active = True, **company_filter ).count()
        process = Supp.objects.filter(created_at__gte=start_of_month,created_at__lte=end_of_month).filter(agent = request.user.id, is_active = True, **company_filter ).filter(Q(status_color=2) | Q(status_color=1)).count()
        cancell = Supp.objects.filter(status_color=4,created_at__gte=start_of_month,created_at__lte=end_of_month).filter(agent = request.user.id, is_active = True, **company_filter ).count()


    dicts = {
        'all':all,
        'active':active,
        'process':process,
        'cancell':cancell
    }
    return dicts

def tableStatusObama(request, company_id=None):

    # Obtener la fecha y hora actual
    now = timezone.now()
    current_month = now.month
    current_year = now.year

    # Obtener el primer y último día del mes actual (con zona horaria)
    start_of_month = timezone.make_aware(datetime(current_year, current_month, 1), timezone.get_current_timezone())
    end_of_month = timezone.make_aware(datetime(current_year, current_month + 1, 1), timezone.get_current_timezone()) if current_month < 12 else timezone.make_aware(datetime(current_year + 1, 1, 1), timezone.get_current_timezone())

    roleAuditar = ['S', 'C', 'AU', 'Admin']

    # Base query con filtro de compañía
    company_filter = {} if request.user.is_superuser else {'company': company_id}

    # Construcción de la consulta basada en el rol del usuario
    if request.user.role in roleAuditar:

        # Realizamos la consulta y agrupamos por el campo 'profiling'
        result = ObamaCare.objects.filter(created_at__gte=start_of_month, created_at__lt=end_of_month,is_active = True, **company_filter).values('profiling').annotate(count=Count('profiling')).order_by('profiling')
    
    elif request.user.role in ['A','SUPP']:
        
        # Realizamos la consulta y agrupamos por el campo 'profiling'
        result = ObamaCare.objects.filter(created_at__gte=start_of_month, created_at__lt=end_of_month, is_active = True, **company_filter).values('profiling').filter(agent=request.user.id).annotate(count=Count('profiling')).order_by('profiling')
    

    return result

def tableStatusSupp(request, company_id=None):

    # Obtener la fecha y hora actual
    now = timezone.now()
    current_month = now.month
    current_year = now.year

    # Obtener el primer y último día del mes actual (con zona horaria)
    start_of_month = timezone.make_aware(datetime(current_year, current_month, 1), timezone.get_current_timezone())
    end_of_month = timezone.make_aware(datetime(current_year, current_month + 1, 1), timezone.get_current_timezone()) if current_month < 12 else timezone.make_aware(datetime(current_year + 1, 1, 1), timezone.get_current_timezone())

    # Roles con acceso ampliado
    roleAuditar = ['S', 'C', 'AU', 'Admin']

    # Base query con filtro de compañía
    company_filter = {} if request.user.is_superuser else {'company': company_id}

    # Construcción de la consulta basada en el rol del usuario
    if request.user.role in roleAuditar:
        # Realizamos la consulta y agrupamos por el campo 'profiling'
        result = Supp.objects.filter(created_at__gte=start_of_month, created_at__lt=end_of_month,is_active = True, **company_filter).values('status').annotate(count=Count('status')).order_by('status')

    elif request.user.role in ['A','SUPP']:

        # Realizamos la consulta y agrupamos por el campo 'profiling'
        result = Supp.objects.filter(created_at__gte=start_of_month, created_at__lt=end_of_month, is_active = True, **company_filter).values('status').filter(agent=request.user.id).annotate(count=Count('status')).order_by('status')

    return result