# Standard Python libraries
import re

# Django utilities
from django.http import JsonResponse

# Django core libraries
from django.contrib.auth.decorators import login_required

# Third-party libraries
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer  

# Application-specific imports
from app.models import *


@login_required(login_url='/login') 
def fetchAca(request, client_id):
    client = Clients.objects.get(id=client_id)
    aca_plan_id = request.POST.get('acaPlanId')

    if aca_plan_id:
        # Si el ID existe, actualiza el registro
        ObamaCare.objects.filter(id=aca_plan_id).update(
            taxes=request.POST.get('taxes'),
            agent_usa=request.POST.get('agent_usa'),
            plan_name=request.POST.get('planName'),
            work=request.POST.get('work'),
            subsidy=request.POST.get('subsidy'),
            carrier=request.POST.get('carrierObama'),
            doc_income=request.POST.get('doc_income'),
            doc_migration=request.POST.get('doc_migration'),
            observation=request.POST.get('observationObama'),
            premium=request.POST.get('premium')
        )
        aca_plan = ObamaCare.objects.get(id=aca_plan_id)
        created = False

    else:
        # Si no hay ID, crea un nuevo registro
        aca_plan, created = ObamaCare.objects.update_or_create(
            client=client,
            agent=request.user,
            company = client.company,
            defaults={
                'taxes': request.POST.get('taxes'),
                'agent_usa': request.POST.get('agent_usa'),
                'plan_name': request.POST.get('planName'),
                'work': request.POST.get('work'),
                'subsidy': request.POST.get('subsidy'),
                'carrier': request.POST.get('carrierObama'),
                'observation': request.POST.get('observationObama'),
                'doc_migration': request.POST.get('doc_migration'),
                'doc_income': request.POST.get('doc_income'),
                'premium': request.POST.get('premium'),
                'status_color': 1,
                'profiling':'NO',
                'status':'IN PROGRESS'
            }
        )

        if not aca_plan.doc_income and aca_plan.doc_migration:
            users = Users.objects.filter(id = 1)
            CustomerRedFlag.objects.create(
                obama = aca_plan,
                agent_create = users,
                description = 'MISSING DOCUMENTS',
                clave = 'UPLOAD DOCUMENTS'
            )

        #Aqui inicia el websocket
        app_name = request.get_host()  # Obtener el host (ej. "127.0.0.1:8000" o "miapp.com")
    
        # Reemplazar ":" y otros caracteres inválidos con "_" para hacer un nombre válido
        app_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', app_name)

        group_name = f'product_alerts_{app_name}'

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'send_alert',
                'event_type': 'newClient',
                'icon': 'success',
                'title': 'New Client!',
                'message': f'New product Obamacare added',
            }
        )

    return JsonResponse({'success': True, 'aca_plan_id': aca_plan.id})

