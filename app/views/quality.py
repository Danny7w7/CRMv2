# Standard Python libraries
import datetime

# Django utilities
from django.http import HttpResponse
from django.template.loader import render_to_string

# Django core libraries
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import redirect, render

# Third-party libraries
from weasyprint import HTML

# Application-specific imports
from app.models import *
from ..forms import *

@login_required(login_url='/login')   
def formCreateControl(request):

    userRole = [ 'A' , 'C', 'SUPP']
    users = Users.objects.filter(role__in = userRole)

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
                call.save()
                
                # Responder con éxito y la URL de redirección
                return redirect('formCreateControl')

    context = {'users':users}

    return render(request, 'forms/formCreateControl.html', context)

@login_required(login_url='/login')   
def tableControl(request):

    quality = ControlQuality.objects.select_related('agent','agent_create').filter(is_active = True)
    call = ControlCall.objects.select_related('agent','agent_create').filter(is_active = True)

    context = {
        'quality' : quality,
        'call' : call
    }

    return render(request, 'table/control.html', context)

@login_required(login_url='/login')   
def createQuality(request):

    userRole = [ 'A' , 'C']
    agents = Users.objects.filter(is_active = True, role__in=userRole )

    if request.method == 'POST':

        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        agent = request.POST.get('agent')

        consultQuality = ControlQuality.objects.filter(date__range=(start_date, end_date), agent = agent)
        agentReport = ControlQuality.objects.select_related('agent').filter(agent = agent).first
        date = datetime.now()

        callAll = ControlCall.objects.filter(date__range=(start_date, end_date), agent = agent)
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

    return render (request,'pdf/createQuality.html', context)

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
    html_content = render_to_string('pdf/template.html', context)

    # Genera el PDF
    pdf_file = HTML(string=html_content).write_pdf()

    # Devuelve el PDF como respuesta HTTP
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="output.pdf"'
    return response
