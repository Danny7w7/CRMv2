#libreria de paises
import json
import urllib.request
from django.http import JsonResponse
from django.shortcuts import render

# Standard Python libraries
import datetime

# Django utilities
from django.utils.timezone import make_aware

# Django core libraries
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.models import AnonymousUser

# Application-specific imports
from app.forms import *
from app.models import *

from ..sms import createOrUpdateChat
from ..whatsApp import createOrUpdateChat as whatssap
from ..decoratorsCompany import *
from ..consents import generateTemporaryToken, validateTemporaryToken

# Vista para crear cliente
@login_required(login_url='/login') 
@company_ownership_required_sinURL
def formCreateClient(request):

    company_id = request.company_id  # Obtener company_id desde request

    user = Users.objects.select_related('company').filter(company = company_id).first()

    if company_id == 1:
        companies = Companies.objects.filter(is_active = True)
    else:
        companies = None

    context = {
        'user' : user,
        'companies' : companies
    }

    if request.method == 'POST':

        date_births = request.POST.get('date_birth')
        fecha_obj = datetime.datetime.strptime(date_births, '%m/%d/%Y').date()
        company = request.POST.get('company')
        companyInstance = Companies.objects.filter(id = company).first()

        social = request.POST.get('social_security')
        if social: formatSocial = social.replace('-','')
        else: formatSocial = None

        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.agent = request.user
            client.is_active = 1
            client.date_birth = fecha_obj
            client.social_security = formatSocial
            client.company = companyInstance
            client.save()

            if client.type_sales in ['ACA', 'ACA/SUPLEMENTARIO']:
                contactClient = ContactClient.objects.create(client=client,agent=request.user)

            contact = Contacts.objects.filter(phone_number=client.phone_number).first()
            if not contact:
                contact = Contacts()
                contact.company = companyInstance
                contact.name = f'{client.first_name} {client.last_name}'
                contact.phone_number = client.phone_number
                contact.is_active = False
                contact.save()

            createOrUpdateChat(contact, companyInstance, request.user)

            contactWhatssap = Contacts_whatsapp.objects.filter(phone_number=client.phone_number).first()
            if not contactWhatssap:
                contactWhatssap = Contacts_whatsapp()
                contactWhatssap.company = companyInstance
                contactWhatssap.name = f'{client.first_name} {client.last_name}'
                contactWhatssap.phone_number = client.phone_number
                contactWhatssap.is_active = False
                contactWhatssap.save()

            whatssap(contactWhatssap, companyInstance, request.user)


            # De forma insofacta se le crea el contacto al cliente.
            
            # Responder con éxito y la URL de redirección
            return redirect('formCreatePlan' ,client.id)
        else:
            return render(request, 'newSale/formCreateClient.html', {'error_message': form.errors})
    else:
        return render(request, 'newSale/formCreateClient.html',context)

