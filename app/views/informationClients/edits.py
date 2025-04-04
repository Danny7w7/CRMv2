# Standard Python libraries
import calendar
import datetime
import json

# Django utilities
from django.http import JsonResponse

# Django core libraries
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

# Application-specific imports
from app.models import *
from app.modelsSMS import *
from ...forms import *
from ..sms import get_last_message_for_chats
from ..decoratorsCompany import *

@login_required(login_url='/login') 
def formEditClient(request, client_id):
    
    client = get_object_or_404(Clients, id=client_id)        

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
        'client': client
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
        'old' : old

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
        phone_number=cleaned_client_data['phone_number'],
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
    dependents = Dependents.objects.select_related('obamacare').filter(obamacare=obamacare)
    letterCard = LettersCard.objects.filter(obamacare = obamacare_id).first()
    apppointment = AppointmentClient.objects.select_related('obamacare','agent_create').filter(obamacare = obamacare_id)
    userCarrier = UserCarrier.objects.filter(obamacare = obamacare_id).first()
    accionRequired = CustomerRedFlag.objects.filter(obamacare = obamacare)    
    paymentDateObama = paymentDate.objects.filter(obamacare = obamacare).first()
        
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

    #Obtener todos los registros de meses pagados de la poliza
    monthsPaid = Payments.objects.filter(obamaCare=obamacare.id)

    #calculo de documente
    obamaDocumente = True if obamacare.doc_migration and obamacare.doc_income else False 

    #calculo de status
    obamaStatus = True if obamacare.status_color == 3 else False

    #Obtener todo los meses en ingles
    monthInEnglish = [calendar.month_name[i] for i in range(1, 13)]

    newApppointment = True if apppointment else False
    
    RoleAuditar = [
        newLetterCard,
        userCarrier,
        obamaStatus,         
        obamaDocumente,
        obamacare.policyNumber, 
        newApppointment
    ]

    c = 0
    for item in RoleAuditar: 
        if item and item != 'None' and item is not None:
            c += 1

    percentage = int(c/6*100)


    social_number = obamacare.client.social_security  # Campo real del modelo
    # Asegurarse de que social_number no sea None antes de formatear
    if social_number:
        formatted_social = f"xxx-xx-{social_number[-4:]}"  # Obtener el formato deseado
    else:
        formatted_social = "N/A"  # Valor predeterminado si no hay número disponible

    #calculo de edad
    hoy = timezone.now().date()
    old = hoy.year - obamacare.client.date_birth.year - ((hoy.month, hoy.day) < (obamacare.client.date_birth.month, obamacare.client.date_birth.day))
   
    obsObama = ObservationAgent.objects.filter(obamaCare=obamacare_id)  
    users = Users.objects.filter(role='C')
    list_drow = DropDownList.objects.filter(profiling_obama__isnull=False)
    description = DropDownList.objects.filter(description__isnull=False)
    obsCus = ObservationCustomer.objects.select_related('agent').filter(client=obamacare.client.id)
    consent = Consents.objects.filter(obamacare = obamacare_id )
    income = IncomeLetter.objects.filter(obamacare = obamacare_id)
    document = DocumentsClient.objects.filter(client = obamacare.client)
    documentObama = DocumentObama.objects.filter(obamacare = obamacare_id)
    incomeffm = IncomeLetterFFM.objects.filter(obamacare = obamacare_id)

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
            
            
            statusRed = ['CANCELED','SALE FALL','PRICING ISSUE','OTHER AGENT','CUSTOMER CANCELED','OTHER PARTY']

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
                return redirect('clientObamacare')
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
                return redirect('clientObamacare')
            else:
                return redirect('clientAccionRequired')      
        
    obamacare.subsidy = f"{float(obamacare.subsidy):.2f}"
    obamacare.premium = f"{float(obamacare.premium):.2f}"

    # Obtener los mensajes de texto del Cliente.
    if request.user.is_superuser:
        contact = Contacts.objects.filter(phone_number=obamacare.client.phone_number, company=obamacare.company.id).first()
    else:
        contact = Contacts.objects.filter(phone_number=obamacare.client.phone_number, company=company_id).first()


    chats = Chat.objects.filter(contact=contact)
    messages = Messages.objects.filter(chat=chats[0].id)
    secretKey = SecretKey.objects.filter(contact=contact.id).first()
    chat = get_last_message_for_chats(chats)[0]
    
    context = {
        'obamacare': obamacare,
        'formatted_social':formatted_social,
        'users': users,
        'obsObamaText': '\n'.join([obs.content for obs in obsObama]),
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
        'monthInEnglish':monthInEnglish,
        'monthsPaid':monthsPaid,
        'accionRequired': accionRequired,
        'way': way,
        'description' : description,
        'old' : old,
        'paymentDateObama': paymentDateObama,
        'incomeffm':incomeffm,
        #SMS Blue
        'contact':contact,
        'chat':chat,
        'messages':messages,
        'secretKey':secretKey
    }

    return render(request, 'edit/editObama.html', context)

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
            obama = obama,
            agent_create=request.user,
            username_carrier=username_carrier,
            password_carrier = password_carrier,
            dateUserCarrier=date 
            )      

        else:

            UserCarrier.objects.create(
            obama=obama,
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
    paymentDateSupp = paymentDate.objects.filter(supp = supp).first()

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
    old = hoy.year - supp.client.date_birth.year - ((hoy.month, hoy.day) < (supp.client.date_birth.month, supp.client.date_birth.day)) 


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
    else:
        contact = Contacts.objects.filter(phone_number=supp.client.phone_number, company_id=company_id).first()

    chats = Chat.objects.filter(contact=contact)
    messages = Messages.objects.filter(chat_id=chats[0].id)
    secretKey = SecretKey.objects.filter(contact_id=contact.id).first()
    chat = get_last_message_for_chats(chats)[0]


    context = {
        'supps': supp,
        'formatted_social':formatted_social,
        'dependents': dependents,
        'obsSuppText': '\n'.join([obs.content for obs in obsSupp]),
        'obsCustomer': obsCus,
        'list_drow': list_drow,
        'old' : old,
        'paymentDateSupp' : paymentDateSupp,
        #SMS Blue
        'contact':contact,
        'chat':chat,
        'messages':messages,
        'secretKey':secretKey
    }
    
    return render(request, 'edit/editSupp.html', context)

def editDepentsObama(request, obamacare_id):
    # Obtener todos los dependientes asociados al ObamaCare
    dependents = Dependents.objects.filter(obamacare=obamacare_id)

    if request.method == "POST":
        for dependent in dependents:

            # Resetear la fecha guardarla como se debe porque la traigo en formato USA
            date_birth = request.POST.get(f'dateBirthDependent_{dependent.id}')

            # Conversión solo si los valores no son nulos o vacíos
            if date_birth not in [None, '']:
                date_birth_new = datetime.strptime(date_birth, '%m/%d/%Y').date()
            else:
                date_birth_new = None
            

            # Obtener los datos enviados por cada dependiente
            dependent_id = request.POST.get(f'dependentId_{dependent.id}')
            name = request.POST.get(f'nameDependent_{dependent.id}')
            apply = request.POST.get(f'applyDependent_{dependent.id}')
            kinship = request.POST.get(f'kinship_{dependent.id}')
            migration_status = request.POST.get(f'migrationStatusDependent_{dependent.id}')
            sex = request.POST.get(f'sexDependent_{dependent.id}')
            
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
            dateNew = datetime.datetime.strptime(date_birth, '%m/%d/%Y').date()

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
