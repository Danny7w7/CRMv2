# Standard Python libraries
import base64
import io
import json
import re
from datetime import timedelta, datetime

# Django utilities
from django.core.files.base import ContentFile
from django.core.signing import BadSignature, Signer
from django.http import HttpResponse
from django.template.loader import render_to_string

# Django core libraries
from django.contrib.auth.models import AnonymousUser
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.translation import activate
from urllib.parse import urlencode

# Third-party libraries
from weasyprint import HTML

# Application-specific imports
from app.models import *
from ..alertWebsocket import websocketAlertGeneric

def consetMedicare(request, client_id, language):

    medicare = Medicare.objects.get(id=client_id)
    contact = OptionMedicare.objects.filter(client = medicare.id).first()
    temporalyURL = None

    typeToken = 'medicare'

    activate(language)
    # Validar si el usuario no está logueado y verificar el token
    if isinstance(request.user, AnonymousUser):
        result = validateTemporaryToken(request, typeToken)
        is_valid_token, *note = result
        if not is_valid_token:
            return HttpResponse(note)
    elif request.user.is_authenticated:
        # Usuario autenticado
        temporalyURL = f"{request.build_absolute_uri('/consetMedicare/')}{client_id}/{language}/?token={generateTemporaryToken(medicare, typeToken)}"
    else:
        # Si el usuario no está logueado y no hay token válido
        return HttpResponse('Acceso denegado. Por favor, inicie sesión o use un enlace válido.')
    
    if request.method == 'POST':
        
        # Usamos la nueva función para guardar los checkboxes en ContactClient
        objectContact = save_contact_medicare_checkboxes(request.POST, contact)

        return generateMedicarePdf(request, medicare ,language)


    context = {
        'medicare':medicare,
        'contact':contact,
        'company':getCompanyPerAgent(medicare.agent_usa),
        'temporalyURL': temporalyURL
    }

    return render(request, 'consent/consetMedicare.html',context)

def consent(request, obamacare_id):
    obamacare = ObamaCare.objects.select_related('client', 'agent').get(id=obamacare_id)
    temporalyURL = None

    typeToken = 'obamacare'
   
    language = request.GET.get('lenguaje', 'es')  # Idioma predeterminado si no se pasa
    activate(language)
    # Validar si el usuario no está logueado y verificar el token
    if isinstance(request.user, AnonymousUser):
        result = validateTemporaryToken(request, typeToken)
        is_valid_token, *note = result
        if not is_valid_token:
            return HttpResponse(note)
    elif request.user.is_authenticated:
        # Usuario autenticado
        temporalyURL = f"{request.build_absolute_uri('/viewConsent/')}{obamacare_id}?token={generateTemporaryToken(obamacare.client , typeToken)}&lenguaje={language}"
    else:
        # Si el usuario no está logueado y no hay token válido
        return HttpResponse('Acceso denegado. Por favor, inicie sesión o use un enlace válido.')
    
    dependents = Dependents.objects.filter(client=obamacare.client)
    supps = Supp.objects.filter(client_id=obamacare.client.id)
    consent = Consents.objects.select_related('obamacare').filter(obamacare = obamacare_id ).last()
    contact = ContactClient.objects.filter(client = obamacare.client.id).first()

    if request.method == 'POST':
        documents = request.FILES.getlist('documents')  # Lista de archivos subidos

        language = request.GET.get('lenguaje', 'es')  # Idioma predeterminado si no se pasa

        objectClient = save_data_from_request(Clients, request.POST, ['agent'],obamacare.client)
        objectObamacare = save_data_from_request(ObamaCare, request.POST, ['signature'], obamacare)
        
        # Usamos la nueva función para guardar los checkboxes en ContactClient
        objectContact = save_contact_client_checkboxes(request.POST, contact)

        for document in documents:
            photo = DocumentsClient(
                file=document,
                client=obamacare.client)  # Crear una nueva instancia de Foto
            photo.save()  # Guardar el archivo en la base de datos
        
        websocketAlertGeneric(
            request,
            'send_alert',
            'signedConsent',
            'success',
            'Signed consent',
            f'The client {obamacare.client.first_name} {obamacare.client.last_name} successfully signed the consent form.',
            'Go to client information',
            f'/editObama/{obamacare.id}/{obamacare.company.id}',
            obamacare.agent.id,
            obamacare.agent.username
        )
        
        return generateConsentPdf(request, objectObamacare, dependents, supps, language)

    context = {
        'valid_migration_statuses': ['PERMANENT_RESIDENT', 'US_CITIZEN', 'EMPLOYMENT_AUTHORIZATION'],
        'obamacare':obamacare,
        'dependents':dependents,
        'consent':consent,
        'contact':contact,
        'company':getCompanyPerAgent(obamacare.agent_usa),
        'temporalyURL': temporalyURL,
        'supps': supps
    }
    return render(request, 'consent/consent1.html', context)

