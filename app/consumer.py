# Standard Python libraries
import json
import logging
import re

# Django utilities
from django.utils import timezone

# Django core libraries
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer


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
   
class GenericAlertConsumer(AsyncWebsocketConsumer):
    async def connect(self):
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
        self.group_name = f'genericAlert_{safe_host}'

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

class WhatsAppConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.numero_chat = self.scope['url_route']['kwargs']['chat_id']
        self.id_empresa = self.scope['url_route']['kwargs']['company_id']
        self.nombre_sala = f"whatsapp_{self.numero_chat}_empresa_{self.id_empresa}"

        logger.info("✅ WebSocket conectado al canal DE WHATSAPP (por logging)")

        print(f"✅ WebSocket conectado al canal DE WHATSAPP: {self.nombre_sala}")


        await self.channel_layer.group_add(self.nombre_sala, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.nombre_sala, self.channel_name)
        print(f"❌ WebSocket desconectado del canal: {self.nombre_sala}")

    async def receive(self, text_data):
        datos = json.loads(text_data)
        contenido = datos.get('mensaje')

        await self.channel_layer.group_send(
            self.nombre_sala,
            {
                'type': 'mensaje_texto',
                'mensaje': contenido,
                'usuario': self.scope['user'].username,
                'fecha': timezone.localtime().strftime('%Y-%m-%d %H:%M:%S'),
                'sender': 'agent',  # Añadimos este campo para indicar que es un mensaje del agente
            }
        )

    async def mensaje_texto(self, event):

        # Obtenemos el valor de 'sender', si no existe, asignamos 'client' por defecto
        sender = event.get('sender', 'agent')

        await self.send(text_data=json.dumps({
            'tipo': 'texto',
            'mensaje': event['mensaje'],
            'usuario': event['usuario'],
            'fecha': event['fecha'],
            'sender': sender,  # Incluimos el campo sender en la respuesta JSON
        }))

    async def mensaje_media(self, event):

        # Obtenemos el valor de 'sender', si no existe, asignamos 'client' por defecto
        sender = event.get('sender', 'agent')
        await self.send(text_data=json.dumps({
            'tipo': 'media',
            'url': event['url_media'],
            'usuario': event['usuario'],
            'fecha': event['fecha'],
            'sender': sender,  # Incluimos el campo sender en la respuesta JSON
        }))

class CallAlertConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # El agente se identifica por la URL: ws://.../ws/call-alert/{agent_id}/
        self.agent_id = self.scope['url_route']['kwargs']['agent_id']
        self.group_name = f'call_alert_agent_{self.agent_id}'

        # Unirse al grupo único del agente
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Salir del grupo al desconectarse
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

        if self.scope['user'].is_authenticated:
            await self.update_agent_status(self.scope['user'].id)

    @database_sync_to_async
    def update_agent_status(self, user_id):
        from app.models import Agent
        try:
            agent = Agent.objects.get(id=user_id)
            agent.current_campaign = None
            agent.last_login = timezone.now()
            agent.status = 'busy'
            agent.save()
        except Agent.DoesNotExist:
            pass

    async def call_answered(self, event):
        await self.send(text_data=json.dumps({
            'type': 'call_answered',
            'clientName': event['clientName'],
            'clientPhone': event['clientPhone'],
            'clientAddress': event['clientAddress'],
            'clientZipCode': event['clientZipCode'],
            'lastCall': event['lastCall'],
            'attempts': event['attempts'],
            'status': event['status'],
            'callId': event['callId'],
        }))