# Django core libraries
from django.contrib.auth.decorators import login_required
from django.db.models import Subquery, OuterRef, Exists
from django.db.models.functions import Substr
from django.shortcuts import render

# Application-specific imports
from app.models import *
from ..decoratorsCompany import *

@login_required(login_url='/login')
@company_ownership_required_sinURL
def clientObamacare(request):

    company_id = request.company_id  # Obtener company_id desde request

    # Rango de fechas del mes actual
    now = timezone.now()
    start_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_month = (start_month + timezone.timedelta(days=32)).replace(day=1)

    obs = ObservationCustomer.objects.filter(
        obamacare=OuterRef('pk'),
        is_active=True,
        created_at__gte=start_month,
        created_at__lt=end_month
    )

    if request.user.is_superuser:

        obamaCare = ObamaCare.objects.select_related('agent','client').annotate(
            truncated_agent_usa=Substr('agent_usa', 1, 8),
            has_observation=Subquery(obs.values('typification')[:1])).exclude(
                id__in=CustomerRedFlag.objects.filter(date_completed__isnull=True).values_list(
                    'obamacare_id', flat=True)).order_by('-created_at')           

    elif request.user.role == 'Admin':         
        obamaCare = ObamaCare.objects.visible_for_user(request.user).select_related('agent','client').only(
            'agent_usa', 'agent__first_name', 'agent__last_name', 'client__first_name', 'client__last_name',
                'client__phone_number', 'status', 'status_color', 'profiling','created_at', 'is_active').annotate(
                    has_observation=Subquery(obs.values('typification')[:1])
                        ).exclude(id__in=CustomerRedFlag.objects.filter(date_completed__isnull=True).values_list(
                            'obamacare_id', flat=True)).order_by('-created_at')    
    else:
        obamaCare = ObamaCare.objects.select_related('agent', 'client').only(
            'agent_usa', 'agent__first_name', 'agent__last_name', 'client__first_name', 'client__last_name',
                'client__phone_number', 'status', 'status_color', 'profiling','created_at', 'is_active').annotate(
                    truncated_agent_usa=Substr('agent_usa', 1, 8),
                    has_observation=Subquery(obs.values('typification')[:1])).filter(is_active = True, company = company_id).exclude(
                        id__in=CustomerRedFlag.objects.filter(date_completed__isnull=True).values_list(
                            'obamacare_id', flat=True)).order_by('-created_at')  

    context = {
        'obamacares': obamaCare,
        'company_id' : company_id
    }    

    return render(request, 'informationClient/clientObamacare.html', context)

@login_required(login_url='/login')
@company_ownership_required_sinURL
def clientAccionRequired(request):

    company_id = request.company_id  # Obtener company_id desde request

    if request.user.is_superuser:
        obamaCare = ObamaCare.objects.select_related('agent', 'client').annotate(
            truncated_agent_usa=Substr('agent_usa', 1, 8),customer_red_flag_clave=Subquery(
                CustomerRedFlag.objects.filter(obamacare=OuterRef('id'), date_completed__isnull=True
                    ).values('clave')[:1] )).filter( id__in=CustomerRedFlag.objects.filter(
                        date_completed__isnull=True ).values_list('obamacare_id', flat=True) ).order_by('-created_at')
    
    elif request.user.role == 'Admin':       
        obamaCare = ObamaCare.objects.visible_for_user(request.user).select_related('agent', 'client').annotate(
            truncated_agent_usa=Substr('agent_usa', 1, 8),customer_red_flag_clave=Subquery(
                CustomerRedFlag.objects.filter(obamacare=OuterRef('id'), date_completed__isnull=True
                    ).values('clave')[:1] )).filter( id__in=CustomerRedFlag.objects.filter(
                        date_completed__isnull=True ).values_list('obamacare', flat=True)).order_by('-created_at')  
        
    elif request.user.role == 'S' :   

        obamaCare = ObamaCare.objects.select_related('agent', 'client').annotate(
            truncated_agent_usa=Substr('agent_usa', 1, 8),customer_red_flag_clave=Subquery(
                CustomerRedFlag.objects.filter(obamacare=OuterRef('id'), date_completed__isnull=True
                    ).values('clave')[:1] )).filter( id__in=CustomerRedFlag.objects.filter(
                        date_completed__isnull=True ).values_list('obamacare', flat=True), is_active = True, company = company_id ).order_by('-created_at')    

    else:        
        obamaCare = ObamaCare.objects.select_related('agent', 'client').annotate(
            truncated_agent_usa=Substr('agent_usa', 1, 8),customer_red_flag_clave=Subquery(
                CustomerRedFlag.objects.filter(obamacare=OuterRef('id'), date_completed__isnull=True
                    ).values('clave')[:1] )).filter( id__in=CustomerRedFlag.objects.filter(
                        date_completed__isnull=True ).values_list('obamacare', flat=True
                            ), is_active = True, agent_id = request.user.id, company = company_id ).order_by('-created_at')


    return render(request, 'informationClient/clientAccionRequired.html', {'obamacares':obamaCare})

