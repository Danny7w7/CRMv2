# Standard Python libraries

# Django utilities

# Django core libraries
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

# Application-specific imports
from app.models import *

@login_required(login_url='/login') 
def customerAssignments(request):
    if request.method == 'POST':
        userId = request.POST.get('user')
        agentUSAId = request.POST.getlist('usAgent')

        user = Users.objects.get(id=userId)
        agentsUSA = USAgent.objects.filter(id__in=agentUSAId)

        user.usaAgents.set(agentsUSA)
        
        messages.success(request, f"Successfully associated agent.")
        

    if request.user.is_superuser:
        users = Users.objects.filter(role='C').exclude(username__in=('MariaCaTi', 'CarmenR'))
        usAgents = usAgents = USAgent.objects.prefetch_related('company').all()
    else:
        users = Users.objects.select_related('company').filter(company_id=request.user.company.id, role='C').exclude(username__in=('MariaCaTi', 'CarmenR'))
        usAgents = USAgent.objects.filter(company__id=request.user.company.id)

    context = {
        'users':users,
        'usAgents':usAgents,
    }

    return render(request, 'supervisorPanel/customerAssignments.html', context)

@login_required(login_url='/login') 
def requestsChangeDate(request):
    changeDateLogs = ChangeDateLogs.objects.select_related(
        'obamacare__client',  # Relación anidada para ObamaCare -> Client
        'supp__client',       # Relación anidada para Supp -> Client
        'created_by',
        'authorized_by'
    ).all()
    return render(request, 'supervisorPanel/requestsChangeDate.html', {'changeDateLogs': changeDateLogs})

@login_required(login_url='/login') 
def requestsChangeAgent(request):
    changeAgentLogs = ChangeAgentLogs.objects.select_related(
        'obamacare__client',  # Relación anidada para ObamaCare -> Client
        'supp__client',       # Relación anidada para Supp -> Client
        'created_by',
        'authorized_by'
    ).all()
    return render(request, 'supervisorPanel/requestsChangeAgent.html', {'changeAgentLogs': changeAgentLogs})

@csrf_exempt
def getReasonChange(request, logId):
    try:
        log_type = request.GET.get('type')

        reason = None

        if log_type == 'Date':
            change_log = ChangeDateLogs.objects.filter(id=logId).first()
            if change_log:
                reason = change_log.reason
        elif log_type == 'Agent':
            change_log = ChangeAgentLogs.objects.filter(id=logId).first()
            if change_log:
                reason = change_log.reason

        if reason:
            return JsonResponse({"reason": reason}, status=200)
        else:
            return JsonResponse({"error": "Log not found or no reason available."}, status=404)

    except Exception as e:
        return JsonResponse({"error": f"Unexpected error: {str(e)}"}, status=500)