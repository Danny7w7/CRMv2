# Standard Python libraries
import calendar
import datetime
import json
from itertools import chain
import re
from datetime import datetime, date

#libreria de paises
import urllib.request
from django.shortcuts import render

# Django utilities
from django.db.models import Sum, Count
from django.http import JsonResponse
from collections import defaultdict

# Django core libraries
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

# Application-specific imports
from app.models import *
from app.modelsSMS import *
from app.views.enterData.forms import countDigits
from ...forms import *
from ..sms import get_last_message_for_chats
from ..decoratorsCompany import *
from ..consents import generateTemporaryToken, getCompanyPerAgent
  

@login_required(login_url='/login') 
def formEditClient(request, client_id):
    
    client = get_object_or_404(Clients, id=client_id)     

    if request.user.is_superuser:
        agentUsa = USAgent.objects.all().prefetch_related("company")
    else:
        agentUsa = USAgent.objects.filter(company = request.user.company).prefetch_related("company")   

    if request.method == 'POST':

        date_births = request.POST.get('date_birth')
        fecha_obj = datetime.datetime.strptime(date_births, '%m/%d/%Y').date()
        fecha_formateada = fecha_obj.strftime('%Y-%m-%d')

        social = request.POST.get('social_security')

        if social: formatSocial = social.replace('-','')
        else: formatSocial = None
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            client = form.save(commit=False)
            client.is_active = 1
            client.date_birth = fecha_formateada
            client.social_security = formatSocial
            
            client.save()
            return redirect('formCreatePlan', client.id) 
        
    # Si el método es GET, mostrar el formulario con los datos del cliente
    form = ClientForm(instance=client)

    context = {
        'form': form, 
        'client': client,
        'agentUsa' : agentUsa
    }

    return render(request, 'edit/formEditClient.html', context)

@login_required(login_url='/login') 
@company_ownership_required(model_name="ClientAlert", id_field="alertClient_id")
def editAlert(request, alertClient_id):

    alert = ClientAlert.objects.select_related('agent').get(id=alertClient_id)  # Ya validado en el decorador

    if request.method == 'POST':

        alert_fields = ['name_client', 'phone_number', 'datetime', 'content' ]

        # Limpiar los campos 
        cleaned_alert_data = clean_fields_to_null(request, alert_fields)

        ClientAlert.objects.filter(id=alertClient_id).update(
                name_client=cleaned_alert_data['name_client'],
                phone_number=cleaned_alert_data['phone_number'],
                datetime=cleaned_alert_data['datetime'],
                content=cleaned_alert_data['content']
            )
        return redirect('alert')

    return render(request, 'edit/editAlert.html', {'editAlert':alert} )

@login_required(login_url='/login')
@company_ownership_required(model_name="Medicare", id_field="medicare_id") 
def editClientMedicare(request, medicare_id):

    # Buscar el cliente
    medicare = get_object_or_404(Medicare.objects.select_related('agent'), id=medicare_id)

    if request.user.is_superuser:
        agentUsa = USAgent.objects.all().prefetch_related("company")
    else:
        agentUsa = USAgent.objects.filter(company = request.user.company).prefetch_related("company")
    
    social_number = medicare.social_security  # Campo real del modelo
    # Asegurarse de que social_number no sea None antes de formatear
    if social_number:
        formatted_social = f"xxx-xx-{social_number[-4:]}"  # Obtener el formato deseado
    else:
        formatted_social = "N/A"  # Valor predeterminado si no hay número disponible

    obsCus = ObservationCustomerMedicare.objects.select_related('agent').filter(medicare=medicare.id)
    list_drow = DropDownList.objects.filter(profiling_supp__isnull=False)

    consent = Consents.objects.filter(medicare = medicare_id )

    #calculo de edad
    hoy = timezone.now().date()
    old = hoy.year - medicare.date_birth.year - ((hoy.month, hoy.day) < (medicare.date_birth.month, medicare.date_birth.day))
   

    if request.method == 'POST':
        action = request.POST.get('action')

        # Campos de Client
        client_fields = [
            'agent_usa', 'first_name', 'last_name', 'phone_number', 'email', 'address', 'zipcode',
            'city', 'state', 'county', 'sex', 'migration_status', 'statusMedicare'
        ]        
        
        #formateo de fecha para guardalar como se debe en BD ya que la obtengo USA
        fecha_str = request.POST.get('date_birth')  # Formato MM/DD/YYYY
        # Conversión solo si los valores no son nulos o vacíos
        if fecha_str not in [None, '']:
            dateNew = datetime.datetime.strptime(fecha_str, '%m/%d/%Y').date()
        else:
            dateNew = None
        

        # Limpiar los campos de Client convirtiendo los vacíos en None
        cleaned_client_data = clean_fields_to_null(request, client_fields)

        # Convierte a mayúsculas los campos necesarios
        fields_to_uppercase = ['first_name', 'last_name', 'address', 'city', 'county']
        for field in fields_to_uppercase:
            if field in cleaned_client_data and cleaned_client_data[field]:
                cleaned_client_data[field] = cleaned_client_data[field].upper()

        # Actualizar Client
        client = Medicare.objects.filter(id=medicare_id).update(
            agent_usa=cleaned_client_data['agent_usa'],
            first_name=cleaned_client_data['first_name'],
            last_name=cleaned_client_data['last_name'],
            phone_number=cleaned_client_data['phone_number'],
            email=cleaned_client_data['email'],
            address=cleaned_client_data['address'],
            zipcode=cleaned_client_data['zipcode'],
            city=cleaned_client_data['city'],
            state=cleaned_client_data['state'],
            county=cleaned_client_data['county'],
            sex=cleaned_client_data['sex'],
            date_birth=dateNew,
            migration_status=cleaned_client_data['migration_status'],
            status=cleaned_client_data['statusMedicare']
        )

        return redirect('clientMedicare')   

    context = {
        'medicare': medicare,
        'formatted_social':formatted_social,
        'consent': consent,
        'obsCustomer': obsCus,
        'list_drow': list_drow,
        'old' : old,
        'agentUsa' : agentUsa
    }

    return render(request, 'edit/editClientMedicare.html', context)

def editClient(request,client_id):

    # Campos de Client
    client_fields = [
        'agent_usa', 'first_name', 'last_name', 'phone_number', 'email', 'address', 'zipcode',
        'city', 'state', 'county', 'sex', 'migration_status', 'apply'
    ]
    
    #formateo de fecha para guardalar como se debe en BD ya que la obtengo USA
    fecha_str = request.POST.get('date_birth')  # Formato MM/DD/YYYY
    # Conversión solo si los valores no son nulos o vacíos
    if fecha_str not in [None, '']:
        dateNew = datetime.datetime.strptime(fecha_str, '%m/%d/%Y').date()
    else:
        dateNew = None
    

    # Limpiar los campos de Client convirtiendo los vacíos en None
    cleaned_client_data = clean_fields_to_null(request, client_fields)

    # Convierte a mayúsculas los campos necesarios
    fields_to_uppercase = ['first_name', 'last_name', 'address', 'city', 'county']
    for field in fields_to_uppercase:
        if field in cleaned_client_data and cleaned_client_data[field]:
            cleaned_client_data[field] = cleaned_client_data[field].upper()


    # Actualizar Client
    client = Clients.objects.filter(id=client_id).update(
        agent_usa=cleaned_client_data['agent_usa'],
        first_name=cleaned_client_data['first_name'],
        last_name=cleaned_client_data['last_name'],
        email=cleaned_client_data['email'],
        address=cleaned_client_data['address'],
        zipcode=cleaned_client_data['zipcode'],
        city=cleaned_client_data['city'],
        state=cleaned_client_data['state'],
        county=cleaned_client_data['county'],
        sex=cleaned_client_data['sex'],
        date_birth=dateNew,
        apply=cleaned_client_data['apply'],
        migration_status=cleaned_client_data['migration_status']
    )

    return client

