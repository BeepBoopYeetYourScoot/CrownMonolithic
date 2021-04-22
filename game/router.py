from rest_framework.routers import DefaultRouter
from . import views
# from django.urls import re_path
# from .services.questionable import consumers

# from channels.routing import route
# from game.consumers import ws_connect, ws_disconnect


router = DefaultRouter()
router.register(r'session-admin', views.SessionAdminViewSet)
router.register(r'lobby', views.LobbyViewSet)
router.register(r'player', views.PlayerViewSet)
router.register(r'producer', views.ProducerViewSet)
router.register(r'broker', views.BrokerViewSet)
# router.register(r'session', views.SessionViewSet)
# router.register(r'player', views.GetOrUpdatePlayerViewSet)
# router.register(r'producer', views.ProducerViewSet)
router.register(r'transactions', views.TransactionViewSet)


# websocket_urlpatterns = [
#     re_path(r'ws/game/', consumers.GameConsumer.as_asgi()),
# ]

