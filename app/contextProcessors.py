from .models import UserPreference, Companies, ClientAlert, Subscriptions
from datetime import date

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

def alert_count(request):

    # Verifica si el usuario está autenticado
    if not request.user.is_authenticated:
        return {'expiredAlerts': [], 'alertCount': 0}
    
    # Roles con acceso ampliado
    roleAuditar = ['S', 'Admin']

    # Construcción de la consulta basada en el rol del usuario
    if request.user.role in roleAuditar:

        #(ALERT) Obtener las alertas vencidas (fechas menores o iguales a la fecha actual)
        expiredAlerts = ClientAlert.objects.filter(datetime__lte=date.today(), is_active=True, company = request.user.company, completed = False)

        # Contar las alertas
        alertCount = expiredAlerts.count()

    elif request.user.role not in roleAuditar:

        #(ALERT) Obtener las alertas vencidas (fechas menores o iguales a la fecha actual)
        expiredAlerts = ClientAlert.objects.filter(datetime__lte=date.today(), is_active=True, agent = request.user.id, completed = False)

        # Contar las alertas
        alertCount = expiredAlerts.count()

    return {'expiredAlerts': expiredAlerts, 'alertCount': alertCount}