def incomeLetter(request, obamacare_id):

    obamacare = ObamaCare.objects.select_related('client').get(id=obamacare_id)
    signed = IncomeLetter.objects.filter(obamacare = obamacare_id).first()

    language = request.GET.get('lenguaje', 'es')  # Idioma predeterminado si no se pasa
    activate(language)

    temporalyURL = None
    typeToken = 'obamacare' 


    # Validar si el usuario no está logueado y verificar el token
    if isinstance(request.user, AnonymousUser):
        typeToken = True #Aqui le indico si buscar el token temporal por el medicare o client_id
        result = validateTemporaryToken(request, typeToken)
        is_valid_token, *note = result
        if not is_valid_token:
            return HttpResponse(note)
    elif request.user.is_authenticated:
        # Usuario autenticado
        temporalyURL = f"{request.build_absolute_uri('/viewIncomeLetter/')}{obamacare_id}?token={generateTemporaryToken(obamacare.client , typeToken)}&lenguaje={language}"
    else:
        # Si el usuario no está logueado y no hay token válido
        return HttpResponse('Acceso denegado. Por favor, inicie sesión o use un enlace válido.')

  
    context = {
        'obamacare': obamacare,
        'signed' : signed,
        'temporalyURL' : temporalyURL
    }

    if request.method == 'POST':
        objectClient = save_data_from_request(Clients, request.POST, ['agent'],obamacare.client)
        objectObamacare = save_data_from_request(ObamaCare, request.POST, ['signature'], obamacare)

        websocketAlertGeneric(
            request,
            'send_alert',
            'signedIncomeLetter',
            'success',
            'Signed Income Letter',
            f'The client {obamacare.client.first_name} {obamacare.client.last_name} successfully signed the Income Letter form.',
            'Go to client information',
            f'/editObama/{obamacare.id}/{obamacare.company.id}',
            obamacare.agent.id,
            obamacare.agent.username
        )

        generateIncomeLetterPDF(request, objectObamacare, language)
        deactivateTemporaryToken(request)
        return render(request, 'consent/endView.html')   
        
    return render(request, 'consent/incomeLetter.html', context)

