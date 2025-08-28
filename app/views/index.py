# Standard Python libraries
import calendar
from datetime import datetime
import json

from app.tasks import *
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
def index(request):
    import redis
    r = redis.Redis(host='localhost', port=6379, db=0)
    print(r.ping())

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

@company_ownership_required_sinURL
def chartSaleIndex(request):
    # Fecha actual y límites del mes
    now = timezone.now()
    start_of_month = timezone.make_aware(datetime(now.year, now.month, 1), timezone.get_current_timezone())
    last_day_of_month = calendar.monthrange(now.year, now.month)[1]
    end_of_month = timezone.make_aware(
        datetime(now.year, now.month, last_day_of_month, 23, 59, 59),
        timezone.get_current_timezone()
    )

    # Excluir IDs de ObamaCare en CustomerRedFlag
    excluded_obama_ids = list(CustomerRedFlag.objects.values_list('obamacare', flat=True))

    company_id = request.company_id  # Obtener company_id desde request
    # Filtro de compañía si no es superusuario
    company_filter = Q() if request.user.is_superuser else Q(agent__company=company_id)

    # Determinar si el usuario tiene acceso ampliado
    has_extended_access = request.user.is_superuser or request.user.role in ['S', 'Admin']

    # Filtrar por el usuario si no tiene acceso ampliado
    user_filter = Q() if has_extended_access else Q(agent=request.user)

    # 📌 **Consulta Directa en ObamaCare**
    obamacare_data = ObamaCare.objects.filter(
        Q(created_at__gte=start_of_month, created_at__lte=end_of_month) & 
        company_filter & user_filter & ~Q(id__in=excluded_obama_ids)
    ).values('agent__first_name').annotate(
        obamacare_count=Count('id', filter=Q(status_color=3), distinct=True),
        obamacare_count_total=Count('id', distinct=True)
    )

    # 📌 **Consulta Directa en Supp**
    supp_data = Supp.objects.filter(
        Q(created_at__gte=start_of_month, created_at__lte=end_of_month) & 
        company_filter & user_filter
    ).values('agent__first_name').annotate(
        supp_count=Count('id', filter=Q(status_color=3), distinct=True),
        supp_count_total=Count('id', distinct=True)
    )

    # Convertir en diccionarios para combinar resultados
    obamacare_dict = {item['agent__first_name']: item for item in obamacare_data}
    supp_dict = {item['agent__first_name']: item for item in supp_data}

    # Unir los datos de ObamaCare y Supp
    combined_data = []
    all_agents = set(obamacare_dict.keys()).union(set(supp_dict.keys()))

    for agent in all_agents:
        combined_data.append({
            'first_name': agent,
            'obamacare_count': obamacare_dict.get(agent, {}).get('obamacare_count', 0),
            'obamacare_count_total': obamacare_dict.get(agent, {}).get('obamacare_count_total', 0),
            'supp_count': supp_dict.get(agent, {}).get('supp_count', 0),
            'supp_count_total': supp_dict.get(agent, {}).get('supp_count_total', 0),
        })

    return combined_data

@company_ownership_required_sinURL
def countSalesObama(request):

    # Obtener el mes y el año actuales
    now = timezone.now()

    # Calcular el primer día del mes
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Calcular el último día del mes
    last_day = calendar.monthrange(now.year, now.month)[1]  # Obtiene el último día del mes
    end_of_month = now.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)

    roleAuditar = ['S', 'C',  'AU', 'Admin']


    company_id = request.company_id  # Obtener company_id desde request
    # Base query con filtro de compañía
    company_filter = {} if request.user.is_superuser else {'company': company_id}

    # Obtener los IDs de ObamaCare que están en CustomerRedFlag
    excluded_obama_ids = list(CustomerRedFlag.objects.values_list('obamacare', flat=True))
    
    if request.user.role in roleAuditar:        
        all = ObamaCare.objects.filter(created_at__gte=start_of_month,created_at__lte=end_of_month,is_active = True,**company_filter).exclude(id__in=excluded_obama_ids).count()
        active = ObamaCare.objects.filter(status_color=3,created_at__gte=start_of_month,created_at__lte=end_of_month,is_active = True, **company_filter).exclude(id__in=excluded_obama_ids).count()
        process = ObamaCare.objects.filter(created_at__gte=start_of_month,created_at__lte=end_of_month,is_active = True, **company_filter).filter(Q(status_color=2) | Q(status_color=1)).exclude(id__in=excluded_obama_ids).count()
        cancell = ObamaCare.objects.filter(status_color=4,created_at__gte=start_of_month,created_at__lte=end_of_month,is_active = True, **company_filter).exclude(id__in=excluded_obama_ids).count()
    elif request.user.role in ['A','SUPP']:
        all = ObamaCare.objects.filter(created_at__gte=start_of_month,created_at__lte=end_of_month).filter(agent = request.user.id, is_active = True, **company_filter ).exclude(id__in=excluded_obama_ids).count()
        active = ObamaCare.objects.filter(status_color=3,created_at__gte=start_of_month,created_at__lte=end_of_month).filter(agent = request.user.id, is_active = True, **company_filter ).exclude(id__in=excluded_obama_ids).count()
        process = ObamaCare.objects.filter(created_at__gte=start_of_month,created_at__lte=end_of_month).filter(Q(status_color=2) | Q(status_color=1)).filter(agent = request.user.id, is_active = True, **company_filter ).exclude(id__in=excluded_obama_ids).count()
        cancell = ObamaCare.objects.filter(status_color=4,created_at__gte=start_of_month,created_at__lte=end_of_month).filter(agent = request.user.id, is_active = True, **company_filter ).exclude(id__in=excluded_obama_ids).count()
       
   
    dicts = {
        'all': all,
        'active':active,
        'process':process,
        'cancell':cancell
    }
    return dicts