@login_required(login_url='/login')
@company_ownership_required_sinURL
def clientSupp(request):

    roleAuditar = ['S', 'C','SUPP', 'AU']
    company_id = request.company_id  # Se asume que el decorador lo agrega a request

    if request.user.is_superuser:
        supp = Supp.objects.visible_for_user(request.user).select_related('agent','client').annotate(
            truncated_agent_usa=Substr('agent_usa', 1, 8)).order_by('-created_at')
        suppPay = False

    elif request.user.role in roleAuditar:
        supp = Supp.objects.visible_for_user(request.user).select_related('agent','client').filter(is_active = True, company = company_id).exclude(status_color = 1).annotate(
            truncated_agent_usa=Substr('agent_usa', 1, 8)).order_by('-created_at')
        suppPay = Supp.objects.select_related('agent','client').filter(is_active = True, status_color = 1 )

        for item in suppPay:
            client_name = item.agent_usa if item.agent_usa else "Sin Name"    
            item.short_name = client_name.split()[0] + " ..." if " " in client_name else client_name

    elif request.user.role == 'Admin':
        supp = Supp.objects.visible_for_user(request.user).select_related('agent','client').order_by('-created_at')
        suppPay = False

    elif request.user.role in ['A', 'C']:
        supp = Supp.objects.visible_for_user(request.user).select_related('agent','client').annotate(
            truncated_agent_usa=Substr('agent_usa', 1, 8)).filter(is_active = True, company = company_id).order_by('-created_at')
        suppPay = False

    return render(request, 'informationClient/clientSupp.html', {'supps':supp,'suppPay':suppPay})

@login_required(login_url='/login')
@company_ownership_required_sinURL
def clientMedicare(request):
    
    roleAuditor = ['S','AU']
    company_id = request.company_id

    if request.user.is_superuser:
        medicare = Medicare.objects.select_related('agent').annotate(
            truncated_agent_usa=Substr('agent_usa', 1, 8)).order_by('-created_at')    
    elif request.user.role == 'Admin':       
        medicare = Medicare.objects.visible_for_user(request.user).select_related('agent').order_by('-created_at')
    elif request.user.role in roleAuditor:
        medicare = Medicare.objects.select_related('agent').annotate(
            truncated_agent_usa=Substr('agent_usa', 1, 8)).filter(is_active = True,company = company_id).order_by('-created_at')   
    else:
        medicare = Medicare.objects.select_related('agent').annotate(
            truncated_agent_usa=Substr('agent_usa', 1, 8)).filter(is_active = True, agent_id = request.user.id,company = company_id).order_by('-created_at')   


    return render(request, 'informationClient/clientMedicare.html', {'medicares':medicare})

@login_required(login_url='/login')   
@company_ownership_required_sinURL 
def tableAlert(request):

    roleAuditar = ['S', 'C',  'AU']
    company_id = request.company_id

    if request.user.is_superuser:
        alert = ClientAlert.objects.select_related('agent').annotate(
            truncated_contect=Substr('content', 1, 20))    
    elif request.user.role in roleAuditar:
        alert = ClientAlert.objects.select_related('agent').annotate(
            truncated_contect=Substr('content', 1, 20)).filter(is_active = True, company = company_id)
    elif request.user.role == 'Admin':
        alert = ClientAlert.objects.select_related('agent').annotate(
            truncated_contect=Substr('content', 1, 20)).filter(company = company_id)
    elif request.user.role == 'A':
        alert = ClientAlert.objects.select_related('agent').annotate(
            truncated_contect=Substr('content', 1, 20)).filter(agent = request.user.id, is_active = True, company = company_id)
    
    return render(request, 'informationClient/alert.html', {'alertC':alert})

