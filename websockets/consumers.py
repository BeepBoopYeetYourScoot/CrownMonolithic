from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
import json
from . import services as ws_services

"""
Пример нормально сконструированного Консумера

Можно работать с моделями прямо из потребителей
import json
from services import get_timer, notifications
"""


# class TimerConsumer(AsyncWebsocketConsumer):
#
#     async def connect(self):
#         self.session_id = self.scope['url_route']['kwargs']['session_id']
#         self.group_name = f'session_{self.session_id}'
#
#         await self.channel_layer.group_add(self.group_name,
#                                            self.channel_name)
#         await self.return_timer()
#         await self.accept()
#
#     async def disconnect(self):
#         await self.channel_layer.discard(self.group_name,
#                                          self.channel_name)
#
#     async def receive(self, text_data):
#         text_data_json = json.loads(text_data)
#         request_type = text_data_json['type']
#
#         if request_type == 'get_timer':
#             await self.return_timer()
#         elif request_type == 'finish_turn':
#             await ws_services.finish_turn_by_players(self.session_id)
#         elif request_type == 'produce_billets':
#             pass
#         elif request_type == 'send_transaction':
#             pass
#         elif request_type == 'accept_transaction':
#             pass
#         elif request_type == 'deny_transaction':
#             pass
#
#     async def return_timer(self):
#         timer = ws_services.get_timer(self.session_id)
#         await self.send(text_data={
#             'action': 'update_timer',
#             'time': timer
#         })
#
#     async def start_session(self):
#         await self.channel_layer.group_send(
#             self.group_name,
#             {
#                 'action': 'start_session',
#             }
#         )
#
#     # FIXME Тут могут возникнуть проблемы
#     async def change_phase(self, phase):
#         await self.channel_layer.group_send(
#             self.group_name,
#             {
#                 'action': 'change_phase',
#                 'phase': phase
#             }
#         )
#
#     async def next_turn(self):
#         await self.channel_layer.group_send(
#             self.group_name,
#             {
#                 'action': 'next_turn'
#             }
#         )
#
#     async def finish_session(self):
#         await self.channel_layer.group_send(
#             self.group_name,
#             {
#                 'action': 'finish_session'
#             }
#         )
#
#     # FIXME Можно сделать так, чтобы фронт сам подтягивал производимые заготовки
#     #  Можно сделать так, чтобы по сокетам сразу отправлялось количество заготовок
#     #  Можно наговнокодить и каждый раз, когда кто-то отправляет транзакцию,
#     #  говорить, чтобы все обновляли список своих транзакций
#     async def produce_billets(self):
#         pass
#
#     async def send_transaction(self):
#         pass
#
#     async def accept_transaction(self):
#         pass
#
#     async def deny_transaction(self):
#         pass


class SessionConsumer(WebsocketConsumer):
    def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        # TODO Тестировать
        self.user_id = self.scope['player.id']
        self.channel_name = f'user_{self.user_id}'
        self.session_group_name = f'session_{self.session_id}'
        # TODO: Добавить логику проверки наличия сессии
        self.group_name = f'session_{self.session_id}'
        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )
        self.accept()
        # self.send_time(<time>)


    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name
        )

    def receive(self, text_data):
        text_data_json = json.loads(text_data)

        # Send message to room group
        if text_data_json['type'] == 'time':
            time = text_data_json['time']
            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {
                    'type': 'send_timer',
                    'time': time
                }
            )
        elif text_data_json['type'] == 'start_game':
            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {
                    "type": "start_game",
                    'start_game': True,
                    'action': 'start_game'
                }
            )
        elif text_data_json['type'] == 'change_player':
            async_to_sync(self.channel_layer.group_send)(
                self.group_name,
                {
                    "type": "change_player",
                }
            )

    # Receive message from room group
    def send_time(self, event):
        """
        Отправляет время
        """
        self.send(text_data=json.dumps({
            'time': '28479',  # event['time'],
            'action': 'timer'
        }))

    def change_player(self, event):
        """
        Сигнализирует о любых изменениях в игроке: транзакции, баланс,
        заготовки и т.д.
        """
        self.send(text_data=json.dumps({
            'action': 'change_player'
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

    def join_player(self, event):
        """
        Сигнализирует о присоединении игрока к сессии
        """
        self.send(text_data=json.dumps({
            'action': 'join_player',
            'data': True
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