@company_ownership_required_sinURL
def countSalesSupp(request):

    # Obtener el mes y el año actuales
    now = timezone.now()

    # Calcular el primer día del mes
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Calcular el último día del mes
    last_day = calendar.monthrange(now.year, now.month)[1]  # Obtiene el último día del mes
    end_of_month = now.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)

    roleAuditar = ['S', 'C',  'AU', 'Admin']

    company_id = request.company_id  # Obtener company_id desde request
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

@company_ownership_required_sinURL
def tableStatusObama(request):

    # Obtener la fecha y hora actual
    now = timezone.now()
    current_month = now.month
    current_year = now.year

    # Obtener el primer y último día del mes actual (con zona horaria)
    start_of_month = timezone.make_aware(datetime(current_year, current_month, 1), timezone.get_current_timezone())
    end_of_month = timezone.make_aware(datetime(current_year, current_month + 1, 1), timezone.get_current_timezone()) if current_month < 12 else timezone.make_aware(datetime(current_year + 1, 1, 1), timezone.get_current_timezone())

    roleAuditar = ['S', 'C', 'AU', 'Admin']

    company_id = request.company_id  # Obtener company_id desde request
    # Base query con filtro de compañía
    company_filter = {} if request.user.is_superuser else {'company': company_id}

    # Obtener los IDs de ObamaCare que están en CustomerRedFlag
    excluded_obama_ids = list(CustomerRedFlag.objects.values_list('obamacare', flat=True))

    # Construcción de la consulta basada en el rol del usuario
    if request.user.role in roleAuditar:

        # Realizamos la consulta y agrupamos por el campo 'profiling'
        result = ObamaCare.objects.filter(created_at__gte=start_of_month, created_at__lt=end_of_month,is_active = True, **company_filter).exclude(id__in=excluded_obama_ids).values('profiling').annotate(count=Count('profiling')).order_by('profiling')
    
    elif request.user.role in ['A','SUPP']:
        
        # Realizamos la consulta y agrupamos por el campo 'profiling'
        result = ObamaCare.objects.filter(created_at__gte=start_of_month, created_at__lt=end_of_month, is_active = True, **company_filter).exclude(id__in=excluded_obama_ids).values('profiling').filter(agent=request.user.id).annotate(count=Count('profiling')).order_by('profiling')
    

    return result

@company_ownership_required_sinURL
def tableStatusSupp(request):

    # Obtener la fecha y hora actual
    now = timezone.now()
    current_month = now.month
    current_year = now.year

    # Obtener el primer y último día del mes actual (con zona horaria)
    start_of_month = timezone.make_aware(datetime(current_year, current_month, 1), timezone.get_current_timezone())
    end_of_month = timezone.make_aware(datetime(current_year, current_month + 1, 1), timezone.get_current_timezone()) if current_month < 12 else timezone.make_aware(datetime(current_year + 1, 1, 1), timezone.get_current_timezone())

    # Roles con acceso ampliado
    roleAuditar = ['S', 'C', 'AU', 'Admin']

    company_id = request.company_id  # Obtener company_id desde request
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