# Standard Python libraries
import json
import re

# Django utilities
from django.http import JsonResponse

# Django core libraries
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse

# Third-party libraries
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer  

# Application-specific imports
from app.models import *
from ...forms import *

@csrf_exempt
def fetchPaymentsMonth(request):
    form = PaymentsForm(request.POST)
    if request.method == 'POST':
        if form.is_valid():
            payment = form.save(commit=False)
            payment.agent = request.user
            payment.save()
            return JsonResponse({'success': True, 'message': 'Payment creado correctamente', 'role': request.user.role})
        else:
            # Si el formulario no es válido, devolvemos los errores en formato JSON
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    elif request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            obamaCare = data.get('obamaCare')
            month = data.get('month')

            # Buscar y eliminar el pago
            payment = Payments.objects.filter(obamaCare=obamaCare, month=month).first()
            if payment:
                payment.delete()
                return JsonResponse({'success': True, 'message': 'Payment eliminado correctamente'})
            else:
                return JsonResponse({'success': False, 'message': 'Payment no encontrado'}, status=404)

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)
    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)

def delete_dependent(request, dependent_id):
    if request.method == 'POST':
        try:
            # Buscar y eliminar el dependiente por ID
            dependent = Dependents.objects.get(id=dependent_id)
            dependent.delete()
            return JsonResponse({'success': True})
        except Dependents.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Dependent not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def delete_supp(request, supp_id):
    if request.method == 'POST':
        try:
            # Buscar y eliminar el dependiente por ID
            supp = Supp.objects.get(id=supp_id)
            supp.delete()
            return JsonResponse({'success': True})
        except Supp.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Dependent not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@csrf_exempt
def fetchActionRequired(request):

    if request.method == 'POST':
        id_value = request.POST.get('id')

        customerRedFlag = CustomerRedFlag.objects.get(id = id_value)
        obama = customerRedFlag.obama
        clients = obama.client

        CustomerRedFlag.objects.filter(id=id_value).update(
            agent_completed=request.user,
            date_completed=timezone.now().date(),
        )

        #Aqui inicia el websocket
        app_name = request.get_host()  # Obtener el host (ej. "127.0.0.1:8000" o "miapp.com")

        # Reemplazar ":" y otros caracteres inválidos con "_" para hacer un nombre válido
        app_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', app_name)

        # Construir la URL absoluta
        url_relativa = reverse('editClientObama', args=[obama.id, 1])
        url_absoluta = request.build_absolute_uri(url_relativa)

        group_name = f'product_alerts_{app_name}'

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'send_alert',
                'event_type': 'action_completed',
                'message': f'The required action ({customerRedFlag.description}) of the client {clients.first_name} {clients.last_name} has already been performed.',
                'extra_info': url_absoluta
            }
        )

        print(f"POST recibido con id: {id_value}")

        return JsonResponse({'success': True, 'message': 'Acción POST procesada', 'id': id_value})

    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)
