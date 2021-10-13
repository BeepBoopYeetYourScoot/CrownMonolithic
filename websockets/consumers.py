from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer
import json

from game import models
from game.serializers import LobbySerializer

"""
Пример нормально сконструированного Консумера

Можно работать с моделями прямо из потребителей
import json
from services import get_timer, notifications
"""


class BrokerConsumer(JsonWebsocketConsumer):
    def connect(self):
        self.broker_id = self.scope['url_route']['kwargs']['broker_id']
        self.group_name = f'broker_{self.broker_id}'
        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
        self.accept()

    def disconnect(self, code):
        self.channel_layer.group_discard(self.group_name, self.channel_name)

    def receive_json(self, content, **kwargs):
        self.send_ws_signal(content['type'])

    def send_ws_signal(self, signal: str):
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                "type": f"{signal}",
            })

    def update_transactions(self, event):
        self.send_json({'type': 'update_transactions'})

    def next_phase(self, event):
        self.send_json({'type': 'next_phase'})

    def next_turn(self, event):
        self.send_json({'type': 'next_turn'})

    def update_timer(self, event):
        self.send_json({'type': 'update_timer'})

    def finish_session(self, event):
        self.send_json({'type': 'finish_session'})


class ProducerConsumer(JsonWebsocketConsumer):
    def connect(self):
        self.producer_id = self.scope['url_route']['kwargs']['producer_id']
        self.group_name = f'producer_{self.producer_id}'
        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
        self.accept()

    def disconnect(self, code):
        self.channel_layer.group_discard(self.group_name, self.channel_name)

    def receive_json(self, content, **kwargs):
        self.send_ws_signal(content['type'])

    def send_ws_signal(self, signal: str):
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                "type": f"{signal}",
            })

    def update_transactions(self, event):
        self.send_json({'type': 'update_transactions'})

    def next_phase(self, event):
        self.send_json({'type': 'next_phase'})

    def next_turn(self, event):
        self.send_json({'type': 'next_turn'})

    def update_timer(self, event):
        self.send_json({'type': 'update_timer'})

    def finish_session(self, event):
        self.send_json({'type': 'finish_session'})


class LobbyListConsumer(JsonWebsocketConsumer):
    """
    Консумер общего канала
    """

    def connect(self):
        """
        Присоединение к группе 'lobbies'
        """
        self.group_name = 'lobbies'
        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
        self.accept()
        self.send(text_data=json.dumps({
            'data': LobbySerializer(models.SessionModel.objects.filter(status='initialized'), many=True).data
        }))

    def disconnect(self, close_code):
        """
        Дисконект
        """
        self.send(text_data=json.dumps(close_code))
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name
        )

    def receive_json(self, content, **kwargs):
        """
        Получает сообщение от клиента
        """
        async_to_sync(self.send)(
            self.group_name,
            {'type': content['type'],
             'data': content['data']}
        )

    def update_lobby_list(self, event):
        """
        Обновляет список лобби при:
        1. Создании сессии
        2. Удалении сессии
        3. Присоединении игрока к лобби
        4. Выходе игрока из лобби
        :param event: сообщение с объектом data из сигнала
        """
        self.send(text_data=json.dumps({
            'data': event['data']
        }))


class LobbyDetailConsumer(JsonWebsocketConsumer):
    """
    Консумер отдельного лобби.
    Отдельные имена каналов (channel_name) по документации хранятся в БД.
    Думаю, их будет удобно кэшировать в Redis.
    Либо же брать из роутов WS
    """

    def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.group_name = f'lobby_{self.session_id}'
        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
        self.accept()

    def disconnect(self, code):
        """
        Отключение от лобби
        """
        self.channel_layer.group_discard(self.group_name, self.channel_name)

    def receive_json(self, content, **kwargs):
        """
        Получает сообщение от клиента
        """
        # Рассылает всем обновление по вступлению игрока
        if content['type'] == 'update_player_list':
            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {
                    'type': 'update_player_list',
                    'player_count': content['player_count'],
                    'session_name': content['session_name'],
                    'data': content['data']
                }
            )
        # Рассылает всем обновление о старте игры
        elif content['type'] == 'start_session':
            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {
                    "type": "start_session",
                    'data': content['data']
                }
            )

    def update_player_list(self, event):
        """
        Обновляет список игроков при
        1. Присоединении игрока к лобби
        2. Выходе игрока из лобби по кнопке
        """
        self.send(text_data=json.dumps({
            'action': 'update_player_list',
            'player_count': event['player_count'],
            'session_name': event['session_name'],
            'data': event['data']
        }))

    def start_session(self, event):
        """
        Отправляет данные о сессии с информацией игроков на маклерах при старте сессии
        """
        self.send(text_data=json.dumps({
            'action': 'start_session',
            'data': event['data']
        }))