@login_required(login_url='/login') 
@company_ownership_required_sinURL
def formCreateAssure(request):

    company_id = request.company_id  # Obtener company_id desde request

    user = Users.objects.select_related('company').filter(company = company_id).first()


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

    if company_id == 1:
        companies = Companies.objects.filter(is_active = True)
    else:
        companies = None

    context = {
        'user' : user,
        'companies' : companies,
        'paises' : paises
    }

    if request.method == 'POST':

        date_births = request.POST.get('date_birth')
        fecha_obj = datetime.datetime.strptime(date_births, '%m/%d/%Y').date()
        company = request.POST.get('company')
        companyInstance = Companies.objects.filter(id = company).first()

        social = request.POST.get('social_security')
        if social: formatSocial = social.replace('-','')
        else: formatSocial = None

        status = 'REGISTERED'

        form = ClientFormAssure(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.agent = request.user
            client.is_active = 1
            client.date_birth = fecha_obj
            client.social_security = formatSocial
            client.company = companyInstance
            client.status = status
            client.status_color = 1                 
            client.save()

            contact = Contacts.objects.filter(phone_number=client.phone_number).first()
            if not contact:
                contact = Contacts()
                contact.company = companyInstance
                contact.name = f'{client.first_name} {client.last_name}'
                contact.phone_number = client.phone_number
                contact.is_active = False
                contact.save()

            createOrUpdateChat(contact, companyInstance, request.user)

            contactWhatssap = Contacts_whatsapp.objects.filter(phone_number=client.phone_number).first()
            if not contactWhatssap:
                contactWhatssap = Contacts_whatsapp()
                contactWhatssap.company = companyInstance
                contactWhatssap.name = f'{client.first_name} {client.last_name}'
                contactWhatssap.phone_number = client.phone_number
                contactWhatssap.is_active = False
                contactWhatssap.save()

            whatssap(contactWhatssap, companyInstance, request.user)
            
            # Responder con éxito y la URL de redirección
            return redirect('formCreatePlanAssure' ,client.id)
        else:
            return render(request, 'newSale/formCreateAssure.html', {'error_message': form.errors})
    else:
        return render(request, 'newSale/formCreateAssure.html',context)

@login_required(login_url='/login') 
@company_ownership_required_sinURL
def formCreateClientLife(request):

    company_id = request.company_id  # Obtener company_id desde request

    user = Users.objects.select_related('company').filter(company = company_id).first()

    if company_id == 1:
        companies = Companies.objects.filter(is_active = True)
    else:
        companies = None

    context = {
        'user' : user,
        'companies' : companies,
        'show_modal': False
    }

    if request.method == 'POST':

        date_births = request.POST.get('date_birth')
        fecha_obj = datetime.datetime.strptime(date_births, '%m/%d/%Y').date()
        company = request.POST.get('company')
        companyInstance = Companies.objects.filter(id = company).first()

        social = request.POST.get('social_security')
        if social: formatSocial = social.replace('-','')
        else: formatSocial = None

        form = ClientLifeForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.agent = request.user
            client.is_active = 1
            client.status_color = 1
            client.status = 'REGISTERED'
            client.date_birth = fecha_obj
            client.social_security = formatSocial
            client.company = companyInstance
            client.observation = request.POST.get('observation')
            client.save()

            contact = Contacts.objects.filter(phone_number=client.phone_number).first()
            if not contact:
                contact = Contacts()
                contact.company = companyInstance
                contact.name = f'{client.full_name}'
                contact.phone_number = client.phone_number
                contact.is_active = False
                contact.save()

            createOrUpdateChat(contact, companyInstance, request.user)

            contactWhatssap = Contacts_whatsapp.objects.filter(phone_number=client.phone_number).first()
            if not contactWhatssap:
                contactWhatssap = Contacts_whatsapp()
                contactWhatssap.company = companyInstance
                contactWhatssap.name = f'{client.full_name}'
                contactWhatssap.phone_number = client.phone_number
                contactWhatssap.is_active = False
                contactWhatssap.save()

            whatssap(contactWhatssap, companyInstance, request.user)

            context = {
                'client' : client,
                'show_modal': True
            }
            
            # Responder con éxito y la URL de redirección
            return render(request, 'newSale/formCreateClientLife.html', context)
        else:
            return render(request, 'newSale/formCreateClientLife.html', {'error_message': form.errors})
    else:
        return render(request, 'newSale/formCreateClientLife.html',context)

@login_required(login_url='/login') 
@company_ownership_required_sinURL
def formCreateClientMedicare(request):

    company_id = request.company_id  # Obtener company_id desde request
    user = Users.objects.select_related('company').filter(company = company_id).first()

    if company_id == 1:
        company = Companies.objects.filter(is_active = True)
    else:
        company = None

    context = {
        'user' : user,
        'company' : company
    }

    if request.method == 'POST':

        date_births = request.POST.get('date_birth')
        language = request.POST.get('language')
        fecha_obj = datetime.datetime.strptime(date_births, '%m/%d/%Y').date()

        #companie
        companies = request.POST.get('companies')
        companiesInstance = Companies.objects.filter(id = companies).first()

        #reseteo de campos
        nameAutorized = request.POST.get('nameAutorized')
        relationship = request.POST.get('relationship')

        if nameAutorized == '': nameAutorized = 'N/A'
        if relationship == 'no_valid': relationship = 'N/A'


        date_medicare = request.POST.get('dateMedicare')
        # Convertir a objeto datetime
        fecha_medicare = datetime.datetime.strptime(date_medicare, '%m/%d/%Y %H')
        # Asegurar compatibilidad con zona horaria
        fecha_formateada_medicare = make_aware(fecha_medicare)

        social = request.POST.get('social_security')

        if social: formatSocial = social.replace('-','')
        else: formatSocial = None

        form = ClientMedicareForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.agent = request.user
            client.is_active = 1
            client.company = companiesInstance
            client.date_birth = fecha_obj
            client.dateMedicare = fecha_formateada_medicare
            client.social_security = formatSocial
            client.relationship = relationship
            client.nameAutorized = nameAutorized
            client.save()

            contact = OptionMedicare.objects.create(client=client,agent=request.user)
            
            # Redirección a la nueva página en otra pestaña
            new_page_url = reverse('consetMedicare', args=[client.id, language])

            context = {
                'new_page_url': new_page_url,
                'company' : companiesInstance
            }
            
            # Redirección de la página actual al index
            return render(request, 'consent/redirectMedicare.html', context)
        
            
        else:
            return render(request, 'newSale/formCreateClientMedicare.html', {'error_message': form.errors})
    else:
        return render(request, 'newSale/formCreateClientMedicare.html', context)

@login_required(login_url='/login') 
@company_ownership_required_sinURL
def formCreatePlan(request ,client_id):
    client = get_object_or_404(Clients, id=client_id)
    company_id = request.company_id  # Obtener company_id desde request
    company = Companies.objects.filter(id = company_id).first()

    type_sale = request.GET.get('type_sale')
    aca_plan = ObamaCare.objects.filter(client=client).first()
    supplementary_plan = Supp.objects.filter(client=client)
    dependents = Dependents.objects.filter(client=client)
    for supp in supplementary_plan:
        supp.premium = f"{float(supp.premium):.2f}" #Esto  es para que se le ponga el premium.

    return render(request, 'forms/formCreatePlan.html', {
        'client': client,
        'aca_plan_data': aca_plan,
        'supplementary_plan_data': supplementary_plan,
        'dependents': dependents,
        'type_sale':type_sale,
        'company': company
    })

@login_required(login_url='/login') 
@company_ownership_required_sinURL
def formCreatePlanAssure(request ,client_id):   

    url = "https://restcountries.com/v3.1/all"
 
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode())

        paises = []

        for country in sorted(data, key=lambda x: x.get('name', {}).get('common', '')):
            nombre = country.get('name', {}).get('common', 'N/A')
            gentilicio = country.get('demonyms', {}).get('eng', {}).get('m', 'N/A')
            paises.append({
                "nombre": nombre,
                "gentilicio": gentilicio
            })     

    if request.method == 'POST':    
        client = get_object_or_404(ClientsAssure, id=client_id)

        full_name_list = request.POST.getlist('full_name[]')
        date_birth_list = request.POST.getlist('date_birth[]')
        sex_list = request.POST.getlist('sex[]')
        kinship_list = request.POST.getlist('kinship[]')
        nationality_list = request.POST.getlist('nationality[]')

        validated_data = []
        hasErrors = False

        # Validar fechas primero
        for full_name, date_birth, sex, kinship, nationality in zip(full_name_list, date_birth_list, sex_list, kinship_list, nationality_list):
            try:
                birthdate_obj = datetime.datetime.strptime(date_birth, "%m-%d-%Y")
                date_birth_formatted = birthdate_obj.strftime("%Y-%m-%d")

                validated_data.append({
                    'full_name': full_name,
                    'date_birth': date_birth_formatted,
                    'sex': sex,
                    'kinship': kinship,
                    'nationality': nationality
                })
            except ValueError:
                hasErrors = True
                messages.error(request, f"Invalid date format for {full_name}. Please use MM-DD-YYYY.")

        if hasErrors:
            messages.error(request, "Some dates were invalid. Please correct them and try again.")

        # Contar cuántos ya tiene
        current_count = DependentsAssure.objects.filter(client=client).count()
        remaining_slots = 6 - current_count

        if remaining_slots <= 0:
            messages.error(request, "This client already has the maximum number of 6 dependents.")

        if not hasErrors and not remaining_slots <= 0 :
            saved_count = 0
            for data in validated_data[:remaining_slots]:  # solo los que quepan
                DependentsAssure.objects.create(
                    client=client,
                    full_name=data['full_name'],
                    date_birth=data['date_birth'],
                    sex=data['sex'],
                    kinship=data['kinship'],
                    country=data['nationality']
                )
                saved_count += 1

            if saved_count < len(validated_data):
                messages.warning(request, f"Only {saved_count} dependents were saved to reach the limit of 6.")
            else:
                messages.success(request, f"All dependents were added successfully.")
                return redirect('formCreateAssure')

    return render(request, 'forms/formCreatePlanAssure.html', {'paises': paises})

