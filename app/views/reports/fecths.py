# Standard Python libraries
import datetime

# Django utilities
from django.http import JsonResponse
from django.db.models import Subquery

# Application-specific imports
from app.models import *
from ..decoratorsCompany import *

def get_observation_detail(request, observation_id):
    try:
        # Obtener el registro específico
        observation = ObservationCustomer.objects.select_related('agent', 'client').get(id=observation_id)
        
        # Preparar los datos para el JSON
        data = {
            'agent_name': f"{observation.agent.first_name} {observation.agent.last_name}",
            'client_name': f"{observation.client.first_name} {observation.client.last_name}",
            'type_police': observation.type_police,
            'type_call': observation.typeCall,
            'created_at': observation.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'typification': observation.typification,
            'content': observation.content,
        }
        
        return JsonResponse(data)
    except ObservationCustomer.DoesNotExist:
        return JsonResponse({'error': 'Registro no encontrado'}, status=404)

@company_ownership_required_sinURL
def SaleModal(request, agent_id):

    company_id = request.company_id  # Obtener company_id desde request
    company_filter = {'company': company_id} if not request.user.is_superuser else {}
    # Obtener los IDs de ObamaCare que están en CustomerRedFlag
    excluded_obama_ids = CustomerRedFlag.objects.values('obamacare_id')

    start_date = request.POST.get('start_date')  # Obtiene start_date desde la URL
    end_date = request.POST.get('end_date')      # Obtiene end_date desde la URL

    if not start_date and not end_date:
        today = timezone.now()
        start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        if today.month == 12:
            end_date = today.replace(day=31, hour=23, minute=59, second=59, microsecond=999999)
        else:
            end_date = (start_date.replace(month=start_date.month + 1) - timezone.timedelta(seconds=1))

    else:
        start_date = timezone.make_aware(
            datetime.datetime.strptime(start_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
        )
        end_date = timezone.make_aware(
            datetime.datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)
        )

    saleModalObama = ObamaCare.objects.select_related('agent', 'client').filter(
        agent_id=agent_id, created_at__range=[start_date, end_date], is_active = True, **company_filter
    ).exclude( id__in=Subquery(excluded_obama_ids))

    saleModalSupp = Supp.objects.select_related('agent', 'client').filter(
        agent_id=agent_id, created_at__range=[start_date, end_date], is_active = True, **company_filter )
    
    saleModalAssure = ClientsAssure.objects.select_related('agent').filter(
        agent_id=agent_id, created_at__range=[start_date, end_date], is_active = True, **company_filter )
    
    saleModalLife = ClientsLifeInsurance.objects.select_related('agent').filter(
        agent_id=agent_id, created_at__range=[start_date, end_date], is_active = True, **company_filter )


    # Preparar los datos en formato JSON
    data = {
        'obama_sales': [
            {
                'client_name': f'{sale.client.first_name} {sale.client.last_name}', 
                'created_at': sale.created_at.strftime('%Y-%m-%d'),
                'details': sale.profiling,  # Asegúrate de tener este campo en tu modelo
                'carrier':sale.carrier
            }
            for sale in saleModalObama
        ],
        'supp_sales': [
            {
                'client_name':  f'{sale.client.first_name} {sale.client.last_name}',
                'created_at': sale.created_at.strftime('%Y-%m-%d'),
                'details': sale.status,  # Asegúrate de tener este campo en tu modelo
                'carrier':  f'{sale.carrier} - {sale.policy_type}'
            }
            for sale in saleModalSupp
        ] + [
            {
                'client_name': f'{sale.first_name} {sale.last_name}',  # Ajusta si el campo se llama distinto
                'created_at': sale.created_at.strftime('%Y-%m-%d'),
                'details': sale.status,        # Ejemplo: tipo de plan funerario
                'carrier': 'ASSURE - FUNERAL MENBRESIA'     # Nombre de la empresa o aseguradora
            }
            for sale in saleModalAssure
        ] + [
            {
                'client_name': f'{sale.full_name}',  # Ajusta si el campo se llama distinto
                'created_at': sale.created_at.strftime('%Y-%m-%d'),
                'details': sale.status,        # Ejemplo: tipo de plan funerario
                'carrier': 'LIFE INSURANCE'     # Nombre de la empresa o aseguradora
            }
            for sale in saleModalLife
        ],
    }

    return JsonResponse({'success': True, 'data': data})