@login_required(login_url='/login') 
def fetchSupp(request, client_id):
    client = Clients.objects.get(id=client_id)
    supp_data = {}
    updated_supp_ids = []  # Lista para almacenar los IDs de los registros suplementarios

    # Filtrar solo los datos que corresponden a suplementario y organizarlos por índices
    for key, value in request.POST.items():
        if key.startswith('supplementary_plan_data'): #pregunta como inicia el string
            # Obtener índice y nombre del campo
            try:
                index = key.split('[')[1].split(']')[0]  # Extrae el índice del suplementario
                field_name = key.split('[')[2].split(']')[0]  # Extrae el nombre del campo
            except IndexError:
                continue  # Ignora las llaves que no tengan el formato esperado
            
            # Inicializar un diccionario para el suplementario si no existe
            if index not in supp_data:
                supp_data[index] = {}

            # Almacenar el valor del campo en el diccionario correspondiente
            supp_data[index][field_name] = value

    # Guardar cada dependiente en la base de datos
    for sup_data in supp_data.values():
        if 'carrierSuple' in sup_data:  # Verificar que al menos el nombre esté presente
            supp_id = sup_data.get('id')  # Obtener el id si está presente

            if supp_id:  # Si se proporciona un id, actualizar el registro existente
                Supp.objects.filter(id=supp_id).update(
                    effective_date=sup_data.get('effectiveDateSupp'),
                    agent_usa=sup_data.get('agent_usa'),
                    carrier=sup_data.get('carrierSuple'),
                    premium=sup_data.get('premiumSupp'),
                    policy_type=sup_data.get('policyTypeSupp'),
                    preventive=sup_data.get('preventiveSupp'),
                    coverage=sup_data.get('coverageSupp'),
                    deducible=sup_data.get('deducibleSupp'),
                    observation=sup_data.get('observationSuple'),
                )
                updated_supp_ids.append(supp_id)  # Agregar el ID actualizado a la lista
            else:  # Si no hay id, crear un nuevo registro
                new_supp = Supp.objects.create(
                    client=client,
                    status='REGISTERED',
                    company = client.company,
                    agent=request.user,
                    effective_date=sup_data.get('effectiveDateSupp'),
                    agent_usa=sup_data.get('agent_usa'),
                    carrier=sup_data.get('carrierSuple'),
                    premium=sup_data.get('premiumSupp'),
                    policy_type=sup_data.get('policyTypeSupp'),
                    preventive=sup_data.get('preventiveSupp'),
                    coverage=sup_data.get('coverageSupp'),
                    deducible=sup_data.get('deducibleSupp'),
                    observation=sup_data.get('observationSuple'),
                    status_color = 1
                )
                updated_supp_ids.append(new_supp.id)  # Agregar el ID creado a la lista


                #Aqui inicia el websocket
                app_name = request.get_host()  # Obtener el host (ej. "127.0.0.1:8000" o "miapp.com")
    
                # Reemplazar ":" y otros caracteres inválidos con "_" para hacer un nombre válido
                app_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', app_name)

                group_name = f'product_alerts_{app_name}'

                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    group_name,
                    {
                        'type': 'send_alert',
                        'event_type': 'newClient',
                        'icon': 'success',
                        'title': 'New Client!',
                        'message': f'New product Supplemental added',
                    }
                )

    return JsonResponse({'success': True,  'supp_ids': updated_supp_ids})

@login_required(login_url='/login')      
def fetchDependent(request, client_id):
    client = Clients.objects.get(id=client_id)
    dependents_data = {}
    updated_dependents_ids = []

    # Procesar datos de dependientes como antes
    for key, value in request.POST.items():
        if key.startswith('dependent'):
            try:
                index = key.split('[')[1].split(']')[0]
                field_name = key.split('[')[2].split(']')[0]
            except IndexError:
                continue
            
            if index not in dependents_data:
                dependents_data[index] = {}

            dependents_data[index][field_name] = value

    # Crear lista de dependientes
    dependents_to_add = []
    for dep_data in dependents_data.values():
        if 'nameDependent' in dep_data:
            dependent_id = dep_data.get('id')

            # Procesar múltiples valores de type_police
            type_police_values = dep_data.get('typePoliceDependents', [])
            type_police = ", ".join(type_police_values.split(',') if type_police_values else [])

            # Lógica para asociar ObamaCare
            obamacare = None
            if 'ACA' in type_police:
                # Buscar un plan ObamaCare para el cliente
                obamacare = ObamaCare.objects.filter(client=client).first()

            # Crear o actualizar Dependent
            if dependent_id:
                dependent = Dependents.objects.get(id=dependent_id)
                for attr, value in {
                    'name': dep_data.get('nameDependent'),
                    'apply': dep_data.get('applyDependent'),
                    'date_birth': dep_data.get('dateBirthDependent'),
                    'migration_status': dep_data.get('migrationStatusDependent'),
                    'sex': dep_data.get('sexDependent'),
                    'kinship': dep_data.get('kinship'),
                    'type_police': type_police,
                    'obamacare': obamacare
                }.items():
                    setattr(dependent, attr, value)
                dependent.save()
            else:
                dependent = Dependents.objects.create(
                    client=client,
                    name=dep_data.get('nameDependent'),
                    apply=dep_data.get('applyDependent'),
                    date_birth=dep_data.get('dateBirthDependent'),
                    migration_status=dep_data.get('migrationStatusDependent'),
                    sex=dep_data.get('sexDependent'),
                    kinship=dep_data.get('kinship'),
                    type_police=type_police,
                    obamacare=obamacare
                )

            dependents_to_add.append(dependent)
            updated_dependents_ids.append(dependent.id)

    # Obtener todos los Supp para este cliente
    supps = Supp.objects.filter(client=client)
    
    # Agregar todos los dependientes a cada Supp
    for supp in supps:
        supp.dependents.clear()  # Limpiar relaciones existentes
        supp.dependents.add(*dependents_to_add)

    return JsonResponse({
        'success': True,
        'dependents_ids': updated_dependents_ids
    })