@login_required(login_url='/login')
@company_ownership_required_sinURL
def formAddObama(request, client_id):

    type_sales = request.session.get('type_sales')
    client = Clients.objects.get(id=client_id)

    if request.method == 'POST':
        company_id = request.company_id  # Obtener company_id desde request
        company_id = Companies.objects.filter(id = company_id).first()

        formObama = ObamaForm(request.POST)
        if formObama.is_valid():
            obama = formObama.save(commit=False)
            obama.agent = request.user
            obama.client = client
            obama.status_color = 1
            obama.is_active = True
            obama.company = company_id
            obama.save()

            client = get_object_or_404(Clients, id=client_id)
            client.type_sales = type_sales
            client.save()

            return redirect('select_client')  # Cambia a tu página de éxito            
        
    return render(request, 'forms/formAddObama.html')

@login_required(login_url='/login')
@company_ownership_required_sinURL
def formAddSupp(request,client_id):

    type_sales = request.session.get('type_sales')
    client = Clients.objects.get(id=client_id)    

    if request.method == 'POST':
        company_id = request.company_id  # Obtener company_id desde request
        company_id = Companies.objects.filter(id = company_id).first()

        observation = request.POST.get('observation')
        effective_dates = request.POST.get('effective_date')
        fecha_obj = datetime.datetime.strptime(effective_dates, '%m/%d/%Y')
        fecha_formateada = fecha_obj.strftime('%Y-%m-%d')

        formSupp = SuppForm(request.POST)
        if formSupp.is_valid():
            supp = formSupp.save(commit=False)
            supp.agent = request.user
            supp.client = client
            supp.status_color = 1
            supp.is_active = True
            supp.effective_date = fecha_formateada
            supp.observation = observation
            supp.status = 'REGISTERED'
            supp.company = company_id
            supp.save()

            client = get_object_or_404(Clients, id=client_id)
            client.type_sales = type_sales
            client.save()          

            return redirect('select_client' )  # Cambia a tu página de éxito           
        
    return render(request, 'forms/formAddSupp.html')

