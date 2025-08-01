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

    excludedUsernames = ['Calidad01', 'mariluz', 'MariaCaTi', 'CarmenR', 'tv', 'zohiraDuarte', 'vladimirDeLaHoz']

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


import smtplib
import ssl
import logging
from email.message import EmailMessage
from typing import Optional, Union, List
from pathlib import Path

logger = logging.getLogger(__name__)

def enviar_email(
    destinatario: Union[str, List[str]],
    asunto: str,
    cuerpo: str,
    archivo_adjunto: Optional[str] = None,
    nombre_archivo: Optional[str] = None,
    cc: Optional[Union[str, List[str]]] = None,
    bcc: Optional[Union[str, List[str]]] = None,
    es_html: bool = False
) -> bool:
    """
    Función reutilizable para enviar emails con archivos adjuntos opcionales.
    
    Args:
        destinatario: Email del destinatario o lista de emails
        asunto: Asunto del email
        cuerpo: Cuerpo del mensaje
        archivo_adjunto: Ruta del archivo a adjuntar (opcional)
        nombre_archivo: Nombre personalizado para el archivo adjunto (opcional)
        cc: Email(s) en copia (opcional)
        bcc: Email(s) en copia oculta (opcional)
        es_html: True si el cuerpo es HTML, False para texto plano
    
    Returns:
        bool: True si el email se envió correctamente, False en caso contrario
    """
    
    try:
        # Validar que exista el archivo adjunto si se especifica
        if archivo_adjunto and not Path(archivo_adjunto).exists():
            print(f"❌ El archivo {archivo_adjunto} no existe")
            logger.error(f"El archivo {archivo_adjunto} no existe")
            return False
        
        # Crear el mensaje de email
        message = EmailMessage()
        message['Subject'] = asunto
        message['From'] = settings.SENDER_EMAIL_ADDRESS
        
        # Configurar destinatarios
        if isinstance(destinatario, list):
            message['To'] = ', '.join(destinatario)
        else:
            message['To'] = destinatario
        
        # Configurar el contenido del mensaje
        if es_html:
            message.set_content(cuerpo, subtype='html')
        else:
            message.set_content(cuerpo)
        
        # Agregar archivo adjunto si se especifica
        if archivo_adjunto:
            with open(archivo_adjunto, 'rb') as archivo:
                contenido_archivo = archivo.read()
            
            # Determinar el nombre del archivo
            if nombre_archivo:
                nombre_final = nombre_archivo
            else:
                nombre_final = Path(archivo_adjunto).name
            
            # Determinar el tipo de archivo
            extension = Path(archivo_adjunto).suffix.lower()
            
            if extension == '.pdf':
                maintype, subtype = 'application', 'pdf'
            elif extension in ['.jpg', '.jpeg']:
                maintype, subtype = 'image', 'jpeg'
            elif extension == '.png':
                maintype, subtype = 'image', 'png'
            elif extension == '.txt':
                maintype, subtype = 'text', 'plain'
            elif extension in ['.xlsx', '.xls']:
                maintype, subtype = 'application', 'vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            elif extension == '.csv':
                maintype, subtype = 'text', 'csv'
            else:
                maintype, subtype = 'application', 'octet-stream'
            
            message.add_attachment(
                contenido_archivo,
                maintype=maintype,
                subtype=subtype,
                filename=nombre_final
            )
        
        # Enviar el email usando SMTP_SSL
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(settings.SMTP_HOST, int(settings.SMTP_PORT), context=context) as server:
            server.login(settings.SENDER_EMAIL_ADDRESS, settings.EMAIL_PASSWORD)
            server.send_message(message)
        
        print(f"✅ Email enviado correctamente a {destinatario}")
        logger.info(f"Email enviado correctamente a {destinatario}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Error de autenticación SMTP: {str(e)}")
        logger.error(f"Error de autenticación SMTP: {str(e)}")
        return False
        
    except smtplib.SMTPException as e:
        print(f"❌ Error SMTP: {str(e)}")
        logger.error(f"Error SMTP: {str(e)}")
        return False
        
    except FileNotFoundError as e:
        print(f"❌ Archivo no encontrado: {str(e)}")
        logger.error(f"Archivo no encontrado: {str(e)}")
        return False
        
    except Exception as e:
        print(f"❌ Error inesperado al enviar email: {str(e)}")
        logger.error(f"Error inesperado al enviar email: {str(e)}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return False



