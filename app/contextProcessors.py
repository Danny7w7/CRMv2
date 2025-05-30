from .models import UserPreference, Companies, Services, Subscriptions

def themeMode(request):
    try:
        userPreference = UserPreference.objects.get(user_id=request.user.id)
    except:
        userPreference = None
    return {
        'userPreference': userPreference,
    }

def company(request):
    try:
        company = Companies.objects.get(id=request.user.company.id)
    except:
        company = None
    return {'nameCompany': company}

def validateSms(request):
    if request.user.is_authenticated:
        companyId = request.user.company.id
        subscripcions = Subscriptions.objects.select_related('service').filter(company_id=companyId, is_active=True)
        subscripcionss = Subscriptions.objects.select_related('service').filter(company_id=companyId, is_active=True).count()
        
        for subscripcion in subscripcions:
            if subscripcionss > 1:
                if subscripcion.service.name in ['SMS', 'WHATSAPP']:
                    return {'smsIsActive':True, 'whatsAppIsActive': True}
            if subscripcion.service.name == 'SMS':
                return {'smsIsActive':True, 'whatsAppIsActive': False}
            if subscripcion.service.name == 'WHATSAPP':
                return {'smsIsActive':False, 'whatsAppIsActive': True}
            
    return {'smsIsActive':False, 'whatsAppIsActive': False}
