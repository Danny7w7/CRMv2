from django.urls import resolve
from django.shortcuts import render

class NoCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Aplicar a todas las páginas, excluyendo archivos estáticos y admin
        if not request.path.startswith('/static/') and not request.path.startswith('/media/') and not request.path.startswith('/admin/'):
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        return response
    
#modulo para manejar el CRM por modulos, osea validar si esta asignado a algun modulo y sino no mostar parte visual

MODULE_PATHS = {
    'OBAMACARE': [ 'formCreateClient', 'formEditClient', 'formCreatePlan','clientAccionRequired','clientObamacare','editObama','viewConsent','viewIncomeLetter','alert','ticketAsing','editTicket','editAlert','select_client','formAddObama','formAddDepend','formCreateAlert','validatePhone','fetchAca','fetchDependent','formCreatePlan','formCreatePlan','updateTypeSales','formAddObama','formAddSupp','formAddDepend','addDepend','validateKey','blockSocialSecurity','agentTicketAssignment','fetchActionRequired','saveCustomerObservationACA','saveDocumentClient','saveAppointment','saveAccionRequired','fetchPaymentsMonth','fetchActionRequired','fetchPaymentOneil','fetchPaymentCarrier','fetchPaymentSherpa','validarCita','paymentDateObama','preComplaint','ILFFM'],
    'SUPP': [ 'formCreateClient', 'formEditClient','formCreatePlan','clientSupp','editSupp','alert','ticketAsing','editTicket','editAlert','select_client','formAddSupp','formAddDepend','formCreateAlert','validatePhone','fetchSupp','fetchDependent','formCreatePlan','formCreatePlan','updateTypeSales','formAddObama','formAddSupp','formAddDepend','addDepend','validateKey','agentTicketAssignment','toggleSuppStatus','saveCustomerObservationSupp','fetchPaymentSuplementals','paymentDateSupp','saveDocumentClientSupp'],
    'ASSURE': [ 'formCreateAssure','formCreatePlanAssure','clientAssure','editAssure','alert','ticketAsing','editTicket','editAlert','selectClientAssure','formCreatePlanAssure','formCreateAlert','validatePhone','blockSocialSecurityAssure','agentTicketAssignment'],
    'LIFE INSURANCE': [ 'formCreateClientLife','clientLifeInsurance','editLife','alert','ticketAsing','editTicket','editAlert','formCreateAlert','ConsentLifeInsurance','validatePhone','blockSocialSecurityLife','agentTicketAssignment'],
    'MEDICARE': [ 'formCreateClientMedicare','editClientMedicare','alert','ticketAsing','editTicket','editAlert','formCreateAlert','clientMedicare','consetMedicare','validatePhone','blockSocialSecurityMedicare','agentTicketAssignment'],
    'FINALL EXPENSES': [ 'formCreateFinalExpenses','clientFinallExpenses','alert','ticketAsing','editTicket','editAlert','formCreateAlert','agentTicketAssignment','editFinallExpenses','clientFinallExpenses','toggleFinallExpenses'],
    'SMS': [ 'smsBlue','chatSms','sendCreateSecretKey','sendSecretKey','deleteContact','sendMessage','startChat','stripe-webhook','payment','readAllMessages','smstemplate','sendTemplate','sendTemplateStatic','adminSms'],
    'WHATSAPP': [ 'whatsappBlue','chatWatsapp','whatsappReply','sendWhatsapp','sendWhatsappConversation','deleteContactWhatsApp','template'],
    'SALE REPORTS': [ 'sale', 'sale6Week','detalleAgente','weekSalesWiew','downloadPdf','reports','downloadAccionRequired','paymentClients'],
    'CUSTOMER REPORTS': [ 'customerPerformance', 'typification','customerTypification','toggleTypification','get_observation_detail','customerStep'],
    'GRAPHICAL REPORTS': [ 'averageCustomer', 'salesPerformance','chart6Week'],
    'QUALITY': [ 'formCreateControl', 'control','createQuality','formCreateQuestionControl','toggleQuestionControl'],
    'BD': [ 'uploadExcel', 'manageAgentAssignments','reportBd','bd','processAndSave','saveData','saveCommentAjax'],
    'COMPARATIVE': [ 'uploadReports','processExcel','headerProcessor', 'paymentsReports', 'paymentsReportsSupp'],
    'TEAM MANAGEMENT': [ 'customerAssginments'],
    'QUOTATION': [ 'marketplace','obtenerCountyfips','obtenerLatLon'],
    'BOOK': ['uploadBook','bookList','bookPages','saveTime','toggleBook','bookReport']
}

EXCLUDED_VIEWS = ['index','toggleDarkMode' ,'motivationalPhrase','login','logout','viewConsent','consetMedicare','formCreateUser', 'addNumbersUsers','incomeLetter','ConsentLifeInsurance','complaint', 'sms','whatsappReply','url_temporal', 'obtainLeadsByGoHighLevel','consentL','sendConsentForm','enviar_email','uploadTempUrl']  # Puedes agregar más si lo necesitas

class ModuleAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        resolver_match = resolve(request.path_info)
        url_name = resolver_match.url_name

        # ✅ Superusuarios pueden ver todo
        if request.user.is_authenticated and request.user.is_superuser:
            return self.get_response(request)

        # ✅ Vistas públicas permitidas
        if url_name in EXCLUDED_VIEWS or url_name is None:
            return self.get_response(request)

        # 🔒 Verificar si la vista pertenece a un módulo
        for module_name, url_names in MODULE_PATHS.items():
            if url_name in url_names:
                if (
                    not request.user.is_authenticated or 
                    not hasattr(request.user, 'company') or
                    not request.user.company.modules.filter(name=module_name).exists()
                ):
                    return render(request, 'auth/404.html', status=403)
                return self.get_response(request)

        # ❌ Vista no está registrada en ningún módulo
        return render(request, 'auth/404.html', status=403)

