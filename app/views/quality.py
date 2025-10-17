# Standard Python libraries
import datetime

# Django utilities
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string

# Django core libraries
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.shortcuts import redirect, render

# Third-party libraries
from weasyprint import HTML

# Application-specific imports
from app.models import *
from ..forms import *

from .decoratorsCompany import * 

@login_required(login_url='/login') 
@company_ownership_required_sinURL  
def formCreateControl(request):

    company_id = request.company_id  # Obtener company_id desde request
    # Definir el filtro de compañía (será un diccionario vacío si es superusuario)
    company_filter = {'company': company_id} if not request.user.is_staff else {}

    userRole = [ 'A' , 'C', 'SUPP', 'S']
    users = Users.objects.filter(role__in = userRole, **company_filter ).order_by('first_name')

    if request.method == 'POST':

        observation = request.POST.get('observation')
        category = request.POST.get('category')
        amount = request.POST.get('amount', 0)
        if amount == '': amount = None

        if request.POST.get('Action') == 'Quality':
            form = ControlQualityForm(request.POST)
            if form.is_valid():
                quality = form.save(commit=False)
                quality.agent_create = request.user 
                quality.is_active = True
                quality.observation = observation
                quality.category = category
                quality.amount = amount
                quality.save()
                
                # Responder con éxito y la URL de redirección
                return redirect('formCreateControl')
            
        elif request.POST.get('Action') == 'Call':
            
            form = ControlCallForm(request.POST)
            if form.is_valid():

                call = form.save(commit=False)
                call.agent_create = request.user
                call.is_active = True
                call.company = request.user.company
                call.save()
                
                # Responder con éxito y la URL de redirección
                return redirect('formCreateControl')

    context = {'users':users}

    return render(request, 'quality/formCreateControl.html', context)

@login_required(login_url='/login')   
@company_ownership_required_sinURL  
def tableControl(request):

    company_id = request.company_id  # Obtener company_id desde request
    # Definir el filtro de compañía (será un diccionario vacío si es superusuario)
    company_filter = {'agent__company': company_id} if not request.user.is_staff else {}

    quality = ControlQuality.objects.select_related('agent','agent_create').filter(is_active = True, **company_filter)
    call = ControlCall.objects.select_related('agent','agent_create').filter(is_active = True, **company_filter)

    context = {
        'quality' : quality,
        'call' : call
    }

    return render(request, 'quality/control.html', context)

@login_required(login_url='/login')  
@company_ownership_required_sinURL  
def createQuality(request):

    company_id = request.company_id  # Obtener company_id desde request
    # Definir el filtro de compañía (será un diccionario vacío si es superusuario)
    company_filter = {'company': company_id} if not request.user.is_staff else {}    
    company_filter_agent = {'agent__company': company_id} if not request.user.is_staff else {} 

    userRole = [ 'A' , 'C', 'SUPP', 'S']
    agents = Users.objects.filter(role__in=userRole, **company_filter ).order_by('first_name')

    if request.method == 'POST':

        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        agent = request.POST.get('agent')

        consultQuality = ControlQuality.objects.filter(date__range=(start_date, end_date), agent = agent, **company_filter_agent)
        agentReport = ControlQuality.objects.select_related('agent').filter(agent = agent, **company_filter_agent).first()
        date = datetime.datetime.now()

        callAll = ControlCall.objects.filter(date__range=(start_date, end_date), agent = agent, **company_filter_agent)
        # Sumar los valores de daily, answered y mins
        totals = callAll.aggregate(
            total_daily=Sum('daily'),
            total_answered=Sum('answered'),
            total_mins=Sum('mins')
        )

        # Acceder a los valores sumados
        total_daily = totals['total_daily']
        total_answered = totals['total_answered']
        total_mins = totals['total_mins']
        
        return generatePdfQuality(
            request, consultQuality, agentReport, start_date, end_date, date, total_daily, total_answered, total_mins
        )

    context = {
        'agents' : agents
    }

    return render (request,'quality/createQuality.html', context)

def generatePdfQuality(request, consultQuality,agentReport,start_date,end_date,date,total_daily, total_answered, total_mins):

    context = {
        'consultQuality' : consultQuality,
        'agentReport' : agentReport,
        'start_date' : start_date,
        'end_date' : end_date,
        'date' : date,
        'total_daily' : total_daily,
        'total_answered' : total_answered,
        'total_mins' : total_mins
    }

    # Renderiza la plantilla HTML a un string
    html_content = render_to_string('pdf/reportQuality.html', context)

    # Genera el PDF
    pdf_file = HTML(string=html_content).write_pdf()

    # Devuelve el PDF como respuesta HTTP
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="output.pdf"'
    return response

