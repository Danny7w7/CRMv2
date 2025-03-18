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
from .views.reports import charts
from .views import users, dbExcel, quality, consents

urlpatterns = [
    path('', index.index, name='index'),
    path('login/', auth.login_, name='login'),
    path('logout/', auth.logout_, name='logout'),

    path('admin/', admin.site.urls),

    path('weeklyLiveView/',tv.weeklyLiveView,name='weeklyLiveView'),
    path('monthLiveView/',tv.monthLiveView,name='monthLiveView'),

    path('weeklyLiveViewTV/',tv.weeklyLiveView,name='weeklyLiveViewTV'),
    path('monthLiveViewTV/',tv.monthLiveView,name='monthLiveViewTV'),

    path('formCreateClient/', forms.formCreateClient, name='formCreateClient'),
    path('formEditClient/<client_id>/', edits.formEditClient, name='formEditClient'),

    path('check-phone-number/', utils.check_phone_number, name = 'check_phone_number'),
    path('motivationalPhrase/', auth.motivationalPhrase, name='motivationalPhrase'),

    path('select_client/', existClient.select_client, name='select_client'),
    path('update-type-sales/<int:client_id>/', existClient.update_type_sales, name='update_type_sales'),

    path('clientObamacare/', table.clientObamacare, name='clientObamacare'),
    path('clientSupp/', table.clientSupp, name='clientSupp'),
    path('clientAccionRequired/', table.clientAccionRequired, name='clientAccionRequired'),
    
    path('toggleObamaStatus/<obamacare_id>/', toggles.toggleObamaStatus, name='toggleObamaStatus'),
    path('toggleSuppStatus/<supp_id>/', toggles.toggleSuppStatus, name='toggleSuppStatus'),

    path('save-customer-observation-aca/', modals.saveCustomerObservationACA, name='saveCustomerObservationACA'),
    path('save-customer-observation-supp/', modals.saveCustomerObservationSupp, name='saveCustomerObservationSupp'),

    path('typification/', modals.typification, name='typification'),
    path('customerPerformance/', tableReports.customerPerformance, name='customerPerformance'),
    path('get-observation-detail/<observation_id>/', fetchsReports.get_observation_detail, name='get_observation_detail'),
    path('toggleTypification/<typifications_id>/', toggles.toggleTypification, name='toggleTypification'),

    path('sale/', tableReports.sale, name='sale'),

    path('editClientObama/<int:obamacare_id>/<int:way>/', edits.editClientObama, name='editClientObama'),
    path('saveDocumentClient/<int:obamacare_id>/<int:way>/', modals.saveDocumentClient, name='saveDocumentClient'),
    path('saveAppointment/<int:obamacare_id>/', modals.saveAppointment, name='saveAppointment'),
    path('editClientSupp/<supp_id>/', edits.editClientSupp, name='editClientSupp'),
    path('saveAccionRequired/', modals.saveAccionRequired, name='saveAccionRequired'),
    
    path('formCreateAlert/', forms.formCreateAlert, name='formCreateAlert'),
    path('alert/', table.tableAlert, name='alert'),
    path('toggleAlert/<alertClient_id>/', toggles.toggleAlert, name='toggleAlert'),
    path('editAlert/<alertClient_id>/', edits.editAlert, name='editAlert'),

    path('formCreateUser/', users.formCreateUser, name='formCreateUser'),
    path('editUser/<user_id>', users.editUser, name='editUser'),
    path('toggleUser/<user_id>/', users.toggleUser, name='toggleUser'),

    # Json
    path('formCreatePlan/<client_id>/', forms.formCreatePlan, name='formCreatePlan'),
    path('fetchAca/<client_id>/', fetchsEnterData.fetchAca, name='fetchAca'),
    path('fetchSupp/<client_id>/', fetchsEnterData.fetchSupp, name='fetchSupp'),
    path('fetchDependent/<client_id>/', fetchsEnterData.fetchDependent, name='fetchDependent'),

    path('fetchPaymentsMonth/', fetchInformations.fetchPaymentsMonth, name='fetchPaymentsMonth'),
    path('fetchActionRequired/', fetchInformations.fetchActionRequired, name='fetchActionRequired'),

    path('formCreatePlan/deleteDependent/<int:dependent_id>/', fetchInformations.delete_dependent, name='delete_dependent'),
    path('formCreatePlan/deleteSupp/<int:supp_id>/', fetchInformations.delete_supp, name='delete_supp'),

    path('upload_excel/', dbExcel.upload_excel, name='upload_excel'),    
    path('process_and_save/', dbExcel.process_and_save, name='process_and_save'),
    path('save_data/', dbExcel.save_data, name='save_data'),
    path('manage_agent_assignments/', dbExcel.manage_agent_assignments, name='manage_agent_assignments'),
    path('bd/', dbExcel.commentDB, name='bd'),
    path('reportBd/', dbExcel.reportBd, name='reportBd'),

    path('formCreateControl/', quality.formCreateControl, name='formCreateControl'),
    path('control/', quality.tableControl, name='control'),
    path('createQuality/', quality.createQuality, name='createQuality'),

    path('salesPerformance/', charts.salesPerformance, name='salesPerformance'),

    path('viewConsent/<obamacare_id>/', consents.consent, name='viewConsent'),
    path('viewIncomeLetter/<obamacare_id>/', consents.incomeLetter, name='incomeLetter'),

    path('averageCustomer', charts.averageCustomer, name='averageCustomer'),
    path('customerTypification', views.customerTypification, name='customerTypification'),

    path('formAddObama/<client_id>', views.formAddObama, name='formAddObama'),
    path('formAddSupp/<client_id>', views.formAddSupp, name='formAddSupp'),
    path('formAddDepend/<client_id>', views.formAddDepend, name='formAddDepend'),
    path('addDepend/', views.addDepend, name='addDepend'),
    
    path('detalle-agente/<agent_id>/', views.SaleModal, name='detalle_agente'),  

    path('sale6Week/', views.sales6WeekReport, name='sale6Week'),  
    path('chart6Week/', views.chart6Week, name='chart6Week'), 

    path('weekSalesWiew/',views.weekSalesWiew, name='weekSalesWiew'),
    path('descargarPdf/<int:week_number>/', views.downloadPdf, name='downloadPdf'),

    path('formCreateClientMedicare/', views.formCreateClientMedicare, name='formCreateClientMedicare'),
    path('consetMedicare/<client_id>/<language>/', views.consetMedicare, name='consetMedicare'),
    path('clientMedicare/', views.clientMedicare, name='clientMedicare'),
    path('editClientMedicare/<medicare_id>/', views.editClientMedicare, name='editClientMedicare'),
    path('save-customer-observation-medicare/', views.saveCustomerObservationMedicare, name='saveCustomerObservationMedicare'),
    path('desactiveMedicare/<medicare_id>/', views.desactiveMedicare, name='desactiveMedicare'),
    path('validarCita/', views.validarCita, name='validarCita'),

    path('reports/', views.reports, name='reports'),
    path('downloadAccionRequired/', views.downloadAccionRequired, name='downloadAccionRequired'),
    path('paymentClients/', views.paymentClients, name='paymentClients'),
    
    #Oneil, Sherpa and Carrier
    path('uploadExcels/', views.uploadExcels, name='uploadExcels'),
    path('processMappedHeadersPayments/', views.processMappedHeadersPayments, name='processMappedHeadersPayments'),
    path('processMappedHeadersCarrier/', views.processMappedHeadersCarrier, name='processMappedHeadersCarrier'),
]