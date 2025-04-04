import telnyx

from celery import shared_task
from datetime import datetime
from celery.utils.log import get_task_logger

from app.models import *
from app.views.consents import getCompanyPerAgent
from app.views.sms import sendIndividualsSms, comprobate_company
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

@shared_task
def smsPayment(request):

    now = datetime.now().date()
    # Filtramos los clientes que cumplen años hoy, ignorando el año
    smsPaymentClients = paymentDate.objects.select_related('obama__client', 'supp__client').filter(
        payment_date__month=now.month,
        payment_date__day=now.day,
    )

    print(f"Clientes encontrados: {smsPaymentClients.count()}")  # Verificar cuántos clientes devuelve la consulta


    for clientBluePayment in smsPaymentClients:

        if clientBluePayment.obama or clientBluePayment.supp:
            selectedAgent = clientBluePayment.supp or clientBluePayment.obama

        if not selectedAgent:  # Si no hay agente, continuar con el siguiente cliente
            print(f"Cliente {clientBluePayment.id} no tiene agente asignado.")
            break

        lines = selectedAgent.agent_usa.split("\n")
        agentFirstName = lines[0].split()[0]

        clientSmsPayment = Clients.objects.filter(phone_number=selectedAgent.client.phone_number).first()
        obmaCliente = ObamaCare.objects.filter(client = clientSmsPayment.id).first()

        if clientSmsPayment:

            company = selectedAgent.client.company  # Obtén la empresa asociada al cliente

            if not comprobate_company(company):

                message = f'''Buen día {clientSmsPayment.first_name} {clientSmsPayment.last_name} 
                Nos comunicamos  de {getCompanyPerAgent(agentFirstName)},  para recordarle que su pago mensual de {obmaCliente.premium}.Si tiene algún inconveniente con el pago, no dude en comunicarse con nuestro departamento de servicio al cliente al 1.855.963.6900. ¡Disfrute los beneficios de su plan de salud!
                Esto es una prueba del salto de linea y del mensaje'''

                # Simulación de envío de mensaje
                #print(f"Simulando envío de SMS a {clientSmsPayment.phone_number}: {message}")
                sendIndividualsSms(
                    request.user.assigned_phone.phone_number,
                    clientSmsPayment.phone_number,
                    request.user,
                    request.user.company,
                    message
                )

                # Log para verificar el envío
                print(f"Mensaje enviado al numero {clientSmsPayment.phone_number} - {clientSmsPayment.first_name} {clientSmsPayment.last_name}")
                logger.info(f"Mensaje enviado al numero {clientSmsPayment.phone_number} - {clientSmsPayment.first_name} {clientSmsPayment.last_name}")

        else:
            print(f"Cliente {selectedAgent} no tiene número registrado para enviar SMS.")
            print(f'Al cliente {clientSmsPayment.first_name} {clientSmsPayment.last_name} - {clientSmsPayment.phone_number} No se le mando mensaje de cumpleaño') 

