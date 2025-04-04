# Standard Python libraries
from django.http import HttpResponse
from django.db.models import F

# Django core libraries
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404, redirect, render 

# Application-specific imports
from app.models import *
from ...forms import ServicesForm

@login_required(login_url='/login') 
def formCreateCompanies(request):

    companies = Companies.objects.exclude(id = 1)

    if request.method == 'POST':
        owner = request.POST.get('owner').upper()
        name = request.POST.get('name').upper()
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        zipcode = request.POST.get('zipcode')
        city = request.POST.get('city')
        state = request.POST.get('state')
        county = request.POST.get('county')
        
        try:
            company = Companies.objects.create(
                owner=owner,
                company_name=name, 
                phone_company=phone,
                company_email=email,
                remaining_balance=0,
                zipcode=zipcode,
                city=city,
                state=state,
                county=county
            )

            context = {
                'msg':f'Companies {company.company_name} creado con éxito.',
                'companies':companies,
                'type':'good'
            }

            return render(request, 'companies/formCreateCompanies.html', context)

        except Exception as e:
            return HttpResponse(str(e))
    
    context = {
        'companies':companies
    }
            
    return render(request, 'companies/formCreateCompanies.html', context)

@login_required(login_url='/login') 
def editCompanies(request, company_id):
    # Obtener el usuario a editar o devolver un 404 si no existe
    company = get_object_or_404(Companies, id=company_id)

    if request.method == 'POST':
        # Recuperar los datos del formulario

        owner = request.POST.get('owner', company.owner)
        name = request.POST.get('name', company.company_name)
        phone = request.POST.get('phone', company.phone_company)
        email = request.POST.get('email', company.company_email)
        zipcode = request.POST.get('zipcode', company.zipcode)
        city = request.POST.get('city', company.city)
        state = request.POST.get('state', company.state)
        county = request.POST.get('county', company.county)
        is_active = request.POST.get('is_active', company.is_active)

        # Actualizar los datos del usuario
        company.owner = owner
        company.company_name = name
        company.phone_company = phone
        company.company_email = email
        company.zipcode = zipcode
        company.city = city
        company.state = state
        company.county = county
        company.is_active = is_active

        # Guardar los cambios
        company.save()

        # Redirigir a otra vista o mostrar un mensaje de éxito
        return redirect('formCreateCompanies')  

    # Renderizar el formulario con los datos actuales del usuario
    context = {'company': company}
    return render(request, 'companies/editCompanies.html', context)

@login_required(login_url='/login') 
def toggleCompanies(request, company_id):
    # Obtener el cliente por su ID
    company = get_object_or_404(Companies, id=company_id)

    users = Users.objects.filter(company=company)
    users.update(is_active=~F('is_active'))
    
    # Cambiar el estado de is_active (True a False o viceversa)
    company.is_active = not company.is_active
    company.save()  # Guardar los cambios en la base de datos
    
    # Redirigir de nuevo a la página actual con un parámetro de éxito
    return redirect('formCreateCompanies')

@login_required(login_url='/login')
def createServices(request):

    dropList = DropDownList.objects.filter(service_company__isnull=False).values_list('service_company', flat=True)

    if request.method == 'POST':

        form = ServicesForm(request.POST)
        if form.is_valid():
            form.save()

        return redirect('createServices')
    
    return render(request, 'companies/createServices.html', {'dropList':dropList})

@login_required(login_url='/login') 
def addSubscription(request):

    company = Companies.objects.filter(is_active = True)
    service = Services.objects.all()

    if request.method == "POST":
        company_ids = request.POST.getlist('company[]')
        service_ids = request.POST.getlist('service[]')
        auto_renew_list = request.POST.getlist('auto_renew[]')
        renewal_periods = request.POST.getlist('renewal_period[]')

        for company_id, service_id, auto_renew, renewal_period in zip(company_ids, service_ids, auto_renew_list, renewal_periods):
            try:
                company = Companies.objects.get(id=company_id)
                service = Services.objects.get(id=service_id)

                Subscriptions.objects.create(
                    company=company,
                    service=service,
                    auto_renew=(auto_renew.lower() == 'true'),  # Convertir a booleano
                    renewal_period=renewal_period
                )
            except (Companies.DoesNotExist, Services.DoesNotExist):
                continue  # Si no encuentra la empresa o servicio, lo ignora

        return redirect('addSubscription')  # Redirige a una página de éxito
    
    context = {
        'company' : company,
        'service' : service
    }

    return render(request, 'companies/addSubscription.html' , context)

# ... (otras importaciones)

@login_required(login_url='/login')
def addNumbers(request):
    company = Companies.objects.filter(is_active=True)
    numbersBD = Numbers.objects.all()
    hasErrors = False

    if request.method == "POST":

        company_ids = request.POST.getlist('company[]')
        numbers = request.POST.getlist('number[]')
        validNumbers = 0

        for company_id, number in zip(company_ids, numbers):
            try:
                company = Companies.objects.get(id=company_id)
                formatted_number = validatePhoneNumber(number)
                
                validations = Numbers.objects.filter(phone_number=formatted_number).first()

                if not validations:

                    if formatted_number:
                        Numbers.objects.create(
                            company=company,
                            phone_number=formatted_number
                        )
                        validNumbers += 1
                    else:
                        messages.error(request, f"El número + <strong>{number}</strong> no es válido.")
                        hasErrors = True
                
                else:
                    messages.error(request, f"El número + <strong> {number} </strong> no ya lo tiene otra company.")
                    hasErrors = True

            except Companies.DoesNotExist:
                messages.error(request, f"La compañía con ID '{company_id}' no existe.")
                hasErrors = True

        if not hasErrors:
            messages.success(request, f"Se agregaron {validNumbers} números correctamente.")
        elif validNumbers > 0:
            messages.warning(request, f"Se agregaron {validNumbers} números, pero hubo errores con algunos.")

        # Redirigir para evitar reenvío del formulario
        return redirect('addNumbers')
    
    context = {
        'company': company,
        'numbersBD': numbersBD
    }

    return render(request, 'companies/addNumbers.html', context)

def validatePhoneNumber(phoneNumber):
    """
    Valida y formatea un número de teléfono según las siguientes reglas:
    - Debe tener 10 u 11 dígitos.
    - Si tiene 11 dígitos, el primero debe ser '1'.
    - Si tiene 10 dígitos, se agrega '1' al inicio.
    - Si tiene más de 11 dígitos y no comienza con '1', se considera inválido.
    - En cualquier otro caso (menos de 10 dígitos), se considera inválido.
    """
    cleanNumber = ''.join(filter(str.isdigit, str(phoneNumber)))
    length = len(cleanNumber)

    if length == 10:
        return '1' + cleanNumber
    elif length == 11:
        if cleanNumber.startswith('1'):
            return cleanNumber
        else:
            return False
    elif length > 11:
        if cleanNumber.startswith('1'):
            return cleanNumber
        else:
            return False
    else:
        return False
    
def toggleNumberCompany(request, number_id):
    # Obtener el cliente por su ID
    number = get_object_or_404(Numbers, id=number_id)
    
    # Cambiar el estado de is_active (True a False o viceversa)
    number.is_active = not number.is_active
    number.save()  # Guardar los cambios en la base de datos
    
    # Redirigir de nuevo a la página actual con un parámetro de éxito
    return redirect('addNumbers')
