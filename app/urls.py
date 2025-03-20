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
from .views import dbExcel, quality, consents

from .views import sms

urlpatterns = [
    #<---------------------------Auth--------------------------->
    path('login/', auth.login_, name='login'),
    path('logout/', auth.logout_, name='logout'),
    path('motivationalPhrase/', auth.motivationalPhrase, name='motivationalPhrase'), # Vista que renderiza la frase motivacional


    #<---------------------------DashBoard--------------------------->
    path('', index.index_redirect, name='home'),  # Nueva ruta sin parámetros
    path('index/<company_id>/', index.index, name='index'), #Home
    path('weeklyLiveView/<company_id>/',tv.weeklyLiveView,name='weeklyLiveView'), # Vista Semanal TV con Sidebard
    path('monthLiveView/<company_id>/',tv.monthLiveView,name='monthLiveView'), # Vista Mensual TV con Sidebard

    path('weeklyLiveViewTV/<company_id>/',tv.weeklyLiveView,name='weeklyLiveViewTV'), # Vista Semanal TV sin Sidebard
    path('monthLiveViewTV/<company_id>/',tv.monthLiveView,name='monthLiveViewTV'), # Vista Mensual TV sin Sidebard


    #<---------------------------Enter Data--------------------------->
    path('formCreateClient/<company_id>/', forms.formCreateClient, name='formCreateClient'), # Formulario para crear Clientes Obamacare
    path('formEditClient/<company_id>/<client_id>/', edits.formEditClient, name='formEditClient'),


    path('formCreatePlan/<company_id>/<client_id>/', forms.formCreatePlan, name='formCreatePlan'),
    path('fetchAca/<client_id>/', fetchsEnterData.fetchAca, name='fetchAca'),
    path('fetchSupp/<client_id>/', fetchsEnterData.fetchSupp, name='fetchSupp'),
    path('fetchDependent/<client_id>/', fetchsEnterData.fetchDependent, name='fetchDependent'),
    path('formCreatePlan/<company_id>/deleteDependent/<int:dependent_id>/', fetchInformations.delete_dependent, name='delete_dependent'),
    path('formCreatePlan/<company_id>/deleteSupp/<int:supp_id>/', fetchInformations.delete_supp, name='delete_supp'),

    path('formCreateClientMedicare/<company_id>/', forms.formCreateClientMedicare, name='formCreateClientMedicare'), # Formulario para crear clientes Medicare

    path('select_client/<company_id>/', existClient.select_client, name='select_client'), # Vista para seleccionar clientes existentes
    path('update-type-sales/<int:client_id>/', existClient.update_type_sales, name='update_type_sales'), # Funcion intermedia que cambia el TypeSale del cliente
    path('formAddObama/<client_id>', forms.formAddObama, name='formAddObama'),
    path('formAddSupp/<client_id>', forms.formAddSupp, name='formAddSupp'),
    path('formAddDepend/<client_id>', forms.formAddDepend, name='formAddDepend'),
    path('addDepend/', forms.addDepend, name='addDepend'),

    path('formCreateAlert/<company_id>/', forms.formCreateAlert, name='formCreateAlert'), # Formulario para crear las Alertas

    #<---------------------------Information Client--------------------------->
    path('clientObamacare/<company_id>/', table.clientObamacare, name='clientObamacare'),
    path('toggleObamaStatus/<obamacare_id>/', toggles.toggleObamaStatus, name='toggleObamaStatus'),
    path('editClientObama/<int:obamacare_id>/<int:way>/', edits.editClientObama, name='editClientObama'),
    path('saveCustomerObservationACA/', modals.saveCustomerObservationACA, name='saveCustomerObservationACA'),
    path('saveDocumentClient/<int:obamacare_id>/<int:way>/', modals.saveDocumentClient, name='saveDocumentClient'),
    path('saveAppointment/<int:obamacare_id>/', modals.saveAppointment, name='saveAppointment'),
    path('saveAccionRequired/', modals.saveAccionRequired, name='saveAccionRequired'),
    path('fetchPaymentsMonth/', fetchInformations.fetchPaymentsMonth, name='fetchPaymentsMonth'),
    path('fetchActionRequired/', fetchInformations.fetchActionRequired, name='fetchActionRequired'),
    path('viewConsent/<obamacare_id>/', consents.consent, name='viewConsent'),
    path('viewIncomeLetter/<obamacare_id>/', consents.incomeLetter, name='incomeLetter'),
    path('validarCita/', modals.validarCita, name='validarCita'),

    path('clientAccionRequired/<company_id>/', table.clientAccionRequired, name='clientAccionRequired'),

    path('clientSupp/<company_id>/', table.clientSupp, name='clientSupp'),
    path('toggleSuppStatus/<supp_id>/', toggles.toggleSuppStatus, name='toggleSuppStatus'),
    path('editClientSupp/<supp_id>/', edits.editClientSupp, name='editClientSupp'),
    path('saveCustomerObservationSupp/', modals.saveCustomerObservationSupp, name='saveCustomerObservationSupp'),

    path('clientMedicare/<company_id>/', table.clientMedicare, name='clientMedicare'),
    path('editClientMedicare/<medicare_id>/', edits.editClientMedicare, name='editClientMedicare'),
    path('save-customer-observation-medicare/', modals.saveCustomerObservationMedicare, name='saveCustomerObservationMedicare'),
    path('desactiveMedicare/<medicare_id>/', modals.desactiveMedicare, name='desactiveMedicare'),

    path('alert/<company_id>/', table.tableAlert, name='alert'),
    path('toggleAlert/<alertClient_id>/', toggles.toggleAlert, name='toggleAlert'),
    path('editAlert/<alertClient_id>/', edits.editAlert, name='editAlert'),


    #<---------------------------SMS--------------------------->
    path('smsBlue/', sms.index, name='smsBlue'),
    path('chatSms/<phoneNumber>/', sms.chat, name='chatSms'),
    path('sendMessage/', sms.sendMessage, name='sendMessage'),
    path('deleteChat/<id>/', sms.deleteContact, name='deleteContact'),

    path('sms/<int:company_id>/', sms.sms, name='sms'),

    path('createSecretKey/<id>/', sms.sendCreateSecretKey, name='sendCreateSecretKey'),
    path('sendSecretKey/<contact_id>/', sms.sendSecretKey, name='sendSecretKey'),
    path('secret-key/', sms.createSecretKey, name='url_temporal'),


    #<---------------------------Sales Reports--------------------------->
    path('sale/<company_id>/', tableReports.sale, name='sale'),

    path('sale6Week/<company_id>/', tableReports.sales6WeekReport, name='sale6Week'),  
    path('detalleAgente/<agent_id>/', fetchsReports.SaleModal, name='detalleAgente'),  

    path('weekSalesWiew/<company_id>/',tableReports.weekSalesWiew, name='weekSalesWiew'),
    path('descargarPdf/<int:week_number>/', download.downloadPdf, name='downloadPdf'),

    path('reports/<company_id>/', tableReports.reports, name='reports'),
    path('downloadAccionRequired/', download.downloadAccionRequired, name='downloadAccionRequired'),
    path('paymentClients/', download.paymentClients, name='paymentClients'),


    #<---------------------------Customer Reports--------------------------->
    path('customerPerformance/<company_id>/', tableReports.customerPerformance, name='customerPerformance'),

    path('typification/<company_id>/', modals.typification, name='typification'),
    path('toggleTypification/<typifications_id>/', toggles.toggleTypification, name='toggleTypification'),
    path('get-observation-detail/<observation_id>/', fetchsReports.get_observation_detail, name='get_observation_detail'),

    path('customerTypification/<company_id>/', tableReports.customerTypification, name='customerTypification'),


    #<---------------------------Graphical Reports--------------------------->
    path('salesPerformance/<company_id>/', charts.salesPerformance, name='salesPerformance'),
    path('chart6Week/<company_id>/', charts.chart6Week, name='chart6Week'), 
    path('averageCustomer/<company_id>/', charts.averageCustomer, name='averageCustomer'),


    #<---------------------------Users--------------------------->    
    path('formCreateUser/<company_id>/', users.formCreateUser, name='formCreateUser'),
    path('editUser/<company_id>/<user_id>', users.editUser, name='editUser'),
    path('toggleUser/<user_id>/', users.toggleUser, name='toggleUser'),


    #<---------------------------Quality---------------------------> 
    path('formCreateControl/<company_id>/', quality.formCreateControl, name='formCreateControl'),
    path('control/<company_id>/', quality.tableControl, name='control'),
    path('createQuality/<company_id>/', quality.createQuality, name='createQuality'),


    #<---------------------------Excel---------------------------> 
    path('upload_excel/<company_id>/', dbExcel.upload_excel, name='upload_excel'),    
    path('process_and_save/', dbExcel.process_and_save, name='process_and_save'),
    path('save_data/', dbExcel.save_data, name='save_data'),
    path('manage_agent_assignments/<company_id>/', dbExcel.manage_agent_assignments, name='manage_agent_assignments'),
    path('bd/', dbExcel.commentDB, name='bd'),
    path('reportBd/<company_id>/', dbExcel.reportBd, name='reportBd'),


    #<---------------------------Consent---------------------------> 
    path('consetMedicare/<client_id>/<language>/', consents.consetMedicare, name='consetMedicare'),


    #<---------------------------Companny---------------------------> 
    path('formCreateCompanies/', companies.formCreateCompanies, name='formCreateCompanies'),
    path('editCompanies/<companies_id>', companies.editCompanies, name='editCompanies'),
    path('toggleCompanies/<companies_id>/', companies.toggleCompanies, name='toggleCompanies'),
    
]