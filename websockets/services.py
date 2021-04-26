from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from game.models import SessionModel
from game.services.normal.data_access import count_session


def get_timer(session_id):
    """
    Возвращает время на текущий ход
    """
    session_instance = SessionModel.objects.get(id=session_id)
    timer = session_instance.turn_time.get(turn=session_instance.current_turn)
    return timer


def notify_start(session_id):
    """
    Уведомляет пользователей о старте сессии
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(f'session_{session_id}', {'type': 'start_session'})


def notify_change_phase(session_id, phase):
    """
    Уведомляет пользователей сессии о смене фазы
    """
    # FIXME Я не ебу, как по-нормальному опрокидывать фазу внутрь вызова
    #  метода Потребителя
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(f'session_{session_id}', {'type': 'change_phase', 'phase': phase})


def notify_next_turn(session_id):
    """
    Уведомляет пользователей о начале нового хода
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(f'session_{session_id}', {'type': 'next_turn'})


def notify_finish(session_id):
    """
    Уведомляет пользователей об окончании игры
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(f'session_{session_id}', {'type': 'finish_session'})


def finish_turn_by_players(session_id):
    """
    Заканчивает ход в сессии, если все игроки завершили ход
    """
    # FIXME При выполнении условия отправлять всему каналу сигнал на пересчёт
    session_instance = SessionModel.objects.get(id=session_id)
    players_finished = session_instance.player.filter(ended_turn=True).count()
    players_in_session = session_instance.player.count()
    channel_layer = get_channel_layer()
    if players_finished == players_in_session:
        if session_instance.phase == 'negotiation':
            async_to_sync(channel_layer.group_send)(f'session_{session_id}',
                                                    {'type': 'change_phase', 'phase': 'transaction'})
        elif session_instance.phase == 'transaction':
            count_session.count_session(session_instance)
            async_to_sync(channel_layer.group_send)(f'session_{session_id}',
                                                    {'type': 'next_turn'})


def notify_billets_produced(producer):
    """
    Уведомляет производителя о том, что у него появились производимые заготовки
    """
    pass


def notify_send_transaction(producer, broker):
    pass
