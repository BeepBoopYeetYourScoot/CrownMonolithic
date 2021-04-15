import random

from django.db import models
from game.services.transporting_cost import get_transporting_cost
from authorization.models import PlayerBaseModel


class SessionModel(models.Model):
	"""
	Модель игровой сессии вместе со всеми настройками
	"""
	GAME_TYPES = (
		('normal', 'Стандартная'),
		('hard', 'Сложная')
	)

	SESSION_STATUSES = (
		('initialized', 'Сессия инициализирована'),
		('started', 'Сессия запущена'),
		('finished', 'Сессия закончилась')
	)

	PHASE_STATUSES = (
		('negotiation', 'Этап переговоров'),
		('transaction', 'Этап заключения сделок')
	)

	name = models.CharField(max_length=150)
	game_type = models.CharField(max_length=15, choices=GAME_TYPES, default='normal')
	turn_count = models.PositiveSmallIntegerField()

	# Всё, что помечено аргументом editable, впоследствии может уйти в админку, поэтому лучше выделять эти
	# параметры отдельно
	number_of_brokers = models.PositiveSmallIntegerField(editable=False, default=0)
	crown_balance = models.PositiveSmallIntegerField(default=0, editable=False)
	status = models.CharField(max_length=15, choices=SESSION_STATUSES, default='initialized', editable=True)
	broker_starting_balance = models.PositiveSmallIntegerField(editable=False, default=0)
	producer_starting_balance = models.PositiveSmallIntegerField(editable=False, default=0)
	transaction_limit = models.PositiveSmallIntegerField(default=2000, editable=False)
	current_turn = models.PositiveSmallIntegerField(verbose_name='Текущий ход', default=0, editable=True)
	turn_phase = models.CharField(max_length=20, choices=PHASE_STATUSES, default='negotiation', editable=True)

	class Meta:
		verbose_name = 'Сессия'
		verbose_name_plural = 'Сессии'

	def __str__(self):
		return self.name


class PlayerModel(PlayerBaseModel):
	ROLES = (
		('unassigned', 'Не назначена'),
		('producer', 'Производитель'),
		('broker', 'Маклер')
	)

	CITIES = (
		('unassigned', 'Не назначен'),
		('IV', "Айво"),
		('WS', "Вемшир"),
		('TT', "Тортуга"),
		('AD', "Алендор"),
		('NF', "Неверфол"),
		('ET', "Этруа")
	)

	nickname = models.CharField(max_length=100, verbose_name='Никнейм')
	role = models.CharField(max_length=20, choices=ROLES, verbose_name='Игровая роль',
							default='unassigned', editable=True)
	role_name = models.CharField(max_length=20, verbose_name='Игровое имя', default='unassigned',
								 editable=True)
	position = models.PositiveSmallIntegerField(verbose_name='Место', default=0,
												editable=False)
	ended_turn = models.BooleanField(default=False)
	city = models.CharField(max_length=20, choices=CITIES, verbose_name='Расположение', default='unassigned')
	balance = models.IntegerField(default=0)
	is_bankrupt = models.BooleanField(default=False)
	status = models.CharField(max_length=20, default='OK', verbose_name='Статус банкротства', editable=False)

	class Meta:
		verbose_name = 'Игрок'
		verbose_name_plural = 'Игроки'

	def __str__(self):
		return f'Игрок {self.nickname}'


class ProducerModel(models.Model):
	player = models.OneToOneField(PlayerModel, on_delete=models.CASCADE, related_name='producer')
	billets_produced = models.IntegerField(default=0)
	billets_stored = models.IntegerField(default=0)

	class Meta:
		verbose_name = 'Производитель'
		verbose_name_plural = 'Производители'

	def __str__(self):
		if self.pk is not None:
			return f'Производитель {self.player.nickname}'
		else:
			super().__str__()


class BrokerModel(models.Model):

	@staticmethod
	def generate_code():
		"""
		Генерирует шестизначный код маклера
		"""
		return random.randint(111111, 999999)

	player = models.OneToOneField(PlayerModel, on_delete=models.CASCADE, related_name='broker')
	code = models.PositiveSmallIntegerField()

	class Meta:
		verbose_name = 'Маклер'
		verbose_name_plural = 'Маклеры'

	def __str__(self):
		if self.pk is not None:
			return f'Маклер {self.player.nickname}'
		else:
			super().__str__()

	def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
		"""
		Генерирует новый код при пересчёте
		"""
		self.code = self.generate_code()
		super().save()


class TransactionModel(models.Model):
	TRANSACTION_STATUSES = (
		('active', 'Сделка на рассмотрении'),
		('accepted', 'Сделка согласована'),
		('denied', 'Сделка отклонена')
	)

	session = models.ForeignKey(SessionModel, on_delete=models.CASCADE, related_name='transaction')
	producer = models.ForeignKey(ProducerModel, on_delete=models.CASCADE, related_name='transaction')
	broker = models.ForeignKey(BrokerModel, on_delete=models.CASCADE, related_name='transaction')
	quantity = models.PositiveSmallIntegerField(default=0)
	price = models.PositiveSmallIntegerField(default=0)
	transporting_cost = models.PositiveSmallIntegerField(default=10, editable=False)
	turn = models.PositiveSmallIntegerField(editable=False)
	status = models.CharField(max_length=15, choices=TRANSACTION_STATUSES, default='active')

	class Meta:
		verbose_name = 'Транзакция'
		verbose_name_plural = 'Транзакции'

	def __str__(self):
		if self.producer is not None and self.broker is not None:
			return f'Сделка в сессии {self.session.name} между {self.producer.player.nickname} и {self.broker.player.nickname}'

	def save(self, *args, **kwargs):
		if not self.pk:
			# FIXME: дорого и не красиво
			self.session = self.producer.player.session
			self.turn = self.session.current_turn
			self.transporting_cost = get_transporting_cost(
				self.session.number_of_brokers,
				self.producer.player.city,
				self.broker.player.city,
			)
		super().save(*args, **kwargs)

# FIXME: Нужно убрать логически повторяющиеся поля
class BalanceDetail(models.Model):
	player = models.OneToOneField(PlayerModel, on_delete=models.CASCADE, related_name='detail')
	start_turn_balance = models.IntegerField(default=0)
	end_turn_balance = models.IntegerField(default=0)
	sales_income = models.IntegerField(default=0)
	fixed_costs = models.IntegerField(default=0)
	variable_costs = models.IntegerField(default=0)
	raw_stuff_costs = models.IntegerField(default=0)
	fine = models.IntegerField(default=0)
	storage = models.IntegerField(default=0)
	logistics = models.IntegerField(default=0)
	purchase_blanks = models.IntegerField(default=0)
	blanks = models.IntegerField(default=0)
	crown = models.IntegerField(default=0)
