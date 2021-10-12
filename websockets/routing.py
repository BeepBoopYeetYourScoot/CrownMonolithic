from django.urls import re_path
from .consumers import BrokerConsumer, ProducerConsumer, LobbyListConsumer, LobbyDetailConsumer

websocket_urlpatterns = [
    re_path(r'ws/detail/(?P<session_id>\w+)/$', LobbyDetailConsumer.as_asgi()),
    re_path(r'ws/lobbies/', LobbyListConsumer.as_asgi()),
    re_path(r'ws/broker_(?P<session_id>\w+)/$', BrokerConsumer.as_asgi()),
    re_path(r'ws/producer_(?P<session_id>\w+)/$', ProducerConsumer.as_asgi()),
]
