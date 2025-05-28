from django.template.loader import render_to_string
from weasyprint import HTML
from weasyprint import HTML
from django.conf import settings
from datetime import date
import boto3
import os

def generate_weekly_pdf(week_number):

    ventas_matriz, detalles_clientes, rango_fechas, dias_semana = weekSalesSummarySms(week_number,2,False)

    html_string = render_to_string('pdf/reportWekkly.html', {
        'ventas_matriz': ventas_matriz,
        'rango_fechas': rango_fechas,
        'detalles_clientes': detalles_clientes,
        'dias_semana': dias_semana,
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

def upload_and_get_temp_url(local_path, s3_filename, expires_in=1800):
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

def weekSalesSummarySms(week_number, company_id=None, is_superuser=False):
    from django.utils.timezone import make_aware
    import datetime
    from collections import defaultdict
    from django.db.models import Subquery

    current_year = datetime.datetime.today().year
    startOfWeek = datetime.datetime.fromisocalendar(current_year, week_number, 1)  # lunes
    endOfWeek = startOfWeek + datetime.timedelta(days=5)  # sábado

    startOfWeek = make_aware(startOfWeek)
    endOfWeek = make_aware(endOfWeek)

    excludedUsernames = ['Calidad01', 'mariluz', 'MariaCaTi', 'StephanieMkt', 'CarmenR', 'tv', 'zohiraDuarte', 'vladimirDeLaHoz']
    userRoles = ['A', 'C', 'S', 'SUPP', 'Admin']

    company_filter = {'company': company_id} if not is_superuser else {}

    from app.models import Users, CustomerRedFlag, ObamaCare, Supp, ClientsAssure, ClientsLifeInsurance  # Ajusta según tu estructura

    excluded_obama_ids = CustomerRedFlag.objects.values('obamacare')
    users = Users.objects.exclude(username__in=excludedUsernames).filter(role__in=userRoles, is_active=True, **company_filter)

    sales_data = defaultdict(lambda: defaultdict(lambda: {"ACA": 0, "SUPP": 0}))
    client_data = defaultdict(lambda: {"clientes_obama": [], "clientes_supp": []})

    all_days = [startOfWeek + datetime.timedelta(days=i) for i in range(6)]  # lunes a sábado

    obamaSales = ObamaCare.objects.select_related('client').filter(created_at__range=[startOfWeek, endOfWeek], **company_filter).exclude(id__in=Subquery(excluded_obama_ids))
    suppSales = Supp.objects.select_related('client').filter(created_at__range=[startOfWeek, endOfWeek], **company_filter)
    assureSales = ClientsAssure.objects.filter(created_at__range=[startOfWeek, endOfWeek], **company_filter)
    lifeSales = ClientsLifeInsurance.objects.filter(created_at__range=[startOfWeek, endOfWeek], **company_filter)

    def get_day_key(dt):
        return dt.strftime('%A')  # Ej: 'Monday', 'Tuesday', ...

    for sale in obamaSales:
        if sale.agent.is_active and sale.agent.username not in excludedUsernames:
            day_key = get_day_key(sale.created_at)
            sales_data[sale.agent.get_full_name()][day_key]["ACA"] += 1
            client_data[sale.agent.get_full_name()]["clientes_obama"].append({
                'nombre': sale.client.first_name,
                'fecha_poliza': sale.created_at.strftime('%Y-%m-%d'),
                'estatus': sale.status
            })

    for sale in suppSales:
        if sale.agent.is_active and sale.agent.username not in excludedUsernames:
            day_key = get_day_key(sale.created_at)
            sales_data[sale.agent.get_full_name()][day_key]["SUPP"] += 1
            client_data[sale.agent.get_full_name()]["clientes_supp"].append({
                'nombre': sale.client.first_name,
                'fecha_poliza': sale.created_at.strftime('%Y-%m-%d'),
                'estatus': sale.status,
                'poliza_type': sale.policy_type
            })

    for sale in assureSales:
        if sale.agent.is_active and sale.agent.username not in excludedUsernames:
            day_key = get_day_key(sale.created_at)
            sales_data[sale.agent.get_full_name()][day_key]["SUPP"] += 1
            client_data[sale.agent.get_full_name()]["clientes_supp"].append({
                'nombre': sale.first_name,
                'fecha_poliza': sale.created_at.strftime('%Y-%m-%d'),
                'estatus': sale.status,
                'poliza_type': 'Assure'
            })

    for sale in lifeSales:
        if sale.agent.is_active and sale.agent.username not in excludedUsernames:
            day_key = get_day_key(sale.created_at)
            sales_data[sale.agent.get_full_name()][day_key]["SUPP"] += 1
            client_data[sale.agent.get_full_name()]["clientes_supp"].append({
                'nombre': sale.full_name,
                'fecha_poliza': sale.created_at.strftime('%Y-%m-%d'),
                'estatus': sale.status,
                'poliza_type': 'Life Insurance'
            })

    week_days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    rango_fechas = f"{startOfWeek.strftime('%d/%m')} - {endOfWeek.strftime('%d/%m')}"

    prepared_data = []

    for agent_name, days_data in sales_data.items():
        agent_row = {'nombre': agent_name, 'dias': []}
        total_aca = 0
        total_supp = 0
        for day in week_days_order:
            day_sales = days_data.get(day, {"ACA": 0, "SUPP": 0})
            agent_row['dias'].append({
                'aca': day_sales["ACA"],
                'supp': day_sales["SUPP"]
            })
            total_aca += day_sales["ACA"]
            total_supp += day_sales["SUPP"]
        agent_row['totales'] = {
            'total_aca': total_aca,
            'total_supp': total_supp
        }
        prepared_data.append(agent_row)

    prepared_client_data = []
    for agent_name, client_info in client_data.items():
        if client_info["clientes_obama"] or client_info["clientes_supp"]:
            prepared_client_data.append({
                'nombre': agent_name,
                'clientes_obama': client_info["clientes_obama"],
                'clientes_supp': client_info["clientes_supp"]
            })

    return prepared_data, prepared_client_data, rango_fechas, week_days_order

