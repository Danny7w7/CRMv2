# Standard Python libraries
import datetime
import csv
import os

import pandas as pd

# Django utilities
from django.http import HttpResponse

# Django core libraries
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, TextField, Value
from django.db.models.functions import Coalesce
from django.shortcuts import redirect, render 

# Application-specific imports
from app.models import *
from ..forms import *

@login_required(login_url='/login')   
def upload_excel(request):
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
                excel_metadata = ExcelFileMetadata.objects.create(
                    file_name=file_name,
                    description=description,
                    uploaded_at=datetime.now()
                )

                # Guardar el DataFrame en la sesión para usarlo después
                request.session['uploaded_data'] = df.to_dict(orient='list')  # Convertir a diccionario serializable
                request.session['uploaded_headers'] = headers
                request.session['metadata_id'] = excel_metadata.id  # Guardar ID del archivo para usarlo luego

            except Exception as e:
                return render(request, 'excel/upload_excel.html', {
                    'form': form,
                    'error': f"Error al procesar el archivo: {str(e)}"
                })

            # Renderizar la página de mapeo
            return render(request, 'excel/map_headers.html', {
                'headers': headers,
                'model_fields': model_fields
            })
    else:
        form = ExcelUploadForm()

    return render(request, 'excel/upload_excel.html', {'form': form})

def process_and_save(request):
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
            return render(request, 'excel/upload_excel.html', {'error': 'No se encontró el archivo Excel. Por favor, súbelo nuevamente.'})

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
            return render(request, 'excel/upload_excel.html', {
                'error': f"Error al procesar el archivo: {str(e)}"
            })

        # Limpiar la sesión y eliminar el archivo temporal
        request.session.pop('uploaded_file_path', None)
        os.remove(uploaded_file_path)

        return render(request, 'excel/header_processed.html', {'mapping': mapping, 'success': True})
    else:
        return render(request, 'excel/upload_excel.html', {'form': ExcelUploadForm()})

