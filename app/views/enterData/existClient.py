# Django core libraries
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from datetime import date


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

@login_required(login_url='/login') 
def updateTypeSales(request, client_id):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Método no permitido."}, status=405)

    type_sales = request.POST.get('type_sales')
    route = request.POST.get('route')

    if route == 'ACA':

        today = date.today()

        # Definir el mes y el día en que empieza el año fiscal (1 de noviembre)
        fiscalYearStart = (11, 1)

        # Determinar las fechas de inicio y fin del rango
        if (today.month, today.day) >= fiscalYearStart:
            # Si estamos en o después del 1 de noviembre, el rango es de este año al siguiente
            startDate = date(today.year, 11, 1)
            endDate = date(today.year + 1, 10, 31)
        else:
            # Si estamos antes del 1 de noviembre, el rango es del año pasado a este
            startDate = date(today.year - 1, 11, 1)
            endDate = date(today.year, 10, 31)

        duplication = ObamaCare.objects.filter(client=client_id, is_active=True, created_at__range=(startDate, endDate))

        if duplication.exists():
            return JsonResponse({"status": "error", "message": "Este cliente ya está activo en ACA."})
        
        request.session['type_sales'] = type_sales
        return JsonResponse({"status": "success", "redirect_url": f"/formAddObama/{client_id}/"})

    elif route == 'SUPP':
        request.session['type_sales'] = type_sales
        return JsonResponse({"status": "success", "redirect_url": f"/formAddSupp/{client_id}/"})

    return JsonResponse({"status": "success", "redirect_url": "/select_client/"})

@login_required(login_url='/login') 
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

