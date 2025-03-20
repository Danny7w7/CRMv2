# Standard Python libraries
from django.http import JsonResponse, HttpResponse

# Django core libraries
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404, redirect, render 

# Application-specific imports
from app.models import *

@login_required(login_url='/login') 
def fromCreateCompanies(request):

    companies = Companies.objects.all()

    if request.method == 'POST':
        owner = request.POST.get('owner').upper()
        name = request.POST.get('name').upper()
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        
        try:     

            companies = Companies.objects.all()
            
            companie = Companies.objects.create(
                owner=owner,
                company_name=name, 
                phone_company=phone,
                company_email=email
            )

            context = {
                'msg':f'Companies {companie.owner} creado con éxito.',
                'companies':companies,
                'type':'good'
            }

            return render(request, 'forms/fromCreateCompanies.html', context)

        except Exception as e:
            return HttpResponse(str(e))
    
    context = {
        'companies' : companies
    }
            
    return render(request, 'forms/fromCreateCompanies.html', context)

@login_required(login_url='/login') 
def editCompanies(request, companies_id):
    # Obtener el usuario a editar o devolver un 404 si no existe
    company = get_object_or_404(Companies, id=companies_id)

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
        return redirect('fromCreateCompanies')  

    # Renderizar el formulario con los datos actuales del usuario
    context = {'company': company}
    return render(request, 'edit/editCompanies.html', context)

@login_required(login_url='/login') 
def toggleCompanies(request, companies_id):
    # Obtener el cliente por su ID
    company = get_object_or_404(company, id=companies_id)
    
    # Cambiar el estado de is_active (True a False o viceversa)
    company.is_active = not company.is_active
    company.save()  # Guardar los cambios en la base de datos
    
    # Redirigir de nuevo a la página actual con un parámetro de éxito
    return redirect('fromCreateCompanies')
