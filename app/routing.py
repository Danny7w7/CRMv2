from django.urls import path
from .consumer import ChatConsumer

websocket_urlpatterns = [
    path('ws/chat/<chat_id>/<company_id>/', ChatConsumer.as_asgi()),
]