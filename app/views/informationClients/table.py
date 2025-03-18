# Django core libraries
from django.contrib.auth.decorators import login_required
from django.db.models import Subquery, OuterRef
from django.db.models.functions import Substr
from django.shortcuts import render

# Application-specific imports
from app.models import *

@login_required(login_url='/login')
def clientObamacare(request):
    

    borja = 'BORJA G CANTON HERRERA - NPN 20673324'
    daniel = 'DANIEL SANTIAGO LAPEIRA ACEVEDO - NPN 19904958'
    luis = 'LUIS EDUARDO LAPEIRA - NPN 20556081'
    gina = 'GINA PAOLA LAPEIRA - NPN 19944280'
    evelyn = 'EVELYN BEATRIZ HERRERA - NPN 20671818'
    danieska = 'DANIESKA LOPEZ SEQUEIRA - NPN 20134539'
    rodrigo = 'RODRIGO G CANTON - NPN 20670005'
    zohira = 'ZOHIRA RAQUEL DUARTE AGUILAR - NPN 19582295'
    vladimir = 'VLADIMIR DE LA HOZ FONTALVO - NPN 19915005'
    
    if request.user.role == 'Admin':       
        obamaCare = ObamaCare.objects.select_related('agent','client').annotate(
            truncated_agent_usa=Substr('agent_usa', 1, 8)).exclude(
                id__in=CustomerRedFlag.objects.filter(date_completed__isnull=True).values_list(
                    'obama_id', flat=True)).order_by('-created_at')    
    elif request.user.username == 'zohiraDuarte':
       obamaCare = ObamaCare.objects.select_related('agent','client').annotate(
            truncated_agent_usa=Substr('agent_usa', 1, 8)).filter(is_active = True, agent_usa = zohira).exclude(
                id__in=CustomerRedFlag.objects.filter(date_completed__isnull=True).values_list(
                    'obama_id', flat=True)).order_by('-created_at') 
    elif request.user.username == 'vladimirDeLaHoz':
        obamaCare = ObamaCare.objects.select_related('agent','client').annotate(
            truncated_agent_usa=Substr('agent_usa', 1, 8)).filter(is_active = True, agent_usa = vladimir).exclude(
                id__in=CustomerRedFlag.objects.filter(date_completed__isnull=True).values_list(
                    'obama_id', flat=True)).order_by('-created_at')
    else:
        obamaCare = ObamaCare.objects.select_related('agent', 'client').annotate(
            truncated_agent_usa=Substr('agent_usa', 1, 8)).filter(is_active = True).exclude(
                id__in=CustomerRedFlag.objects.filter(date_completed__isnull=True).values_list(
                    'obama_id', flat=True)).order_by('-created_at')      


    return render(request, 'informationClient/clientObamacare.html', {'obamacares':obamaCare})

@login_required(login_url='/login')
def clientAccionRequired(request):
    
    if request.user.role == 'Admin':       
        obamaCare = ObamaCare.objects.select_related('agent', 'client').annotate(
            truncated_agent_usa=Substr('agent_usa', 1, 8),customer_red_flag_clave=Subquery(
                CustomerRedFlag.objects.filter(obama_id=OuterRef('id'), date_completed__isnull=True
                    ).values('clave')[:1] )).filter( id__in=CustomerRedFlag.objects.filter(
                        date_completed__isnull=True ).values_list('obama_id', flat=True) ).order_by('-created_at')
        
    elif request.user.role == 'S' :   

        obamaCare = ObamaCare.objects.select_related('agent', 'client').annotate(
            truncated_agent_usa=Substr('agent_usa', 1, 8),customer_red_flag_clave=Subquery(
                CustomerRedFlag.objects.filter(obama_id=OuterRef('id'), date_completed__isnull=True
                    ).values('clave')[:1] )).filter( id__in=CustomerRedFlag.objects.filter(
                        date_completed__isnull=True ).values_list('obama_id', flat=True), is_active = True ).order_by('-created_at')    

    else:        
        obamaCare = ObamaCare.objects.select_related('agent', 'client').annotate(
            truncated_agent_usa=Substr('agent_usa', 1, 8),customer_red_flag_clave=Subquery(
                CustomerRedFlag.objects.filter(obama_id=OuterRef('id'), date_completed__isnull=True
                    ).values('clave')[:1] )).filter( id__in=CustomerRedFlag.objects.filter(
                        date_completed__isnull=True ).values_list('obama_id', flat=True), is_active = True, agent_id = request.user.id ).order_by('-created_at')


    return render(request, 'informationClient/clientAccionRequired.html', {'obamacares':obamaCare})

@login_required(login_url='/login')
def clientSupp(request):

    roleAuditar = ['S', 'C','SUPP', 'AU']
    
    if request.user.role in roleAuditar:
        supp = Supp.objects.select_related('agent','client').filter(is_active = True).exclude(status_color = 1).annotate(
            truncated_agent_usa=Substr('agent_usa', 1, 8)).order_by('-created_at')
        suppPay = Supp.objects.select_related('agent','client').filter(is_active = True, status_color = 1 )

        for item in suppPay:
            client_name = item.agent_usa if item.agent_usa else "Sin Name"    
            item.short_name = client_name.split()[0] + " ..." if " " in client_name else client_name

    elif request.user.role == 'Admin':
        supp = Supp.objects.select_related('agent','client').annotate(
            truncated_agent_usa=Substr('agent_usa', 1, 8)).order_by('-created_at')
        suppPay = False
    elif request.user.role in ['A', 'C']:
        supp = Supp.objects.select_related('agent','client').annotate(
            truncated_agent_usa=Substr('agent_usa', 1, 8)).filter(agent = request.user.id, is_active = True).order_by('-created_at')
        suppPay = False

    return render(request, 'informationClient/clientSupp.html', {'supps':supp,'suppPay':suppPay})

@login_required(login_url='/login')
def clientMedicare(request):
    
    roleAuditor = ['S','AU']
    
    if request.user.role == 'Admin':       
        medicare = Medicare.objects.select_related('agent').annotate(
            truncated_agent_usa=Substr('agent_usa', 1, 8)).order_by('-created_at')
    elif request.user.role in roleAuditor:
        medicare = Medicare.objects.select_related('agent').annotate(
            truncated_agent_usa=Substr('agent_usa', 1, 8)).filter(is_active = True).order_by('-created_at')   
    else:
        medicare = Medicare.objects.select_related('agent').annotate(
            truncated_agent_usa=Substr('agent_usa', 1, 8)).filter(is_active = True, agent_id = request.user.id).order_by('-created_at')   


    return render(request, 'informationClient/clientMedicare.html', {'medicares':medicare})

@login_required(login_url='/login')    
def tableAlert(request):

    roleAuditar = ['S', 'C',  'AU']
    
    if request.user.role in roleAuditar:
        alert = ClientAlert.objects.select_related('agent').annotate(
            truncated_contect=Substr('content', 1, 20)).filter(is_active = True)
    elif request.user.role == 'Admin':
        alert = ClientAlert.objects.select_related('agent').annotate(
            truncated_contect=Substr('content', 1, 20))
    elif request.user.role == 'A':
        alert = ClientAlert.objects.select_related('agent').annotate(
            truncated_contect=Substr('content', 1, 20)).filter(agent = request.user.id, is_active = True)
    
    return render(request, 'informationClient/alert.html', {'alertC':alert})