@login_required(login_url='/login')
@company_ownership_required(model_name="ObamaCare", id_field="obamacare_id")
def editObama(request ,obamacare_id, way):

    company_id = request.user.company.id

    obamacare = ObamaCare.objects.select_related('agent', 'client').filter(id=obamacare_id).first()
    dependents = Dependents.objects.prefetch_related('obamacare').filter(obamacare=obamacare)
    letterCard = LettersCard.objects.filter(obamacare = obamacare_id).first()
    apppointment = AppointmentClient.objects.select_related('obamacare','agent_create').filter(obamacare = obamacare_id)
    userCarrier = UserCarrier.objects.filter(obamacare = obamacare_id).first()
    accionRequired = CustomerRedFlag.objects.filter(obamacare = obamacare)    
    paymentDateObama = PaymentDate.objects.filter(obamacare = obamacare).first()

    if company_id == 1:
        agentUsa = USAgent.objects.all().prefetch_related("company")
    else:
        agentUsa = USAgent.objects.filter(company = request.user.company).prefetch_related("company")
        
    if letterCard and letterCard.letters and letterCard.card: 
        newLetterCard = True
    else: 
        newLetterCard = False

    if letterCard and letterCard.letters: 
        banderaLetters = True
    else: 
        banderaLetters = False

    if letterCard and  letterCard.card: 
        banderaCard = True
    else: 
        banderaCard = False


    #calculo de documente
    obamaDocumente = True if obamacare.doc_migration and obamacare.doc_income else False 

    #calculo de status
    obamaStatus = True if obamacare.status_color == 3 else False

    newApppointment = True if apppointment else False
    
    RoleAuditar = [
        newLetterCard,
        userCarrier,
        obamaStatus,         
        obamaDocumente,
        obamacare.policyNumber, 
        newApppointment,
        paymentDateObama
    ]

    c = 0
    for item in RoleAuditar: 
        if item and item != 'None' and item is not None:
            c += 1

    percentage = int(c/7*100)

    social_number = obamacare.client.social_security  # Campo real del modelo
    # Asegurarse de que social_number no sea None antes de formatear
    if social_number:
        formatted_social = f"xxx-xx-{social_number[-4:]}"  # Obtener el formato deseado
    else:
        formatted_social = "N/A"  # Valor predeterminado si no hay número disponible

    #calculo de edad
    if not obamacare.client.date_birth:
        old = None
    else:
        hoy = timezone.now().date()
        old = hoy.year - obamacare.client.date_birth.year - ((hoy.month, hoy.day) < (obamacare.client.date_birth.month, obamacare.client.date_birth.day))
   
    obsObama = ObservationAgent.objects.select_related('user').filter(obamaCare=obamacare_id)  
    users = Users.objects.filter(role='C', company = company_id)
    usersActive = Users.objects.filter(role='C', company = company_id, is_active = True)
    userInactive = Users.objects.filter(company = company_id)
    list_drow = DropDownList.objects.filter(profiling_obama__isnull=False)
    description = DropDownList.objects.filter(description__isnull=False)
    obsCus = ObservationCustomer.objects.select_related('agent').filter(obamacare=obamacare_id)
    consent = Consents.objects.filter(obamacare = obamacare_id )
    income = IncomeLetter.objects.filter(obamacare = obamacare_id)
    document = DocumentsClient.objects.filter(client = obamacare.client)
    documentObama = DocumentObamaSupp.objects.filter(obamacare = obamacare)
    incomeffm = IncomeLetterFFM.objects.filter(obamacare = obamacare_id)
    complaint = Complaint.objects.filter(obamacare = obamacare_id).exclude(pdf='')
    smsTemplate = SmsTemplate.objects.select_related('contentTemplate').filter(obamacare = obamacare_id)
    smsTemplateAll = ContentTemplate.objects.filter(company = company_id)    
    temporalyURL = f"{request.build_absolute_uri('/viewConsent/')}{obamacare_id}?token={generateTemporaryToken(obamacare.client , 'obamacare')}&lenguaje={'es'}"

    fechaLimite =  datetime.datetime(2025, 10, 31, 23, 59, 59, tzinfo=timezone.get_current_timezone())

    
    currentYear = datetime.datetime.now().year
    currentDate = datetime.datetime.now().date()

    if currentDate >= date(currentYear, 11, 1):
        # Si ya estamos en nov o después, el próximo período es del año siguiente
        startDate = date(currentYear + 1, 11, 1)
        endDate = date(currentYear + 2, 10, 31)
    else:
        # Si estamos antes de nov, el próximo período comienza este año
        startDate = date(currentYear, 11, 1)
        endDate = date(currentYear + 1, 10, 31)

    renovation = ObamaCare.objects.filter(is_active = True, company = request.user.company, client = obamacare.client, created_at__gte = startDate,  created_at__lte = endDate )

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'save_obamacare':

            editClient(request, obamacare.client.id)
            dependents= editDepentsObama(request, obamacare_id)

            usernameCarrier(request, obamacare.id)

            # Campos de ObamaCare
            obamacare_fields = [
                'taxes', 'planName', 'carrierObama', 'profiling', 'subsidy', 'ffm', 'required_bearing',
                'doc_income', 'doc_migration', 'statusObama', 'work', 'date_effective_coverage',
                'date_effective_coverage_end', 'observationObama', 'agent_usa_obamacare','policyNumber','premium'
            ]
            
            # Limpiar los campos de ObamaCare convirtiendo los vacíos en None
            cleaned_obamacare_data = clean_fields_to_null(request, obamacare_fields)

            # Convierte a mayúsculas los campos necesarios
            fields_to_uppercase = ['planName']
            for field in fields_to_uppercase:
                if field in cleaned_obamacare_data and cleaned_obamacare_data[field]:
                    cleaned_obamacare_data[field] = cleaned_obamacare_data[field].upper()

            #formateo de fecha para guardalar como se debe en BD ya que la obtengo USA
            date_bearing = request.POST.get('date_bearing')  # Formato MM/DD/YYYY
            date_effective_coverage = request.POST.get('date_effective_coverage')  # Formato MM/DD/YYYY
            date_effective_coverage_end = request.POST.get('date_effective_coverage_end')  # Formato MM/DD/YYYY

            # Conversión solo si los valores no son nulos o vacíos
            if date_bearing not in [None, '']:
                date_bearing_new = datetime.datetime.strptime(date_bearing, '%m/%d/%Y').date()
            else:
                date_bearing_new = None

            if date_effective_coverage not in [None, '']:
                date_effective_coverage_new = datetime.datetime.strptime(date_effective_coverage, '%m/%d/%Y').date()
            else:
                date_effective_coverage_new = None

            if date_effective_coverage_end not in [None, '']:
                date_effective_coverage_end_new = datetime.datetime.strptime(date_effective_coverage_end, '%m/%d/%Y').date()
            else:
                date_effective_coverage_end_new = None

            # Recibir el valor seleccionado del formulario
            selected_profiling = request.POST.get('statusObama')

            sw = True

            # Recorrer los usuarios
            for list_drows in list_drow:
                # Comparar el valor seleccionado con el username de cada usuario
                if selected_profiling == 'ACTIVE' or selected_profiling == 'SELF-ENROLMENT':
                    color = 3
                    sw = False
                    break  # Si solo te interesa el primer match, puedes salir del bucle
            
            for list_drows in list_drow:
                if selected_profiling == list_drows.profiling_obama:
                    if selected_profiling != 'ACTIVE':
                        color = 2
                        sw = False
                        break
            
            
            statusRed = ['CANCELED','SALE FALL','PRICING ISSUE','CUSTOMER CANCELED','OTHER PARTY']

            if selected_profiling in statusRed:
                sw = False
                color = 4     

            if cleaned_obamacare_data['profiling'] is not None:
                profiling_date = timezone.now().date()
                profiling = cleaned_obamacare_data['profiling']
            else:
                profiling_date = obamacare.profiling_date
                profiling = obamacare.profiling


            if selected_profiling is not None:  # Solo actualizamos profiling_date si profiling no es None                 
                statusObama = cleaned_obamacare_data['statusObama']
            else:
                statusObama = obamacare.status  # Mantener el valor anterior si profiling es None                 
                sw = False

            if sw :
                color = 1   

            # Actualizar ObamaCare
            ObamaCare.objects.filter(id=obamacare_id).update(
                taxes=cleaned_obamacare_data['taxes'],
                agent_usa=cleaned_obamacare_data['agent_usa_obamacare'],
                plan_name=cleaned_obamacare_data['planName'],
                carrier=cleaned_obamacare_data['carrierObama'],
                profiling=profiling,
                policyNumber=cleaned_obamacare_data['policyNumber'],
                profiling_date=profiling_date,  # Se actualiza solo si profiling no es None - DannyZz
                subsidy=cleaned_obamacare_data['subsidy'],
                ffm=int(cleaned_obamacare_data['ffm']) if cleaned_obamacare_data['ffm'] else None,
                required_bearing=cleaned_obamacare_data['required_bearing'],
                date_bearing=date_bearing_new,
                doc_income=cleaned_obamacare_data['doc_income'],
                status_color = color,
                doc_migration=cleaned_obamacare_data['doc_migration'],
                status=statusObama,
                work=cleaned_obamacare_data['work'],
                premium=cleaned_obamacare_data['premium'],
                date_effective_coverage=date_effective_coverage_new,
                date_effective_coverage_end=date_effective_coverage_end_new,
                observation=cleaned_obamacare_data['observationObama']
            )
           
            if banderaCard:
                dateCard = letterCard.dateCard
                cards = letterCard.card                
            else:
                dateCard = timezone.now().date()
                cards = json.loads(request.POST.get('card', 'false').lower())  

            if banderaLetters:
                dateLetters = letterCard.dateLetters
                letters = letterCard.letters 
            else:
                dateLetters = timezone.now().date() 
                letters = json.loads(request.POST.get('letters', 'false').lower())

            if not banderaCard or banderaLetters:
                idPost = request.POST.get('letterCardID')
            else:
                idPost = None

            if not newLetterCard:      

                if idPost:

                    LettersCard.objects.filter(id = idPost).update(
                    obamacare=obamacare,
                    agent_create=request.user,
                    letters=letters,
                    dateLetters = dateLetters,
                    card=cards,
                    dateCard = dateCard )

                else:

                    LettersCard.objects.create(
                    obamacare=obamacare,
                    agent_create=request.user,
                    letters=letters,
                    dateLetters = dateLetters,
                    card=cards,
                    dateCard = dateCard )

            if way == 1:
                if obamacare.created_at > fechaLimite:
                    return redirect('clientObamacare')
                else:
                    return redirect('clientObamacarePass')
            else:
                return redirect('clientAccionRequired')

        elif action == 'save_observation_agent':
            
            obs = request.POST.get('obs_agent')

            if obs:
                id_client = request.POST.get('id_client')
                client = Clients.objects.get(id=id_client)
                id_obama = ObamaCare.objects.get(id=obamacare_id)
                id_user = request.user

                # Crear y guardar la observación
                ObservationAgent.objects.create(
                    client=client,
                    obamaCare=id_obama,
                    user=id_user,
                    content=obs
                )
            
            if way == 1:
                if obamacare.created_at > fechaLimite:
                    return redirect('clientObamacare')
                else:
                    return redirect('clientObamacarePass')
            else:
                return redirect('clientAccionRequired')      
        
    obamacare.subsidy = f"{float(obamacare.subsidy):.2f}"
    obamacare.premium = f"{float(obamacare.premium):.2f}"

    # Obtener los agentes disponibles.
    if request.user.role == 'S' or request.user.is_superuser or request.user.is_staff:
        agents = Users.objects.filter(is_active=True, is_staff=False, company=request.user.company)
    else:
        agents = None

    # Obtener los mensajes de texto del Cliente.
    if request.user.is_superuser:
        contact = Contacts.objects.filter(phone_number=obamacare.client.phone_number, company=obamacare.company.id).first()
    elif obamacare.agent_usa in request.user.agent_seguro.values_list('name', flat=True):
    # Tiene relación con el agente aunque no sea de su compañía
        contact = Contacts.objects.filter(phone_number=obamacare.client.phone_number, company_id=obamacare.company.id).first()
    else:
        contact = Contacts.objects.filter(phone_number=obamacare.client.phone_number, company=company_id).first()


    chat = Chat.objects.filter(contact=contact)
    if chat:
        messages = Messages.objects.filter(chat=chat[0].id)
        secretKey = SecretKey.objects.filter(contact=contact.id).first()
        chat = get_last_message_for_chats(chat)[0]
    else:
        messages = None
        secretKey = None
    
    context = {
        'obamacare': obamacare,
        'formatted_social':formatted_social,
        'users': users,
        'usersActive' : usersActive,
        'userInactive' : userInactive,
        'obsObamaText': '\n'.join([f"{obs.content} - {obs.user.first_name} {obs.user.last_name}  - {obs.created_at.strftime('%b %d, %Y')}"for obs in obsObama]),
        'obsCustomer': obsCus,
        'list_drow': list_drow,
        'dependents' : dependents,
        'consent': consent,
        'income': income,
        'document' : document,
        'documentObama' : documentObama,
        'percentage': percentage,
        'letterCard': letterCard,
        'apppointment' : apppointment,
        'userCarrier': userCarrier,
        'c':c,
        'accionRequired': accionRequired,
        'way': way,
        'description' : description,
        'old' : old,
        'paymentDateObama': paymentDateObama,
        'incomeffm':incomeffm,
        'complaint':complaint,
        'smsTemplate': smsTemplate,
        'smsTemplateAll' : smsTemplateAll,
        'temporalyURL' : temporalyURL,
        'fechaLimite' : fechaLimite,
        'renovation' : renovation,
        'agentUsa' : agentUsa,
        #SMS Blue
        'contact':contact,
        'chat':chat,
        'messages':messages,
        'secretKey':secretKey,
        'companyInsurance':getCompanyPerAgent(obamacare.agent_usa),
        'paymentsSummary': getPaymentsSummary(obamacare.id),
        'agents': agents
    }

    return render(request, 'edit/editObama.html', context)

