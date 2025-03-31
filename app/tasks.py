import telnyx

from celery import shared_task
from datetime import datetime
from celery.utils.log import get_task_logger

from app.models import *
from app.views import getCompanyPerAgent
from django.conf import settings

logger = get_task_logger(__name__)

@shared_task
def my_daily_task():

    now = datetime.now().date()

    # Filtramos los clientes que cumplen años hoy, ignorando el año
    birthdayClients = Clients.objects.filter(
        date_birth__month=now.month,
        date_birth__day=now.day,
        is_active=True
    )

    for clientBlue in birthdayClients:
        lines = clientBlue.agent_usa.split("\n")
        agentFirstName = lines[0].split()[0] 
        
        clientSms = Clients.objects.using('message_app').filter(phone_number=clientBlue.phone_number).first()

        if clientSms:
            chat = Chat.objects.select_related('agent').using('message_app').filter(client=clientSms).first()
            telnyx.api_key = settings.TELNYX_API_KEY
            telnyx.Message.create(
                from_=f"+{chat.agent.assigned_phone.phone_number}",
                to=f'+{clientBlue.phone_number}',
                text= f'¡Feliz cumpleaños, {clientBlue.first_name} {clientBlue.last_name}! 🎉 De parte de todo el equipo de {getCompanyPerAgent(agentFirstName)}, le deseamos un año lleno de salud y bienestar. Recuerde que su agente de seguros, {clientBlue.agent_usa}, está siempre a su disposición para cualquier duda o apoyo con su póliza. ¡Que tenga un excelente día!'
            )
            # Log para verificar el envío
            print(f"Mensaje enviado al numero {clientBlue.phone_number} - {clientBlue.first_name} {clientBlue.last_name}")
            logger.info(f"Mensaje enviado al numero {clientBlue.phone_number} - {clientBlue.first_name} {clientBlue.last_name}")
        else:
            print(f'Al cliente {clientBlue.first_name} {clientBlue.last_name} - {clientBlue.phone_number} No se le mando mensaje de cumpleaño') 

