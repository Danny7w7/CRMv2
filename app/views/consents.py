# Standard Python libraries
import base64
import io
import json
import logging
import re
import smtplib
import ssl
from datetime import timedelta, datetime
from types import SimpleNamespace

# Django utilities
from django.core.files.base import ContentFile
from django.core.signing import BadSignature, Signer
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from email.message import EmailMessage

# Django core libraries
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.translation import activate
from django.views.decorators.http import require_POST
from urllib.parse import urlencode

# Third-party libraries
from weasyprint import HTML

# Application-specific imports
from app.models import *
from ..alertWebsocket import websocketAlertGeneric
from app.utils import enviar_email, uploadTempUrl
logger = logging.getLogger(__name__)

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

    if request.user.is_superuser:
        agentUsa = USAgent.objects.all().prefetch_related("company")
    else:
        agentUsa = USAgent.objects.filter(company = obamacare.company).prefetch_related("company")

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
    
    dependents = Dependents.objects.filter(obamacare=obamacare)
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
        'supps': supps,
        'agentUsa' : agentUsa
    }

    return render(request, 'consent/consent1.html', context)

def complaint(request, obamacare_id,validationUniq):

    obamacare = ObamaCare.objects.select_related('client', 'agent').get(id=obamacare_id)
    complaint = Complaint.objects.filter(obamacare=obamacare_id).last()
    temporalyURL = None
    id_complaint = f"{obamacare.id:08d}"
    typeToken = 'obamacare'

    # Validar si el usuario no está logueado y verificar el token
    if isinstance(request.user, AnonymousUser):
        result = validateTemporaryToken(request, typeToken)
        is_valid_token, *note = result
        if not is_valid_token:
            return HttpResponse(note)
    elif request.user.is_authenticated:
        # Usuario autenticado
        temporalyURL = request.build_absolute_uri(f"/complaint/{obamacare_id}/{validationUniq}/?token={generateTemporaryToken(obamacare.client, typeToken)}")
    else:
        # Si el usuario no está logueado y no hay token válido
        return HttpResponse('Acceso denegado. Por favor, inicie sesión o use un enlace válido.')
    

    if request.method == 'POST':
        
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
            
        return generateComplaintPdf(request, obamacare, validationUniq)

    context = {
        'valid_migration_statuses': ['PERMANENT_RESIDENT', 'US_CITIZEN', 'EMPLOYMENT_AUTHORIZATION'],
        'obamacare':obamacare,
        'company':getCompanyPerAgent(obamacare.agent_usa),
        'temporalyURL': temporalyURL,
        'complaint':complaint,
        'id_complaint' :id_complaint
    }
    return render(request, 'complaint/complaint.html', context)
    
def incomeLetter(request, obamacare_id):

    obamacare = ObamaCare.objects.select_related('client').get(id=obamacare_id)
    signed = IncomeLetter.objects.filter(obamacare = obamacare_id).first()

    language = request.GET.get('lenguaje', 'es')  # Idioma predeterminado si no se pasa
    activate(language)

    temporalyURL = None
    typeToken = 'obamacare' 


    # Validar si el usuario no está logueado y verificar el token
    if isinstance(request.user, AnonymousUser):
        typeToken = 'obamacare' #Aqui le indico si buscar el token temporal por el medicare o client_id
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

    id = f"{obamacare.id:08d}"

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
        'var':var,
        'id': id
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

