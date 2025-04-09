# Standard Python libraries
import re

# Third-party imports
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

def websocketAlertGeneric(request, type, eventType, icon, title, message, buttonMessage, absoluteUrl, agentId, agentUsername):
    #Aqui inicia el websocket
    app_name = request.get_host()  # Obtener el host (ej. "127.0.0.1:8000" o "miapp.com")

    # Reemplazar ":" y otros caracteres inválidos con "_" para hacer un nombre válido
    app_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', app_name)

    group_name = f'genericAlert_{app_name}'

    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': type,
            'event_type': eventType,
            'icon': icon,
            'title': title,
            'message': message,
            'buttonMessage': buttonMessage,
            'absoluteUrl': absoluteUrl,
            'agent': {
                'id': agentId,
                'username': agentUsername
            }
        }
    )

    