def generateConsentPdf(request, obamacare, dependents, supps, language):
    token = request.GET.get('token')

    current_date = datetime.now().strftime("%A, %B %d, %Y %I:%M")
    date_more_3_months = (datetime.now() + timedelta(days=360)).strftime("%A, %B %d, %Y %I:%M")

    contact = ContactClient.objects.filter(client = obamacare.client).first()

    # Obtener los campos con valor True
    true_fields = []

    if contact.sms: true_fields.append('sms')
    if contact.phone: true_fields.append('phone')
    if contact.email: true_fields.append('email')
    if contact.whatsapp: true_fields.append('whatsapp')

    # Variable con los nombres de los campos
    var = ", ".join(true_fields)
    

    consent = Consents.objects.create(
        obamacare=obamacare,
    )

    signature_data = request.POST.get('signature')
    format, imgstr = signature_data.split(';base64,')
    ext = format.split('/')[-1]
    image = ContentFile(base64.b64decode(imgstr), name=f'firma.{ext}')

    consent.signature = image
    consent.save()

    context = {
        'obamacare':obamacare,
        'dependents':dependents,
        'supps':supps,
        'consent':consent,
        'company':getCompanyPerAgent(obamacare.agent_usa),
        'social_security':request.POST.get('socialSecurity'),
        'current_date':current_date,
        'date_more_3_months':date_more_3_months,
        'ip':getIPClient(request),
        'var':var
    }

    activate(language)
    # Renderiza la plantilla HTML a un string
    html_content = render_to_string('consent/templatePdfConsent.html', context)

    # Genera el PDF
    pdf_file = HTML(string=html_content).write_pdf()

    # Usa BytesIO para convertir el PDF en un archivo
    pdf_io = io.BytesIO(pdf_file)
    pdf_io.seek(0)  # Asegúrate de que el cursor esté al principio del archivo

    # Guarda el PDF en el modelo usando un ContentFile
    pdf_name = f'Consent{obamacare.client.first_name}_{obamacare.client.last_name}#{obamacare.client.phone_number} {datetime.now().strftime("%m-%d-%Y-%H:%M")}.pdf'  # Nombre del archivo

    consent.pdf.save(pdf_name, ContentFile(pdf_io.read()), save=True)

    base_url = reverse('incomeLetter', args=[obamacare.id])
    query_params = urlencode({'token': token,'lenguaje': language})
    url = f'{base_url}?{query_params}'

    return redirect(url)

def generateMedicarePdf(request, medicare ,language):
    token = request.GET.get('token')

    current_date = datetime.now().strftime("%A, %B %d, %Y %I:%M")

    contact = OptionMedicare.objects.filter(client = medicare.id).first()

    # Obtener los campos con valor True
    true_fields = []

    if contact.prescripcion: true_fields.append('Planes de Prescripción de Medicare Parte D')
    if contact.advantage: true_fields.append('Planes de Medicare Advantage (Parte C) y Planes de Costo')
    if contact.dental: true_fields.append('Productos Dental-Visión-Oescucha')
    if contact.complementarios: true_fields.append('Productos de Complementarios de Hospitalización')
    if contact.suplementarios: true_fields.append('Planes Suplementarios de Medicare (Medigap)')

    # Variable con los nombres de los campos
    var = ", ".join(true_fields)    

    consent = Consents.objects.create(
        medicare=medicare,
    )

    signature_data = request.POST.get('signature')
    format, imgstr = signature_data.split(';base64,')
    ext = format.split('/')[-1]
    image = ContentFile(base64.b64decode(imgstr), name=f'firma.{ext}')

    consent.signature = image
    consent.save()

    context = {
        'medicare':medicare,
        'consent':consent,
        'company':getCompanyPerAgent(medicare.agent_usa),
        'ip':getIPClient(request),
        'current_date':current_date,
        'var':var
    }

    activate(language)
    # Renderiza la plantilla HTML a un string
    html_content = render_to_string('consent/templatePdfConsentMedicare.html', context)

    # Genera el PDF
    pdf_file = HTML(string=html_content).write_pdf()

    # Usa BytesIO para convertir el PDF en un archivo
    pdf_io = io.BytesIO(pdf_file)
    pdf_io.seek(0)  # Asegúrate de que el cursor esté al principio del archivo

    # Guarda el PDF en el modelo usando un ContentFile
    pdf_name = f'Consent-medicare{medicare.first_name}_{medicare.last_name}#{medicare.phone_number} {datetime.now().strftime("%m-%d-%Y-%H:%M")}.pdf'  # Nombre del archivo

    consent.pdf.save(pdf_name, ContentFile(pdf_io.read()), save=True)

    return render(request, 'consent/endView.html')

