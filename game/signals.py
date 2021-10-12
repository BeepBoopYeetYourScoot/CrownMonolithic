from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver
from game import models
from game.services.normal.data_access import count_session
from game.services.normal.data_access.timer import initialize_thread_timer, next_turn_thread_timer

"""
Чтобы установить сигнал, добавьте в метод ready класса <App>Config импорт файла с сигналом
"""


@receiver([post_save], sender=models.SessionModel)
def timer(sender, instance=None, created=False, **kwargs):
    if instance.current_turn == 1 and instance.status == 'started' and instance.turn_phase == 'negotiation':
        initialize_thread_timer(instance)
    elif instance.status == 'started' and instance.current_turn <= instance.turn_count:
        next_turn_thread_timer(instance)


@receiver(post_save, sender=models.TurnTime)
def update_timer(sender, instance=None, created=False, **kwargs):
    """
    Сигнал на обновление таймера у игроков, если в Сессии добавили время
    """
    if not created:
        channel_layer = get_channel_layer()
        broker_players = instance.session.player.filter(role='broker')
        producer_players = instance.session.player.filter(role='producer')
        for broker_player in broker_players:
            async_to_sync(channel_layer.group_send)(f'broker_{broker_player.broker.id}', {'type': 'update_timer'})
        for producer_player in producer_players:
            async_to_sync(channel_layer.group_send)(f'producer_{producer_player.producer.id}',
                                                    {'type': 'update_timer'})


@receiver(post_save, sender=models.TransactionModel)
def update_transactions(sender, instance=None, created=False, **kwargs):
    """
    Сигнал на обновление списка сделок у игроков
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(f'broker_{instance.broker_id}', {'type': 'update_transactions'})
    async_to_sync(channel_layer.group_send)(f'producer_{instance.producer_id}', {'type': 'update_transactions'})


@receiver(post_save, sender=models.SessionModel)
def next_turn(sender, instance=None, created=False, **kwargs):
    """
    Отправляет сигналы на завершение хода или сессии
    """
    channel_layer = get_channel_layer()
    active_players = instance.player.filter(status='OK')
    broker_players = active_players.filter(role='broker')
    producer_players = active_players.filter(role='producer')

    if instance.status == 'active' and instance.current_turn < instance.turn_count:
        for broker in broker_players:
            async_to_sync(channel_layer.group_send)(f'broker_{broker.id}', {'type': 'next_turn'})
        for producer in producer_players:
            async_to_sync(channel_layer.group_send)(f'producer_{producer.id}', {'type': 'next_turn'})

    elif instance.status == 'finished':
        for broker in broker_players:
            async_to_sync(channel_layer.group_send)(f'broker_{broker.id}', {'type': 'finish_session'})
        for producer in producer_players:
            async_to_sync(channel_layer.group_send)(f'producer_{producer.id}', {'type': 'finish_session'})


@receiver(post_save, models.PlayerModel)
def finish_turn_by_players(sender, instance=None, created=False, **kwargs):
    """
    Завершает ход, если все игроки тыкнули "Завершить ход"
    """
    active_players_count = instance.session.player.filter(status='OK').count()
    players_finished_turn_count = instance.session.player.filter(status='OK', ended_turn=True).count()

    if active_players_count == players_finished_turn_count:
        count_session.count_session(instance.session)