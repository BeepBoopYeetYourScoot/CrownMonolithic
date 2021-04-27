from django.urls import re_path
from .consumers import LobbyConsumer, SessionConsumer


websocket_urlpatterns = [
    re_path(r'ws/detail/(?P<session_id>\w+)/$', SessionConsumer.as_asgi()),
    re_path(r'ws/lobby/', LobbyConsumer.as_asgi())
]