def generateIncomeLetterPDF(request, obamacare, language):
    current_date = datetime.now().strftime("%A, %B %d, %Y %I:%M")

    incomeLetter = IncomeLetter.objects.create(
        obamacare=obamacare,
    )
    signature_data = request.POST.get('signature')
    format, imgstr = signature_data.split(';base64,')
    ext = format.split('/')[-1]
    image = ContentFile(base64.b64decode(imgstr), name=f'firma.{ext}')
    incomeLetter.signature = image
    incomeLetter.save()

    context = {
        'obamacare':obamacare,
        'current_date':current_date,
        'ip':getIPClient(request),
        'incomeLetter':incomeLetter
    }

    activate(language)

    # Renderiza la plantilla HTML a un string
    html_content = render_to_string('consent/templatePdfIncomeLetter.html', context)

    # Genera el PDF
    pdf_file = HTML(string=html_content).write_pdf()

    # Usa BytesIO para convertir el PDF en un archivo
    pdf_io = io.BytesIO(pdf_file)
    pdf_io.seek(0)  # Asegúrate de que el cursor esté al principio del archivo

    # Guarda el PDF en el modelo usando un ContentFile
    pdf_name = f'IncomeOfLetter{obamacare.client.first_name}_{obamacare.client.last_name}#{obamacare.client.phone_number} {datetime.now().strftime("%A, %B %d, %Y %I:%M")}.pdf'  # Nombre del archivo

    incomeLetter.pdf.save(pdf_name, ContentFile(pdf_io.read()), save=True)

def ILFFM(request, obamacare):
    current_date = datetime.now().strftime("%A, %B %d, %Y %I:%M")
    obamacare = ObamaCare.objects.filter(id = obamacare).first()
    signature = IncomeLetter.objects.filter(obamacare = obamacare).latest('created_at')

    language = request.GET.get('lenguaje', 'es')  # Idioma predeterminado si no se pasa
    activate(language)

    incomeLetter = IncomeLetterFFM(obamacare=obamacare)

    context = {
        'obamacare':obamacare,
        'current_date':current_date,
        'ip':getIPClient(request),
        'signature': signature
    } 

    # Renderiza la plantilla HTML a un string
    html_content = render_to_string('consent/templatePdfIncomeLetterFFM.html', context)

    # Genera el PDF
    pdf_file = HTML(string=html_content).write_pdf()

    # Guardar el PDF en el modelo
    pdf_name = f'IncomeOfLetterFFM_{obamacare.client.first_name}_{obamacare.client.last_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    
    # Usar un solo BytesIO para ambas operaciones
    pdf_buffer = io.BytesIO(pdf_file)
    
    # Guardar en el modelo
    incomeLetter.pdf.save(pdf_name, ContentFile(pdf_buffer.getvalue()))
    incomeLetter.save()
    
    # Reiniciar el buffer para la respuesta
    pdf_buffer.seek(0)

    # Crear respuesta HTTP
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{pdf_name}"'
    
    return response