def getPaymentsSummary(obamacareId):
    summary = defaultdict(lambda: {
        "oneil": 0,
        "lapeira": 0,
        "carrier": False,
        "sherpa": False
    })

    # Inicializar todos los meses con ceros
    for i in range(1, 13):
        month = calendar.month_abbr[i].lower()
        summary[month]  # Esto ejecuta el lambda y deja el mes listo con todos ceros

    # Oneil y Lapeira
    oneilPayments = PaymentsOneil.objects.filter(obamacare_id=obamacareId).order_by("coverageMonth", "-created_at")

    seenLapeiraMonths = set()
    seenOneilMonths = set()

    for payment in oneilPayments:
        month = calendar.month_abbr[payment.coverageMonth.month].lower()
        if payment.agency.lower() == "lapeira & associates llc":
            if month not in seenLapeiraMonths:
                summary[month]["lapeira"] = float(payment.payable)
                seenLapeiraMonths.add(month)
        else:
            if month not in seenOneilMonths:
                summary[month]["oneil"] = float(payment.payable)
                seenOneilMonths.add(month)

    # Carrier
    carrierPayments = PaymentsCarriers.objects.filter(obamacare_id=obamacareId).order_by("coverageMonth", "-created_at")
    seenCarrierMonths = set()

    for payment in carrierPayments:
        month = calendar.month_abbr[payment.coverageMonth.month].lower()
        if month not in seenCarrierMonths:
            summary[month]["carrier"] = payment.is_active
            seenCarrierMonths.add(month)

    # Sherpa
    sherpaPayments = PaymentsSherpa.objects.filter(obamacare_id=obamacareId).order_by("coverageMonth", "-created_at")
    seenSherpaMonths = set()

    for payment in sherpaPayments:
        month = calendar.month_abbr[payment.coverageMonth.month].lower()
        if month not in seenSherpaMonths:
            summary[month]["sherpa"] = payment.is_active
            seenSherpaMonths.add(month)

    # Retornar los meses en orden (enero a diciembre)
    orderedSummary = {
        calendar.month_abbr[i].lower(): summary[calendar.month_abbr[i].lower()]
        for i in range(1, 13)
    }

    return orderedSummary

