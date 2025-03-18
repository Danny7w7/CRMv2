# Standard Python libraries
import datetime

# Django utilities
from django.http import JsonResponse

# Application-specific imports
from app.models import *

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

def SaleModal(request, agent_id):

    start_date = request.POST.get('start_date')  # Obtiene start_date desde la URL
    end_date = request.POST.get('end_date')      # Obtiene end_date desde la URL
    print(start_date)

    if not start_date and not end_date:
        today = timezone.now()
        start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        if today.month == 12:
            end_date = today.replace(day=31, hour=23, minute=59, second=59, microsecond=999999)
        else:
            end_date = (start_date.replace(month=start_date.month + 1) - timezone.timedelta(seconds=1))

    else:
        start_date = timezone.make_aware(
            datetime.strptime(start_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
        )
        end_date = timezone.make_aware(
            datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)
        )

    saleModalObama = ObamaCare.objects.select_related('agent', 'client').filter(
        agent_id=agent_id, created_at__range=[start_date, end_date], is_active = True
    )
    saleModalSupp = Supp.objects.select_related('agent', 'client').filter(
        agent_id=agent_id, created_at__range=[start_date, end_date], is_active = True
    )


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
                'carrier':  f'{sale.company} - {sale.policy_type}'
            }
            for sale in saleModalSupp
        ],
    }

    return JsonResponse({'success': True, 'data': data})
