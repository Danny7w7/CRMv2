# Standard Python libraries
import json
import re

# Django utilities
from django.http import JsonResponse

# Django core libraries
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse

# Application-specific imports
from app.models import *
from ...forms import *
from ...alertWebsocket import websocketAlertGeneric

@csrf_exempt
def blockSocialSecurity(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        action = request.POST.get('action')
        client_id = request.POST.get('client_id')

        try:
            client = Clients.objects.get(id=client_id)
        except Clients.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Cliente no encontrado.'})

        if action == 'validate_key':
            provided_key = request.POST.get('key')
            correct_key = 'Sseguros22@'  # 🔹 Cambia esto por una validación más segura

            if provided_key == correct_key:
                return JsonResponse({'status': 'success', 'social': client.social_security})
            else:
                return JsonResponse({'status': 'error', 'message': 'Clave incorrecta o no hay número disponible.'})

        elif action == 'save_social':
            new_social = request.POST.get('new_social')

            if not new_social or len(new_social) != 9 or not new_social.isdigit():
                return JsonResponse({'status': 'error', 'message': 'Número de seguro social inválido.'})

            client.social_security = new_social
            client.save()
            return JsonResponse({'status': 'success', 'message': 'Número de seguro social guardado correctamente.'})

    return JsonResponse({'status': 'error', 'message': 'Solicitud no válida.'}, status=400)

@csrf_exempt
def blockSocialSecurityMedicare(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        action = request.POST.get('action')
        client_id = request.POST.get('client_id')

        try:
            client = Medicare.objects.get(id=client_id)
        except Medicare.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Cliente no encontrado.'})

        if action == 'validate_key':
            provided_key = request.POST.get('key')
            correct_key = 'Sseguros22@'  # 🔹 Cambia esto por una validación más segura

            if provided_key == correct_key:
                return JsonResponse({'status': 'success', 'social': client.social_security})
            else:
                return JsonResponse({'status': 'error', 'message': 'Clave incorrecta o no hay número disponible.'})

        elif action == 'save_social':
            new_social = request.POST.get('new_social')

            if not new_social or len(new_social) != 9 or not new_social.isdigit():
                return JsonResponse({'status': 'error', 'message': 'Número de seguro social inválido.'})

            client.social_security = new_social
            client.save()
            return JsonResponse({'status': 'success', 'message': 'Número de seguro social guardado correctamente.'})

    return JsonResponse({'status': 'error', 'message': 'Solicitud no válida.'}, status=400)

@csrf_exempt  # Solo usar en pruebas; manejar CSRF en producción correctamente
def fetchPaymentsMonth(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)  # Leer JSON del request
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)

        obamaCare_id = data.get('obamaCare')
        month = data.get('month')
        type_pay = data.get('type_pay')  # Obtener el tipo de pago
        type_discount = data.get('type_discount')  # Obtener el tipo de descuento

        # Validación de los datos recibidos
        if not obamaCare_id or not month:
            return JsonResponse({'success': False, 'message': 'Faltan datos'}, status=400)

        # Obtener la instancia de ObamaCare
        obama = ObamaCare.objects.filter(id=obamaCare_id).first()
        if not obama:
            return JsonResponse({'success': False, 'message': 'ObamaCare no encontrado'}, status=404)

        # Ahora, según el tipo de checkbox seleccionado, asignamos el tipo de pago o descuento
        if type_pay:
            type = 'pay'  # Si el tipo de pago es 'pay'
        elif type_discount:
            type = 'discount'  # Si el tipo de pago es 'discount'
        else:
            type = 'unknown'  # Si ninguno está seleccionado, asignamos 'unknown'


        
        # Crear el formulario de Payments con los datos recibidos
        form_data = {
            'obamaCare': obamaCare_id,
            'month': month,
            'typePayment': type,  # Asignar el tipo de pago o descuento
            'company': obama.company.id,  # Asignar la compañía, usando el ID
        }

        # Crear el formulario de Payments con los datos
        form = PaymentsForm(form_data)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.agent = request.user  # Asignar el agente (usuario que hace la solicitud)
            payment.save()
            return JsonResponse({'success': True, 'message': 'Payment creado correctamente', 'role': request.user.role})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)


    elif request.method == 'DELETE':
        try:
            # Asegúrate de que el contenido de la solicitud sea JSON
            data = json.loads(request.body.decode('utf-8'))  # Decodificar correctamente si es necesario
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)

        obamaCare_id = data.get('obamaCare')
        month = data.get('month')

        if not obamaCare_id or not month:
            return JsonResponse({'success': False, 'message': 'Faltan datos'}, status=400)

        # Buscar y eliminar el pago
        payment = Payments.objects.filter(obamaCare=obamaCare_id, month=month).first()
        if payment:
            payment.delete()
            return JsonResponse({'success': True, 'message': 'Payment eliminado correctamente'})
        else:
            return JsonResponse({'success': False, 'message': 'Payment no encontrado'}, status=404)

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

def delete_supp(request ,supp_id):
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

        # Construir la URL absoluta
        url_relativa = reverse('editObama', args=[obama.company.id,obama.id, 1])
        url_absoluta = request.build_absolute_uri(url_relativa)

        websocketAlertGeneric(
            request,
            'send_alert',
            'actionCompleted',
            'info',
            'New Action Required completed',
            f'The required action ({customerRedFlag.description}) of the client {clients.first_name} {clients.last_name} has already been performed.',
            'Go to customer with the required action completed.',
            url_absoluta
        )

        return JsonResponse({'success': True, 'message': 'Acción POST procesada', 'id': id_value})

    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)