def getPaymentsSuplementalSummary(suppId):
    summary = defaultdict(lambda: {
        "status": None,
        "payment": None,
    })

    # Inicializar todos los meses con ceros
    for i in range(1, 13):
        month = calendar.month_abbr[i].lower()
        summary[month]  # Esto ejecuta el lambda y deja el mes listo con todos ceros

    suplementalsStatuses = StatusSuplementals.objects.filter(supp_id=suppId).order_by("coverageMonth", "-created_at")
    suplementalsPayments = PaymentsSuplementals.objects.filter(supp_id=suppId).order_by("coverageMonth", "-created_at")
    seenStatusMonths = set()
    seePaymentsMonths = set()

    for status in suplementalsStatuses:
        month = calendar.month_abbr[status.coverageMonth.month].lower()
        if month not in seenStatusMonths:
            summary[month]["status"] = status.is_active
            seenStatusMonths.add(month)

    for payment in suplementalsPayments:
        month = calendar.month_abbr[payment.coverageMonth.month].lower()
        if month not in seePaymentsMonths:
            summary[month]["payment"] = payment.is_active
            seePaymentsMonths.add(month)

    # Retornar los meses en orden (enero a diciembre)
    orderedSummary = {
        calendar.month_abbr[i].lower(): summary[calendar.month_abbr[i].lower()]
        for i in range(1, 13)
    }

    return orderedSummary

def usernameCarrier(request, obamacare):

    obama = ObamaCare.objects.filter(id=obamacare).first()   
    id = request.POST.get('usernameCarrierID') 
    if id: userrCarrier = UserCarrier.objects.filter(id = id)
    username_carrier = request.POST.get('usernameCarrier') 
    password_carrier = request.POST.get('passwordCarrier')  

    if username_carrier is not None and password_carrier is not None:

        # Conversión solo si los valores no son nulos o vacíos
        if username_carrier is not None and password_carrier is not None:
            date = timezone.now().date()
        else:
            username_carrier = userrCarrier.username_carrier
            password_carrier = userrCarrier.password_carrier
            date = userrCarrier.dateUserCarrier

        if id:
            UserCarrier.objects.filter(id = id).update(
            obamacare = obama,
            agent_create=request.user,
            username_carrier=username_carrier,
            password_carrier = password_carrier,
            dateUserCarrier=date 
            )      

        else:

            UserCarrier.objects.create(
            obamacare=obama,
            agent_create=request.user,
            username_carrier=username_carrier,
            password_carrier = password_carrier,
            dateUserCarrier=date  
            )

@login_required(login_url='/login')
@company_ownership_required(model_name="Supp", id_field="supp_id")
def editSupp(request, supp_id):

    company_id = request.user.company.id

    supp = Supp.objects.select_related('client','agent').filter(id=supp_id).first()
    obsSupp = ObservationAgent.objects.filter(supp=supp_id)
    obsCus = ObservationCustomer.objects.select_related('agent').filter(client=supp.client.id)
    list_drow = DropDownList.objects.filter(profiling_supp__isnull=False)
    paymentDateSupp = PaymentDate.objects.filter(supp = supp).first()
    users = Users.objects.filter(role='SUPP', company = company_id, is_active = True)
    documentSupp = DocumentObamaSupp.objects.filter(supp = supp)
    cignaSuplemental = CignaSuplemental.objects.filter(supp = supp_id )

    # Obtener el objeto Supp que tiene el id `supp_id`
    supp_instance = Supp.objects.get(id=supp_id)

    # Obtener todos los dependientes asociados a este Supp
    dependents = supp_instance.dependents.all()
    
    action = request.POST.get('action')
  
    social_number = supp.client.social_security  # Campo real del modelo
    # Asegurarse de que social_number no sea None antes de formatear
    if social_number:
        formatted_social = f"xxx-xx-{social_number[-4:]}"  # Obtener el formato deseado
    else:
        formatted_social = "N/A"  # Valor predeterminado si no hay número disponible

    #calculo de edad
    hoy = timezone.now().date()
    old = ''
    if supp.client.date_birth:
        old = hoy.year - supp.client.date_birth.year - ((hoy.month, hoy.day) < (supp.client.date_birth.month, supp.client.date_birth.day)) 

    
    if company_id == 1:
        agentUsa = USAgent.objects.all().prefetch_related("company")
    else:
        agentUsa = USAgent.objects.filter(company = request.user.company).prefetch_related("company")


    if request.method == 'POST':

        if action == 'save_supp':

            editClient(request, supp.client.id)
            dependents = editDepentsSupp(request, supp_id)

            #formateo de fecha para guardalar como se debe en BD ya que la obtengo USA
            date_effective_coverage = request.POST.get('date_effective_coverage')  # Formato MM/DD/YYYY
            date_effective_coverage_end = request.POST.get('date_effective_coverage_end')  # Formato MM/DD/YYYY
            effectiveDateSupp = request.POST.get('effectiveDateSupp')  # Formato MM/DD/YYYY


            # Si la fecha no viene vacia la convertimos y si viene vacia la colocamos null
            if date_effective_coverage not in [None, '']:
                date_effective_coverage_new = datetime.datetime.strptime(date_effective_coverage, '%m/%d/%Y').date()
            else:
                date_effective_coverage_new = None

            if date_effective_coverage_end not in [None, '']:
                date_effective_coverage_end_new = datetime.datetime.strptime(date_effective_coverage_end, '%m/%d/%Y').date()
            else:
                date_effective_coverage_end_new = None

            if effectiveDateSupp not in [None, '']:
                effectiveDateSupp_new = datetime.datetime.strptime(effectiveDateSupp, '%m/%d/%Y').date()
            else:
                effectiveDateSupp_new = None
            
                
            # Campos de Supp
            supp_fields = [
                'effectiveDateSupp', 'carrierSuple', 'premiumSupp', 'preventiveSupp', 'coverageSupp', 'deducibleSupp',
                'statusSupp', 'typePaymeSupp', 'observationSuple', 'agent_usa','policyNumber'
            ]
            
            # Limpiar los campos de ObamaCare convirtiendo los vacíos en None
            cleaned_supp_data = clean_fields_to_null(request, supp_fields)

            # Recibir el valor seleccionado del formulario
            selected_status= request.POST.get('statusSupp')

            color = 1         

            for list_drow in list_drow:
                if selected_status == list_drow.profiling_supp:
                    if selected_status != 'ACTIVE':
                        color = 2
                        break         
                    if selected_status == 'ACTIVE' or selected_status == 'SELF-ENROLMENT':
                        color = 3 
                        break  
            
            statusRed = ['BANK DRAFT CANCELLED - CUSTOMER REQUEST','TERM - INSURED REQUEST','TERM - LAPSE NON PAYMENT'
                         ,'AUTOMATIC TERMINATION','TERM - INSURED REQUEST (PAYMENT ERROR)','WITHDRAWN (PAYMENT ERROR)']

            if selected_status in statusRed:
                color = 4   


            # Actualizar Supp
            Supp.objects.filter(id=supp_id).update(
                effective_date=effectiveDateSupp_new,
                agent_usa=cleaned_supp_data['agent_usa'],
                carrier=cleaned_supp_data['carrierSuple'],
                premium=cleaned_supp_data['premiumSupp'],
                preventive=cleaned_supp_data['preventiveSupp'],
                coverage=cleaned_supp_data['coverageSupp'],
                deducible=cleaned_supp_data['deducibleSupp'],
                status=cleaned_supp_data['statusSupp'],
                policyNumber=cleaned_supp_data['policyNumber'],
                status_color=color,
                date_effective_coverage=date_effective_coverage_new,
                date_effective_coverage_end=date_effective_coverage_end_new,
                payment_type=cleaned_supp_data['typePaymeSupp'],
                observation=cleaned_supp_data['observationSuple']
            )

            return redirect('clientSupp' )  
              
        elif action == 'save_supp_agent':

            obs = request.POST.get('obs_agent')

            if obs:
                id_client = request.POST.get('id_client')
                client = Clients.objects.get(id=id_client)
                id_supp = Supp.objects.get(id=supp_id)
                id_user = request.user

                # Crear y guardar la observación
                ObservationAgent.objects.create(
                    client=client,
                    supp=id_supp,
                    user=id_user,
                    content=obs
                )
            
                return redirect('clientSupp')
            
    supp.premium = f"{float(supp.premium):.2f}"

    # Obtener los mensajes de texto del Cliente.
    if request.user.is_superuser:
        contact = Contacts.objects.filter(phone_number=supp.client.phone_number, company_id=supp.company.id).first()
    elif supp.agent_usa in request.user.agent_seguro.values_list('name', flat=True):
    # Tiene relación con el agente aunque no sea de su compañía
        contact = Contacts.objects.filter(phone_number=supp.client.phone_number, company_id=supp.company.id).first()
    else:
        contact = Contacts.objects.filter(phone_number=supp.client.phone_number, company_id=company_id).first()

    chat = Chat.objects.filter(contact=contact)
    if chat:
        messages = Messages.objects.filter(chat_id=chat[0].id)
        secretKey = SecretKey.objects.filter(contact_id=contact.id).first()
        chat = get_last_message_for_chats(chat)[0]
    else:
        messages = None
        secretKey = None

    # Obtener los agentes disponibles.
    if request.user.role == 'S' or request.user.is_superuser or request.user.is_staff:
        agents = Users.objects.filter(is_active=True, is_staff=False, company=request.user.company)
    else:
        agents = None


    context = {
        'supps': supp,
        'formatted_social':formatted_social,
        'dependents': dependents,
        'obsSuppText': '\n'.join([obs.content for obs in obsSupp]),
        'obsCustomer': obsCus,
        'list_drow': list_drow,
        'old' : old,
        'paymentDateSupp' : paymentDateSupp,
        'users' : users,
        'documentSupp' : documentSupp,
        'agentUsa' : agentUsa,
        'cignaSuplemental' : cignaSuplemental,
        #SMS Blue
        'contact':contact,
        'chat':chat,
        'messages':messages,
        'secretKey':secretKey,
        'paymentsSummary':getPaymentsSuplementalSummary(supp_id),
        'agents': agents,
    }
    
    return render(request, 'edit/editSupp.html', context)

