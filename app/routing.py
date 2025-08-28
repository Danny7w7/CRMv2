from django.urls import path
from .consumer import *

websocket_urlpatterns = [
    path('ws/chat/<chat_id>/<company_id>/', ChatConsumer.as_asgi()),
    path('ws/alerts/', GenericAlertConsumer.as_asgi()),
    path('ws/chatWatsapp/<chat_id>/<company_id>/', WhatsAppConsumer.as_asgi()),
    path('ws/callAlerts/<agent_id>/', CallAlertConsumer.as_asgi())
]