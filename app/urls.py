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
from django.contrib import admin
from django.urls import path

from .views import auth, index, tv, utils
from .views.informationClients import table, toggles, modals, edits
from .views.informationClients import fetchs as fetchInformations
from .views.enterData import existClient, forms
from .views.enterData import fetchs as fetchsEnterData
from .views.reports import fecths as fetchsReports
from .views.reports import table as tableReports
from .views.reports import charts, download
from .views import users, dbExcel, quality, consents

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
    path('formEditClient/<client_id>/', edits.formEditClient, name='formEditClient'), # Formulario para editar SOLO LOS CLIENTES

    path('formCreatePlan/<client_id>/', forms.formCreatePlan, name='formCreatePlan'),
    path('fetchAca/<client_id>/', fetchsEnterData.fetchAca, name='fetchAca'),
    path('fetchSupp/<client_id>/', fetchsEnterData.fetchSupp, name='fetchSupp'),
    path('fetchDependent/<client_id>/', fetchsEnterData.fetchDependent, name='fetchDependent'),
    path('formCreatePlan/deleteDependent/<int:dependent_id>/', fetchInformations.delete_dependent, name='delete_dependent'),
    path('formCreatePlan/deleteSupp/<int:supp_id>/', fetchInformations.delete_supp, name='delete_supp'),

    path('formCreateClientMedicare/', forms.formCreateClientMedicare, name='formCreateClientMedicare'), # Formulario para crear clientes Medicare

    path('select_client/', existClient.select_client, name='select_client'), # Vista para seleccionar clientes existentes
    path('update-type-sales/<int:client_id>/', existClient.update_type_sales, name='update_type_sales'), # Funcion intermedia que cambia el TypeSale del cliente
    path('formAddObama/<client_id>', forms.formAddObama, name='formAddObama'),
    path('formAddSupp/<client_id>', forms.formAddSupp, name='formAddSupp'),
    path('formAddDepend/<client_id>', forms.formAddDepend, name='formAddDepend'),
    path('addDepend/', forms.addDepend, name='addDepend'),

    path('formCreateAlert/', forms.formCreateAlert, name='formCreateAlert'), # Formulario para crear las Alertas

    #<---------------------------Information Client--------------------------->
    path('clientObamacare/', table.clientObamacare, name='clientObamacare'),
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

    path('clientAccionRequired/', table.clientAccionRequired, name='clientAccionRequired'),

    path('clientSupp/', table.clientSupp, name='clientSupp'),
    path('toggleSuppStatus/<supp_id>/', toggles.toggleSuppStatus, name='toggleSuppStatus'),
    path('editClientSupp/<supp_id>/', edits.editClientSupp, name='editClientSupp'),
    path('saveCustomerObservationSupp/', modals.saveCustomerObservationSupp, name='saveCustomerObservationSupp'),

    path('clientMedicare/', table.clientMedicare, name='clientMedicare'),
    path('editClientMedicare/<medicare_id>/', edits.editClientMedicare, name='editClientMedicare'),
    path('save-customer-observation-medicare/', modals.saveCustomerObservationMedicare, name='saveCustomerObservationMedicare'),
    path('desactiveMedicare/<medicare_id>/', modals.desactiveMedicare, name='desactiveMedicare'),

    path('alert/', table.tableAlert, name='alert'),
    path('toggleAlert/<alertClient_id>/', toggles.toggleAlert, name='toggleAlert'),
    path('editAlert/<alertClient_id>/', edits.editAlert, name='editAlert'),


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

    path('typification/', modals.typification, name='typification'),
    path('toggleTypification/<typifications_id>/', toggles.toggleTypification, name='toggleTypification'),
    path('get-observation-detail/<observation_id>/', fetchsReports.get_observation_detail, name='get_observation_detail'),

    path('customerTypification', tableReports.customerTypification, name='customerTypification'),


    #<---------------------------Graphical Reports--------------------------->
    path('salesPerformance/', charts.salesPerformance, name='salesPerformance'),
    path('chart6Week/', charts.chart6Week, name='chart6Week'), 
    path('averageCustomer', charts.averageCustomer, name='averageCustomer'),


    #<---------------------------Users--------------------------->    
    path('formCreateUser/', users.formCreateUser, name='formCreateUser'),
    path('editUser/<user_id>', users.editUser, name='editUser'),
    path('toggleUser/<user_id>/', users.toggleUser, name='toggleUser'),


    #<---------------------------Quality---------------------------> 
    path('formCreateControl/', quality.formCreateControl, name='formCreateControl'),
    path('control/', quality.tableControl, name='control'),
    path('createQuality/', quality.createQuality, name='createQuality'),


    #<---------------------------Excel---------------------------> 
    path('upload_excel/', dbExcel.upload_excel, name='upload_excel'),    
    path('process_and_save/', dbExcel.process_and_save, name='process_and_save'),
    path('save_data/', dbExcel.save_data, name='save_data'),
    path('manage_agent_assignments/', dbExcel.manage_agent_assignments, name='manage_agent_assignments'),
    path('bd/', dbExcel.commentDB, name='bd'),
    path('reportBd/', dbExcel.reportBd, name='reportBd'),


    #<---------------------------Consent---------------------------> 
    path('consetMedicare/<client_id>/<language>/', consents.consetMedicare, name='consetMedicare'),
    
]