# Standard Python libraries
import datetime
import re

# Django utilities
from django.http import JsonResponse, HttpResponse
from django.utils.timezone import make_aware

# Django core libraries
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

# Third-party libraries
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer  

# Application-specific imports
from app.models import *


@login_required(login_url='/login') 
def saveCustomerObservationACA(request):
    if request.method == "POST":
        content = request.POST.get('textoIngresado')
        plan_id = request.POST.get('plan_id')
        type_plan = request.POST.get('type_plan')
        typeCall = request.POST.get('typeCall')  
        way = request.POST.get('way')        


        # Obtenemos las observaciones seleccionadas
        observations = request.POST.getlist('observaciones[]')  # Lista de valores seleccionados
        
        # Convertir las observaciones a una cadena (por ejemplo, separada por comas o saltos de línea)
        typification_text = ", ".join(observations)  # Puedes usar "\n".join(observations) si prefieres saltos de línea
    
        plan = ObamaCare.objects.get(id=plan_id)

        if content.strip():  # Validar que el texto no esté vacío
            ObservationCustomer.objects.create(
                client=plan.client,
                agent=request.user,
                id_plan=plan.id,
                type_police=type_plan,
                typeCall=typeCall,
                typification=typification_text, # Guardamos las observaciones en el campo 'typification'
                content=content
            )
            messages.success(request, "Observación guardada exitosamente.")
        else:
            messages.error(request, "El contenido de la observación no puede estar vacío.")

        return redirect('editObama', plan.id, way)       
        
    else:
        return HttpResponse("Método no permitido.", status=405)

@login_required(login_url='/login') 
def saveCustomerObservationSupp(request):
    if request.method == "POST":
        content = request.POST.get('textoIngresado')
        plan_id = request.POST.get('plan_id')
        type_plan = request.POST.get('type_plan')
        typeCall = request.POST.get('typeCall')        

        # Obtenemos las observaciones seleccionadas
        observations = request.POST.getlist('observaciones[]')  # Lista de valores seleccionados
        
        # Convertir las observaciones a una cadena (por ejemplo, separada por comas o saltos de línea)
        typification_text = ", ".join(observations)  # Puedes usar "\n".join(observations) si prefieres saltos de línea

        plan = Supp.objects.get(id=plan_id) 

        if content.strip():  # Validar que el texto no esté vacío
            ObservationCustomer.objects.create(
                client=plan.client,
                agent=request.user,
                id_plan=plan.id,
                type_police=type_plan,
                typeCall=typeCall,
                typification=typification_text, # Guardamos las observaciones en el campo 'typification'
                content=content
            )
            messages.success(request, "Observación guardada exitosamente.")
        else:
            messages.error(request, "El contenido de la observación no puede estar vacío.")

        return redirect('editSupp', plan.id)        
        
    else:
        return HttpResponse("Método no permitido.", status=405)


@login_required(login_url='/login') 
def saveCustomerObservationMedicare(request):
    if request.method == "POST":
        content = request.POST.get('textoIngresado')
        medicare_id = request.POST.get('plan_id')
        typeCall = request.POST.get('typeCall')        

        # Obtenemos las observaciones seleccionadas
        observations = request.POST.getlist('observaciones[]')  # Lista de valores seleccionados
        
        # Convertir las observaciones a una cadena (por ejemplo, separada por comas o saltos de línea)
        typification_text = ", ".join(observations)  # Puedes usar "\n".join(observations) si prefieres saltos de línea

        medicare = Medicare.objects.filter(id = medicare_id).first()

        if content.strip():  # Validar que el texto no esté vacío
            ObservationCustomerMedicare.objects.create(
                medicare=medicare,
                agent=request.user,
                typeCall=typeCall,
                typification=typification_text, # Guardamos las observaciones en el campo 'typification'
                content=content
            )
            messages.success(request, "Observación guardada exitosamente.")
        else:
            messages.error(request, "El contenido de la observación no puede estar vacío.")

        return redirect('editClientMedicare', medicare_id)       
        
    else:
        return HttpResponse("Método no permitido.", status=405)

