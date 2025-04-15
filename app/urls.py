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
from .views import dbExcel, quality, consents, sms, utils, supervisorPanel


urlpatterns = [
    #<---------------------------Auth--------------------------->
    path('login/', auth.login_, name='login'),
    path('logout/', auth.logout_, name='logout'),
    path('motivationalPhrase/', auth.motivationalPhrase, name='motivationalPhrase'), # Vista que renderiza la frase motivacional


    #<---------------------------DashBoard--------------------------->
    path('', index.index, name='index'), #Home
    path('weeklyLiveView/',tv.weeklyLiveView,name='weeklyLiveView'), # Vista Semanal TV con Sidebard
    path('monthLiveView/',tv.monthLiveView,name='monthLiveView'), # Vista Mensual TV con Sidebard

    path('weeklyLiveViewTV/',tv.weeklyLiveView,name='weeklyLiveViewTV'), # Vista Semanal TV sin Sidebard
    path('monthLiveViewTV/',tv.monthLiveView,name='monthLiveViewTV'), # Vista Mensual TV sin Sidebard


    #<---------------------------Enter Data--------------------------->
    path('formCreateClient/', forms.formCreateClient, name='formCreateClient'), # Formulario para crear Clientes Obamacare
    path('formEditClient/<client_id>/', edits.formEditClient, name='formEditClient'),

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
    path('update-type-sales/<int:client_id>/', existClient.update_type_sales, name='update_type_sales'), # Funcion intermedia que cambia el TypeSale del cliente
    path('formAddObama/<client_id>/', forms.formAddObama, name='formAddObama'),
    path('formAddSupp/<client_id>', forms.formAddSupp, name='formAddSupp'),
    path('formAddDepend/<client_id>', forms.formAddDepend, name='formAddDepend'),
    path('addDepend/', forms.addDepend, name='addDepend'),

    path('formCreateAlert/', forms.formCreateAlert, name='formCreateAlert'), # Formulario para crear las Alertas

    #<---------------------------Information Client--------------------------->
    path('clientObamacare/', table.clientObamacare, name='clientObamacare'),
    path('toggleObamaStatus/<obamacare_id>/', toggles.toggleObamaStatus, name='toggleObamaStatus'),
    path('editObama/<int:obamacare_id>/<int:way>/', edits.editObama, name='editObama'),
    path('blockSocialSecurity/', fetchInformations.blockSocialSecurity, name='blockSocialSecurity'),
    path('saveCustomerObservationACA/', modals.saveCustomerObservationACA, name='saveCustomerObservationACA'),
    path('saveDocumentClient/<int:obamacare_id>/<int:way>/', modals.saveDocumentClient, name='saveDocumentClient'),
    path('saveAppointment/<int:obamacare_id>/', modals.saveAppointment, name='saveAppointment'),
    path('saveAccionRequired/', modals.saveAccionRequired, name='saveAccionRequired'),
    path('fetchPaymentsMonth/', fetchInformations.fetchPaymentsMonth, name='fetchPaymentsMonth'),
    path('fetchActionRequired/', fetchInformations.fetchActionRequired, name='fetchActionRequired'),
    path('viewConsent/<obamacare_id>/', consents.consent, name='viewConsent'),
    path('viewIncomeLetter/<obamacare_id>/', consents.incomeLetter, name='incomeLetter'),
    path('validarCita/', modals.validarCita, name='validarCita'),
    path('paymentDateObama/<obama_id>/', modals.paymentDateObama, name='paymentDateObama'),

    path('clientAccionRequired/', table.clientAccionRequired, name='clientAccionRequired'),

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
    path('paymentDateSupp/<supp_id>/', modals.paymentDateSupp, name='paymentDateSupp'),

    path('clientMedicare/', table.clientMedicare, name='clientMedicare'),
    path('editClientMedicare/<medicare_id>/', edits.editClientMedicare, name='editClientMedicare'),
    path('blockSocialSecurityMedicare/', fetchInformations.blockSocialSecurityMedicare, name='blockSocialSecurityMedicare'),
    path('save-customer-observation-medicare/', modals.saveCustomerObservationMedicare, name='saveCustomerObservationMedicare'),
    path('desactiveMedicare/<medicare_id>/', modals.desactiveMedicare, name='desactiveMedicare'),

    path('alert/', table.tableAlert, name='alert'),
    path('toggleAlert/<alertClient_id>/', toggles.toggleAlert, name='toggleAlert'),
    path('editAlert/<int:alertClient_id>/', edits.editAlert, name='editAlert'),

    #<---------------------------tiketc--------------------------->
    path('ticketAsing/', table.ticketAsing, name='ticketAsing'),
    path('agentTicketAssignment/', modals.agentTicketAssignment, name='agentTicketAssignment'),
    path('editTicket/<ticket_id>/', edits.editTicket, name='editTicket'),
    path('toggleTicketStatus/<ticket_id>/', toggles.toggleTicketStatus, name='toggleTicketStatus'),


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


    #<---------------------------Sales Reports--------------------------->
    path('sale/', tableReports.sale, name='sale'),

    path('sale6Week/', tableReports.sales6WeekReport, name='sale6Week'),  
    path('detalleAgente/<agent_id>/', fetchsReports.SaleModal, name='detalleAgente'),  

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


    #<---------------------------Graphical Reports--------------------------->
    path('salesPerformance/', charts.salesPerformance, name='salesPerformance'),
    path('chart6Week/', charts.chart6Week, name='chart6Week'), 
    path('averageCustomer/', charts.averageCustomer, name='averageCustomer'),

    
    #<---------------------------Supervisor Panel--------------------------->
    path('customerAssginments/', supervisorPanel.customerAssginments, name='customerAssginments'),


    #<---------------------------Users--------------------------->    
    path('formCreateUser/', users.formCreateUser, name='formCreateUser'),
    path('editUser/<user_id>', users.editUser, name='editUser'),
    path('toggleUser/<user_id>/', users.toggleUser, name='toggleUser'),


    #<---------------------------Quality---------------------------> 
    path('formCreateControl/', quality.formCreateControl, name='formCreateControl'),
    path('control/', quality.tableControl, name='control'),
    path('createQuality/', quality.createQuality, name='createQuality'),


    #<---------------------------Excel---------------------------> 
    path('uploadExcel/', dbExcel.uploadExcel, name='uploadExcel'),    
    path('processAndSave/', dbExcel.processAndSave, name='processAndSave'),
    path('saveData/', dbExcel.saveData, name='saveData'),
    path('manageAgentAssignments/', dbExcel.manageAgentAssignments, name='manageAgentAssignments'),
    path('bd/', dbExcel.commentDB, name='bd'),
    path('reportBd/', dbExcel.reportBd, name='reportBd'),


    #<---------------------------Consent---------------------------> 
    path('consetMedicare/<client_id>/<language>/', consents.consetMedicare, name='consetMedicare'),
    #carta con la FFM
    path('ILFFM/<obamacare>/', consents.ILFFM, name='ILFFM'),


    #<---------------------------Company---------------------------> 
    path('formCreateCompanies/', companies.formCreateCompanies, name='formCreateCompanies'),
    path('editCompanies/<company_id>', companies.editCompanies, name='editCompanies'),
    path('toggleCompanies/<company_id>/', companies.toggleCompanies, name='toggleCompanies'),
    path('createServices/', companies.createServices, name='createServices'),
    path('addSubscription/', companies.addSubscription, name='addSubscription'),
    path('addNumbers/', companies.addNumbers, name='addNumbers'),
    path('toggleNumberCompany/<number_id>/', companies.toggleNumberCompany, name='toggleNumberCompany'),
    path('addNumbersUsers/', companies.addNumbersUsers, name='addNumbersUsers'),
    
    #<---------------------------Utils---------------------------> 
    path('toggleDarkMode/', utils.toggleDarkMode, name='toggleDarkMode'),
]