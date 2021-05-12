from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from game import models
from game.services.normal.data_access import count_session
from django.dispatch import receiver
from django.db.models import signals

"""
Методы потребителя:
 - send_timer
 - start_game
 - change_player
"""


# Нужен новый action new_session и всё к нему сопутствующее


@receiver([signals.post_save], sender=models.SessionModel)
def notify_change_session(sender, **kwargs):
    """
    Уведомляет пользователей о старте сессии
    """
    session_instance = kwargs['instance']
    channel_layer = get_channel_layer()
    if session_instance.status == 'initialized':
        async_to_sync(channel_layer.group_send)(
            'find_session',
            {'type': 'update_lobby'})
    elif session_instance.status == 'started':
        if session_instance.current_turn == 1 and session_instance.turn_phase == 'negotiation':
            async_to_sync(channel_layer.group_send)(
                'find_session',
                {'type': 'start_game'})
        elif session_instance.turn_phase == 'negotiation':
            async_to_sync(channel_layer.group_send)(
                f'session_{session_instance.id}',
                {'type': 'next_turn'})
        async_to_sync(channel_layer.group_send)(
            f'session_{session_instance.id}',
            {'type': 'change_player'}
        )
    elif session_instance.status == 'finished':
        async_to_sync(channel_layer.group_send)(
            f'session_{session_instance.id}',
            {'type': 'finish_session'})


@receiver([signals.post_delete], sender=models.SessionModel)
def notify_delete_session(sender, **kwargs):
    if not kwargs['instance'].status == 'initialized':
        return

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'find_session',
        {
            'type': 'join_player'
        }
    )


@receiver([signals.post_save], sender=models.PlayerModel)
def notify_join_player(sender, **kwargs):
    """
    Уведомляет о присоединении игрока к сессии
    """
    if not kwargs['created']:
        return

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'find_session',
        {
            'type': 'join_player'
        }
    )


@receiver([signals.post_delete], sender=models.PlayerModel)
def notify_exit_player(sender, **kwargs):
    """
    Уведомляет о выходе игрока из сессии
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'find_session',
        {
            'type': 'exit_player'
        }
    )


@receiver([signals.post_save], sender=models.ProducerModel)
def notify_producer(sender, **kwargs):
    """
    Уведомляет производителя при производстве заготовок и пересчёте
    """
    producer_instance = kwargs['instance']
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'session_{producer_instance.player.session.id}',
        {
            'type': 'change_player'
        }
    )


@receiver([signals.post_save], sender=models.BrokerModel)
def notify_broker(sender, **kwargs):
    """
    Уведомляет маклера при пересчёте
    """
    broker_instance = kwargs['instance']
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'session_{broker_instance.player.session.id}',
        {'type': 'change_player'})


# @receiver([signals.post_save], sender=models.PlayerModel)
# def notify_players(sender, **kwargs):
#     """
#     Уведомляет пользователей при пересчёте
#     """
#     player_instance = kwargs['instance']
#     channel_layer = get_channel_layer()
#     async_to_sync(channel_layer.group_send)(
#         f'session_{player_instance.session.id}',
#         {
#             'type': 'change_player'
#         }
#     )


@receiver([signals.post_save], sender=models.TransactionModel)
def notify_transaction(sender, **kwargs):
    """
    Уведомляет пользователей, когда создаётся новая транзакция в сессии
    """
    transaction_instance = kwargs['instance']
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'session_{transaction_instance.session.id}',
        {
            'type': 'change_player'
        }
    )


@receiver([signals.post_save], sender=models.PlayerModel)
def finish_turn_by_players(sender, **kwargs):
    """
    Заканчивает ход в сессии, если все игроки завершили ход
    """
    player = kwargs['instance']
    session_instance = models.SessionModel.objects.get(id=player.session.id)
    players_finished = session_instance.player\
        .filter(ended_turn=True, is_bankrupt=False).count()
    players_in_session = session_instance.player\
        .filter(is_bankrupt=False).count()
    if players_finished == players_in_session:
        if session_instance.turn_phase == 'negotiation':
            count_session.change_phase(session_instance, 'transaction')
        elif session_instance.turn_phase == 'transaction':
            count_session.count_session(session_instance)
