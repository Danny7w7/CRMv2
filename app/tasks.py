from django.conf import settings
from requests import request
import telnyx

from celery import shared_task
from datetime import datetime, date, timedelta
from celery.utils.log import get_task_logger

from app.models import *
from app.views.consents import getCompanyPerAgent
from app.views.sms import sendIndividualsSms, comprobate_company

logger = get_task_logger(__name__)

@shared_task
def my_daily_task():
    now = datetime.now().date()
    # Filtramos los clientes que cumplen años hoy, ignorando el año
    birthdayClients = Clients.objects.filter(
        date_birth__month=now.month,
        date_birth__day=now.day
    )

    for clientBlue in birthdayClients:
        lines = clientBlue.agent_usa.split("\n")
        agentFirstName = lines[0].split()[0] 
        clientSms = Clients.objects.filter(phone_number=clientBlue.phone_number).first()

        if clientSms:
            chat = Chat.objects.select_related('agent').filter(contact_id=clientSms.id).first()

            sendIndividualsSms(
                chat.agent.assigned_phone.phone_number,
                clientBlue.phone_number,
                Users.objects.get(id=1),
                clientSms.company,
                f'¡Feliz cumpleaños, {clientBlue.first_name} {clientBlue.last_name}! 🎉 \nTodo el equipo de {getCompanyPerAgent(agentFirstName)} le desea un año lleno de salud, éxitos y bienestar. \nRecuerde que su agente de seguros, {clientBlue.agent_usa}, está siempre disponible para apoyarle con su póliza. \n¡Que tenga un día maravilloso! 🌟'
            )

@shared_task
def smsPayment():
    now = datetime.now().date()
    payments = paymentDate.objects.select_related('obamacare__client__agent', 'supp__client__agent').filter(
        payment_date__month=now.month,
        payment_date__day=now.day,
    )

    for payment in payments:
        if payment.obamacare or payment.supp:
            plan = payment.supp or payment.obamacare

        if not plan:  # Si no hay plan, continuar con el siguiente plan
            break

        lines = plan.agent_usa.split("\n")
        agentFirstName = lines[0].split()[0]

        if plan.client:
            company = plan.client.company  # Obtén la empresa asociada al cliente

            if not comprobate_company(company):
                message =f'Hola {plan.client.first_name} {plan.client.last_name} 👋,{getCompanyPerAgent(agentFirstName)} le recuerda que su pago de ${plan.premium} de su póliza de {plan.carrier} se vence en 2 días. 💚'

                sendIndividualsSms(
                    plan.client.agent.assigned_phone.phone_number,
                    plan.client.phone_number,
                    Users.objects.get(id=1),
                    plan.client.company,
                    message
                )

@shared_task
def reportBoos():
    # date = datetime.today() - timedelta(days=3)
    date = datetime(datetime.today().year, datetime.today().month, 21)

    obama = ObamaCare.objects.select_related('agent').filter(created_at = date)
    supp = Supp.objects.select_related('agent').filter(created_at = date)
    medicare = Medicare.objects.filter(created_at = date)
    assure = ClientsAssure.objects.filter(created_at = date)
    lifeInsurance = ClientsLifeInsurance.objects.filter(created_at = date)

    print(supp)
    print(date)

    mensageObama = []
    mensageSupp = []
    mensageMedicare = []
    mensageAssure = []
    mensageLife = []
    

    if obama.exists():
        for index, policy in enumerate(obama): # Usamos enumerate para el contador y un nombre más claro para la variable
            mensageObama.append(f'Póliza #{index + 1} es de {policy.agent.first_name} y su estado es {policy.status}')
    else:
        mensageObama.append('no hay poliza obama')

    if supp.exists():
        for index, policy in enumerate(supp): # Usamos enumerate para el contador y un nombre más claro para la variable
            mensageSupp.append(f'Póliza #{index + 1} es de {policy.agent.first_name} y su estado es {policy.status}')
    else:
        mensageSupp.append('no hay poliza supp')

    if medicare.exists():
        for index, policy in enumerate(medicare): # Usamos enumerate para el contador y un nombre más claro para la variable
            mensageMedicare.append(f'Póliza #{index + 1} es de {policy.agent.first_name} y su estado es {policy.status}')
    else:
        mensageMedicare.append('no hay poliza medicare')
    
    if assure.exists():
        for index, policy in enumerate(assure): # Usamos enumerate para el contador y un nombre más claro para la variable
            mensageAssure.append(f'Póliza #{index + 1} es de {policy.agent.first_name} y su estado es {policy.status}')
    else:
        mensageAssure.append('no hay poliza assure')

    if lifeInsurance.exists():
        for index, policy in enumerate(lifeInsurance): # Usamos enumerate para el contador y un nombre más claro para la variable
            mensageLife.append(f'Póliza #{index + 1} es de {policy.agent.first_name} y su estado es {policy.status}')
    else:
        mensageLife.append('no hay poliza life')

    print(mensageObama)
    print(mensageSupp)
    print(mensageMedicare)
    print(mensageAssure)
    print(mensageLife)

    mensage = (
        f"La polizas de la fecha {date} es:\n"
        f"Obama: {', '.join(mensageObama)}\n"
        f"Supp: {', '.join(mensageSupp)}\n"
        f"Medicare: {', '.join(mensageMedicare)}\n"
        f"Assure: {', '.join(mensageAssure)}\n"
        f"Life: {', '.join(mensageLife)}"
    )

    print(mensage)

    telnyx.api_key = settings.TELNYX_API_KEY
    telnyx.Message.create(
        from_=f'+17869848427', # Your Telnyx number
        to=f'+17863034781', # numero del jefe
        text= mensage
    )

    

   