@login_required(login_url='/login')
@company_ownership_required(model_name="ClientsAssure", id_field="assure_id")
def editAssure(request, assure_id):

    company_id = request.user.company.id

    assure = ClientsAssure.objects.select_related('agent').filter(id=assure_id).first()
    obsAssure = ObservationAgent.objects.filter(assure=assure_id)
    obsCus = ObservationCustomer.objects.select_related('agent').filter(assure=assure_id)
    list_drow = DropDownList.objects.filter(profiling_supp__isnull=False)
    paymentDateAssure = PaymentDate.objects.filter(assure = assure_id).first()
    users = Users.objects.filter(role='SUPP', company = company_id, is_active = True)

    if request.user.is_superuser:
        agentUsa = USAgent.objects.all().prefetch_related("company")
    else:
        agentUsa = USAgent.objects.filter(company = request.user.company).prefetch_related("company")

    # Obtener todos los dependientes asociados a este Supp
    dependents = DependentsAssure.objects.filter(client = assure_id)
  
    social_number = assure.social_security  # Campo real del modelo
    # Asegurarse de que social_number no sea None antes de formatear
    if social_number:
        formatted_social = f"xxx-xx-{social_number[-4:]}"  # Obtener el formato deseado
    else:
        formatted_social = "N/A"  # Valor predeterminado si no hay número disponible

    action = request.POST.get('action')

    #calculo de edad
    hoy = timezone.now().date()
    old = hoy.year - assure.date_birth.year - ((hoy.month, hoy.day) < (assure.date_birth.month, assure.date_birth.day)) 

    paises = []  # Inicializa la lista por si hay error

    try:
        url = "https://raw.githubusercontent.com/Dinuks/country-nationality-list/master/countries.json"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())

            for country in sorted(data, key=lambda x: x.get('en_short_name', '')):
                nombre = country.get('en_short_name', 'N/A')
                gentilicio = country.get('nationality', 'N/A')
                paises.append({
                    "nombre": nombre,
                    "gentilicio": gentilicio
                })

    except Exception as e:
        paises = []  # O podrías cargar valores por defecto si lo prefieres   


    if request.method == 'POST':

        if action == 'saveAssure':

            #formateo de fecha para guardalar como se debe en BD ya que la obtengo USA
            date_effective_coverage = request.POST.get('date_effective_coverage')  # Formato MM/DD/YYYY
            date_effective_coverage_end = request.POST.get('date_effective_coverage_end')  # Formato MM/DD/YYYY
            date_birth = request.POST.get('date_birth')  # Formato MM/DD/YYYY

            # Si la fecha no viene vacia la convertimos y si viene vacia la colocamos null
            if date_effective_coverage not in [None, '']:
                date_effective_coverage_new = datetime.datetime.strptime(date_effective_coverage, '%m/%d/%Y').date()
            else:
                date_effective_coverage_new = None

            if date_effective_coverage_end not in [None, '']:
                date_effective_coverage_end_new = datetime.datetime.strptime(date_effective_coverage_end, '%m/%d/%Y').date()
            else:
                date_effective_coverage_end_new = None  

            if date_birth not in [None, '']:
                date_birth_new = datetime.datetime.strptime(date_birth, '%m/%d/%Y').date()
            else:
                date_birth_new = None 
                
            # Campos de Supp
            assure_fields = [
                'agent_usa', 'first_name', 'last_name','phone_number','email','address','zipcode','city','state','county',
                'sex','migration_status','nationality','status','policyNumber','payment_type'
            ]
            
            # Limpiar los campos de ObamaCare convirtiendo los vacíos en None
            cleaned_assure_data = clean_fields_to_null(request, assure_fields)

            # Recibir el valor seleccionado del formulario
            selected_status= request.POST.get('statusAssure')

            color = 1         

            for list_drow in list_drow:
                if selected_status == list_drow.profiling_supp:
                    if selected_status != 'ACTIVE':
                        color = 2
                        break         
                    if selected_status == 'ACTIVE' or selected_status == 'SELF-ENROLMENT':
                        color = 3 
                        break  
            
            statusRed = ['BANK DRAFT CANCELLED - CUSTOMER REQUEST','TERM - INSURED REQUEST','TERM - LAPSE NON PAYMENT'
                            ,'AUTOMATIC TERMINATION','TERM - INSURED REQUEST (PAYMENT ERROR)','WITHDRAWN (PAYMENT ERROR)']

            if selected_status in statusRed:
                color = 4   
        

            # Actualizar Supp
            ClientsAssure.objects.filter(id=assure_id).update(
                agent_usa=cleaned_assure_data['agent_usa'],
                first_name=cleaned_assure_data['first_name'],
                last_name=cleaned_assure_data['last_name'],
                phone_number=cleaned_assure_data['phone_number'],
                email=cleaned_assure_data['email'],
                address=cleaned_assure_data['address'],
                zipcode=cleaned_assure_data['zipcode'],
                city=cleaned_assure_data['city'],
                state=cleaned_assure_data['state'],
                county=cleaned_assure_data['county'],
                nationality=cleaned_assure_data['nationality'],
                sex=cleaned_assure_data['sex'],
                migration_status=cleaned_assure_data['migration_status'],
                status=cleaned_assure_data['status'],
                status_color=color,
                date_birth=date_birth_new,
                date_effective_coverage=date_effective_coverage_new,
                date_effective_coverage_end=date_effective_coverage_end_new,
                policyNumber=cleaned_assure_data['policyNumber'],
                payment_type=cleaned_assure_data['payment_type'],
            )

            return redirect('clientAssure' )  

        if action == 'saveAssureAgent':

            obs = request.POST.get('obs_agent')

            if obs:
                id_assure = ClientsAssure.objects.get(id=assure_id)
                id_user = request.user

                # Crear y guardar la observación
                ObservationAgent.objects.create(
                    assure=id_assure,
                    user=id_user,
                    content=obs
                )
            
                return redirect('clientAssure')
            
    # Obtener los mensajes de texto del Cliente.
    if request.user.is_superuser:
        contact = Contacts.objects.filter(phone_number=assure.phone_number, company_id=assure.company.id).first()
    elif assure.agent_usa in request.user.agent_seguro.values_list('name', flat=True):
    # Tiene relación con el agente aunque no sea de su compañía
        contact = Contacts.objects.filter(phone_number=assure.phone_number, company_id=assure.company.id).first()
    else:
        contact = Contacts.objects.filter(phone_number=assure.phone_number, company_id=company_id).first()

    chats = Chat.objects.filter(contact=contact)
    messages = Messages.objects.filter(chat_id=chats[0].id)
    secretKey = SecretKey.objects.filter(contact_id=contact.id).first()
    chat = get_last_message_for_chats(chats)[0]

    context = {
        'assure': assure,
        'paises' : paises,
        'formatted_social':formatted_social,
        'dependents': dependents,
        'obsSuppText': '\n'.join([obs.content for obs in obsAssure]),
        'obsCustomer': obsCus,
        'list_drow': list_drow,
        'old' : old,
        'paymentDateAssure' : paymentDateAssure,
        'users' : users,
        'agentUsa' : agentUsa,
        #SMS Blue
        'contact':contact,
        'chat':chat,
        'messages':messages,
        'secretKey':secretKey
    }
    
    return render(request, 'edit/editAssure.html', context)

