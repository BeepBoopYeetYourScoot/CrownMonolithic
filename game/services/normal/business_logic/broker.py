from game.models import BrokerModel
from game.services.broker import AbstractBroker


class BrokerNormal(AbstractBroker):
	"""
	Класс маклера для версии "Нормал"
	"""

	def __init__(self, broker: BrokerModel):
		self.id = broker.id
		self.balance = broker.player.balance
		self.billets_bought = 0
		self.transactions = []
		self.is_bankrupt = False
		self.status = 'OK'
		self.balance_detail = broker.player.detail

	fixed_costs = 1000

	def count_proceeds(self, market_price) -> float:
		"""Считает выручку от продажи заготовок"""
		proceeds = self.billets_bought * market_price
		return proceeds