@login_required(login_url='/login')   
@company_ownership_required_sinURL 
def ticketAsing(request):
        
    roleAuditar = ['S', 'C',  'AU','SUPP']
    company_id = request.company_id
    
    if request.user.is_superuser:
        ticket = AgentTicketAssignment.objects.select_related('obamacare', 'supp','assure', 'agent_create', 'agent_customer').all()
    elif request.user.role in roleAuditar:
        ticket = AgentTicketAssignment.objects.select_related('obamacare', 'supp', 'assure','agent_create', 'agent_customer').filter(
            company = company_id, is_active = True)
    elif request.user.role == 'Admin':
        ticket = AgentTicketAssignment.objects.select_related('obamacare', 'supp', 'assure','agent_create', 'agent_customer').filter(company = company_id)
    elif request.user.role == 'A':
        ticket = AgentTicketAssignment.objects.select_related('obamacare', 'supp', 'assure','agent_create', 'agent_customer').filter(
            agent_create = request.user.id, company = company_id, is_active = True)
        
    color = []
        
    for item in ticket:    
        if item.status == 'IN PROGRESS':
            color.append('warning')
        if item.status == 'CANCELLED':
            color.append('danger')
        if item.status == 'COMPLETED':
            color.append('success')

    lista = zip(ticket, color)

    context = {
        'lista' : lista
    }

    return render(request, 'informationClient/ticketAsing.html',context)

@login_required(login_url='/login')   
@company_ownership_required_sinURL 
def clientAssure(request):
        
    roleAuditar = ['S', 'C',  'AU','SUPP']
    company_id = request.company_id
    
    if request.user.is_superuser:
        assure = ClientsAssure.objects.select_related('agent').all()
    elif request.user.role in roleAuditar:
        assure = ClientsAssure.objects.select_related('agent').filter(
            company = company_id, is_active = True)
    elif request.user.role == 'Admin':
        assure = ClientsAssure.objects.visible_for_user(request.user).select_related('agent').order_by('-created_at')
    elif request.user.role == 'A':
        assure = ClientsAssure.objects.select_related('agent').filter(
            agent = request.user.id, company = company_id, is_active = True)

    return render(request, 'informationClient/clientAssure.html', {'assure':assure})

@login_required(login_url='/login')   
@company_ownership_required_sinURL 
def clientLifeInsurance(request):

    roleAuditar = ['S', 'C',  'AU','SUPP']
    company_id = request.company_id
    
    if request.user.is_superuser:
        life = ClientsLifeInsurance.objects.select_related('agent').all()
    elif request.user.role in roleAuditar:
        life = ClientsLifeInsurance.objects.select_related('agent').filter(
            company = company_id, is_active = True)
    elif request.user.role == 'Admin':
        life = ClientsLifeInsurance.objects.visible_for_user(request.user).select_related('agent').order_by('-created_at')
    elif request.user.role == 'A':
        life = ClientsLifeInsurance.objects.select_related('agent').filter(
            agent = request.user.id, company = company_id, is_active = True)

    return render(request, 'informationClient/clientLifeInsurance.html', {'life':life})

@login_required(login_url='/login')   
@company_ownership_required_sinURL 
def clientFinallExpenses(request):
        
    roleAuditar = ['S', 'C',  'AU','SUPP']
    company_id = request.company_id
    
    if request.user.is_superuser:
        finalE = FinallExpenses.objects.select_related('agent','company').all()
    elif request.user.role in roleAuditar:
        finalE = FinallExpenses.objects.select_related('agent').filter(
            company = company_id, is_active = True)
    elif request.user.role == 'Admin':
        finalE = FinallExpenses.objects.visible_for_user(request.user).select_related('agent').order_by('-created_at')
    elif request.user.role == 'A':
        finalE = FinallExpenses.objects.select_related('agent').filter(
            agent = request.user.id, company = company_id, is_active = True)

    return render(request, 'informationClient/clientFinallExpenses.html', {'finalE':finalE})



