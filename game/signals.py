from django.db.models.signals import post_save
from django.dispatch import receiver
from game import models
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