def ConsentLifeInsurance(request, client_id):
    
    client = ClientsLifeInsurance.objects.select_related('agent').filter(id=client_id).first()
    answers = AnswerLifeInsurance.objects.filter(client = client_id)

    answers_dict = {}
    if answers:
        for answer in answers:
            answers_dict[f'q{answer.ask.id}'] = answer.answer

    print(answers_dict,'*********holis como estas')
    temporalyURL = None
    typeToken = 'lifeInsurance'
   
    language = request.GET.get('lenguaje', 'es')  # Idioma predeterminado si no se pasa
    activate(language)
    # Validar si el usuario no está logueado y verificar el token
    if isinstance(request.user, AnonymousUser):
        result = validateTemporaryToken(request, typeToken)
        is_valid_token, *note = result
        if not is_valid_token:
            return HttpResponse(note)
    elif request.user.is_authenticated:
        # Usuario autenticado
        temporalyURL = f"{request.build_absolute_uri('/ConsentLifeInsurance/')}{client_id}?token={generateTemporaryToken(client , typeToken)}&lenguaje={language}"
    else:
        # Si el usuario no está logueado y no hay token válido
        return HttpResponse('Acceso denegado. Por favor, inicie sesión o use un enlace válido.')

    if request.method == 'POST':

        from django.http import HttpResponse

        if request.user.is_authenticated:
            debug_log = "<h2>DEBUG CONSENTIMIENTO</h2>"
            try:
                asks = AskLifeInsurance.objects.all()  
                answersUpdate = AnswerLifeInsurance.objects.filter(client=client_id)  
                
                debug_log += f"<p>Preguntas encontradas: {asks.count()}</p>"
                debug_log += f"<p>Respuestas previas: {answersUpdate.count()}</p>"

                if answersUpdate.exists():
                    for ask in asks:
                        answer = request.POST.get(str(ask.id)) 
                        debug_log += f"<p>Actualizando → PREGUNTA: {ask.id} | RESPUESTA: {answer}</p>"
                        AnswerLifeInsurance.objects.filter(client=client, ask=ask).update(answer=answer)
                else:
                    for ask in asks:
                        answer = request.POST.get(str(ask.id))
                        debug_log += f"<p>Creando → PREGUNTA: {ask.id} | RESPUESTA: {answer}</p>"
                        AnswerLifeInsurance.objects.create(
                            client=client,
                            agent=request.user,
                            ask=ask,
                            answer=answer,
                            company=client.company
                        )

                return HttpResponse(debug_log + "<hr><strong>✔️ GUARDADO</strong>")

            except Exception as e:
                return HttpResponse(debug_log + f"<hr><strong>❌ ERROR:</strong> {str(e)}")

        else:

            language = request.GET.get('lenguaje', 'es')  # Idioma predeterminado si no se pasa
            print('AQUI EMPIEZA A ACTUALIZAR ********************************')
            print(answers)
            for answer in answers:
                # Usa el ID de la pregunta (ask.id) como clave
                key = str(answer.ask.id)
                value = request.POST.get(key)
                
                # Crea un mini diccionario que tenga el nombre correcto del campo
                post_data = {'answer': value}
                
                print('La instancia es de answer:', answer)
                print('Antes de actualizar:', answer.answer, '***********')
                
                updated = save_data_from_request(AnswerLifeInsurance, post_data, ['signature'], answer)
                
                if updated:
                    print("Después:", updated.answer)
                else:
                    print("❌ Error al actualizar.")


            print('TERMINE DE ACTUALIZAR **********************')
            
            #websocketAlertGeneric(
            #    request,
            #    'send_alert',
            #    'signedConsent',
            #    'success',
            #    'Signed consent',
            #    f'The client {client.first_name} {obamacare.client.last_name} successfully signed the consent form.',
            #    'Go to client information',
            #    f'/editObama/{obamacare.id}/{obamacare.company.id}',
            #    obamacare.agent.id,
            #    obamacare.agent.username
            #)
            
            generateConsentPdfLifeInsurance(request, client, language)  
            deactivateTemporaryToken(request)
            return render(request, 'consent/endView.html')     

    context = {
        'client':client,
        'temporalyURL': temporalyURL,
        'answers':answers_dict
    }
    return render(request, 'consent/lifeInsurance.html', context)