def generateComplaintPdf(request, obamacare,validationUniq):

    id_complaint = f"{obamacare.id:08d}"
    current_date = datetime.now().strftime("%A, %B %d, %Y %I:%M")    
    complaint = Complaint.objects.get(id=validationUniq)

    signature_data = request.POST.get('signature')
    format, imgstr = signature_data.split(';base64,')
    ext = format.split('/')[-1]
    image = ContentFile(base64.b64decode(imgstr), name=f'firma.{ext}')

    complaint.signature = image
    complaint.save()

    context = {
        'obamacare':obamacare,
        'company':getCompanyPerAgent(obamacare.agent_usa),
        'current_date':current_date,
        'ip':getIPClient(request),
        'complaint':complaint,
        'id_complaint' :id_complaint
    }

    # Renderiza la plantilla HTML a un string
    html_content = render_to_string('complaint/templateComplaint.html', context)

    # Genera el PDF
    pdf_file = HTML(string=html_content).write_pdf()

    # Usa BytesIO para convertir el PDF en un archivo
    pdf_io = io.BytesIO(pdf_file)
    pdf_io.seek(0)  # Asegúrate de que el cursor esté al principio del archivo

    # Guarda el PDF en el modelo usando un ContentFile
    pdf_name = f'Complaint {obamacare.client.first_name}_{obamacare.client.last_name}#{obamacare.client.phone_number} {datetime.now().strftime("%A, %B %d, %Y %I:%M")}.pdf'  # Nombre del archivo

    complaint.pdf.save(pdf_name, ContentFile(pdf_io.read()), save=True)

    deactivateTemporaryToken(request)

    return render(request, 'consent/endView.html')

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

    id = f"{obamacare.id:08d}"

    context = {
        'obamacare':obamacare,
        'current_date':current_date,
        'ip':getIPClient(request),
        'incomeLetter':incomeLetter,
        'id': id
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
    id = f"{obamacare.id:08d}"

    context = {
        'obamacare':obamacare,
        'current_date':current_date,
        'ip':getIPClient(request),
        'signature': signature,
        'id': id
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

        if request.user.is_authenticated:
            asks = AskLifeInsurance.objects.all()  
            answersUpdate = AnswerLifeInsurance.objects.filter(client = client_id)  
            
            
            if answersUpdate:
                for ask in asks:
                    answer = request.POST.get(str(ask.id)) 
                    AnswerLifeInsurance.objects.filter(ask = ask.id).update(
                        answer=answer
                    )    
            else:
                for ask in asks:
                    answer = request.POST.get(str(ask.id))
                    AnswerLifeInsurance.objects.create(
                        client=client,
                        agent=request.user,
                        ask=ask,
                        answer=answer,
                        company=client.company
                    )
                

            return redirect('ConsentLifeInsurance', client_id)

        else:

            language = request.GET.get('lenguaje', 'es')  # Idioma predeterminado si no se pasa
            for answer in answers:
                # Usa el ID de la pregunta (ask.id) como clave
                key = str(answer.ask.id)
                value = request.POST.get(key)
                
                # Crea un mini diccionario que tenga el nombre correcto del campo
                post_data = {'answer': value}
                
                updated = save_data_from_request(AnswerLifeInsurance, post_data, ['signature'], answer)
            
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

@csrf_exempt
def sendConsentForm(request):

    try:

        now = datetime.now()        
        
        # Obtener el archivo PDF
        pdf_file = request.FILES.get('pdf_file')
        
        if not pdf_file:
            return JsonResponse({
                'success': False,
                'error': 'No se encontró el archivo PDF'
            }, status=400)
        
        # Leer el contenido del PDF
        pdf_content = pdf_file.read()

        import tempfile

        # Guardamos el PDF temporalmente
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(pdf_content)
            temp_pdf_path = temp_pdf.name  # Esto es lo que necesita uploadTempUrl

        # Luego lo pasas aquí
        s3_key = f"consent_forms/test_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        s3_url = uploadTempUrl(temp_pdf_path, s3_key)

        email_subject = f"📄 Consent Lapeira - {now.strftime('%d/%m/%Y')}"
        email_body = f"""Estimado/a,

            Se ha generado un Consent proveniente de Lapeira.com {now.strftime('%d de %B de %Y a las %H:%M')}.

            Para mas informacion contactar a el equipo de IT.

            Saludos cordiales,
            Sistema de Reportes"""

        # Llamar a la función reutilizable
        email_enviado = enviar_email(
            destinatario='it.bluestream2@gmail.com',
            asunto=email_subject,
            cuerpo=email_body,
            archivo_adjunto=temp_pdf_path,
            nombre_archivo=f'Consent {pdf_file.name}'
        )
        
        
        return JsonResponse({
            'success': True,
            'message': 'Formulario enviado correctamente'
        })
        
    except Exception as e:
        #logger.error(f'Error general al enviar formulario de consentimiento: {str(e)}', exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)

def consentL(request):
    """Vista para mostrar el formulario de consentimiento"""
    response = render(request, 'consent/consentL.html')
    response["Content-Security-Policy"] = "frame-ancestors https://lapeirainsurance.com https://truinsurancegroup.com/"
    return response

def cignaSuplemental(request, supp_id):
    temporalyURL = None
    typeToken = 'obamacare'
    supp = Supp.objects.select_related('client', 'agent').get(id=supp_id)

    # Validar acceso
    if isinstance(request.user, AnonymousUser):
        result = validateTemporaryToken(request, typeToken)
        is_valid_token, *note = result
        if not is_valid_token:
            return HttpResponse(note)
    elif request.user.is_authenticated:
        temporalyURL = request.build_absolute_uri(
            f"/cignaSuplemental/{supp_id}/?token={generateTemporaryToken(supp.client, typeToken)}"
        )
    else:
        return HttpResponse('Acceso denegado. Por favor, inicie sesión o use un enlace válido.')
    
    # cargar draft
    draft = CignaSuplementalDraft.objects.filter(supp=supp).first()
    form_data = draft.data if draft else {}
    form_data = SimpleNamespace(**form_data) 

    if request.method == 'POST':
        # ✅ Capturar todos los datos del formulario
        uno = request.POST.get('uno')
        dos = request.POST.get('dos')
        tres = request.POST.get('tres')
        cuatro = request.POST.get('cuatro')
        cinco = request.POST.get('cinco')
        seis = request.POST.get('seis')
        siete = request.POST.get('siete')
        ocho = request.POST.get('ocho')
        phoneFinancial = request.POST.get('phoneFinancial')
        addressFinancial = request.POST.get('addressFinancial')
        numberRouting = request.POST.get('numberRouting')
        accountNumber = request.POST.get('accountNumber')
        dateWithdrawal = request.POST.get('dateWithdrawal')
        monthly = request.POST.get('monthly')
        quarterly = request.POST.get('quarterly')
        semiAnnually = request.POST.get('semiAnnually')
        annually = request.POST.get('annually')
        personalChecking = request.POST.get('personalChecking')
        personalSavings = request.POST.get('personalSavings')
        corporate = request.POST.get('corporate')
        nueve = request.POST.get('nueve')
        diez = request.POST.get('diez')
        once = request.POST.get('once')
        doce = request.POST.get('doce')
        nameEmployer = request.POST.get('nameEmployer')
        nameDepositor = request.POST.get('nameDepositor')

        # ✅ Crear el registro en BD
        cignaS = CignaSuplemental.objects.create(supp=supp)

        # ✅ Procesar la firma
        signature_data = request.POST.get('signature')
        format, imgstr = signature_data.split(';base64,')
        ext = format.split('/')[-1]
        image = ContentFile(base64.b64decode(imgstr), name=f'firma.{ext}')
        cignaS.signature = image
        cignaS.save()

        # ✅ Preparar contexto
        id_complaint = f"{supp.id:08d}"
        current_date = datetime.now().strftime("%A, %B %d, %Y %I:%M")
        context = {
            'supp': supp,
            'ip': getIPClient(request),
            'cignaS': cignaS,
            'id_complaint': id_complaint,
            # 🔽 Incluimos todos los campos del formulario en el contexto
            'uno': uno, 'dos': dos, 'tres': tres, 'cuatro': cuatro,
            'cinco': cinco, 'seis': seis, 'siete': siete, 'ocho': ocho,
            'phoneFinancial': phoneFinancial, 'addressFinancial': addressFinancial,
            'numberRouting': numberRouting, 'accountNumber': accountNumber,
            'dateWithdrawal': dateWithdrawal, 'monthly': monthly,
            'quarterly': quarterly, 'semiAnnually': semiAnnually, 'annually': annually,
            'personalChecking': personalChecking, 'personalSavings': personalSavings,
            'corporate': corporate, 'nueve': nueve, 'diez': diez,
            'once': once, 'doce': doce, 'nameEmployer': nameEmployer, 'nameDepositor': nameDepositor,
        }

        # ✅ Renderizar template y generar PDF
        html_content = render_to_string('consent/templateCignaSuplemental.html', context)
        pdf_file = HTML(string=html_content).write_pdf()
        pdf_io = io.BytesIO(pdf_file)
        pdf_io.seek(0)

        pdf_name = f'Consent Cigna Suplemental {supp.client.first_name}_{supp.client.last_name}#{supp.client.phone_number} {current_date}.pdf'
        cignaS.pdf.save(pdf_name, ContentFile(pdf_io.read()), save=True)

        # ✅ Notificar
        websocketAlertGeneric(
            request,
            'send_alert',
            'signedConsent',
            'success',
            'Signed consent',
            f'The client {supp.client.first_name} {supp.client.last_name} successfully signed the consent form.',
            'Go to client information',
            f'/editSupp/{supp.id}',
            supp.agent.id,
            supp.agent.username
        )

        deactivateTemporaryToken(request)
        return render(request, 'consent/endView.html')

    # GET → mostrar formulario
    context = {
        'temporalyURL': temporalyURL,
        'supp': supp,
        'form_data' : form_data
    }
    return render(request, 'consent/cignaSuplemental.html', context)

@csrf_exempt
def saveCignaDraft(request, supp_id):
    if request.method == "POST":
        supp = Supp.objects.get(id=supp_id)
        data = json.loads(request.body.decode("utf-8"))

        draft, created = CignaSuplementalDraft.objects.get_or_create(supp=supp)
        draft.data = data
        draft.save()

        return JsonResponse({"status": "ok"})
    return JsonResponse({"error": "Invalid request"}, status=400)

@require_POST
def sendEmailComplaint(request):
    try:
        idFirstConsent = request.POST.get('firstConsent')
        idLastConsent = request.POST.get('lastConsent')
        idComplaint = request.POST.get('complaint')
        unscrupulousAgent = request.POST.get('nameUnscrupulousAgent')
        unscrupulousAgentNPN = request.POST.get('npnUnscrupulousAgent')

        firstConsentObject = Consents.objects.select_related(
            "obamacare", 
            "obamacare__client"
        ).filter(id=idFirstConsent).first()
        lastConsentObject = Consents.objects.filter(id=idLastConsent).first()
        complaintObject = Complaint.objects.filter(id=idComplaint).first()

        # Validar que los objetos existan
        if not firstConsentObject or not lastConsentObject or not complaintObject:
            return JsonResponse({
                'success': False, 
                'error': 'No se encontraron todos los objetos requeridos'
            }, status=400)

        firstName = firstConsentObject.obamacare.client.first_name.split()[0]
        lastName = firstConsentObject.obamacare.client.last_name.split()[0][0]
        agentUsa = firstConsentObject.obamacare.agent_usa.upper()
        match = re.match(r"^(.*?)\s*-\s*NPN\s*(\d+)$", agentUsa)   

        
        agentUsa = match.group(1).strip()
        npnAgentUsa = match.group(2).strip()

        # Preparar los archivos PDF - LEER EL CONTENIDO
        pdf_files = []
        
        # Obtener contenido del primer consent
        if firstConsentObject.pdf:
            try:
                firstConsentObject.pdf.open()
                first_pdf_content = firstConsentObject.pdf.read()
                firstConsentObject.pdf.close()
                pdf_files.append({
                    'content': first_pdf_content,
                    'filename': f'{firstConsentObject.pdf.name}.pdf'
                })
            except Exception as e:
                logger.error(f"Error leyendo primer PDF: {e}")
        
        # Obtener contenido del último consent
        if lastConsentObject.pdf:
            try:
                lastConsentObject.pdf.open()
                last_pdf_content = lastConsentObject.pdf.read()
                lastConsentObject.pdf.close()
                pdf_files.append({
                    'content': last_pdf_content,
                    'filename': f'{lastConsentObject.pdf.name}'
                })
            except Exception as e:
                logger.error(f"Error leyendo último PDF: {e}")
        
        # Obtener contenido del complaint
        if complaintObject.pdf:
            try:
                complaintObject.pdf.open()
                complaint_pdf_content = complaintObject.pdf.read()
                complaintObject.pdf.close()
                pdf_files.append({
                    'content': complaint_pdf_content,
                    'filename': f'{complaintObject.pdf.name}.pdf'
                })
            except Exception as e:
                logger.error(f"Error leyendo PDF de complaint: {e}")

        # Verificar que tengamos al menos un PDF
        if not pdf_files:
            return JsonResponse({
                'success': False, 
                'error': 'No se pudieron leer los archivos PDF'
            }, status=400)

        body = f"""
WHOMEVER MAY CONCERNED
ATN: HEALTH MARKETPLACE FRAUD DEPARTMENT

With this email, I hereby would like to report our client's concern about another agent or broker who may have engaged in fraud or abusive conduct by making unauthorized changes to my client's enrollment within the Health Marketplace.

Attached pls find the following documents:

1. Initial consent signed by our client {firstName} {lastName}., dated {firstConsentObject.created_at.strftime("%B %d, %Y")}, where our client {firstName} {lastName} authorizes our agent {agentUsa}, as the Agent on Record for any enrollment or application in the Health Marketplace.

2. Most recent consent signed by our client {firstName} {lastName}., dated {lastConsentObject.created_at.strftime("%B %d, %Y")}, where our client {firstName} {lastName} confirms and authorizes our agent {agentUsa}, as the Agent on Record for any enrollment or application in the Health Marketplace.

3. Complaint form signed by our client {firstName} {lastName}., dated {complaintObject.created_at.strftime("%B %d, %Y")}, against {unscrupulousAgent}, NPN: {unscrupulousAgentNPN}, stating that our client did NOT authorize {unscrupulousAgent} to initiate any enrollment or make changes to our client's application in the Health Marketplace.

In summary, our client {firstName} {lastName}. would like to report this fraudulent activity and expects the Health Marketplace to act accordingly to the legal framework established for this type of illegal activity.
{getCompanyPerAgent(agentUsa)}
Agent: {agentUsa}
NPN: {npnAgentUsa}
    """

        # Enviar email
        success = send_email_with_pdfs(
            subject="Fraud Report",
            email_from=settings.SENDER_EMAIL_ADDRESS_FRAUD,
            email_password=settings.EMAIL_PASSWORD_FRAUD,
            body=body,
            receiver_email=["FFMProducerAssisterHelpDesk@cms.hhs.gov"],
            pdf_files=pdf_files
        )

        if success:
            saveEmailInDatabase(body, firstConsentObject.obamacare, firstConsentObject, lastConsentObject, complaintObject)
            return JsonResponse({
                'success': True, 
                'message': 'Email enviado exitosamente',
                'files_sent': len(pdf_files)
            })
        else:
            return JsonResponse({
                'success': False, 
                'error': 'Error al enviar el email'
            }, status=500)

    except Exception as e:
        logger.error(f"Error en sendEmailComplaint: {e}")
        return JsonResponse({
            'success': False, 
            'error': f'Error interno: {str(e)}'
        }, status=500)

def saveEmailInDatabase(body, obamacare, firstConsent, lastConsent, complaint):
    try:
        email_record = EmailFraudReportRecord.objects.create(
            body=body,
            obamacare=obamacare,
            first_consent=firstConsent,
            last_consent=lastConsent,
            complaint=complaint
        )
        return email_record
    except Exception as e:
        logger.error(f"Error guardando email en base de datos: {e}")
        return None

def send_email_with_pdfs(subject, email_from, email_password, body, receiver_email, pdf_files):
    """
    Envía un email con múltiples archivos PDF adjuntos.
    
    Args:
        subject (str): Asunto del email
        email_from (str): Email del remitente
        email_password (str): Contraseña del remitente
        body (str): Cuerpo del mensaje
        receiver_email (list): Lista de emails destinatarios
        pdf_files (list): Lista de diccionarios con información de PDFs
                         Formato: [{'content': pdf_content, 'filename': 'nombre.pdf'}, ...]
                         O lista de tuplas: [(pdf_content, 'nombre.pdf'), ...]
    
    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    try:
        # Configurar mensaje
        message = EmailMessage()
        message['Subject'] = subject
        message['From'] = email_from
        message['To'] = ', '.join(receiver_email)
        message.set_content(body)

        # Adjuntar múltiples PDFs
        for i, pdf_file in enumerate(pdf_files):
            # Soporte para diferentes formatos de entrada
            if isinstance(pdf_file, dict):
                pdf_content = pdf_file['content']
                filename = pdf_file.get('filename', f'documento_{i+1}.pdf')
            elif isinstance(pdf_file, (tuple, list)) and len(pdf_file) >= 2:
                pdf_content = pdf_file[0]
                filename = pdf_file[1]
            else:
                # Si solo se pasa el contenido, usar nombre genérico
                pdf_content = pdf_file
                filename = f'documento_{i+1}.pdf'
            
            # Validar que el contenido no esté vacío
            if pdf_content:
                message.add_attachment(
                    pdf_content,
                    maintype='application',
                    subtype='pdf',
                    filename=filename
                )
            else:
                print(f"⚠️ Advertencia: PDF vacío omitido - {filename}")

        # Enviar email
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(settings.SMTP_HOST, int(settings.SMTP_PORT), context=context) as server:
            server.login(email_from, email_password)
            server.send_message(message)

        pdf_count = len([pdf for pdf in pdf_files if (isinstance(pdf, dict) and pdf['content']) or 
                        (isinstance(pdf, (tuple, list)) and pdf[0]) or 
                        (not isinstance(pdf, (dict, tuple, list)) and pdf)])
        print(f"✅ Email enviado exitosamente a {receiver_email} con {pdf_count} archivo(s) PDF adjunto(s)")
        return True

    except Exception as e:
        print(f"❌ Error al enviar email: {str(e)}")
        return False