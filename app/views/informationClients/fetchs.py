# Standard Python libraries
import json
from calendar import monthrange
from datetime import datetime, date
from typing import Optional

# Django utilities
from django.http import JsonResponse

# Django core libraries
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.urls import reverse

# Application-specific imports
from app.models import *
from ...forms import *
from ...alertWebsocket import websocketAlertGeneric
from ..consents import getCompanyPerAgent

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

@csrf_exempt
def blockSocialSecurityAssure(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        action = request.POST.get('action')
        client_id = request.POST.get('client_id')

        try:
            client = ClientsAssure.objects.get(id=client_id)
        except ClientsAssure.DoesNotExist:
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
def blockSocialSecurityLife(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        action = request.POST.get('action')
        client_id = request.POST.get('client_id')

        try:
            client = ClientsLifeInsurance.objects.get(id=client_id)
        except ClientsLifeInsurance.DoesNotExist:
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
@require_POST
def fetchPaymentOneil(request, obamacareId):
    insuranceCompany = request.POST.get('insuranceCompany')  # Puede ser None
    coverageMonthInput = request.POST.get('coverageMonth')
    payable = request.POST.get('payable')

    # Parsear fechas
    rangeCoverageMonth = parseMonthInputToDate(coverageMonthInput)
    firstDay = rangeCoverageMonth.replace(day=1)
    lastDay = rangeCoverageMonth.replace(day=monthrange(rangeCoverageMonth.year, rangeCoverageMonth.month)[1])

    # Filtros dinámicos
    filters = {
        'obamacare_id': obamacareId,
        'coverageMonth__range': (firstDay, lastDay),
        'payable': payable,
    }

    # Agregar agencia solo si viene válida
    if insuranceCompany:
        filters['agency'] = insuranceCompany.strip()

    payment = PaymentsOneil.objects.filter(**filters)


    if payment.exists():
        return JsonResponse({
            'success': False,
            'message': 'There is already a registration for this ObamaCare and this month'
        })
    
    try:
        obamacare = ObamaCare.objects.get(id=obamacareId)
        payment = PaymentsOneil()
        payment.obamacare = obamacare
        if insuranceCompany:
            payment.agency = insuranceCompany
        else:
            payment.agency = getCompanyPerAgent(obamacare.agent_usa)
        payment.coverageMonth = parseMonthInputToDate(request.POST.get('coverageMonth'))
        payment.payday = request.POST.get('payday')
        payment.payable = request.POST.get('payable')
        payment.save()

    except ObamaCare.DoesNotExist:
        return JsonResponse({'success': False,'message': 'ObamaCare not found'})
    except:
        return JsonResponse({'success': False,'message': 'Error creating payment, please contact an administrator.'})

    return JsonResponse({'success': True,'message': 'Payment successfully created'})

@csrf_exempt
@require_POST
def fetchPaymentCarrier(request, obamacareId):
    
    # Parsear fechas
    rangeCoverageMonth = parseMonthInputToDate(request.POST.get('coverageMonth'))
    firstDay = rangeCoverageMonth.replace(day=1)
    lastDay = rangeCoverageMonth.replace(day=monthrange(rangeCoverageMonth.year, rangeCoverageMonth.month)[1])

    payment = PaymentsCarriers.objects.filter(
        obamacare_id=obamacareId,
        coverageMonth__range=(firstDay, lastDay)
    )

    if payment.exists():
        return JsonResponse({
            'success': False,
            'message': 'There is already a registration for this ObamaCare and this month'
        })
    
    try:
        obamacare = ObamaCare.objects.get(id=obamacareId)
        payment = PaymentsCarriers()
        payment.obamacare = obamacare
        payment.carrier = obamacare.carrier
        payment.coverageMonth = parseMonthInputToDate(request.POST.get('coverageMonth'))
        payment.is_active = True if request.POST.get('status') == 'Active' else False
        payment.save()

    except ObamaCare.DoesNotExist:
        return JsonResponse({'success': False,'message': 'ObamaCare not found'})
    except:
        return JsonResponse({'success': False,'message': 'Error creating payment, please contact an administrator.'})

    return JsonResponse({'success': True,'message': 'Payment successfully created'})

@csrf_exempt
@require_POST
def fetchPaymentSherpa(request, obamacareId):
    
    # Parsear fechas
    rangeCoverageMonth = parseMonthInputToDate(request.POST.get('coverageMonth'))
    firstDay = rangeCoverageMonth.replace(day=1)
    lastDay = rangeCoverageMonth.replace(day=monthrange(rangeCoverageMonth.year, rangeCoverageMonth.month)[1])

    payment = PaymentsSherpa.objects.filter(
        obamacare_id=obamacareId,
        coverageMonth__range=(firstDay, lastDay)
    )

    if payment.exists():
        return JsonResponse({
            'success': False,
            'message': 'There is already a registration for this ObamaCare and this month'
        })
    
    try:
        obamacare = ObamaCare.objects.get(id=obamacareId)
        payment = PaymentsSherpa()
        payment.obamacare = obamacare
        payment.coverageMonth = parseMonthInputToDate(request.POST.get('coverageMonth'))
        payment.is_active = True if request.POST.get('status') == 'Active' else False
        payment.save()

    except ObamaCare.DoesNotExist:
        return JsonResponse({'success': False,'message': 'ObamaCare not found'})
    except:
        return JsonResponse({'success': False,'message': 'Error creating payment, please contact an administrator.'})

    return JsonResponse({'success': True,'message': 'Payment successfully created'})

@csrf_exempt
@require_POST
def fetchPaymentSuplementals(request, suppId):
    
    # Parsear fechas
    rangeCoverageMonth = parseMonthInputToDate(request.POST.get('coverageMonth'))
    firstDay = rangeCoverageMonth.replace(day=1)
    lastDay = rangeCoverageMonth.replace(day=monthrange(rangeCoverageMonth.year, rangeCoverageMonth.month)[1])

    payment = PaymentsSuplementals.objects.filter(
        supp_id=suppId,
        coverageMonth__range=(firstDay, lastDay)
    )

    if payment.exists():
        return JsonResponse({
            'success': False,
            'message': 'There is already a registration for this Suplemental Plan and this month'
        })
    
    try:
        supp = Supp.objects.get(id=suppId)
        payment = PaymentsSuplementals()
        payment.supp = supp
        payment.coverageMonth = parseMonthInputToDate(request.POST.get('coverageMonth'))
        payment.is_active = True if request.POST.get('status') == 'active' else False
        payment.save()

    except Supp.DoesNotExist:
        return JsonResponse({'success': False,'message': 'Suplemental Plan not found'})
    except:
        return JsonResponse({'success': False,'message': 'Error creating payment, please contact an administrator.'})

    return JsonResponse({'success': True,'message': 'Status Suplementals successfully created'})

@csrf_exempt
def fetchPaymentsMonth(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)

        obamaCare_id = data.get('obamacare')
        month = data.get('month')
        type_payment = data.get('type')  # Solo un campo: 'pay' o 'discount'

        if not obamaCare_id or not month or not type_payment:
            return JsonResponse({'success': False, 'message': 'Faltan datos'}, status=400)

        obama = ObamaCare.objects.filter(id=obamaCare_id).first()
        if not obama:
            return JsonResponse({'success': False, 'message': 'ObamaCare no encontrado'}, status=404)

        form_data = {
            'obamacare': obamaCare_id,
            'month': month,
            'typePayment': type_payment,
            'company': obama.company.id,
        }

        form = PaymentsForm(form_data)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.agent = request.user
            payment.save()
            return JsonResponse({'success': True, 'message': 'Payment creado correctamente'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    elif request.method == 'DELETE':
        try:
            data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)

        obamaCare_id = data.get('obamacare')
        month = data.get('month')
        type_payment = data.get('type')

        if not obamaCare_id or not month or not type_payment:
            return JsonResponse({'success': False, 'message': 'Faltan datos'}, status=400)

        payment = Payments.objects.filter(obamacare=obamaCare_id, month=month, typePayment=type_payment).first()
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

        customerRedFlag = CustomerRedFlag.objects.select_related('agent_create').get(id = id_value)
        obama = customerRedFlag.obamacare
        clients = obama.client

        CustomerRedFlag.objects.filter(id=id_value).update(
            agent_completed=request.user,
            date_completed=timezone.now().date(),
        )

        # Construir la URL absoluta
        url_relativa = reverse('editObama', args=[obama.id, 1])
        url_absoluta = request.build_absolute_uri(url_relativa)

        websocketAlertGeneric(
            request,
            'send_alert',
            'actionCompleted',
            'info',
            'New Action Required completed',
            f'The required action ({customerRedFlag.description}) of the client {clients.first_name} {clients.last_name} has already been performed.',
            'Go to customer with the required action completed.',
            url_absoluta,
            customerRedFlag.agent_create.id,
            customerRedFlag.agent_create.username

        )

        return JsonResponse({'success': True, 'message': 'Acción POST procesada', 'id': id_value})

    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)

def countDigits(numero):
  """
  Esta función toma un valor (esperando que sea un número o una cadena numérica)
  y devuelve la cantidad de dígitos que tiene.
  Maneja el caso en que la entrada sea una cadena.
  """
  try:
    # Intenta convertir la cadena a un entero
    numero_entero = int(numero)
    # Ahora podemos calcular el valor absoluto y luego la longitud de su representación en string
    return len(str(abs(numero_entero)))
  except (TypeError, ValueError):
    # Si la conversión a entero falla (no es una cadena numérica válida),
    # intentamos contar la longitud de la cadena original (si es una cadena)
    if isinstance(numero, str):
      return len(numero)
    else:
      # Si no es ni un número convertible a entero ni una cadena, devolvemos 0 o raise un error
      return 0  # O podrías hacer raise TypeError("Se esperaba un número o una cadena numérica.")

@csrf_exempt
def validatePhone(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        phoneNumber = data.get('phone_number')

        amount = countDigits(phoneNumber)

        if amount == 10:
            newNumber = int(f'1{phoneNumber}')
        else:
            newNumber = phoneNumber

        exists = Clients.objects.filter(phone_number=newNumber).exists()

        return JsonResponse({'exists': exists})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def validateKey(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        accessKey = data.get('access_key')
        phoneNumber = data.get('phone_number')

        amount = countDigits(phoneNumber)

        if amount == 10:
            newNumber = int(f'1{phoneNumber}')
        else:
            newNumber = phoneNumber

        keys = KeyAccess.objects.all()

        for key in keys:   
            if  accessKey == key.password:
                allowed = True

                client = Clients.objects.filter(phone_number = newNumber).first()

                # Aquí guardamos el registro
                KeyAccessLog.objects.create(
                    user=request.user,
                    client=client,
                    password=key
                )               

        return JsonResponse({'allowed': allowed})
    return JsonResponse({'error': 'Invalid request'}, status=400)

def parseMonthInputToDate(monthStr: str) -> Optional[date]:
    """
    Converts a 'YYYY-MM' string from an <input type="month"> to a date object
    using the first day of the month.

    Args:
        monthStr (str): A string in the format 'YYYY-MM'.

    Returns:
        date: A date object with day=1, or None if the input is invalid.
    """
    try:
        return datetime.datetime.strptime(monthStr + "-01", "%Y-%m-%d").date()
    except ValueError:
        return None