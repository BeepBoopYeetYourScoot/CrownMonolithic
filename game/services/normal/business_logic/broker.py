from game.models import PlayerModel
from game.services.broker import AbstractBroker


class BrokerNormal(AbstractBroker):
	"""
	Класс маклера для версии "Нормал"
	"""

	def __init__(self, broker_player: PlayerModel):
		self.id = broker_player.id
		self.balance = broker_player.balance
		self.billets_bought = 0
		self.transactions = []
		self.is_bankrupt = False
		self.status = 'OK'
		self.balance_detail = broker_player.detail

	fixed_costs = 1000

	def count_proceeds(self, market_price) -> float:
		"""Считает выручку от продажи заготовок"""
		proceeds = self.billets_bought * market_price
		return proceeds
