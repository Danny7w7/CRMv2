from django.template.loader import render_to_string
from weasyprint import HTML
from weasyprint import HTML
from django.conf import settings
from datetime import date
import boto3
import os

def generate_weekly_pdf(week_number):
    from .views.reports.table import  weekSalesSummary # Ajusta la importación según tu estructura

    ventas_matriz, detalles_clientes, rango_fechas, dias_semana = weekSalesSummary(week_number)

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

