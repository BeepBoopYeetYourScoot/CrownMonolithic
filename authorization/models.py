from django.db import models
import binascii
import os
from django.conf import settings
from CrownMonolithic.utils import get_session_model


class PlayerManager(models.Manager):
    def create_player(self, session, nickname):
        """
        Создает игрока и токен.
        """
        player = self.create(nickname=nickname, session=session)
        PlayerTokenModel.objects.create(player=player)
        return player


class PlayerBaseModel(models.Model):
    nickname = models.CharField('nickname', max_length=100)
    session = models.ForeignKey(settings.SESSION_MODEL, on_delete=models.CASCADE,
                                related_name='player', verbose_name='Сессия', default=0)
    objects = PlayerManager()

    class Meta:
        verbose_name = 'Игрок'
        verbose_name_plural = 'Игроки'
        abstract = True

    def __str__(self):
        return f'Игрок {self.nickname}'


class PlayerTokenModel(models.Model):
    key = models.CharField('key', max_length=100)
    player = models.OneToOneField(settings.PLAYER_MODEL, on_delete=models.CASCADE,
                                  related_name='token', verbose_name='player')
    created = models.DateTimeField('Creation time', auto_now_add=True)

    class Meta:
        verbose_name = 'Токен'
        verbose_name_plural = 'Токены'

    @classmethod
    def generate_key(cls):
        return binascii.hexlify(os.urandom(20)).decode()

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super().save(*args, **kwargs)
