"""
URL configuration for project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from .views import auth, index, tv
from .views.informationClients import table, toggles, modals, edits
from .views.informationClients import fetchs as fetchInformations
from .views.enterData import existClient, forms
from .views.enterData import fetchs as fetchsEnterData
from .views.reports import fecths as fetchsReports
from .views.reports import table as tableReports
from .views.reports import charts, download
from .views.users import users, companies
from .views import dbExcel, quality, consents, sms, utils, supervisorPanel, whatsApp, comparativeReports, leadConector, book
from .views.dialer import agentDialer, adminDialer, dialerLogic


urlpatterns = [
    #<---------------------------Auth--------------------------->
    path('login/', auth.login_, name='login'),
    path('logout/', auth.logout_, name='logout'),
    path('motivationalPhrase/', auth.motivationalPhrase, name='motivationalPhrase'), # Vista que renderiza la frase motivacional

    path('marketplace/', auth.buscarPlanes, name='marketplace'),


    #<---------------------------DashBoard--------------------------->
    path('', index.index, name='index'), #Home
    path('tableStatusSale/', index.tableStatusSale, name='tableStatusSale'),
    path('weeklyLiveView/',tv.weeklyLiveView,name='weeklyLiveView'), # Vista Semanal TV con Sidebard
    path('monthLiveView/',tv.monthLiveView,name='monthLiveView'), # Vista Mensual TV con Sidebard

    path('weeklyLiveViewTV/',tv.weeklyLiveView,name='weeklyLiveViewTV'), # Vista Semanal TV sin Sidebard
    path('monthLiveViewTV/',tv.monthLiveView,name='monthLiveViewTV'), # Vista Mensual TV sin Sidebard


    #<---------------------------Enter Data--------------------------->
    path('formCreateClient/', forms.formCreateClient, name='formCreateClient'), # Formulario para crear Clientes Obamacare
    path('formEditClient/<client_id>/', edits.formEditClient, name='formEditClient'),
    path('validatePhone/', fetchInformations.validatePhone, name='validatePhone'),
    path('validateKey/', fetchInformations.validateKey, name='validateKey'),


    path('formCreateClientLife/', forms.formCreateClientLife, name='formCreateClientLife'), # Formulario para crear Clientes Life Life Insurance .. 

    path('formCreateAssure/', forms.formCreateAssure, name='formCreateAssure'),
    path('formCreatePlanAssure/<client_id>/', forms.formCreatePlanAssure, name='formCreatePlanAssure'),
    path('selectClientAssure/', existClient.selectClientAssure, name='selectClientAssure'), # Vista para seleccionar clientes existentes


    path('formCreatePlan/<client_id>/', forms.formCreatePlan, name='formCreatePlan'),
    path('fetchAca/<client_id>/', fetchsEnterData.fetchAca, name='fetchAca'),
    path('fetchSupp/<client_id>/', fetchsEnterData.fetchSupp, name='fetchSupp'),
    path('fetchDependent/<client_id>/', fetchsEnterData.fetchDependent, name='fetchDependent'),
    path('formCreatePlan/deleteDependent/<int:dependent_id>/', fetchInformations.delete_dependent, name='delete_dependent'),
    path('formCreatePlan/deleteSupp/<int:supp_id>/', fetchInformations.delete_supp, name='delete_supp'),

    path('formCreateClientMedicare/', forms.formCreateClientMedicare, name='formCreateClientMedicare'), # Formulario para crear clientes Medicare

    path('select_client/', existClient.select_client, name='select_client'), # Vista para seleccionar clientes existentes
    path('updateTypeSales/<int:client_id>/', existClient.updateTypeSales, name='updateTypeSales'), # Funcion intermedia que cambia el TypeSale del cliente
    path('formAddObama/<client_id>/', forms.formAddObama, name='formAddObama'),
    path('formAddSupp/<client_id>/', forms.formAddSupp, name='formAddSupp'),
    path('formAddDepend/<client_id>/', forms.formAddDepend, name='formAddDepend'),
    path('addDepend/', forms.addDepend, name='addDepend'),

    path('formCreateAlert/', forms.formCreateAlert, name='formCreateAlert'), # Formulario para crear las Alertas
    
    path('formCreateFinalExpenses/', forms.formCreateFinalExpenses, name='formCreateFinalExpenses'),

    #<---------------------------Information Client--------------------------->
    path('clientObamacare/', table.clientObamacare, name='clientObamacare'),
    path('clientObamacarePass/', table.clientObamacarePass, name='clientObamacarePass'),
    path('saveRenovation/', edits.saveRenovation, name='saveRenovation'),

    path('toggleObamaStatus/<obamacare_id>/', toggles.toggleObamaStatus, name='toggleObamaStatus'),
    path('editObama/<int:obamacare_id>/<int:way>/', edits.editObama, name='editObama'),
    path('blockSocialSecurity/', fetchInformations.blockSocialSecurity, name='blockSocialSecurity'),
    path('saveCustomerObservationACA/', modals.saveCustomerObservationACA, name='saveCustomerObservationACA'),
    path('saveDocumentClient/<int:obamacare_id>/<int:way>/', modals.saveDocumentClient, name='saveDocumentClient'),
    path('saveAppointment/<int:obamacare_id>/', modals.saveAppointment, name='saveAppointment'),
    path('saveAccionRequired/', modals.saveAccionRequired, name='saveAccionRequired'),
    path('fetchPaymentsMonth/', fetchInformations.fetchPaymentsMonth, name='fetchPaymentsMonth'),
    path('fetchActionRequired/', fetchInformations.fetchActionRequired, name='fetchActionRequired'),
    path('fetchPaymentOneil/<obamacareId>/', fetchInformations.fetchPaymentOneil, name='fetchPaymentOneil'),
    path('fetchPaymentCarrier/<obamacareId>/', fetchInformations.fetchPaymentCarrier, name='fetchPaymentCarrier'),
    path('fetchPaymentSherpa/<obamacareId>/', fetchInformations.fetchPaymentSherpa, name='fetchPaymentSherpa'),
    path('validarCita/', modals.validarCita, name='validarCita'),
    path('paymentDateObama/<obama_id>/', modals.paymentDateObama, name='paymentDateObama'),
    path('preComplaint/', modals.preComplaint, name='preComplaint'),
    path('changePlanDate/<int:plan_id>/', modals.changePlanDate, name='changePlanDate'),
    path('changePlanAgent/<int:plan_id>/', modals.changePlanAgent, name='changePlanAgent'),
    path('fetchChangePlanDate/<int:change_id>/', modals.fetchChangePlanDate, name='fetchChangePlanDate'),
    path('fetchChangePlanAgent/<int:change_id>/', modals.fetchChangePlanAgent, name='fetchChangePlanAgent'),

    path('clientAccionRequired/', table.clientAccionRequired, name='clientAccionRequired'),

    path('clientLifeInsurance/', table.clientLifeInsurance, name='clientLifeInsurance'), # Vista de clientes Life Insurance
    path('editLife/<client_id>/', edits.editLife, name='editLife'),
    path('toggleLifeStatus/<client_id>/', toggles.toggleLifeStatus, name='toggleLifeStatus'),
    path('blockSocialSecurityLife/', fetchInformations.blockSocialSecurityLife, name='blockSocialSecurityLife'),
    path('paymentDateLife/<client_id>/', modals.paymentDateLife, name='paymentDateLife'),
    path('saveCustomerObservationLife/', modals.saveCustomerObservationLife, name='saveCustomerObservationLife'),

    path('clientAssure/', table.clientAssure, name='clientAssure'),
    path('editAssure/<assure_id>/', edits.editAssure, name='editAssure'),
    path('toggleAssureStatus/<assure_id>/', toggles.toggleAssureStatus, name='toggleAssureStatus'),
    path('blockSocialSecurityAssure/', fetchInformations.blockSocialSecurityAssure, name='blockSocialSecurityAssure'),
    path('paymentDateAssure/<assure_id>/', modals.paymentDateAssure, name='paymentDateAssure'),
    path('saveCustomerObservationAssure/', modals.saveCustomerObservationAssure, name='saveCustomerObservationAssure'),

    path('clientSupp/', table.clientSupp, name='clientSupp'),
    path('toggleSuppStatus/<supp_id>/', toggles.toggleSuppStatus, name='toggleSuppStatus'),
    path('editSupp/<supp_id>/', edits.editSupp, name='editSupp'),
    path('saveCustomerObservationSupp/', modals.saveCustomerObservationSupp, name='saveCustomerObservationSupp'),
    path('fetchPaymentSuplementalsstatus/<suppId>/', fetchInformations.fetchPaymentSuplementals, name='fetchPaymentSuplementals'),
    path('paymentDateSupp/<supp_id>/', modals.paymentDateSupp, name='paymentDateSupp'),
    path('saveDocumentClientSupp/<int:supp_id>/', modals.saveDocumentClientSupp, name='saveDocumentClientSupp'),

    path('clientMedicare/', table.clientMedicare, name='clientMedicare'),
    path('editClientMedicare/<medicare_id>/', edits.editClientMedicare, name='editClientMedicare'),
    path('blockSocialSecurityMedicare/', fetchInformations.blockSocialSecurityMedicare, name='blockSocialSecurityMedicare'),
    path('save-customer-observation-medicare/', modals.saveCustomerObservationMedicare, name='saveCustomerObservationMedicare'),
    path('desactiveMedicare/<medicare_id>/', modals.desactiveMedicare, name='desactiveMedicare'),

    path('clientFinallExpenses/', table.clientFinallExpenses, name='clientFinallExpenses'),
    path('editFinallExpenses/<finallExpenses_id>/', edits.editFinallExpenses, name='editFinallExpenses'),
    path('toggleFinallExpenses/<finallExpenses_id>/', toggles.toggleFinallExpenses, name='toggleFinallExpenses'),

    path('alert/', table.tableAlert, name='alert'),
    path('toggleAlert/<alertClient_id>/', toggles.toggleAlert, name='toggleAlert'),
    path('editAlert/<int:alertClient_id>/', edits.editAlert, name='editAlert'),

    #<---------------------------ticket--------------------------->
    path('ticketAsing/', table.ticketAsing, name='ticketAsing'),
    path('agentTicketAssignment/', modals.agentTicketAssignment, name='agentTicketAssignment'),
    path('editTicket/<ticket_id>/', edits.editTicket, name='editTicket'),
    path('toggleTicketStatus/<ticket_id>/', toggles.toggleTicketStatus, name='toggleTicketStatus'),

    path('leadsByGoHighLevel/', leadConector.obtainLeadsByGoHighLevel, name='obtainLeadsByGoHighLevel'),

    #<---------------------------SMS--------------------------->
    path('smsBlue/', sms.index, name='smsBlue'),
    path('chatSms/<chatId>/', sms.chat, name='chatSms'),
    path('startChat/<phoneNumber>/', sms.startChat, name='startChat'),
    path('sendMessage/', sms.sendMessage, name='sendMessage'),
    path('deleteChat/<id>/', sms.deleteContact, name='deleteContact'),

    path('sms/<int:company_id>/', sms.sms, name='sms'),

    path('createSecretKey/<id>/', sms.sendCreateSecretKey, name='sendCreateSecretKey'),
    path('sendSecretKey/<contact_id>/', sms.sendSecretKey, name='sendSecretKey'),
    path('secret-key/', sms.createSecretKey, name='url_temporal'),

    path('readAllMessages/<chat_id>/<company_id>/', sms.readAllMessages, name='readAllMessages'),

    path('webhook/', sms.stripe_webhook, name='stripe-webhook'),
    path('payment/<str:type>/<int:company_id>/', sms.payment_type, name='payment'),

    path('adminSms/', sms.adminSms, name='adminSms'),

    path('smstemplate/', sms.smstemplate, name='smstemplate'),


    #<---------------------------Dialer--------------------------->
    path('dialer/agentDashboard/', agentDialer.agentDashboard, name='agentDashboard'),
    path('dialer/selectCampaign/', agentDialer.selectCampaign, name='selectCampaign'),

    # path('dialer/adminDashboard/', adminDialer.adminDashboard, name='adminDashboard'),
    path('dialer/adminDashboard/campaigns/', adminDialer.campaigns, name='campaigns'),
    # path('dialer/adminDashboard/campaigns/details/<int:campaign_id>/', adminDialer.campaignDetail, name='campaignDetail'),

    #Json endpoints for dialer logic
    path('api/dialer/adminDashboard/campaigns/create/', adminDialer.createCampaigns, name='createCampaigns'),
    path('api/dialer/adminDashboard/campaigns/configure/', adminDialer.configCampaigns, name='configCampaigns'),
    path('api/dialer/adminDashboard/campaigns/getList/', adminDialer.getListCampaigns, name='getListCampaigns'),
    path('api/dialer/adminDashboard/campaigns/processExcelForDialer/', adminDialer.processExcelForDialer, name='processExcelForDialer'),    
    path('api/dialer/agentDashboard/campaign/login/', agentDialer.loginCampaign, name='loginCampaign'),
    path('api/dialer/agentDashboard/changeStatus/<int:agent_id>/', agentDialer.changeStatus, name='changeStatus'),
    path('api/dialer/agentDashboard/getStats/', agentDialer.getStats, name='getStats'),
    path('api/dialer/agentDashboard/tipification/', agentDialer.typifyCall, name='typifyCall'),
    path('api/dialer/iniciateCalls/<int:campaign_id>/', dialerLogic.iniciateCalls, name='iniciateCalls'),
    path('api/dialer/tranferCallToAgent/', dialerLogic.endpointTranferCallToAgent, name='tranferCallToAgent'),
    path('api/dialer/webhooks/', dialerLogic.webhooksTelnyx, name='webhooks'),


    #<---------------------------Sales Reports--------------------------->
    path('sale/', tableReports.sale, name='sale'),

    path('sale6Week/', tableReports.sales6WeekReport, name='sale6Week'),  
    path('sale/detalleAgente/', fetchsReports.detalleAgente, name='detalleAgente'),  

    path('weekSalesWiew/',tableReports.weekSalesWiew, name='weekSalesWiew'),
    path('descargarPdf/<int:week_number>/', download.downloadPdf, name='downloadPdf'),

    path('reports/', tableReports.reports, name='reports'),
    path('downloadAccionRequired/', download.downloadAccionRequired, name='downloadAccionRequired'),
    path('paymentClients/', download.paymentClients, name='paymentClients'),


    #<---------------------------Customer Reports--------------------------->
    path('customerPerformance/', tableReports.customerPerformance, name='customerPerformance'),

    path('typification/', tableReports.typification, name='typification'),
    path('toggleTypification/<typifications_id>/', toggles.toggleTypification, name='toggleTypification'),
    path('get-observation-detail/<observation_id>/', fetchsReports.get_observation_detail, name='get_observation_detail'),

    path('customerTypification/', tableReports.customerTypification, name='customerTypification'),

    path('customerStep/', tableReports.customerStep, name='customerStep'),
    
    #<---------------------------Payments Reports--------------------------->
    path('paymentsReports/', tableReports.paymentsReports, name='paymentsReports'),
    path('paymentsReportsSupp/', tableReports.paymentsReportsSupp, name='paymentsReportsSupp'),


    #<---------------------------Graphical Reports--------------------------->
    path('salesPerformance/', charts.salesPerformance, name='salesPerformance'),
    path('chart6Week/', charts.chart6Week, name='chart6Week'), 
    path('averageCustomer/', charts.averageCustomer, name='averageCustomer'),
    path('mixSale/', charts.mixSale, name='mixSale'),

    
    #<---------------------------Supervisor Panel--------------------------->
    path('customerAssignments/', supervisorPanel.customerAssignments, name='customerAssignments'),
    path('requestsChangeDate/', supervisorPanel.requestsChangeDate, name='requestsChangeDate'),
    path('requestsChangeAgent/', supervisorPanel.requestsChangeAgent, name='requestsChangeAgent'),
    path('getReasonChange/<int:logId>/', supervisorPanel.getReasonChange, name='getReasonChange'),


    #<---------------------------Users--------------------------->    
    path('formCreateUser/', users.formCreateUser, name='formCreateUser'),
    path('editUser/<user_id>', users.editUser, name='editUser'),
    path('toggleUser/<user_id>/', users.toggleUser, name='toggleUser'),

    path('userModule/', users.userModule, name='userModule'),
    path('assign-modules/<int:company_id>/', users.assignModulesModal, name='assignModulesModal'), 

    #<---------------------------Quality---------------------------> 
    path('formCreateControl/', quality.formCreateControl, name='formCreateControl'),
    path('control/', quality.tableControl, name='control'),
    path('createQuality/', quality.createQuality, name='createQuality'),

    path('formCreateQuestionControl/', quality.formCreateQuestionControl, name='formCreateQuestionControl'),
    path('toggleQuestionControl/<question_id>/', toggles.toggleControlQuestions, name='toggleControlQuestions'),

    path('formAsignationQuestionControl/', quality.formAsignationQuestionControl, name='formAsignationQuestionControl'),

    path('formOE/', quality.formOE, name='formOE'),
    path('tableOE/', quality.tableOE, name='tableOE'),
    path("tableOE/detail/<int:agent_id>/", quality.tableOEDetail, name="tableOEDetail"),

    #<---------------------------Excel---------------------------> 
    path('uploadExcel/', dbExcel.uploadExcel, name='uploadExcel'),    
    path('processAndSave/', dbExcel.processAndSave, name='processAndSave'),
    path('saveData/', dbExcel.saveData, name='saveData'),
    path('manageAgentAssignments/', dbExcel.manageAgentAssignments, name='manageAgentAssignments'),
    path('bd/', dbExcel.commentDB, name='bd'),
    path('reportBd/', dbExcel.reportBd, name='reportBd'),
    path('saveCommentAjax', dbExcel.saveCommentAjax, name='saveCommentAjax'),


    #<---------------------------Consent---------------------------> 
    path('viewConsent/<obamacare_id>/', consents.consent, name='viewConsent'),
    path('viewIncomeLetter/<obamacare_id>/', consents.incomeLetter, name='incomeLetter'),
    path('consetMedicare/<client_id>/<language>/', consents.consetMedicare, name='consetMedicare'),
    #carta con la FFM
    path('ILFFM/<obamacare>/', consents.ILFFM, name='ILFFM'),
    path('ConsentLifeInsurance/<client_id>/', consents.ConsentLifeInsurance, name='ConsentLifeInsurance'), #Consent Life Insurance

    path('complaint/<obamacare_id>/<validationUniq>/', consents.complaint, name='complaint'),

    path('consentL/', consents.consentL, name='consentL'),
    path('sendConsentForm/', consents.sendConsentForm, name='sendConsentForm'),

    path('cignaSuplemental/<supp_id>/', consents.cignaSuplemental, name='cignaSuplemental'),

    #<---------------------------Company---------------------------> 
    path('formCreateCompanies/', companies.formCreateCompanies, name='formCreateCompanies'),
    path('editCompanies/<company_id>', companies.editCompanies, name='editCompanies'),
    path('toggleCompanies/<company_id>/', companies.toggleCompanies, name='toggleCompanies'),
    path('createServices/', companies.createServices, name='createServices'),
    path('addSubscription/', companies.addSubscription, name='addSubscription'),
    path('addNumbers/', companies.addNumbers, name='addNumbers'),
    path('toggleNumberCompany/<number_id>/', companies.toggleNumberCompany, name='toggleNumberCompany'),
    path('addNumbersUsers/', companies.addNumbersUsers, name='addNumbersUsers'),


    #<---------------------------Comparative Report---------------------------> 
    path('uploadReports/', comparativeReports.uploadReports, name='uploadReports'),
    path('processExcel/', comparativeReports.processExcel, name='processExcel'),
    path('headerProcessor/', comparativeReports.headerProcessor, name='headerProcessor'),


    #<---------------------------Utils---------------------------> 
    path('toggleDarkMode/', utils.toggleDarkMode, name='toggleDarkMode'),


    #<---------------------------Book---------------------------> 
    path('uploadBook/', book.uploadBook, name='uploadBook'),
    path('bookList/', book.bookList, name='bookList'),
    path('bookPages/<int:pdf_id>/', book.bookPages, name='bookPages'),
    path('saveTime/', book.saveTime, name='saveTime'),
    path('toggleBook/<book_id>/', book.toggleBook, name='toggleBook'),
    path('bookReport/', book.bookReport, name='bookReport'),
    

    #<---------------------------WHATSAPP--------------------------->
    path('sendWhatsapp/', whatsApp.sendWhatsapp, name='sendWhatsapp'),
    path('whatsappReply/<company_id>/', whatsApp.whatsappReply, name='whatsappReply'),
    path('whatsappBlue/', whatsApp.index, name='whatsappBlue'),
    path('chatWatsapp/<chatId>/', whatsApp.chat, name='chatWatsapp'),
    path('sendWhatsappConversation/', whatsApp.sendWhatsappConversation, name='sendWhatsappConversation'),
    path('deleteContactWhatsApp/<id>/', whatsApp.deleteContactWhatsApp, name='deleteContactWhatsApp'),
    path('template/<contact_id>/', whatsApp.template, name='template'),

]