@login_required(login_url='/login')
@company_ownership_required(model_name="ClientsLifeInsurance", id_field="client_id")
def editLife(request, client_id):

    company_id = request.user.company.id

    client = ClientsLifeInsurance.objects.select_related('agent').filter(id=client_id).first()
    obsCus = ObservationCustomer.objects.select_related('agent').filter(life_insurance=client_id)
    obsLife = ObservationAgent.objects.filter(life_insurance=client_id)
    paymentDateLife = PaymentDate.objects.filter(life_insurance = client_id).first()
    list_drow = DropDownList.objects.filter(profiling_supp__isnull=False)
    consent = Consents.objects.filter(lifeInsurance = client_id )

    if request.user.is_superuser:
        agentUsa = USAgent.objects.all().prefetch_related("company")
    else:
        agentUsa = USAgent.objects.filter(company = request.user.company).prefetch_related("company")

    action = request.POST.get('action')

    #calculo de edad
    hoy = timezone.now().date()
    old = ''
    if client.date_birth:
        old = hoy.year - client.date_birth.year - ((hoy.month, hoy.day) < (client.date_birth.month, client.date_birth.day)) 


    social_number = client.social_security  # Campo real del modelo
    # Asegurarse de que social_number no sea None antes de formatear
    if social_number:
        formatted_social = f"xxx-xx-{social_number[-4:]}"  # Obtener el formato deseado
    else:
        formatted_social = "N/A"  # Valor predeterminado si no hay número disponible

    if request.method == 'POST':

        if action == 'saveLife':

            #formateo de fecha para guardalar como se debe en BD ya que la obtengo USA
            date_effective_coverage = request.POST.get('date_effective_coverage')  # Formato MM/DD/YYYY
            date_effective_coverage_end = request.POST.get('date_effective_coverage_end')  # Formato MM/DD/YYYY
            date_birth = request.POST.get('date_birth')  # Formato MM/DD/YYYY

            # Si la fecha no viene vacia la convertimos y si viene vacia la colocamos null
            if date_effective_coverage not in [None, '']:
                date_effective_coverage_new = datetime.datetime.strptime(date_effective_coverage, '%m/%d/%Y').date()
            else:
                date_effective_coverage_new = None

            if date_effective_coverage_end not in [None, '']:
                date_effective_coverage_end_new = datetime.datetime.strptime(date_effective_coverage_end, '%m/%d/%Y').date()
            else:
                date_effective_coverage_end_new = None  

            if date_birth not in [None, '']:
                date_birth_new = datetime.datetime.strptime(date_birth, '%m/%d/%Y').date()
            else:
                date_birth_new = None 
                
            # Campos de Supp
            life_fields = [
                'agent_usa', 'full_name','phone_number','address','zipcode','city','state','county',
                'sex','status','policyNumber','payment_type', 'face_amount', 'addicional_protector', 'premium'
            ]
            
            # Limpiar los campos de ObamaCare convirtiendo los vacíos en None
            cleaned_life_data = clean_fields_to_null(request, life_fields)

            # Recibir el valor seleccionado del formulario
            selected_status= request.POST.get('statusLife')

            color = 1         

            for list_drow in list_drow:
                if selected_status == list_drow.profiling_supp:
                    if selected_status != 'ACTIVE':
                        color = 2
                        break         
                    if selected_status == 'ACTIVE' or selected_status == 'SELF-ENROLMENT':
                        color = 3 
                        break  
            
            statusRed = ['BANK DRAFT CANCELLED - CUSTOMER REQUEST','TERM - INSURED REQUEST','TERM - LAPSE NON PAYMENT'
                            ,'AUTOMATIC TERMINATION','TERM - INSURED REQUEST (PAYMENT ERROR)','WITHDRAWN (PAYMENT ERROR)']

            if selected_status in statusRed:
                color = 4   
        

            # Actualizar Supp
            ClientsLifeInsurance.objects.filter(id=client_id).update(
                agent_usa=cleaned_life_data['agent_usa'],
                full_name=cleaned_life_data['full_name'],
                phone_number=cleaned_life_data['phone_number'],
                address=cleaned_life_data['address'],
                zipcode=cleaned_life_data['zipcode'],
                city=cleaned_life_data['city'],
                state=cleaned_life_data['state'],
                county=cleaned_life_data['county'],
                sex=cleaned_life_data['sex'],
                status=cleaned_life_data['status'],
                status_color=color,
                date_birth=date_birth_new,
                date_effective_coverage=date_effective_coverage_new,
                date_effective_coverage_end=date_effective_coverage_end_new,
                policyNumber=cleaned_life_data['policyNumber'],
                payment_type=cleaned_life_data['payment_type'],
                face_amount=cleaned_life_data['face_amount'],
                addicional_protector=cleaned_life_data['addicional_protector'],
                premium=cleaned_life_data['premium'],
            )

            return redirect('clientLifeInsurance' )  

        if action == 'saveLifeAgent':

            obs = request.POST.get('obs_agent')

            if obs:
                id_life = ClientsLifeInsurance.objects.get(id=client_id)
                id_user = request.user

                # Crear y guardar la observación
                ObservationAgent.objects.create(
                    life_insurance=id_life,
                    user=id_user,
                    content=obs
                )
            
                return redirect('clientLifeInsurance')
        

    # Obtener los mensajes de texto del Cliente.
    if request.user.is_superuser:
        contact = Contacts.objects.filter(phone_number=client.phone_number, company_id=client.company.id).first()
    elif client.agent_usa in request.user.agent_seguro.values_list('name', flat=True):
        # Tiene relación con el agente aunque no sea de su compañía
        contact = Contacts.objects.filter(phone_number=client.phone_number, company_id=client.company.id).first()
    else:
        contact = Contacts.objects.filter(phone_number=client.phone_number, company_id=company_id).first()

    chats = Chat.objects.filter(contact=contact)
    messages = Messages.objects.filter(chat_id=chats[0].id)
    secretKey = SecretKey.objects.filter(contact_id=contact.id).first()
    chat = get_last_message_for_chats(chats)[0]


    context = {
        'client': client,
        'consent':consent,
        'formatted_social':formatted_social,
        'obsSuppText': '\n'.join([obs.content for obs in obsLife]),
        'obsCustomer': obsCus,
        'list_drow': list_drow,
        'old' : old,
        'paymentDateLife':paymentDateLife,
        'agentUsa' : agentUsa,
        #SMS Blue
        'contact':contact,
        'chat':chat,
        'messages':messages,
        'secretKey':secretKey
    }
    
    return render(request, 'edit/editLife.html', context)

