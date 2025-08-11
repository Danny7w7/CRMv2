# Standard Python libraries
import datetime
import csv
import os

import pandas as pd

# Django utilities
from django.http import HttpResponse, JsonResponse

# Django core libraries
from django.contrib.auth.decorators import login_required
from django.db.models import Count, TextField, Value
from django.db.models.functions import Coalesce
from django.shortcuts import redirect, render 
from django.views.decorators.csrf import csrf_exempt

# Application-specific imports
from app.models import *
from ..forms import *
from .decoratorsCompany import * 

@login_required(login_url='/login') 
@company_ownership_required_sinURL    
def uploadExcel(request):

    company_id = request.company_id  # Obtener company_id desde request
    company = Companies.objects.filter(id = company_id).first()

    headers = []  # Cabeceras del archivo Excel
    model_fields = [field.name for field in BdExcel._meta.fields if field.name not in ['id', 'agent_id', 'excel_metadata']]

    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        file_name = request.POST.get('file_name')
        description = request.POST.get('description')

        if form.is_valid() and file_name:
            excel_file = request.FILES['file']            

            try:
                # Leer el archivo Excel para extraer las cabeceras
                df = pd.read_excel(excel_file, engine='openpyxl')
                headers = list(df.columns)  # Extraer las cabeceras del archivo

                # Convertir valores a tipos compatibles con JSON
                df = df.applymap(
                    lambda x: x.isoformat() if isinstance(x, pd.Timestamp) else x
                )

                # Crear un registro en ExcelFileMetadata
                try:
                    excel_metadata = ExcelFileMetadata.objects.create(
                        file_name=file_name,
                        description=description,
                        uploaded_at=datetime.datetime.now(),
                        company = company
                    )
                except Exception as e:
                    print("❌ Error al crear el registro en ExcelFileMetadata:", str(e))


                # Guardar el DataFrame en la sesión para usarlo después
                request.session['uploaded_data'] = df.to_dict(orient='list')  # Convertir a diccionario serializable
                request.session['uploaded_headers'] = headers
                request.session['metadata_id'] = excel_metadata.id  # Guardar ID del archivo para usarlo luego

            except Exception as e:
                return render(request, 'addExcelsDB/uploadExcel.html', {
                    'form': form,
                    'error': f"Error al procesar el archivo: {str(e)}"
                })

            # Renderizar la página de mapeo
            return render(request, 'addExcelsDB/mapHeaders.html', {
                'headers': headers,
                'model_fields': model_fields
                
            })
    else:
        form = ExcelUploadForm()

    return render(request, 'addExcelsDB/uploadExcel.html', {'form': form})

def processAndSave(request):
    if request.method == 'POST':
        # Obtener el mapeo entre los campos del modelo y las cabeceras del archivo
        mapping = {}
        for key, value in request.POST.items():
            if key.startswith('mapping_'):
                model_field = key.replace('mapping_', '')  # Campo del modelo
                header = value  # Cabecera del archivo seleccionada
                mapping[model_field] = header

        # Recuperar la ruta del archivo desde la sesión
        uploaded_file_path = request.session.get('uploaded_file_path')
        if not uploaded_file_path or not os.path.exists(uploaded_file_path):
            return render(request, 'addExcelsDB/uploadExcel.html', {'error': 'No se encontró el archivo Excel. Por favor, súbelo nuevamente.'})

        try:
            # Leer el archivo Excel desde la ruta temporal
            df = pd.read_excel(uploaded_file_path, engine='openpyxl')

            # Iterar sobre las filas del DataFrame y guardar en la BD
            for _, row in df.iterrows():
                data = {}
                for model_field, header in mapping.items():
                    if header in df.columns:  # Verificar que la cabecera esté en el archivo
                        data[model_field] = row[header]
                BdExcel.objects.create(**data)

        except Exception as e:
            return render(request, 'addExcelsDB/uploadExcel.html', {
                'error': f"Error al procesar el archivo: {str(e)}"
            })

        # Limpiar la sesión y eliminar el archivo temporal
        request.session.pop('uploaded_file_path', None)
        os.remove(uploaded_file_path)

        return render(request, 'excel/header_processed.html', {'mapping': mapping, 'success': True})
    else:
        return render(request, 'addExcelsDB/uploadExcel.html', {'form': ExcelUploadForm()})

