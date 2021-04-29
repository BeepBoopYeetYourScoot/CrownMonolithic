from game.services.producer import AbstractProducer


class ProducerNormal(AbstractProducer):
	"""
	Класс производителя для версии "Нормал"
	"""

	def __init__(self, balance):
		self.id = 0
		self.balance = balance
		self.billets_produced = 0
		self.billets_stored = 0
		self.billets_cost = 30
		self.transactions = []
		self.is_bankrupt = False
		self.status = 'OK'
		self.balance_detail = {
			'start_turn_balance': balance,
			'fixed_costs': 0,
			'variable_costs': 0,
			'raw_stuff_costs': 0,
			'storage': 0,
			'logistics': 0,
			'sales_income': 0,
			'end_turn_balance': 0
		}

	def count_fixed_costs(self) -> float:
		"""
		Считает постоянные затраты производителя в зависимости от числа производимых заготовок
		"""
		if self.billets_produced <= 10:
			fixed_costs = 600
		elif self.billets_produced <= 20:
			fixed_costs = 1000
		elif self.billets_produced <= 30:
			fixed_costs = 1400
		elif self.billets_produced <= 50:
			fixed_costs = 2000
		elif self.billets_produced <= 100:
			fixed_costs = 4000
		else:
			fixed_costs = 15000
		self.balance_detail['fixed_costs'] = fixed_costs
		return fixed_costs

	def count_variable_costs(self) -> int:
		"""
		Считает переменные затраты в зависимости от числа производимых заготовок
		"""
		if self.billets_produced <= 10:
			job_costs = 80 * self.billets_produced
		elif self.billets_produced <= 20:
			job_costs = 70 * self.billets_produced
		elif self.billets_produced <= 30:
			job_costs = 55 * self.billets_produced
		elif self.billets_produced <= 50:
			job_costs = 40 * self.billets_produced
		elif self.billets_produced <= 100:
			job_costs = 30 * self.billets_produced
		# FIXME: лишний вызов
		self.balance_detail['variable_costs'] = job_costs\
												+ self.count_negotiation_costs()
		return job_costs + self.billets_cost * self.billets_produced

	def count_storage_costs(self) -> int:
		"""
		Считает затраты на хранение заготовок
		"""
		storage_costs = self.billets_stored * 50
		self.balance_detail['storage'] = storage_costs
		return storage_costs

	def count_logistics_costs(self) -> int:
		"""
		Считает затраты на доставку заготовок
		"""
		costs = 0
		for transaction in self.transactions:
			costs += transaction['terms']['quantity'] * transaction['terms']['transporting_cost']
		self.balance_detail['logistics'] = costs
		return costs

	def count_negotiation_costs(self) -> int:
		"""
		Считает затраты на проведение переговоров
		"""
		return len(self.transactions) * 20

	def make_deal(self, deal: dict) -> None:
		"""
		Формирует сделку с маклером
		"""
		self.transactions.append(deal)
		return

	def count_proceeds(self) -> int:
		"""
		Считает прибыль от продажи заготовок
		"""
		proceeds = 0
		for transaction in self.transactions:
			proceeds += transaction['terms']['quantity'] * transaction['terms']['price']

		self.balance_detail['sales_income'] = proceeds
		return proceeds

	@property
	def billets_left(self) -> int:
		"""
		Заготовки, оставшиеся у производителя после совершения сделок
		"""
		billets_requested = 0
		for transaction in self.transactions:
			billets_requested += transaction['terms']['quantity']
		billets_left = self.billets_stored + self.billets_produced - billets_requested
		return billets_left

	def store_billets(self) -> None:
		"""
		Отправляет заготовки на склад
		"""
		self.billets_stored = self.billets_left
		self.billets_produced = 0
		return

	def produce(self, billet_amount) -> None:
		"""
		Отправляет заготовки в прозизводство
		"""
		self.billets_produced = billet_amount
		self.balance_detail['raw_stuff_costs'] = billet_amount\
												 * self.billets_cost
		return

	def set_end_turn_balance(self) -> None:
		"""
		Записывает в детализацию баланс на конец хода
		"""
		self.balance_detail['end_turn_balance'] = self.balance
		return