@login_required(login_url='/login')  
@company_ownership_required_sinURL  
def formCreateQuestionControl(request):

    company_id = request.company_id
    company = Companies.objects.filter(id=company_id).first()

    if request.user.is_superuser:
        questions = ControlQuestions.objects.select_related('company').all()
    else:
        questions = ControlQuestions.objects.filter(company = company_id, is_active = True)

    if request.method == 'POST':

        question = request.POST.get('question')

        if question is not None:

            ControlQuestions.objects.create(
                user = request.user,
                questions = question,
                company = company
            )

            return redirect('formCreateQuestionControl')

    return render(request, 'quality/formCreateQuestionControl.html',{'questions': questions})

@login_required(login_url='/login')  
@company_ownership_required_sinURL  
def formAsignationQuestionControl(request):

    company_id = request.company_id
    company = Companies.objects.filter(id=company_id).first()

    if request.user.is_superuser:
        questions = ControlQuestions.objects.select_related('company').all()
        user = Users.objects.all()
        client = Clients.objects.all()
    else:
        questions = ControlQuestions.objects.filter(company = company_id, is_active = True)
        user = Users.objects.filter(company = company_id, is_active = True)
        client = Clients.objects.filter(company = company_id, is_active = True)

    context = {
        'questions': questions,
        'users': user,
        'client':client
    }

    if request.method == 'POST':

        agentID = request.POST.get('agent')
        agent = Users.objects.filter(id = agentID).first()
        clientID = request.POST.get('client')
        clients = Clients.objects.filter(id = clientID).first()
        obs = request.POST.get('obs')

        for question in questions:
            key = f"question_{question.id}"
            answer = request.POST.get(key)

            QuestionTracking.objects.create(
                control_agent = request.user,
                sales_agent = agent,
                client=clients,
                company = company,
                control_question = question,
                answer = answer,
                obs = obs
            )
    
    return render (request, 'quality/formAsignationQuestionControl.html', context)

@login_required(login_url='/login')  
@company_ownership_required_sinURL
def formOE(request):

    company_id = request.company_id

    if request.user.is_superuser:
        user = Users.objects.all()
        clients = Clients.objects.all()
    else:
        user = Users.objects.filter(company = company_id, is_active = True)
        clients = Clients.objects.filter(company = company_id, is_active = True)

    eo = DropDownList.objects.exclude(errores_omision__isnull=True).values_list('errores_omision','id')

    if request.method == 'POST':

        agentID = request.POST.get('agent')
        clientIDs = request.POST.get('client')

        usersID = Users.objects.filter(id=agentID).first()
        clientID = Clients.objects.filter(id=clientIDs).first()
        companyID = Companies.objects.filter(id=company_id).first()

        for key, value in request.POST.items():
            if key.startswith("question_"):  # ejemplo: question_5
                eo_id = key.split("_")[1]   # "5"
                eo_obj = DropDownList.objects.get(id=eo_id)

                # Crear registro en ErroresOmision
                ErroresOmision.objects.create(
                    agentCreated=request.user,
                    agent=usersID,
                    client=clientID,
                    eoID=eo_obj,
                    eo=value,
                    company=companyID
                )        

    context = {
        'users': user,
        'client': clients,
        'eo': eo
    }

    return render (request, 'quality/formOE.html', context)

@login_required(login_url='/login')  
@company_ownership_required_sinURL
def tableOE(request):

    company_id = request.company_id

    if request.user.is_superuser:        
        eo = ErroresOmision.objects.values(
            'agent_id','agent__first_name','agent__last_name' ,'eo', 'eoID__errores_omision', 'company__company_name' ).annotate(total=Count('id'))
    else:
        eo = ErroresOmision.objects.filter(company = company_id).values( 
            'agent_id','agent__first_name','agent__last_name' ,'eo', 'eoID__errores_omision', 'company__company_name' ).annotate(total=Count('id'))

    if request.method == 'POST':

        startDatePost = request.POST['start_date']
        endDatePost = request.POST['end_date']

        startDate = timezone.make_aware(
            datetime.datetime.strptime(startDatePost, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
        )
        endDate = timezone.make_aware(
            datetime.datetime.strptime(endDatePost, '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)
        )

        eo = eo.filter(created_at__range=(startDate, endDate))

    # Limpiar los caracteres '\r' de la descripción
    for item in eo:
        if item['eoID__errores_omision']:
            item['eoID__errores_omision'] = item['eoID__errores_omision'].strip()

    return render(request, 'quality/tableOE.html',{'eo':eo})

@login_required(login_url='/login')
@company_ownership_required_sinURL
def tableOEDetail(request, agent_id):
    company_id = request.company_id

    if request.user.is_superuser:
        qs = ErroresOmision.objects.filter(agent_id=agent_id)
    else:
        qs = ErroresOmision.objects.filter(agent_id=agent_id, company=company_id)

    data = []
    for eo in qs:
        data.append({
            "created_at": eo.created_at.strftime("%Y-%m-%d %H:%M"),
            "question": eo.eoID.errores_omision if eo.eoID else "",
            "answer": eo.eo,
            "client": f"{eo.client.first_name} {eo.client.last_name}",
        })

    return JsonResponse({"data": data})