@login_required(login_url='/login')
@company_ownership_required_sinURL
def formAddDepend(request ,client_id):
    lista = []
    lista2 = []
    dependents = Dependents.objects.filter(client_id=client_id)

    supp = Supp.objects.filter(client_id=client_id)
    obama = ObamaCare.objects.filter(client_id=client_id).first()

    if obama:
        lista2.append('ACA')

    for supp in supp:
        supp.policy_type = supp.policy_type.split(",")
        for i in supp.policy_type:
            lista2.append(i)

    for dependent in dependents:
        dependent.type_police = dependent.type_police.split(",")
        for i in dependent.type_police:
            lista.append(i)

    if request.method == 'POST':
       
        # Recuperar todos los dependientes enviados
        dependent_ids = request.POST.getlist('dependentId')

        # Iterar sobre cada dependiente para procesar sus datos
        for index, dependent_id in enumerate(dependent_ids):
            try:
                observations = request.POST.getlist(f'typePoliceDependents[{index}][]')
                if observations:
                    # Buscar el dependiente correspondiente
                    dependent = Dependents.objects.get(id=dependent_id)
                    
                    # Obtener los valores actuales de type_police
                    current_type_police = dependent.type_police.split(",") if dependent.type_police else []

                    # Concatenar y guardar
                    updated_type_police = list(set(current_type_police + observations))
                    dependent.type_police = ",".join(updated_type_police)
                    dependent.save()

                    # Asociar a las pólizas correspondientes
                    for observation in observations:
                        supp_instance = Supp.objects.filter(policy_type=observation, client_id=client_id).first()
                        if supp_instance:
                            supp_instance.dependents.add(dependent)

            except Exception as e:
                return (f"Error processing dependent {dependent_id}: {e}")

        return redirect('select_client')

    context = {
        'dependents': dependents,
        'lista': lista,
        'lista2': lista2,
        'client_id': client_id
    }

    return render(request, 'forms/formAddDepend.html', context)