def save_data(request):
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
            return render(request, 'excel/upload_excel.html', {'error': 'No se encontraron datos para procesar.'})

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
            return render(request, 'excel/map_headers.html', {
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

        return render(request, 'excel/success.html', {'message': 'Datos guardados exitosamente.'})
    else:
        return redirect('excel/upload_excel')

@login_required(login_url='/login')   
def manage_agent_assignments(request):
    if request.method == 'POST':
        # Obtener el archivo seleccionado y los agentes
        file_id = request.POST.get('file_name')
        user_ids = request.POST.getlist('users')  # Usuarios para asignar o quitar
        action = request.POST.get('action')  # Determinar si es asignar o quitar

        if not file_id:
            return render(request, 'excel/manage_agent_assignments.html', {
                'files': ExcelFileMetadata.objects.all(),
                'users': Users.objects.filter(role='A',is_active=True),
                'error': 'Debes seleccionar un archivo.'
            })

        # Recuperar el archivo seleccionado
        try:
            file = ExcelFileMetadata.objects.get(id=file_id)
        except ExcelFileMetadata.DoesNotExist:
            return render(request, 'excel/manage_agent_assignments.html', {
                'files': ExcelFileMetadata.objects.all(),
                'users': Users.objects.filter(role='A',is_active=True),
                'error': 'El archivo seleccionado no es válido.'
            })

        # Validar que se seleccionen usuarios
        if not user_ids:
            return render(request, 'excel/manage_agent_assignments.html', {
                'files': ExcelFileMetadata.objects.all(),
                'users': Users.objects.filter(role='A',is_active=True),
                'error': 'Debes seleccionar al menos un usuario.'
            })

        if action == 'assign':
            # Asignar registros equitativamente a los agentes seleccionados
            users = Users.objects.filter(id__in=user_ids, role='A')
            if not users.exists():
                return render(request, 'excel/manage_agent_assignments.html', {
                    'files': ExcelFileMetadata.objects.all(),
                    'users': Users.objects.filter(role='A',is_active=True),
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

            return render(request, 'excel/manage_agent_assignments.html', {
                'files': ExcelFileMetadata.objects.all(),
                'users': Users.objects.filter(role='A',is_active=True),
                'success': f'Registros de {file.file_name} distribuidos exitosamente entre los usuarios seleccionados.'
            })

        elif action == 'remove':
            # Quitar asignaciones de los usuarios seleccionados
            BdExcel.objects.filter(excel_metadata=file, agent_id__in=user_ids).update(agent_id=None)

            return render(request, 'excel/manage_agent_assignments.html', {
                'files': ExcelFileMetadata.objects.all(),
                'users': Users.objects.filter(role='A',is_active=True),
                'success': f'Asignaciones eliminadas para los agentes seleccionados del archivo {file.file_name}.'
            })

        else:
            return render(request, 'excel/manage_agent_assignments.html', {
                'files': ExcelFileMetadata.objects.all(),
                'users': Users.objects.filter(role='A',is_active=True),
                'error': 'Acción no válida.'
            })

    return render(request, 'excel/manage_agent_assignments.html', {
        'files': ExcelFileMetadata.objects.all(),
        'users': Users.objects.filter(role='A',is_active=True)
    })

@login_required(login_url='/login')
def commentDB(request):

    roleAuditar = ['S', 'Admin']

    # Obtén las opciones para el select desde el modelo DropDownList
    optionBd = DropDownList.objects.values_list('status_bd', flat=True).exclude(status_bd__isnull=True)
    comenntAgent = CommentBD.objects.all()

    # Filtra los registros dependiendo del rol del usuario
    if request.user.role in roleAuditar:
        bd = BdExcel.objects.all()
    else:
        bd = BdExcel.objects.filter(agent_id=request.user.id, is_sold = False)

    # Si es una solicitud POST, procesamos la observación
    if request.method == 'POST':
        record_id = request.POST.get('record_id')
        observation = request.POST.get('observation')

        # Validar que se envíen los datos necesarios
        if not record_id or not observation:
            messages.error(request, "Please select a valid option.")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        try:
            # Obtener el objeto BdExcel correspondiente al record_id
            bd_excel_record = BdExcel.objects.get(id=record_id)

            # Crear un nuevo comentario en la tabla CommentBD
            CommentBD.objects.create(
                bd_excel=bd_excel_record,  # Relacionar con el objeto BdExcel
                agent_create=request.user,  # Relacionar con el usuario actual
                content=observation,  # Guardar el comentario
                excel_metadata=bd_excel_record.excel_metadata
            )

            # Verificar si la opción seleccionada es "sold"
            if observation == 'SOLD':
                # Actualizar el campo is_sold en BdExcel
                bd_excel_record.is_sold = True
                bd_excel_record.save()

            messages.success(request, "Observation saved successfully.")
        except BdExcel.DoesNotExist:
            messages.error(request, "Record not found.")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")

        # Redirige a la página previa después de guardar
        return redirect(request.META.get('HTTP_REFERER', '/'))

    # Si es una solicitud GET, simplemente renderizamos la vista con los datos
    context = {
        'optionBd': optionBd,
        'bd': bd,
        'comenntAgent':comenntAgent
    }

    return render(request, 'table/bd.html', context)

@login_required(login_url='/login')
def reportBd(request):
    BD = ExcelFileMetadata.objects.all()

    if request.method == "POST":
        action = request.POST.get("action")  # Identificar qué formulario se está enviando

        if action == "show":
            # Procesar formulario de listar
            filterBd = request.POST.get("bd")
            if not filterBd:
                return render(request, 'table/reportBd.html', {'BDS': BD, 'error': 'Please select a BD'})

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

            return render(request, 'table/reportBd.html', context)

        elif action == "download":
            # Procesar formulario de descargar
            filterBd = request.POST.get("filterBd")  # Recibimos el BD ya seleccionado
            content_label = request.POST.get("content_label")
            if not filterBd or not content_label:
                return render(request, 'table/reportBd.html', {'BDS': BD, 'error': 'Please select a category'})

            # Llamar a la función de descarga
            return downloadBdExcelByCategory(int(filterBd), content_label)

    return render(request, 'table/reportBd.html', {'BDS': BD})

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