def editDepentsObama(request, obamacare_id):
    # Obtener todos los dependientes asociados al ObamaCare
    dependents = Dependents.objects.filter(obamacare=obamacare_id)

    if request.method == "POST":
        for dependent in dependents:

            # Resetear la fecha guardarla como se debe porque la traigo en formato USA
            date_birth = request.POST.get(f'dateBirthDependent_{dependent.id}')

            # Conversión solo si los valores no son nulos o vacíos
            if date_birth not in [None, '']:
                date_birth_new = datetime.datetime.strptime(date_birth, '%m/%d/%Y').date()
            else:
                date_birth_new = None
            

            # Obtener los datos enviados por cada dependiente
            dependent_id = request.POST.get(f'dependentId_{dependent.id}')
            name = request.POST.get(f'nameDependent_{dependent.id}')
            apply = request.POST.get(f'applyDependent_{dependent.id}')
            kinship = request.POST.get(f'kinship_{dependent.id}')
            migration_status = request.POST.get(f'migrationStatusDependent_{dependent.id}')
            sex = request.POST.get(f'sexDependent_{dependent.id}')
            policyNumber = request.POST.get(f'policyNumberDependent_{dependent.id}')
            
            # Verificar si el ID coincide
            if dependent.id == int(dependent_id):  # Verificamos si el ID coincide
                
                # Verificamos que todos los campos tengan datos
                if name and apply and kinship and date_birth and migration_status and sex:
                    dependent.name = name
                    dependent.apply = apply
                    dependent.kinship = kinship
                    dependent.date_birth = date_birth_new
                    dependent.migration_status = migration_status
                    dependent.sex = sex
                    dependent.policyNumber = policyNumber

                    dependent.save()

    # Retornar todos los dependientes actualizados (o procesados)
    return dependents

def editDepentsSupp(request, supp_id):
    
    # Obtener el objeto Supp que tiene el id `supp_id`
    supp_instance = Supp.objects.get(id=supp_id)

    # Obtener todos los dependientes asociados a este Supp
    dependents = supp_instance.dependents.all()

    if request.method == "POST":
        for dependent in dependents:

            date_birth = request.POST.get(f'dateBirthDependent_{dependent.id}')
            dateNew = datetime.datetime.strptime(date_birth, '%m/%d/%Y').date() if date_birth not in [None, ''] else None

            # Aquí obtenemos los datos enviados a través del formulario para cada dependiente
            dependent_id = request.POST.get(f'dependentId_{dependent.id}')  # Cambiar a 'dependentId_{dependent.id}'
            
            if dependent_id is None:
                continue  # Si no se encuentra el dependentId, continuamos con el siguiente dependiente
            
            # Verificamos si el dependent_id recibido coincide con el ID del dependiente actual
            if dependent.id == int(dependent_id):
                name = request.POST.get(f'nameDependent_{dependent.id}')
                apply = request.POST.get(f'applyDependent_{dependent.id}')
                kinship = request.POST.get(f'kinship_{dependent.id}')
                date_birth = request.POST.get(f'dateBirthDependent_{dependent.id}')
                migration_status = request.POST.get(f'migrationStatusDependent_{dependent.id}')
                sex = request.POST.get(f'sexDependent_{dependent.id}')
                
                
                # Verificamos si los demás campos existen y no son None
                if name and apply and kinship and date_birth and migration_status and sex:
                    # Actualizamos los campos del dependiente
                    dependent.name = name
                    dependent.apply = apply
                    dependent.kinship = kinship
                    dependent.date_birth = dateNew
                    dependent.migration_status = migration_status
                    dependent.sex = sex
                    
                    # Guardamos el objeto dependiente actualizado
                    dependent.save()
    
    # Retornar los dependientes que fueron actualizados o procesados
    return dependents

def clean_field_to_null(value):
    """
    Limpia el valor de un campo. Si el valor está vacío (cadena vacía, None o solo espacios),
    devuelve `None` para que se guarde como NULL en la base de datos.
    """
    if value == '' or value is None or value.strip() == '':
        return None
    return value

def clean_fields_to_null(request, field_names):
    """
    Limpia un conjunto de campos obtenidos desde `request.POST`, 
    convirtiendo los valores vacíos en `None` (NULL en la base de datos).
    Devuelve un diccionario con los campos limpiados.
    """
    cleaned_data = {}
    for field in field_names:
        value = request.POST.get(field)
        cleaned_data[field] = clean_field_to_null(value)
    return cleaned_data

@login_required(login_url='/login')
@company_ownership_required(model_name="AgentTicketAssignment", id_field="ticket_id")
def editTicket(request, ticket_id):

    ticket = AgentTicketAssignment.objects.select_related('obamacare', 'supp', 'agent_create', 'agent_customer').filter(id = ticket_id).first()

    if request.method == 'POST':

        response = request.POST.get('response') 
        status = request.POST.get('status')  

        AgentTicketAssignment.objects.filter(id = ticket_id).update(
            response=response,
            status=status,
            end_date = timezone.now().date(),
            company=request.user.company 
        )  

        return redirect('ticketAsing')

    return render(request, 'edit/editTicket.html', {'ticket':ticket})

@login_required(login_url='/login')
@company_ownership_required(model_name="FinallExpenses", id_field="finallExpenses_id")
def editFinallExpenses(request, finallExpenses_id):

    finalExpenses = FinallExpenses.objects.select_related('agent').filter(id = finallExpenses_id).first()

    if request.method == 'POST':

        #formateo de fecha para guardalar como se debe en BD ya que la obtengo USA
        date_birth = request.POST.get('date_birth')  # Formato MM/DD/YYYY
        date_birth_new = datetime.datetime.strptime(date_birth, '%m/%d/%Y').date()

        phoneNumber = request.POST.get('phone_number')
        amount = countDigits(phoneNumber)
        if amount == 10:
            newNumber = int(f'1{phoneNumber}')
        else:
            newNumber = phoneNumber

        # Campos de ObamaCare
        finallExpenses_fields = [
            'first_name', 'last_name', 'gender', 'relationship', 'current_city', 'current_state', 'hospitalized_currently','height_ft','weight_lbs',
            'hospitalized_10_years', 'hospitalized_5_years', 'hospitalized_3_years', 'hospitalized_6_months', 'cancer_stroke_history',
            'cancer_free_2_years', 'cancer_free_5_years', 'cancer_free_10_years','tobacco_use','tobacco_bp_10_years','tobacco_5_years','tobacco_12_months'
        ]

        # Limpiar los campos de ObamaCare convirtiendo los vacíos en None
        cleaned_finallExpenses_data = clean_fields_to_null(request, finallExpenses_fields)

        # Actualizar ObamaCare
        FinallExpenses.objects.filter(id=finallExpenses_id).update(
            first_name=cleaned_finallExpenses_data['first_name'],
            last_name=cleaned_finallExpenses_data['last_name'],
            gender=cleaned_finallExpenses_data['gender'],
            relationship=cleaned_finallExpenses_data['relationship'],
            current_city=cleaned_finallExpenses_data['current_city'],
            current_state=cleaned_finallExpenses_data['current_state'],
            hospitalized_currently=cleaned_finallExpenses_data['hospitalized_currently'],
            hospitalized_10_years=cleaned_finallExpenses_data['hospitalized_10_years'],
            hospitalized_5_years=cleaned_finallExpenses_data['hospitalized_5_years'],
            hospitalized_3_years=cleaned_finallExpenses_data['hospitalized_3_years'],
            hospitalized_6_months=cleaned_finallExpenses_data['hospitalized_6_months'],
            cancer_stroke_history=cleaned_finallExpenses_data['cancer_stroke_history'],
            cancer_free_2_years=cleaned_finallExpenses_data['cancer_free_2_years'],
            cancer_free_5_years=cleaned_finallExpenses_data['cancer_free_5_years'],
            cancer_free_10_years=cleaned_finallExpenses_data['cancer_free_10_years'],
            tobacco_use=cleaned_finallExpenses_data['tobacco_use'],
            tobacco_bp_10_years=cleaned_finallExpenses_data['tobacco_bp_10_years'],
            tobacco_5_years=cleaned_finallExpenses_data['tobacco_5_years'],
            tobacco_12_months=cleaned_finallExpenses_data['tobacco_12_months'],
            height_ft=cleaned_finallExpenses_data['height_ft'],
            weight_lbs=cleaned_finallExpenses_data['weight_lbs'],
            date_birth=date_birth_new,
            phone_number=newNumber
        )

        return redirect('clientFinallExpenses')            

    return render(request, 'edit/editFinallExpenses.html', {'finalExpenses':finalExpenses})
    