def saveData(request):
    if request.method == 'POST':
        # Obtener el mapeo entre los campos del modelo y las cabeceras del archivo
        mapping = {}
        for key, value in request.POST.items():
            if key.startswith('mapping_'):
                model_field = key.replace('mapping_', '')
                header = value
                if header:
                    mapping[model_field] = header

        # Recuperar los datos cargados previamente desde la sesión
        uploaded_data = request.session.get('uploaded_data')
        metadata_id = request.session.get('metadata_id')
        if not uploaded_data or not metadata_id:
            return render(request, 'addExcelsDB/uploadExcel.html', {'error': 'No se encontraron datos para procesar.'})

        # Recuperar el registro de ExcelFileMetadata
        excel_metadata = ExcelFileMetadata.objects.get(id=metadata_id)

        # Convertir el diccionario de vuelta a un DataFrame
        df = pd.DataFrame(uploaded_data)

        # Inicializar una lista para errores
        errors = []
        valid_data = []  # Datos válidos para guardar

        # Validar cada fila
        for index, row in df.iterrows():
            row_errors = {}
            data = {}
            for model_field, header in mapping.items():
                if header in df.columns:
                    value = row[header]
                    # Validaciones por campo del modelo
                    if model_field == 'first_name' and not isinstance(value, str):
                        row_errors[model_field] = 'Debe ser una cadena de texto.'
                    elif model_field == 'last_name' and value is not None and not isinstance(value, str):
                        row_errors[model_field] = 'Debe ser una cadena de texto o nulo.'
                    elif model_field == 'phone':
                        try:
                            value = int(value)
                        except (ValueError, TypeError):
                            row_errors[model_field] = 'Debe ser un número entero.'
                    elif model_field == 'zipCode':
                        try:
                            value = int(value)
                        except (ValueError, TypeError):
                            row_errors[model_field] = 'Debe ser un número entero.'
                    elif model_field == 'agent_id' and value is not None:
                        try:
                            value = int(value)
                        except (ValueError, TypeError):
                            row_errors[model_field] = 'Debe ser un número entero o nulo.'

                    data[model_field] = value

            if row_errors:
                errors.append({'row': index + 1, 'errors': row_errors})
            else:
                # Agregar datos válidos para guardarlos más tarde
                valid_data.append(data)

        # Si hay errores, mostrarlos al usuario
        if errors:
            return render(request, 'addExcelsDB/mapHeaders.html', {
                'headers': request.session['uploaded_headers'],
                'model_fields': [field.name for field in BdExcel._meta.fields if field.name not in ('id','agent_id' ,'excel_metadata')],
                'errors': errors
            })

        # Guardar los datos válidos
        for data in valid_data:
            BdExcel.objects.create(excel_metadata=excel_metadata, **data)

        # Limpiar los datos de la sesión
        request.session.pop('uploaded_data', None)
        request.session.pop('uploaded_headers', None)
        request.session.pop('metadata_id', None)

        return render(request, 'addExcelsDB/success.html', {'message': 'Datos guardados exitosamente.'})
    else:
        return redirect('addExcelsDB/uploadExcel')