def desactiveMedicare(request, medicare_id):
    # Obtener el cliente por su ID
    medicare = get_object_or_404(Medicare, id=medicare_id)
    
    # Cambiar el estado de is_active (True a False o viceversa)
    medicare.is_active = not medicare.is_active
    medicare.save()  # Guardar los cambios en la base de datos
    
    # Redirigir de nuevo a la página actual con un parámetro de éxito
    return redirect('clientMedicare')
 
def validarCita(request):
    fecha_str = request.GET.get('fecha')
    agente = request.GET.get('agente')

    try:
        # Convertir la fecha recibida en un objeto datetime
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M")
        fecha = make_aware(fecha)  # Asegurar que tenga zona horaria

        # Verificar si ya hay una cita en esa fecha y hora para el mismo agente
        cita_existente = Medicare.objects.filter(dateMedicare=fecha, agent_usa=agente).exists()

        return JsonResponse({"ocupado": cita_existente})
    
    except ValueError:
        return JsonResponse({"error": "Fecha no válida"}, status=400)

@login_required(login_url='/login')
def saveDocumentClient(request, obamacare_id, way):
    if request.method == "POST":
        obama = get_object_or_404(ObamaCare, id=obamacare_id)
        documents = request.FILES.getlist("documents")  # 📌 Recibe la lista de archivos
        filenames = request.POST.getlist("filenames")  # 📌 Recibe la lista de nombres

        if not documents:
            return JsonResponse({"success": False, "message": "No se han subido archivos."})

        for index, document in enumerate(documents):
            # ✅ Usa el nombre si existe, si no, asigna "Documento sin nombre"
            document_name = filenames[index].strip() if index < len(filenames) and filenames[index].strip() else document.name

            # ✅ Guarda el documento con el nombre en la BD
            DocumentObama.objects.create(
                file=document,
                name=document_name,  # ✅ Guardar nombre del documento
                obama=obama,
                agent_create=request.user
            )

        messages.success(request, "Archivos subidos correctamente.")
        return JsonResponse({"success": True, "message": "Archivos subidos correctamente.", "redirect_url": f"/editObama/{obamacare_id}/{way}/"})
    
    return JsonResponse({"success": False, "message": "Método no permitido."}, status=405)

@login_required(login_url='/login')
def saveAccionRequired(request):

    description = request.POST.get('description') 
    plan_id = request.POST.get('plan_id') 

    opcion = DropDownList.objects.filter( description = description).first()
    obama = ObamaCare.objects.select_related('client').get(id = plan_id)

    CustomerRedFlag.objects.create(
        obama=obama,
        agent_create=request.user,
        description=description,
        clave = opcion.clave
    )

    #Aqui inicia el websocket
    app_name = request.get_host()  # Obtener el host (ej. "127.0.0.1:8000" o "miapp.com")

    # Reemplazar ":" y otros caracteres inválidos con "_" para hacer un nombre válido
    app_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', app_name)

    group_name = f'product_alerts_{app_name}'

    channel_layer = get_channel_layer()

    # Construir la URL absoluta
    url_relativa = reverse('editObama', args=[obama.id, 2])
    url_absoluta = request.build_absolute_uri(url_relativa)

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'send_alert',
            'event_type': 'newAccionRequired',
            'icon': 'warning',
            'title': 'New Action Required',
            'buttonMessage': 'Go to customer with required action.',
            'message': f'New action required for the customer: {obama.client.first_name} {obama.client.last_name}',
            'absoluteUrl': url_absoluta,
            'agent': {
                'id': obama.agent.id,
                'username': obama.agent.username
            }
        }
    )
    
    return redirect('editObama', obama.id, 1 )  

@login_required(login_url='/login')
def saveAppointment(request, obamacare_id):
    
    obama = ObamaCare.objects.get(id = obamacare_id)
    appointment = request.POST.get('appointment') 
    dateAppointment = request.POST.get('dateAppointment') 
    timeAppointment = request.POST.get('timeAppointment') 
    way = request.POST.get('way')  

    # Conversión de date a la BD requerido
    dateAppointmentNew = datetime.datetime.strptime(dateAppointment, '%m/%d/%Y').date()          

    AppointmentClient.objects.create(
        obama=obama,
        agent_create=request.user,
        appointment=appointment,
        dateAppointment = dateAppointmentNew,
        timeAppointment=timeAppointment,
    )

    return redirect('editObama', obamacare_id, way)   

