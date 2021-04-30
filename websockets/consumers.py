from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
import json

from game import models
import datetime
from . import services as ws_services

"""
Пример нормально сконструированного Консумера

Можно работать с моделями прямо из потребителей
import json
from services import get_timer, notifications
"""


class SessionConsumer(WebsocketConsumer):
    def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        # TODO: Добавить логику проверки наличия сессии
        self.group_name = f'session_{self.session_id}'
        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
        # async_to_sync(self.channel_layer.group_send)(self.group_name,
        #                                              {'type': 'change_player'})
        async_to_sync(self.channel_layer.group_send)(self.group_name,
                                                     {'type': 'update_timer'})
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name
        )

    def receive(self, text_data):
        text_data_json = json.loads(text_data)

        # Send message to room group
        if text_data_json['type'] == 'change_player':
            async_to_sync(self.channel_layer.group_send)(self.group_name,
                                                         {"type": "change_player"})
        elif text_data_json['type'] == 'update_timer':
            async_to_sync(self.channel_layer.group_send)(self.group_name,
                                                         {'type': 'update_timer'})

    def change_player(self, event):
        """
        Сигнализирует о любых изменениях в игроке: транзакции, баланс,
        заготовки и т.д.
        """
        self.send(text_data=json.dumps({
            'action': 'change_player'
        }))

    def update_timer(self, event):
        """
        При смене фазы или пересчёте сигналит обновить таймер
        """
        session_instance = models.SessionModel.objects.get(id=self.session_id)
        turn_time_intervals = session_instance.turn_time.filter(turn=session_instance.current_turn).first()
        if session_instance.turn_phase == 'negotiation':
            turn_time = turn_time_intervals.negotiation_time
        else:
            turn_time = turn_time_intervals.transaction_time
        now = datetime.datetime.now(datetime.timezone.utc)
        ends = turn_time_intervals.started + turn_time
        time_left = ends - now

        self.send(text_data=json.dumps({
            'action': 'update_timer',
            'time': {
                'minutes': time_left.total_seconds() // 60,
                'seconds': time_left.total_seconds() % 60
            }
        }))


class LobbyConsumer(WebsocketConsumer):
    """
    Консьюмер до старта сессии
    """

    def connect(self):
        """
        Соединение к группе 'find_session'
        """
        self.group_name = 'find_session'
        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'update_lobby'
            }
        )
        self.accept()

    def disconnect(self, close_code):
        """
        Дисконект
        """
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name
        )

    def receive(self, text_data):
        """
        Получает сообщение от клиента
        """
        text_data_json = json.loads(text_data)

        # Рассылает всем обновление по вступлению игрока
        if text_data_json['type'] == 'join_player':
            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {
                    'type': 'join_player',
                    'time': True
                }
            )
        # Рассылает всем обновление о выходе игрока
        elif text_data_json['type'] == 'exit_player':
            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {
                    "type": "exit_player",
                    'exit_player': True,
                }
            )
        # Рассылает всем обновление о старте игры
        elif text_data_json['type'] == 'start_game':
            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {
                    "type": "start_game",
                }
            )
        elif text_data_json['type'] == 'update_lobby':
            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {
                    'type': 'update_lobby'
                }
            )

    def join_player(self, event):
        """
        Сигнализирует о присоединении игрока к сессии
        """
        self.send(text_data=json.dumps({
            'action': 'join_player',
            'time': True
        }))

    def exit_player(self, event):
        """
        Сигнализирует о выходе игрока из сессии
        """
        self.send(text_data=json.dumps({
            'action': 'exit_player',
            'data': True
        }))

    def start_game(self, event):
        """
        Сигнализирует о старте игры
        """
        self.send(text_data=json.dumps({
            'action': 'start_game',
            'start_game': 'true'
        }))

    def update_lobby(self, event):
        """
        Сигнализирует об обновлении списка лобби
        """
        self.send(text_data=json.dumps({
            'action': 'update_lobby'
        }))