@login_required(login_url='/login') 
@company_ownership_required_sinURL  
def manageAgentAssignments(request):

    company_id = request.company_id  # Obtener company_id desde request    
    # Definir el filtro de compañía (será un diccionario vacío si es superusuario)
    company_filter = {'company': company_id} if not request.user.is_superuser else {}

    if request.method == 'POST':
        # Obtener el archivo seleccionado y los agentes
        file_id = request.POST.get('file_name')
        user_ids = request.POST.getlist('users')  # Usuarios para asignar o quitar
        action = request.POST.get('action')  # Determinar si es asignar o quitar

        if not file_id:
            return render(request, 'addExcelsDB/manageAgentAssignments.html', {
                'files': ExcelFileMetadata.objects.filter(**company_filter),
                'users': Users.objects.filter(role='A',is_active=True, **company_filter),
                'error': 'Debes seleccionar un archivo.'
            })

        # Recuperar el archivo seleccionado
        try:
            file = ExcelFileMetadata.objects.filter(id=file_id, **company_filter).first()
        except ExcelFileMetadata.DoesNotExist:
            return render(request, 'addExcelsDB/manageAgentAssignments.html', {
                'files': ExcelFileMetadata.objects.filter(**company_filter),
                'users': Users.objects.filter(role='A',is_active=True, **company_filter),
                'error': 'El archivo seleccionado no es válido.'
            })

        # Validar que se seleccionen usuarios
        if not user_ids:
            return render(request, 'addExcelsDB/manageAgentAssignments.html', {
                'files': ExcelFileMetadata.objects.filter(**company_filter),
                'users': Users.objects.filter(role='A',is_active=True, **company_filter),
                'error': 'Debes seleccionar al menos un usuario.'
            })

        if action == 'assign':
            # Asignar registros equitativamente a los agentes seleccionados
            users = Users.objects.filter(id__in=user_ids, role='A', **company_filter)
            if not users.exists():
                return render(request, 'addExcelsDB/manageAgentAssignments.html', {
                    'files': ExcelFileMetadata.objects.filter(**company_filter),
                    'users': Users.objects.filter(role='A',is_active=True, **company_filter),
                    'error': 'Los usuarios seleccionados no son válidos.'
                })

            # Recuperar registros asociados al archivo
            records = BdExcel.objects.filter(excel_metadata=file)

            # Distribuir registros equitativamente
            user_count = len(users)
            user_ids = list(users.values_list('id', flat=True))
            for i, record in enumerate(records):
                record.agent_id = user_ids[i % user_count]
                record.save()

            return render(request, 'addExcelsDB/manageAgentAssignments.html', {
                'files': ExcelFileMetadata.objects.filter(** company_filter),
                'users': Users.objects.filter(role='A',is_active=True, **company_filter),
                'success': f'Registros de {file.file_name} distribuidos exitosamente entre los usuarios seleccionados.'
            })

        elif action == 'remove':
            # Quitar asignaciones de los usuarios seleccionados
            BdExcel.objects.filter(excel_metadata=file, agent_id__in=user_ids).update(agent_id=None)

            return render(request, 'addExcelsDB/manageAgentAssignments.html', {
                'files': ExcelFileMetadata.objects.filter(** company_filter),
                'users': Users.objects.filter(role='A',is_active=True, **company_filter),
                'success': f'Asignaciones eliminadas para los agentes seleccionados del archivo {file.file_name}.'
            })

        else:
            return render(request, 'addExcelsDB/manageAgentAssignments.html', {
                'files': ExcelFileMetadata.objects.filter(**company_filter),
                'users': Users.objects.filter(role='A',is_active=True, **company_filter),
                'error': 'Acción no válida.'
            })

    return render(request, 'addExcelsDB/manageAgentAssignments.html', {
        'files': ExcelFileMetadata.objects.filter(**company_filter),
        'users': Users.objects.filter(role='A',is_active=True, **company_filter)
    })

@login_required(login_url='/login')
@company_ownership_required_sinURL  
def commentDB(request):

    company_id = request.company_id  # Obtener company_id desde request    
    # Definir el filtro de compañía (será un diccionario vacío si es superusuario)
    company_filter = {'excel_metadata__company': company_id} if not request.user.is_superuser else {}
    company_filter2 = {'company': company_id} if not request.user.is_superuser else {}

    roleAuditar = ['S', 'Admin']
    filterBd = None

    # Obtén las opciones para el select desde el modelo DropDownList
    optionBd = DropDownList.objects.values_list('status_bd', flat=True).exclude(status_bd__isnull=True)
    comenntAgent = CommentBD.objects.all()

    # Filtra los registros dependiendo del rol del usuario
    if request.user.role in roleAuditar:
        bd = BdExcel.objects.filter(**company_filter)
        bdName = ExcelFileMetadata.objects.filter(**company_filter2)
    else:
        bd = BdExcel.objects.filter(agent_id=request.user.id, is_sold = False, **company_filter)
        bdName = ExcelFileMetadata.objects.filter(**company_filter2)

    if request.method == 'POST':        

        filterBd =  request.POST.get('bd')
        bd = bd.filter(excel_metadata = filterBd)    


    # Si es una solicitud GET, simplemente renderizamos la vista con los datos
    context = {
        'optionBd': optionBd,
        'bd': bd,
        'comenntAgent':comenntAgent,
        'bdName' : bdName,
        'filter' : filterBd
    }

    return render(request, 'addExcelsDB/bd.html', context)

