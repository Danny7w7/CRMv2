#libreria necesarias
from django.template.loader import render_to_string
from weasyprint import HTML
from weasyprint import HTML
from django.conf import settings
import boto3
import os

from django.utils.timezone import make_aware
import datetime
from collections import defaultdict
from django.db.models import Subquery
from app.models import CustomerRedFlag, ObamaCare, Supp, ClientsAssure, ClientsLifeInsurance  # Ajusta según tu estructura

def generateWeeklyPdf(week_number):

    ventas_matriz, detalles_clientes, rango_fechas, dias_semana, totales_por_dia, gran_total_aca, gran_total_supp = weekSalesSummarySms(week_number)

    html_string = render_to_string('pdf/reportWekkly.html', {
        'ventas_matriz': ventas_matriz,
        'rango_fechas': rango_fechas,
        'detalles_clientes': detalles_clientes,
        'dias_semana': dias_semana,
        'totales_por_dia': totales_por_dia,
        'gran_total_aca': gran_total_aca,
        'gran_total_supp': gran_total_supp,
        'week_number': week_number
    })

    html = HTML(string=html_string)
    pdf = html.write_pdf()

    # Guardar localmente
    filename = f'reporte_semana_{week_number}.pdf'
    local_path = os.path.join(settings.MEDIA_ROOT, 'reportes', filename)

    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    with open(local_path, 'wb') as f:
        f.write(pdf)

    return local_path, filename

def uploadTempUrl(local_path, s3_filename, expires_in=1800):
    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME
    )

    bucket = settings.AWS_STORAGE_BUCKET_NAME
    s3.upload_file(local_path, bucket, s3_filename, ExtraArgs={'ACL': 'private'})

    url = s3.generate_presigned_url(
        ClientMethod='get_object',
        Params={'Bucket': bucket, 'Key': s3_filename},
        ExpiresIn=expires_in
    )

    return url

