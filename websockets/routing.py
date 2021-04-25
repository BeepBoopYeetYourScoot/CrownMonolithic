from django.urls import re_path
from . import consumers


websocket_urlpatterns = [
    re_path(r'ws/detail/(?P<session_id>\w+)/$', consumers.TimerConsumer.as_asgi()),
    re_path(r'ws/lobby/', consumers.SessionConsumer.as_asgi())
]