@login_required(login_url='/login')
@csrf_exempt
def saveCommentAjax(request):
    record_id = request.POST.get('record_id')
    observation = request.POST.get('observation')

    if not record_id or not observation:
        return JsonResponse({'success': False, 'message': 'Please select a valid option.'}, status=400)

    try:
        bd_excel_record = BdExcel.objects.get(id=record_id)

        CommentBD.objects.create(
            bd_excel=bd_excel_record,
            agent_create=request.user,
            content=observation,
            excel_metadata=bd_excel_record.excel_metadata
        )

        if observation == 'SOLD':
            bd_excel_record.is_sold = True
            bd_excel_record.save()

        return JsonResponse({'success': True, 'message': 'Observation saved successfully.'})
    except BdExcel.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Record not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required(login_url='/login')
@company_ownership_required_sinURL  
def reportBd(request):
        
    company_id = request.company_id  # Obtener company_id desde request    
    # Definir el filtro de compañía (será un diccionario vacío si es superusuario)
    company_filter = {'company': company_id} if not request.user.is_superuser else {}

    BD = ExcelFileMetadata.objects.filter(**company_filter)

    if request.method == "POST":
        action = request.POST.get("action")  # Identificar qué formulario se está enviando

        if action == "show":
            # Procesar formulario de listar
            filterBd = request.POST.get("bd")
            if not filterBd:
                return render(request, 'addExcelsDB/reportBd.html', {'BDS': BD, 'error': 'Please select a BD'})

            filterBd = int(filterBd)
            nameBd = ExcelFileMetadata.objects.filter(id=filterBd).first()

            # Generar datos para mostrar en la tabla
            comment_with_content = (
                CommentBD.objects
                .filter(excel_metadata=filterBd)
                .exclude(content__isnull=True, content__exact='')
                .values(content_label=Coalesce('content', Value('PENDING', output_field=TextField())))
                .annotate(amount=Count('content'))
            )

            pending_count = (
                BdExcel.objects
                .filter(excel_metadata_id=filterBd)
                .exclude(id__in=CommentBD.objects.filter(excel_metadata=filterBd).values_list('bd_excel', flat=True))
                .count()
            )

            all_comments = list(comment_with_content)
            if pending_count > 0:
                all_comments.append({'content_label': 'PENDING', 'amount': pending_count})

            context = {
                'BDS': BD,
                'all_comments': all_comments,
                'nameBd': nameBd,
                'filterBd': filterBd,  # Pasamos el BD seleccionado al contexto
            }

            return render(request, 'addExcelsDB/reportBd.html', context)

        elif action == "download":
            # Procesar formulario de descargar
            filterBd = request.POST.get("filterBd")  # Recibimos el BD ya seleccionado
            content_label = request.POST.get("content_label")
            if not filterBd or not content_label:
                return render(request, 'addExcelsDB/reportBd.html', {'BDS': BD, 'error': 'Please select a category'})

            # Llamar a la función de descarga
            return downloadBdExcelByCategory(int(filterBd), content_label)

    return render(request, 'addExcelsDB/reportBd.html', {'BDS': BD})

def downloadBdExcelByCategory(filterBd, content_label):
    if content_label == "PENDING":
        # Obtener registros sin comentarios
        bd_excel_data = BdExcel.objects.filter(
            excel_metadata_id=filterBd
        ).exclude(
            id__in=CommentBD.objects.filter(excel_metadata=filterBd).values_list('bd_excel', flat=True)
        )
    else:
        # Obtener registros relacionados con la categoría
        bd_excel_data = BdExcel.objects.filter(
            excel_metadata_id=filterBd,
            commentbd__content=content_label
        ).distinct()

    # Crear el archivo CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="Excel_{content_label}.csv"'

    writer = csv.writer(response)
    writer.writerow(['First Name', 'Last Name', 'Phone', 'Address', 'City', 'State', 'Zip Code', 'Agent ID', 'Is Sold'])

    for item in bd_excel_data:
        writer.writerow([
            item.first_name,
            item.last_name or '',
            item.phone,
            item.address or '',
            item.city or '',
            item.state or '',
            item.zipCode or '',
            item.agent_id or '',
            'Yes' if item.is_sold else 'No'
        ])

    return response

