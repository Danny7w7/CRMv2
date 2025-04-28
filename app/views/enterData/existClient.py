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

def updateTypeSales(request ,client_id):
    type_sales = request.POST.get('type_sales')
    route = request.POST.get('route')
    if route == 'ACA':   
        request.session['type_sales'] = type_sales 
        return redirect('formAddObama', client_id)
    elif route == 'SUPP': 
        request.session['type_sales'] = type_sales
        return redirect('formAddSupp', client_id)
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

