# Standard Python libraries
from datetime import datetime

# Django utilities
from django.template.loader import render_to_string

# Django core libraries
from django.contrib import messages
from django.shortcuts import redirect, render

# Application-specific imports
from app.models import *

def customerAssginments(request):
    if request.method == 'POST':
        userId = request.POST.get('user')
        agentUSAId = request.POST.getlist('usAgent')

        user = Users.objects.get(id=userId)
        agentsUSA = USAgent.objects.filter(id__in=agentUSAId)

        user.usaAgents.set(agentsUSA)
        
        messages.success(request, f"Successfully associated agent.")
        

    if request.user.is_superuser:
        users = Users.objects.filter(role='C').exclude(username__in=('MariaCaTi', 'CarmenR'))
        usAgents = USAgent.objects.select_related('company').all()
    else:
        users = Users.objects.select_related('company').filter(company_id=request.user.company.id, role='C').exclude(username__in=('MariaCaTi', 'CarmenR'))
        usAgents = USAgent.objects.filter(company__id=request.user.company.id)

    context = {
        'users':users,
        'usAgents':usAgents,
    }

    return render(request, 'supervisorPanel/customerAssignments.html', context)