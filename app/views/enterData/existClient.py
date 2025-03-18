# Django core libraries
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

# Application-specific imports
from app.models import *


@login_required(login_url='/login') 
def select_client(request):

    if request.user.role == 'Admin': clients = Clients.objects.all()
    else: clients = Clients.objects.filter(is_active = True)
    
    return render(request, 'agents/select_client.html', {'clients':clients})

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