@require_http_methods(["POST"])
def saveRenovation(request):

    try:
        
        # Obtener datos originales
        originalClientId = request.POST.get('originalClientId')
        clientIstancia = Clients.objects.get(id=originalClientId)
        
        # DATOS DEL CLIENTE
        clientData = {
            'first_name': request.POST.get('first_name', '').strip(),
            'last_name': request.POST.get('last_name', '').strip(),
            'email': request.POST.get('email', '').strip(),
            'address': request.POST.get('address', '').strip(),
            'zipcode': request.POST.get('zipcode', '').strip(),
            'city': request.POST.get('city', '').strip(),
            'state': request.POST.get('state', '').strip(),
            'county': request.POST.get('county', '').strip(),
            'sex': request.POST.get('sex', '').strip(),
            'migration_status': request.POST.get('migration_status', '').strip(),
            'apply': request.POST.get('apply', '').strip(),
            'agent_usa': request.POST.get('agent_usa', '').strip()
        }
        
        # DATOS DEL PLAN OBAMACARE
        obamacareData = {
            'agent_usa_obamacare': request.POST.get('agent_usa_obamacare', '').strip(),
            'taxes': request.POST.get('taxes', '').strip(),
            'carrier': request.POST.get('carrier', '').strip(),
            'work': request.POST.get('work', '').strip(),
            'subsidy': request.POST.get('subsidy', '').strip(),
            'doc_income': request.POST.get('doc_income', '').strip(),
            'doc_migration': request.POST.get('doc_migration', '').strip(),
            'plan_name': request.POST.get('plan_name', '').strip(),
            'premium': request.POST.get('premium', '').strip(),
            'observation': request.POST.get('observation', '').strip()
        }
        
        # DATOS DE DEPENDIENTES
        dependents_data = []
        
        # Buscar todos los campos que empiecen con 'renovation_dependent_'
        dependent_fields = {}
        for key, value in request.POST.items():
            if key.startswith('renovation_dependent_'):
                # Extraer el tipo de campo y el ID del dependiente
                # Formato esperado: renovation_dependent_[campo]_[dependent_id]
                parts = key.split('_')
                if len(parts) >= 4:
                    field_type = parts[2]  # name, apply, sex, etc.
                    dependent_id = '_'.join(parts[3:])  # Puede ser un ID complejo
                    
                    if dependent_id not in dependent_fields:
                        dependent_fields[dependent_id] = {}
                    
                    dependent_fields[dependent_id][field_type] = value.strip()
        
        # Procesar cada dependiente encontrado
        for dependent_id, fields in dependent_fields.items():
            dependent_info = {
                'dependent_id': dependent_id,
                'name': fields.get('name', ''),
                'apply': fields.get('apply', ''),
                'sex': fields.get('sex', ''),
                'kinship': fields.get('kinship', ''),
                'birth': fields.get('birth', ''),
                'age': fields.get('age', ''),
                'policy': fields.get('policy', ''),
                'migration': fields.get('migration', ''),
                'index': fields.get('index', ''),
                'is_existing': 'id' in fields,  # Si tiene 'id' es un dependiente existente
                'original_id': fields.get('id', '') if 'id' in fields else None
            }
            dependents_data.append(dependent_info)
        
        # VALIDACIONES BÁSICAS
        validation_errors = []
        
        # Validar cliente
        if not clientData['first_name']:
            validation_errors.append('El nombre es requerido')
        if not clientData['last_name']:
            validation_errors.append('El apellido es requerido')
        if not clientData['email']:
            validation_errors.append('El email es requerido')
        elif not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', clientData['email']):
            validation_errors.append('El formato del email no es válido')
        
        # Validar obamacare
        if not obamacareData['plan_name']:
            validation_errors.append('El nombre del plan es requerido')
        if not obamacareData['premium']:
            validation_errors.append('La prima es requerida')
        
        # Validar dependientes
        for i, dependent in enumerate(dependents_data):
            if dependent['name'] and not dependent['sex']:
                validation_errors.append(f'El sexo del dependiente #{i+1} es requerido')
            if dependent['name'] and not dependent['migration']:
                validation_errors.append(f'El estatus migratorio del dependiente #{i+1} es requerido')
        
        if validation_errors:
            return JsonResponse({
                'success': False,
                'errors': validation_errors,
                'message': 'Por favor corrija los errores en el formulario'
            }, status=400)
        
        #formateo de fecha para guardalar como se debe en BD ya que la obtengo USA
        fecha_str = request.POST.get('date_birth')  # Formato MM/DD/YYYY
        # Conversión solo si los valores no son nulos o vacíos
        if fecha_str not in [None, '']:
            dateNew = datetime.datetime.strptime(fecha_str, '%m/%d/%Y').date()
        else:
            dateNew = None

        # Actualizar Client
        Clients.objects.filter(id=originalClientId).update(
            agent_usa=clientData['agent_usa'],
            first_name=clientData['first_name'],
            last_name=clientData['last_name'],
            email=clientData['email'],
            address=clientData['address'],
            zipcode=clientData['zipcode'],
            city=clientData['city'],
            state=clientData['state'],
            county=clientData['county'],
            sex=clientData['sex'],
            date_birth=dateNew,
            apply=clientData['apply'],
            migration_status=clientData['migration_status']
        )        

        fecha_deseada = datetime.datetime(2025, 11, 1, 16, 15, 2, 361874)
        saveObama = ObamaCare.objects.create(
            agent_usa=obamacareData['agent_usa_obamacare'],
            taxes=obamacareData['taxes'],
            carrier=obamacareData['carrier'],
            work=obamacareData['work'],
            subsidy=obamacareData['subsidy'],
            doc_income=obamacareData['doc_income'],
            doc_migration=obamacareData['doc_migration'],
            plan_name=obamacareData['plan_name'],
            premium=obamacareData['premium'],
            observation=obamacareData['observation'],
            profiling='PENDING',
            status='IN PROGRESS',
            status_color = 1,
            agent = request.user,
            client = clientIstancia,
            is_active = True,
            company = request.user.company            
        )

        #ESTO SE TENIE QUE BORRAR EL PRIMERO DE NOVIEMBRE
        ObamaCare.objects.filter(id=saveObama.id).update(
            created_at = fecha_deseada
        )
        
        for dep in dependents_data:
            # Validar datos antes de convertir
            birthDate = dep['birth'] or None

            if birthDate not in [None, '']:
                dateNew = datetime.datetime.strptime(birthDate, '%m/%d/%Y').date()
            else:
                dateNew = None

            existingDep = Dependents.objects.filter(
                client=originalClientId,
                name=dep['name'],
                apply=dep['apply'],
                sex=dep['sex'],
                kinship=dep['kinship'],
                date_birth=dateNew,
                migration_status=dep['migration'],
                type_police='ACA'
            ).first()

            if existingDep:
                existingDep.obamacare.add(saveObama)  

            else:
                newDep = Dependents.objects.create(
                    client_id=originalClientId,
                    name=dep['name'],
                    apply=dep['apply'],
                    sex=dep['sex'],
                    policyNumber=dep['policy'],
                    kinship=dep['kinship'],
                    date_birth=dateNew,
                    migration_status=dep['migration'],
                    type_police='ACA'
                )
                newDep.obamacare.add(saveObama)
        
        return redirect('editObama', saveObama.id ,1 )
    
    except Exception as e:
        print(e)
        return render(request, "auth/404.html", {"message": "Error al guardar, revisar formulario."})
        




