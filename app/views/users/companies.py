# Standard Python libraries
from django.http import HttpResponse
from django.db.models import F

# Django core libraries
from django.contrib.auth.decorators import login_required
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
        
        try:
            company = Companies.objects.create(
                owner=owner,
                company_name=name, 
                phone_company=phone,
                company_email=email,
                remaining_balance=0
            )

            companies = Companies.objects.all()

            context = {
                'msg':f'Companies {company.company_name} creado con éxito.',
                'companies':companies,
                'type':'good'
            }

            return render(request, 'forms/formCreateCompanies.html', context)

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
        is_active = request.POST.get('is_active', company.is_active)

        # Actualizar los datos del usuario
        company.owner = owner
        company.company_name = name
        company.phone_company = phone
        company.company_email = email
        company.is_active = is_active

        # Guardar los cambios
        company.save()

        # Redirigir a otra vista o mostrar un mensaje de éxito
        return redirect('formCreateCompanies')  

    # Renderizar el formulario con los datos actuales del usuario
    context = {'company': company}
    return render(request, ' companies/editCompanies.html', context)

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
        
    if request.method == 'POST':

        form = ServicesForm(request.POST)
        if form.is_valid():
            form.save()

        return redirect('createServices')
    
    return render(request, 'companies/createServices.html')


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
