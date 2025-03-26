import json
import re
from channels.generic.websocket import AsyncWebsocketConsumer
import logging

logger = logging.getLogger('django')

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        logger.debug('Conecto')
        chat_id = self.scope['url_route']['kwargs']['chat_id']
        company_id = self.scope['url_route']['kwargs']['company_id']
        self.room_name = f"chat_{chat_id}_company_{company_id}"
        self.room_group_name = f'{self.room_name}'
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        logger.debug('Leave room group')
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):

        try:
            text_data_json = json.loads(text_data)
            message = text_data_json['message']

            # Obtenemos el ID del usuario que envía el mensaje
            if self.scope['user'].is_authenticated:
                sender_id = self.scope['user'].id
                username = self.scope['user'].username
            else:
                sender_id = None
                username = 'Anonymous'

            # if sender_id:
            #     # Enviar mensaje al grupo de la sala
            #     await self.channel_layer.group_send(
            #         self.room_group_name,
            #         {
            #             'type': 'chat_message',
            #             'message': message,
            #             'username': username,
            #             'datetime': timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S'),
            #             'sender_id': sender_id
            #         }
            #     )
            # else:
            #     # Manejar el caso de usuario no autenticado si es necesario
            #     pass

        except json.JSONDecodeError:
            print("Error decodificando JSON")
        except KeyError:
            print("Error: 'message' no encontrado en los datos")

    async def chat_message(self, event):
        message = event['message']
        username = event['username']
        datetime = event['datetime']
        sender_id = event['sender_id']
        
        current_user_id = self.scope['user'].id if self.scope['user'].is_authenticated else None
        
        await self.send(text_data=json.dumps({
            'type': 'SMS',
            'message': message,
            'username': username,
            'datetime': datetime,
            'is_sms': isinstance(sender_id, str)
        }))

    async def MMS(self, event):
        message = event['message']  # Esta será la URL del medio
        username = event['username']
        datetime = event['datetime']
        sender_id = event['sender_id']
        
        current_user_id = self.scope['user'].id if self.scope['user'].is_authenticated else None
        
        await self.send(text_data=json.dumps({
            'type': 'MMS',
            'message': message,
            'username': username,
            'datetime': datetime,
            'is_sms': isinstance(sender_id, str),
            'media_url': message  # Incluimos la URL del medio en el mensaje
        }))
   
class ProductAlertConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        #asi estaba antes
        #self.group_name = 'product_alerts'
        #await self.channel_layer.group_add(self.group_name, self.channel_name)
        #await self.accept()

        # Obtener la dirección del host del WebSocket
        raw_host = self.scope["headers"]
        host = None
        for header in raw_host:
            if header[0] == b'host':
                host = header[1].decode("utf-8")
                break

        if not host:
            host = "default"

        # Limpiar el host para que sea un nombre de grupo válido
        safe_host = re.sub(r'[^a-zA-Z0-9_.-]', '_', host)
        self.group_name = f'product_alerts_{safe_host}'

        print(f"Conectando WebSocket al grupo: {self.group_name}")

        # Unirse al grupo
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        event_type = data.get('event_type', 'general')  # Tipo de evento
        message = data.get('message', '')


       # Enviar el mensaje a todos los clientes conectados con el event_type
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'send_alert',
                'event_type': event_type,
                'message': message,
                'agent': data.get('agent', '')
            }
        )

    async def send_alert(self, event):
        event_type = event.get('event_type', 'general')
        icon = event['icon']
        title = event['title']
        message = event['message']
        buttonMessage = event['buttonMessage']
        absoluteUrl = event.get('absoluteUrl', '')
        agent = event.get('agent', '')

        await self.send(text_data=json.dumps({
            'event_type': event_type,
            'icon': icon,
            'title': title,
            'message': message,
            'buttonMessage': buttonMessage,
            'absoluteUrl': absoluteUrl,
            'agent': agent # Enviar extra_info al frontend
        }))