def generateConsentPdfLifeInsurance(request, client, language):
    token = request.GET.get('token')

    current_date = datetime.now().strftime("%A, %B %d, %Y %I:%M")
    date_more_3_months = (datetime.now() + timedelta(days=360)).strftime("%A, %B %d, %Y %I:%M") 
     
    answers = AnswerLifeInsurance.objects.filter(client = client.id)
    answers_dict = {}
    if answers:
        for answer in answers:
            answers_dict[f'q{answer.ask.id}'] = answer.answer 

    consent = Consents.objects.create(
        lifeInsurance=client,
    )

    signature_data = request.POST.get('signature')
    format, imgstr = signature_data.split(';base64,')
    ext = format.split('/')[-1]
    image = ContentFile(base64.b64decode(imgstr), name=f'firma.{ext}')

    consent.signature = image
    consent.save()

    context = {
        'answers':answers_dict,
        'client':client,
        'consent':consent,
        'company':getCompanyPerAgent(client.agent_usa),
        'social_security':request.POST.get('socialSecurity'),
        'current_date':current_date,
        'date_more_3_months':date_more_3_months,
        'ip':getIPClient(request)    
    }

    activate(language)
    # Renderiza la plantilla HTML a un string
    html_content = render_to_string('consent/templatePdfLifeInsurance.html', context)

    # Genera el PDF
    pdf_file = HTML(string=html_content).write_pdf()

    # Usa BytesIO para convertir el PDF en un archivo
    pdf_io = io.BytesIO(pdf_file)
    pdf_io.seek(0)  # Asegúrate de que el cursor esté al principio del archivo

    # Guarda el PDF en el modelo usando un ContentFile
    pdf_name = f'Consent{client.full_name} #{client.phone_number} {datetime.now().strftime("%m-%d-%Y-%H:%M")}.pdf'  # Nombre del archivo

    consent.pdf.save(pdf_name, ContentFile(pdf_io.read()), save=True)

def save_data_from_request(model_class, post_data, exempted_fields, instance=None):
    """
    Guarda o actualiza los datos de un request.POST en la base de datos utilizando un modelo específico.

    Args:
        model_class (models.Model): Modelo de Django al que se guardarán los datos.
        post_data (QueryDict): Datos enviados en el request.POST.
        instance (models.Model, optional): Instancia existente del modelo para actualizar.
                                        Si es None, se creará un nuevo registro.

    Returns:
        models.Model: Instancia del modelo guardada o actualizada.
        False: Si ocurre algún error durante el proceso.
    """
    try:
        # Crear un diccionario con las columnas del modelo y sus valores correspondientes
        model_fields = [field.name for field in model_class._meta.fields]
        data_to_save = {}

        for field in model_fields:
            if field in exempted_fields:
                continue
            if field in post_data:
                data_to_save[field] = post_data[field]

        if instance:
            # Si se proporciona una instancia, actualizamos sus campos
            for field, value in data_to_save.items():
                setattr(instance, field, value)
            instance.save()
            return instance
        else:
            # Si no hay instancia, creamos una nueva
            instance = model_class(**data_to_save)
            instance.save()
            return instance

    except Exception as e:
        return False

def save_contact_client_checkboxes(post_data, contact_instance):
    """
    Guarda o actualiza los campos de tipo checkbox en ContactClient (phone, email, sms, whatsapp).
    
    Args:
        post_data (QueryDict): Datos enviados en el request.POST.
        contact_instance (ContactClient): Instancia de ContactClient a actualizar.

    Returns:
        ContactClient: Instancia de ContactClient actualizada.
    """
    checkbox_fields = ['phone', 'email', 'sms', 'whatsapp']
    
    # Asegúrate de que solo los campos seleccionados se marquen como True
    for field in checkbox_fields:
        # Si el checkbox está marcado (enviará 'on'), lo asignamos como True
        if post_data.get(field) == 'on':
            setattr(contact_instance, field, True)
        else:
            setattr(contact_instance, field, False)
    
    contact_instance.save()  # Guardar la instancia actualizada
    return contact_instance

def save_contact_medicare_checkboxes(post_data, contact_instance):
    """
    Guarda o actualiza los campos de tipo checkbox en ContactClient (phone, email, sms, whatsapp).
    
    Args:
        post_data (QueryDict): Datos enviados en el request.POST.
        contact_instance (ContactClient): Instancia de ContactClient a actualizar.

    Returns:
        ContactClient: Instancia de ContactClient actualizada.
    """
    checkbox_fields = ['prescripcion', 'advantage', 'dental', 'complementarios','suplementarios']
    
    # Asegúrate de que solo los campos seleccionados se marquen como True
    for field in checkbox_fields:
        # Si el checkbox está marcado (enviará 'on'), lo asignamos como True
        if post_data.get(field) == 'on':
            setattr(contact_instance, field, True)
        else:
            setattr(contact_instance, field, False)
    
    contact_instance.save()  # Guardar la instancia actualizada
    return contact_instance