def weekSalesSummarySms(week_number):

    current_year = datetime.datetime.today().year
    startOfWeek = datetime.datetime.fromisocalendar(current_year, week_number, 1)  # lunes
    endOfWeek = startOfWeek + datetime.timedelta(days=5)  # sábado

    startOfWeek = make_aware(startOfWeek)
    endOfWeek = make_aware(endOfWeek)

    excludedUsernames = ['Calidad01', 'mariluz', 'MariaCaTi', 'StephanieMkt', 'CarmenR', 'tv', 'zohiraDuarte', 'vladimirDeLaHoz']

    excluded_obama_ids = CustomerRedFlag.objects.values('obamacare')

    sales_data = defaultdict(lambda: defaultdict(lambda: {"ACA": 0, "SUPP": 0}))
    client_data = defaultdict(lambda: {"clientes_obama": [], "clientes_supp": []})

    obamaSales = ObamaCare.objects.select_related('client').filter(created_at__range=[startOfWeek, endOfWeek], company = 2 , is_active=True).exclude(id__in=Subquery(excluded_obama_ids))
    suppSales = Supp.objects.select_related('client').filter(created_at__range=[startOfWeek, endOfWeek], company = 2 , is_active=True)
    assureSales = ClientsAssure.objects.filter(created_at__range=[startOfWeek, endOfWeek], company = 2 , is_active=True)
    lifeSales = ClientsLifeInsurance.objects.filter(created_at__range=[startOfWeek, endOfWeek], company = 2, is_active=True)

    def get_day_key(dt):
        return dt.strftime('%A')  # Ej: 'Monday', 'Tuesday', ...

    for sale in obamaSales:
        if sale.agent.is_active and sale.agent.username not in excludedUsernames:
            day_key = get_day_key(sale.created_at)
            sales_data[sale.agent.get_full_name()][day_key]["ACA"] += 1

            # Agregar cliente a la lista
            client_data[sale.agent.get_full_name()]["clientes_obama"].append({
                'nombre': sale.client.first_name,  # Ajusta según tu modelo
                'fecha_poliza': sale.created_at.strftime('%Y-%m-%d'),
                'estatus': sale.status 
            })

    for sale in suppSales:
        if sale.agent.is_active and sale.agent.username not in excludedUsernames:
            day_key = get_day_key(sale.created_at)
            sales_data[sale.agent.get_full_name()][day_key]["SUPP"] += 1

            # Agregar cliente a la lista
            client_data[sale.agent.get_full_name()]["clientes_supp"].append({
                'nombre': sale.client.first_name,  # Ajusta según tu modelo
                'fecha_poliza': sale.created_at.strftime('%Y-%m-%d'),
                'estatus': sale.status,
                'policy_type': sale.policy_type
            })

    for sale in assureSales:
        if sale.agent.is_active and sale.agent.username not in excludedUsernames:
            day_key = get_day_key(sale.created_at)
            sales_data[sale.agent.get_full_name()][day_key]["SUPP"] += 1

            # Agregar cliente a la lista
            client_data[sale.agent.get_full_name()]["clientes_supp"].append({
                'nombre': sale.first_name,  # Ajusta según tu modelo
                'fecha_poliza': sale.created_at.strftime('%Y-%m-%d'),
                'estatus': sale.status,
                'policy_type': 'ASSURE'
            })

    for sale in lifeSales:
        if sale.agent.is_active and sale.agent.username not in excludedUsernames:
            day_key = get_day_key(sale.created_at)
            sales_data[sale.agent.get_full_name()][day_key]["SUPP"] += 1

            # Agregar cliente a la lista
            client_data[sale.agent.get_full_name()]["clientes_supp"].append({
                'nombre': sale.full_name,  # Ajusta según tu modelo
                'fecha_poliza': sale.created_at.strftime('%Y-%m-%d'),
                'estatus': sale.status,
                'policy_type': 'LIFE INSURANCE'
            })

    week_days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    rango_fechas = f"{startOfWeek.strftime('%d/%m')} - {endOfWeek.strftime('%d/%m')}"

    prepared_data = []
    
    # Inicializar totales por día
    totales_por_dia = {}
    for day in week_days_order:
        totales_por_dia[day] = {"ACA": 0, "SUPP": 0}
    
    # Variables para totales generales
    gran_total_aca = 0
    gran_total_supp = 0
    
    for agent_name, days_data in sales_data.items():
        agent_row = {
            'nombre': agent_name,
            'dias': []
        }
        
        # Variables para calcular totales del agente
        total_aca = 0
        total_supp = 0
        
        for day in week_days_order:
            day_sales = days_data.get(day, {"ACA": 0, "SUPP": 0})
            agent_row['dias'].append({
                'aca': day_sales["ACA"],
                'supp': day_sales["SUPP"]
            })
            
            # Sumar a los totales del agente
            total_aca += day_sales["ACA"]
            total_supp += day_sales["SUPP"]
            
            # Sumar a los totales por día
            totales_por_dia[day]["ACA"] += day_sales["ACA"]
            totales_por_dia[day]["SUPP"] += day_sales["SUPP"]
        
        # Agregar totales del agente
        agent_row['totales'] = {
            'total_aca': total_aca,
            'total_supp': total_supp
        }
        
        # Sumar a los grandes totales
        gran_total_aca += total_aca
        gran_total_supp += total_supp
        
        prepared_data.append(agent_row)

    prepared_client_data = []

    for agent_name, client_info in client_data.items():
        if client_info["clientes_obama"] or client_info["clientes_supp"]:
            prepared_client_data.append({
                'nombre': agent_name,
                'clientes_obama': client_info["clientes_obama"],
                'clientes_supp': client_info["clientes_supp"]
            })
    
    return prepared_data, prepared_client_data, rango_fechas, week_days_order, totales_por_dia, gran_total_aca, gran_total_supp
