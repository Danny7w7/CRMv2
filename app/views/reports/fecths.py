# Standard Python libraries
import datetime

# Django utilities
from django.http import HttpResponse, JsonResponse
from django.db.models import Subquery, Q
from django.utils.timezone import make_aware
from datetime import datetime, timedelta
from django.shortcuts import render, get_object_or_404

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
def detalleAgente(request):

    company_id = request.company_id  # Obtener company_id desde request
    company_filter = {'company': company_id} if not request.user.is_superuser else {}

    agent_id = request.GET.get('agent_id')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    agente = get_object_or_404(Users, id=agent_id)

    if not start_date or not end_date:
        today = timezone.now()
        start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = (start_date.replace(month=start_date.month + 1) - timedelta(seconds=1)) if start_date.month < 12 else today.replace(month=12, day=31, hour=23, minute=59)
    else:
        start_date = make_aware(datetime.strptime(start_date, '%Y-%m-%d').replace(hour=0, minute=0))
        end_date = make_aware(datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59))

    filtro_fecha = Q(created_at__range=(start_date, end_date))
    filtro_agente = Q(agent=agente)

    context = {
        'obamacare': ObamaCare.objects.select_related('client').filter(filtro_agente & filtro_fecha, **company_filter, is_active = True),
        'supp': Supp.objects.select_related('client').filter(filtro_agente & filtro_fecha, **company_filter, is_active = True),
        'medicare': Medicare.objects.filter(filtro_agente & filtro_fecha, **company_filter, is_active = True),
        'assure': ClientsAssure.objects.filter(filtro_agente & filtro_fecha, **company_filter, is_active = True),
        'life': ClientsLifeInsurance.objects.filter(filtro_agente & filtro_fecha, **company_filter, is_active = True),
    }

    return render(request, 'saleReports/templateModal.html', context)


