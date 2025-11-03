# Standard Python libraries
import datetime
import csv
import os
import json

import pandas as pd

# Django utilities
from django.http import HttpResponse, JsonResponse

# Django core libraries
from django.contrib.auth.decorators import login_required
from django.db.models import Count, TextField, Value, Q
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
    company = Companies.objects.filter(id=company_id).first()

    headers = []  # Cabeceras del archivo Excel
    model_fields = [
        field.name for field in BdExcel._meta.fields
        if field.name not in ['id', 'agent_id', 'excel_metadata']
    ]

    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        file_name = request.POST.get('file_name')
        description = request.POST.get('description')

        if form.is_valid() and file_name:
            excel_file = request.FILES['file']

            try:
                # Leer archivo Excel
                df = pd.read_excel(excel_file, engine='openpyxl')
                headers = list(df.columns)

                # Convertir valores no serializables (como datetime) a texto
                df = df.applymap(
                    lambda x: (
                        x.isoformat() if isinstance(x, (datetime.datetime, pd.Timestamp))
                        else str(x) if isinstance(x, datetime.date)
                        else x
                    )
                )

                # Crear registro en ExcelFileMetadata
                excel_metadata = ExcelFileMetadata.objects.create(
                    file_name=file_name,
                    description=description,
                    uploaded_at=datetime.datetime.now(),
                    company=company
                )

                # Guardar el DataFrame en sesión
                request.session['uploaded_data'] = df.to_dict(orient='list')
                request.session['uploaded_headers'] = headers
                request.session['metadata_id'] = excel_metadata.id

            except Exception as e:
                return render(request, 'addExcelsDB/uploadExcel.html', {
                    'form': form,
                    'error': f"Error al procesar el archivo: {str(e)}"
                })

            # Pasar al mapeo
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
        mapping = {}
        for key, value in request.POST.items():
            if key.startswith('mapping_'):
                model_field = key.replace('mapping_', '')
                header = value
                if header:
                    mapping[model_field] = header

        uploaded_data = request.session.get('uploaded_data')
        metadata_id = request.session.get('metadata_id')

        if not uploaded_data or not metadata_id:
            return render(request, 'addExcelsDB/uploadExcel.html', {
                'error': 'No se encontraron datos para procesar.'
            })

        excel_metadata = ExcelFileMetadata.objects.get(id=metadata_id)
        df = pd.DataFrame(uploaded_data)

        errors = []
        saved_count = 0

        valid_model_fields = [
            f.name for f in BdExcel._meta.fields
            if f.name not in ['id', 'excel_metadata', 'other']
        ]

        for index, row in df.iterrows():
            row_errors = {}
            data = {}
            phone_valid = True

            for model_field, header in mapping.items():
                if header in df.columns:
                    value = row[header]

                    # Limpieza de NaN o NaT
                    if pd.isna(value) or value in ['NaT', 'nan']:
                        value = None

                    # Validaciones básicas
                    if model_field == 'first_name' and value and not isinstance(value, str):
                        row_errors[model_field] = 'Debe ser texto.'
                    elif model_field == 'phone':
                        try:
                            value = int(value)
                        except (ValueError, TypeError):
                            row_errors[model_field] = 'Debe ser número.'
                            phone_valid = False
                    elif model_field == 'zipCode':
                        try:
                            value = int(value)
                        except (ValueError, TypeError):
                            row_errors[model_field] = 'Debe ser número entero.'

                    data[model_field] = value

            # Guardar columnas no mapeadas
            other_data = {
                col: row[col]
                for col in df.columns
                if col not in mapping.values()
            }
            data['other'] = json.dumps(other_data, ensure_ascii=False)

            if phone_valid:
                BdExcel.objects.create(excel_metadata=excel_metadata, **data)
                saved_count += 1
            else:
                row_errors['phone'] = "Fila descartada: phone inválido, no se guardó."

            if row_errors:
                errors.append({'row': index + 1, 'errors': row_errors})

        request.session.pop('uploaded_data', None)
        request.session.pop('uploaded_headers', None)
        request.session.pop('metadata_id', None)

        return render(request, 'addExcelsDB/success.html', {
            'message': f"Se guardaron {saved_count} registros correctamente.",
            'errors': errors
        })

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
    company_id = request.company_id

    # ✅ 1) Obtener timeline (Comentarios + Observaciones)
    if request.GET.get('get_comments'):
        record_id = request.GET.get('record_id')

        comments = CommentBD.objects.filter(
            bd_excel_id=record_id
        ).select_related('agent_create').values(
            'content', 'created_at',
            'agent_create__first_name', 'agent_create__last_name'
        )

        observations = ObservationBD.objects.filter(
            bd_excel_id=record_id
        ).select_related('agent_create').values(
            'content', 'created_at',
            'agent_create__first_name', 'agent_create__last_name'
        )

        timeline = []

        for c in comments:
            timeline.append({
                'text': c['content'],
                'agent_name': f"{c['agent_create__first_name']} {c['agent_create__last_name']}".strip() or "Sistema",
                'date': c['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
                'type': 'Tipificación'
            })

        for o in observations:
            timeline.append({
                'text': o['content'],
                'agent_name': f"{o['agent_create__first_name']} {o['agent_create__last_name']}".strip() or "Sistema",
                'date': o['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
                'type': 'Observación'
            })

        timeline = sorted(timeline, key=lambda x: x['date'], reverse=True)

        return JsonResponse({'comments': timeline})


    # ✅ 2) Petición AJAX de DataTables
    if request.GET.get('draw'):
        return commentDBAjax(request, company_id)


    # ✅ 3) Guardar tipificación u observación (POST AJAX)
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':

        record_id = request.POST.get('record_id')
        excel_metadata_id = request.POST.get('record_id_coment')
        text = request.POST.get('observation')
        mode = request.POST.get('type')  # "comment" o "observation"

        if not record_id or not text or text == 'no_valid':
            return JsonResponse({'success': False, 'error': 'Datos incompletos'}, status=400)

        try:
            bd_excel = BdExcel.objects.get(id=record_id)

            if mode == 'observation':
                ObservationBD.objects.create(
                    bd_excel=bd_excel,
                    agent_create=request.user,
                    excel_metadata_id=excel_metadata_id,
                    content=text
                )
            else:
                CommentBD.objects.create(
                    bd_excel=bd_excel,
                    agent_create=request.user,
                    excel_metadata_id=excel_metadata_id,
                    content=text
                )

            return JsonResponse({'success': True})

        except BdExcel.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Registro no encontrado'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


    # ✅ 4) Render normal de página
    company_filter2 = {'company': company_id} if not request.user.is_superuser else {}

    context = {
        'optionBd': DropDownList.objects.values_list('status_bd', flat=True).exclude(status_bd__isnull=True),
        'comenntAgent': CommentBD.objects.all(),
        'bdName': ExcelFileMetadata.objects.filter(**company_filter2),
        'filter': request.POST.get('bd') if request.method == 'POST' else None
    }

    return render(request, 'addExcelsDB/bd.html', context)

@login_required(login_url='/login')
@csrf_exempt
def commentDBAjax(request, company_id):
    """Maneja las peticiones AJAX de DataTables"""
    
    # Parámetros de DataTables
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 50))
    search_value = request.GET.get('search[value]', '')
    
    # Filtros
    company_filter = {'excel_metadata__company': company_id} if not request.user.is_superuser else {}
    roleAuditar = ['S', 'Admin']
    
    # Filtrar registros según rol
    if request.user.role in roleAuditar:
        bd = BdExcel.objects.select_related('excel_metadata').filter(**company_filter)
    else:
        bd = BdExcel.objects.select_related('excel_metadata').filter(
            agent_id=request.user.id, 
            is_sold=False, 
            **company_filter
        )
    
    # Filtrar por archivo Excel si existe
    filterBd = request.GET.get('bd_filter')
    if filterBd:
        bd = bd.filter(excel_metadata=filterBd)
    
    # Búsqueda global
    if search_value:
        bd = bd.filter(
            Q(first_name__icontains=search_value) |
            Q(last_name__icontains=search_value) |
            Q(phone__icontains=search_value) |
            Q(city__icontains=search_value) |
            Q(state__icontains=search_value) |
            Q(zipCode__icontains=search_value)
        )
    
    # Total de registros
    records_total = bd.count()
    
    # Aplicar paginación
    bd_page = bd[start:start + length]
    
    # 🔧 FUNCIÓN AUXILIAR para limpiar valores NaN/None/Infinity
    def clean_value(value):
        """Convierte valores inválidos en None o strings"""
        if value is None:
            return None
        if isinstance(value, float):
            if value != value:  # Detecta NaN
                return None
            if value == float('inf') or value == float('-inf'):
                return None
        return value
    
    def clean_dict(data):
        """Limpia un diccionario recursivamente"""
        if not isinstance(data, dict):
            return data
        cleaned = {}
        for key, value in data.items():
            if isinstance(value, dict):
                cleaned[key] = clean_dict(value)
            elif isinstance(value, list):
                cleaned[key] = [clean_value(v) for v in value]
            else:
                cleaned[key] = clean_value(value)
        return cleaned
    
    # Preparar datos
    data = []
    for item in bd_page:
        # Parsear other
        pretty_other = None
        try:
            if item.other:
                parsed = json.loads(item.other)
                # Limpiar valores NaN/None/Infinity del diccionario
                pretty_other = clean_dict(parsed)
        except Exception as e:
            print(f"Error parseando 'other' del registro {item.id}: {e}")
            pretty_other = None
        
        row = {
            'id': item.id,
            'is_sold': item.is_sold,
            'first_name': item.first_name or '',
            'last_name': item.last_name or '',
            'phone': item.phone or '',
            'address': item.address or '',
            'city': item.city or '',
            'state': item.state or '',
            'pretty_other': pretty_other,
            'excel_metadata': item.excel_metadata.id if item.excel_metadata else None
        }
        data.append(row)
    
    return JsonResponse({
        'draw': draw,
        'recordsTotal': records_total,
        'recordsFiltered': records_total,
        'data': data
    })

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

