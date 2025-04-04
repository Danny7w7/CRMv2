import openpyxl

# Django utilities
from django.http import HttpResponse
from django.template.loader import render_to_string

# Django core libraries
from django.contrib.auth.decorators import login_required
from django.db.models import Q

# Third-party libraries
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration  # Agregar aquí

# Application-specific imports
from app.models import *
from .table import weekSalesSummary
from ..decoratorsCompany import *

def downloadPdf(request, week_number):
    # Obtener el resumen de la semana seleccionada
    resumen_semana, rango_fechas = weekSalesSummary(week_number)

    # Renderizar la plantilla específica para el PDF
    html_string = render_to_string('pdf/reportWekkly.html', {
        'resumen_semana': resumen_semana,
        'rango_fechas': rango_fechas,
        'week_number': week_number
    })

    # Crear un objeto HTML de WeasyPrint
    font_config = FontConfiguration()
    html = HTML(string=html_string)
    
    # Generar el PDF
    pdf = html.write_pdf(font_config=font_config)

    # Crear una respuesta HTTP con el PDF
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_semana_{week_number}.pdf"'
    return response

@login_required(login_url='/login')
@company_ownership_required_sinURL
def downloadAccionRequired(request):

    company_id = request.company_id  # Obtener company_id desde request
    # Definir el filtro de compañía (será un diccionario vacío si es superusuario)
    company_filter = Q(obamacare__company=company_id) if not request.user.is_superuser else Q()

    accionRequired = request.POST.get("accionRequired")
    start_date = request.POST.get("start_date")
    end_date = request.POST.get("end_date")

    pending_filter = Q()
    completed_filter = Q()
    date_filter = Q()

    if accionRequired == 'PENDING':
        pending_filter = Q(date_completed=None)
    elif accionRequired == 'COMPLETED':
        completed_filter = ~Q(date_completed=None)

    # Ajustar filtros de fecha si están definidos
    if start_date and end_date:  # Asegurarse de que las fechas no sean None
        date_filter = Q(created_at__range=[start_date, end_date])
    elif start_date:
        date_filter = Q(created_at__gte=start_date)
    elif end_date:
        date_filter = Q(created_at__lte=end_date)

    # Obtener las Acciones requeridas que correspondan a los filtros aplicados
    actionRequireds = CustomerRedFlag.objects.select_related("obamacare__client", "agent_create","agent_completed").filter(
        pending_filter & completed_filter & date_filter & company_filter
    )


    # ✅ Crear un nuevo archivo Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Clientes Action Required"

    # ✅ Encabezados
    headers = ["First Name (Clients)", "Last Name (Clients)", "Status Client","Action Required", "Solution", "Date", "Agent Created", "Date Completed","Agent Completed"]
    ws.append(headers)

    # ✅ Agregar datos al archivo Excel
    for i in actionRequireds:
        ws.append([
            i.obamacare.client.first_name,
            i.obamacare.client.last_name,
            i.obamacare.status,
            i.description,
            i.clave,
            i.created_at.strftime("%m-%d-%Y") if i.created_at else '',
            f"{i.agent_create.first_name } {i.agent_create.last_name}" if i.agent_create else '',
            i.date_completed.strftime("%m-%d-%Y") if i.date_completed else '',  # Convertir fecha a string legible
            f"{i.agent_completed.first_name} {i.agent_completed.last_name}" if i.agent_completed else ''
        ])

    # ✅ Preparar la respuesta HTTP
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f'attachment; filename="clientes Ation Required.xlsx"'
    wb.save(response)

    return response 

@login_required(login_url='/login')
@company_ownership_required_sinURL
def paymentClients(request):

    company_id = request.company_id  # Obtener company_id desde request
    # Definir el filtro de compañía (será un diccionario vacío si es superusuario)
    company_filter = {'company': company_id} if not request.user.is_superuser else {}

    months = request.POST.getlist("months")  # Capturar lista de meses seleccionados
    # Obtener pagos que correspondan a los meses seleccionados
    clients = Payments.objects.select_related("obamaCare").filter(month__in=months,  **company_filter)

    # ✅ Crear un nuevo archivo Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Clientes_PAYMENT"

    # ✅ Encabezados
    headers = ["First Name", "Last Name", "Plan", "Carrier", "Profiling", "Date-Profiling", "Status", "Created At","Month","Date payment was marked"]
    ws.append(headers)

    # ✅ Agregar datos al archivo Excel
    for client in clients:
        if client.obamaCare.is_active:
            ws.append([
                client.obamaCare.client.first_name,
                client.obamaCare.client.last_name,
                client.obamaCare.plan_name,
                client.obamaCare.carrier,
                client.obamaCare.profiling,
                client.obamaCare.profiling_date.strftime("%m-%d-%Y") if client.obamaCare.profiling_date else '',
                client.obamaCare.status,
                client.obamaCare.created_at.strftime("%m-%d-%Y") if client.obamaCare.created_at else '',  # Convertir fecha a string legible
                client.month,
                client.created_at.strftime("%m-%d-%Y")
            ])

    # ✅ Preparar la respuesta HTTP
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f'attachment; filename="clientes.xlsx"'
    wb.save(response)

    return response 