def getCompanyPerAgent(agent):
    agent_upper = agent.upper()

    if "GINA" in agent_upper or "LUIS" in agent_upper:
        company = "TRUINSURANCE GROUP LLC"
    elif any(substring in agent_upper for substring in ["DANIEL", "ZOHIRA", "DANIESKA", "VLADIMIR", "FRANK"]):
        company = "LAPEIRA & ASSOCIATES LLC"
    elif any(substring in agent_upper for substring in ["BORJA", "RODRIGO", "EVELYN"]):
        company = "SECUREPLUS INSURANCE LLC"
    else:
        company = ""  # Valor predeterminado si no hay coincidencia
    return company

def getIPClient(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]  # Puede haber múltiples IPs separadas por comas
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# View para generar solo el token
def generateTemporaryToken(client, typeToken):
    signer = Signer()

    expiration_time = timezone.now() + timedelta(minutes=90)

    # Crear el token con la fecha de expiración usando JSON
    data = {
        'client_id': client.id,
        'expiration': expiration_time.isoformat(),
    }
    signed_data = signer.sign(json.dumps(data))  # Firmar los datos serializados
    token = urlsafe_base64_encode(force_bytes(signed_data))  # Codificar seguro para URL

    # Guardar solo el token en la base de datos
    if typeToken == 'lifeInsurance':
        TemporaryToken.objects.create(
            life_insurance=client,
            token=token,
            expiration=expiration_time
        )
    elif typeToken == 'obamacare':
        TemporaryToken.objects.create(
            client=client,
            token=token,
            expiration=expiration_time
        )
    else:
        TemporaryToken.objects.create(
            medicare = client,
            token=token,
            expiration=expiration_time
        )

    # Retornar solo el token (no se genera ni guarda la URL temporal)
    return token

# Vista para verificar y procesar la URL temporal
def validateTemporaryToken(request, typeToken):
    token = request.POST.get('token') or request.GET.get('token')

    if not token:
        return False, 'Token no proporcionado. Not found token.'

    signer = Signer()
    
    try:
        signed_data = force_str(urlsafe_base64_decode(token))
        data = json.loads(signer.unsign(signed_data))

        if typeToken == 'obamacare':
            client_id = data.get('client_id')
            expiration_time = timezone.datetime.fromisoformat(data['expiration'])
            # Verificar si el token está activo y no ha expirado
            tempToken = TemporaryToken.objects.get(token=token, client_id=client_id)
        elif typeToken == 'lifeInsurance':
            life_insurance = data.get('client_id')
            expiration_time = timezone.datetime.fromisoformat(data['expiration'])
            # Verificar si el token está activo y no ha expirado
            tempToken = TemporaryToken.objects.get(token=token, life_insurance_id=life_insurance)
        else:
            medicare_id = data.get('client_id')
            expiration_time = timezone.datetime.fromisoformat(data['expiration'])
            # Verificar si el token está activo y no ha expirado
            tempToken = TemporaryToken.objects.get(token=token, medicare_id=medicare_id)

        if not tempToken.is_active:
            return False, 'Enlace desactivado. Link deactivated.'

        if tempToken.is_expired():
            return False, 'Enlace ha expirado. Link expired.'

        return True, 'Success'
    
    except (BadSignature, ValueError, KeyError):
        return False, 'Token inválido o alterado. Invalid token.'

def deactivateTemporaryToken(request):
    token = request.POST.get('token') or request.GET.get('token')
    if not token:
        return False, 'Token no proporcionado. Not found token.'
    
    tempToken = TemporaryToken.objects.get(token=token)
    tempToken.is_active = False
    tempToken.save()

def redirect_with_token(request, view_name, *args, **kwargs):
    token = request.GET.get('token')
    url = reverse(view_name, args=args, kwargs=kwargs)
    query_params = urlencode({'token': token})
    return redirect(f'{url}?{query_params}')
