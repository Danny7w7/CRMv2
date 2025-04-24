from django.urls import path, re_path
from .consumer import *

websocket_urlpatterns = [
    path('ws/chat/<chat_id>/<company_id>/', ChatConsumer.as_asgi()),
    re_path(r'ws/alerts/$', GenericAlertConsumer.as_asgi()),
    path('ws/chatWatsapp/<chat_id>/<company_id>/', WhatsAppConsumer.as_asgi())

]