@login_required(login_url='/login')
def addDepend(request):

    nameDependent = request.POST.get('nameDependent')
    applyDependent = request.POST.get('applyDependent')
    dateBirthDependent = request.POST.get('dateBirthDependent')
    migrationStatusDependent = request.POST.get('migrationStatusDependent')
    sexDependent = request.POST.get('sexDependent')        
    kinship = request.POST.get('kinship')  
    client_id = request.POST.get('client_id') 

    # Conversión solo si los valores no son nulos o vacíos
    if dateBirthDependent not in [None, '']:
        dateNew = datetime.datetime.strptime(dateBirthDependent, '%m/%d/%Y').date()
    else:
        dateNew = None

    # Obtenemos las polizas seleccionadas
    observations = request.POST.getlist('typePoliceDependents[]')  # Lista de valores seleccionados
    
    # Convertir las observaciones a una cadena (por ejemplo, separada por comas o saltos de línea)
    typification_text = ", ".join(observations)  # Puedes usar "\n".join(observations) si prefieres saltos de línea

    obama = ObamaCare.objects.get(client_id=client_id)
    client = Clients.objects.get(id=client_id)

    if nameDependent.strip():  # Validar que el texto no esté vacío
        dependent = Dependents.objects.create(
            client=client,
            name=nameDependent,
            apply=applyDependent,
            date_birth=dateNew,
            migration_status=migrationStatusDependent,
            type_police=typification_text, # Guardamos las observaciones en el campo 'typification'
            sex=sexDependent,
            obamacare = obama,
            kinship=kinship
        )
    
    # Asociar el Dependent solo a las pólizas seleccionadas en observations
        for observation in observations:
            # Buscar la póliza correspondiente al nombre o tipo
            supp_instance = Supp.objects.filter(policy_type=observation, client=client).first()
            if supp_instance:
                supp_instance.dependents.add(dependent)

    return redirect('select_client')    

@login_required(login_url='/login') 
@company_ownership_required_sinURL
def formCreateAlert(request):

    if request.method == 'POST':
        company_id = request.company_id  # Obtener company_id desde request
        company  = Companies.objects.filter(id = company_id).first()
        formClient = ClientAlertForm(request.POST)
        if formClient.is_valid():
            alert = formClient.save(commit=False)
            alert.agent = request.user
            alert.is_active = True
            alert.company = company
            alert.save()
            return redirect('formCreateAlert',)  # Cambia a tu página de éxito

    return render(request, 'newSale/formCreateAlert.html')
