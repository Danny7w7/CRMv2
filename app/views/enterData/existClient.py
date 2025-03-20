# Django core libraries
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

# Application-specific imports
from app.models import *
from ..decoratorsCompany import company_ownership_required


@login_required(login_url='/login') 
@company_ownership_required
def select_client(request, company_id):

    if request.user.is_superuser: 
        clients = Clients.objects.all()
    elif request.user.role == 'Admin': 
        clients = Clients.objects.filter(company = company_id)
    else: clients = Clients.objects.filter(is_active = True, company = company_id)
    
    return render(request, 'newSale/selectClient.html', {'clients':clients})

def update_type_sales(request, client_id):
    if request.method == 'POST':
        type_sales = request.POST.get('type_sales')
        route = request.POST.get('route')
        if type_sales:
            client = get_object_or_404(Clients, id=client_id)
            client.type_sales = type_sales
            client.save()
            # Redirige a la URL previa con el ID del cliente
            if route == 'ACA': return redirect('formAddObama', client_id=client_id)
            elif route == 'SUPP': return redirect('formAddSupp', client_id=client_id)
            elif route == 'DEPEND': return redirect('formAddDepend', client_id=client_id)
            else: return redirect('select_client')

