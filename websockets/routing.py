from django.urls import re_path
from .consumers import BrokerConsumer, ProducerConsumer, LobbyListConsumer, LobbyDetailConsumer

websocket_urlpatterns = [
    re_path(r'ws/detail/(?P<session_id>\w+)/$', LobbyDetailConsumer.as_asgi()),
    re_path(r'ws/lobby/', LobbyListConsumer.as_asgi()),
    re_path(r'ws/broker_(?P<broker_id>\w+)/$', BrokerConsumer.as_asgi()),
    re_path(r'ws/producer_(?P<producer_id>\w+)/$', ProducerConsumer.as_asgi()),
]
