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

        return redirect('editClientObama', plan.id, way)       
        
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

        return redirect('editClientSupp', plan.id)        
        
    else:
        return HttpResponse("Método no permitido.", status=405)

@login_required(login_url='/login') 
def typification(request):
        
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    agent = Users.objects.filter(role__in=['A', 'C'])
    
    # Consulta base
    typification = ObservationCustomer.objects.select_related('agent', 'client').filter(is_active = True)

    # Si no se proporcionan fechas, mostrar registros del mes actual   
    # Obtener el primer día del mes actual con zona horaria
    today = timezone.now()
    first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Obtener el último día del mes actual
    if today.month == 12:
        # Si es diciembre, el último día será el 31
        last_day_of_month = today.replace(day=31, hour=23, minute=59, second=59, microsecond=999999)
    else:
        # Para otros meses, usar el día anterior al primer día del siguiente mes
        last_day_of_month = (first_day_of_month.replace(month=first_day_of_month.month+1) - timezone.timedelta(seconds=1))
    
    typification = typification.filter(created_at__range=[first_day_of_month, last_day_of_month])

    if request.method == 'POST':

        # Obtener parámetros de fecha del request
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')       
        nameAgent = request.POST.get('agent')
        nameTypification = request.POST.get('typification')

        # Consulta base
        typification = ObservationCustomer.objects.select_related('agent', 'client').filter(is_active = True)   
        
     
        # Convertir fechas a objetos datetime con zona horaria
        start_date = timezone.make_aware(
            datetime.strptime(start_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
        )
        end_date = timezone.make_aware(
            datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)
        )
        
        typification = typification.filter(
            created_at__range=[start_date, end_date],
            agent = nameAgent,
            typification__contains = nameTypification
        )

        # Ordenar por fecha de creación descendente
        typification = typification.order_by('-created_at')

        return render(request, 'table/typification.html', {
            'typification': typification,
            'start_date': start_date,
            'end_date': end_date,
            'agents' : agent
        })

    return render(request, 'customerReports/typification.html', {
            'typification': typification,
            'start_date': start_date,
            'end_date': end_date,
            'agents' : agent
        })

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
        return JsonResponse({"success": True, "message": "Archivos subidos correctamente.", "redirect_url": f"/editClientObama/{obamacare_id}/{way}/"})
    
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
    url_relativa = reverse('editClientObama', args=[obama.id, 2])
    url_absoluta = request.build_absolute_uri(url_relativa)

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'send_alert',
            'event_type': 'new_accion_required',
            'message': f'New action required for the customer: {obama.client.first_name} {obama.client.last_name}',
            'extra_info': url_absoluta,
            'agent': {
                'id': obama.agent.id,
                'username': obama.agent.username
            }
        }
    )
    
    return redirect('editClientObama', obama.id, 1 )  

@login_required(login_url='/login')
def saveAppointment(request, obamacare_id):
    
    obama = ObamaCare.objects.get(id = obamacare_id)
    appointment = request.POST.get('appointment') 
    dateAppointment = request.POST.get('dateAppointment') 
    timeAppointment = request.POST.get('timeAppointment') 
    way = request.POST.get('way')  

    # Conversión de date a la BD requerido
    dateAppointmentNew = datetime.strptime(dateAppointment, '%m/%d/%Y').date()          

    AppointmentClient.objects.create(
        obama=obama,
        agent_create=request.user,
        appointment=appointment,
        dateAppointment = dateAppointmentNew,
        timeAppointment=timeAppointment,
    )

    return redirect('editClientObama', obamacare_id, way)   

