# Django core libraries
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

# Application-specific imports
from app.models import *
from ..decoratorsCompany import *


@login_required(login_url='/login') 
@company_ownership_required_sinURL
def select_client(request):

    company_id = request.company_id  # Obtener company_id desde request

    if request.user.is_superuser: 
        clients = Clients.objects.all()
    elif request.user.role == 'Admin': 
        clients = Clients.objects.filter(company = company_id)
    else: clients = Clients.objects.filter(is_active = True, company = company_id)

    context = {
        'clients' : clients,
        'company_id' : company_id
    }
    
    return render(request, 'newSale/selectClient.html', context)

@company_ownership_required_sinURL
def update_type_sales(request ,client_id):
    company_id = request.company_id  # Obtener company_id desde request
    type_sales = request.POST.get('type_sales')
    route = request.POST.get('route')
    if type_sales:
        # Redirige a la URL previa con el ID del cliente
        if route == 'ACA': return redirect('formAddObama', client_id, type_sales)
        elif route == 'SUPP': return redirect('formAddSupp', client_id, type_sales)
        elif route == 'DEPEND': return redirect('formAddDepend', client_id)
        else: return redirect('select_client')

@company_ownership_required_sinURL
def selectClientAssure(request):

    company_id = request.company_id  # Obtener company_id desde request

    if request.user.is_superuser: 
        clients = ClientsAssure.objects.all()
    elif request.user.role == 'Admin': 
        clients = ClientsAssure.objects.filter(company = company_id)
    else: clients = ClientsAssure.objects.filter(is_active = True, company = company_id)

    context = {
        'clients' : clients,
        'company_id' : company_id
    }

    return render(request, 'newSale/selectClientAssure.html', context)

