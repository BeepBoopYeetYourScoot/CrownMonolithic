from game.services.producer import AbstractProducer
from game.models import ProducerModel


class ProducerNormal(AbstractProducer):
    """
    Класс производителя для версии "Нормал"
    """

    def __init__(self, producer: ProducerModel):
        self.id = producer.id
        self.balance = producer.player.balance
        self.billets_produced = producer.billets_produced
        self.billets_stored = producer.billets_stored
        self.billets_cost = 30
        self.transactions = []
        self.is_bankrupt = False
        self.status = 'OK'
        self.balance_detail = producer.player.detail

    def count_fixed_costs(self) -> int:
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
        return int(fixed_costs)

    def count_variable_costs(self) -> int:
        """
        Считает переменные затраты в зависимости от числа производимых заготовок
        """
        op_ex = None
        if self.billets_produced <= 10:
            op_ex = 80 * self.billets_produced
        elif self.billets_produced <= 20:
            op_ex = 70 * self.billets_produced
        elif self.billets_produced <= 30:
            op_ex = 55 * self.billets_produced
        elif self.billets_produced <= 50:
            op_ex = 40 * self.billets_produced
        elif self.billets_produced <= 100:
            op_ex = 30 * self.billets_produced
        return op_ex

    def count_storage_costs(self) -> int:
        """
        Считает затраты на хранение заготовок
        """
        storage_costs = self.billets_stored * 50
        return storage_costs

    def count_logistics_costs(self) -> int:
        """
        Считает затраты на доставку заготовок
        """
        costs = 0
        for transaction in self.transactions:
            if transaction.paid:
                costs += transaction.quantity * transaction.transporting_cost
        return costs

    def count_negotiation_costs(self) -> int:
        """
        Считает затраты на проведение переговоров.
        Учитывает только сделки, которые смогли оплатить маклеры
        """
        return len([tr for tr in self.transactions if tr.paid]) * 20

    def count_proceeds(self) -> int:
        """
        Считает выручку от продажи заготовок
        """
        proceeds = 0
        for transaction in self.transactions:
            if transaction.paid:
                proceeds += transaction.delivered * transaction.price
        return proceeds

    @property
    def billets_left(self) -> int:
        """
        Заготовки, оставшиеся у производителя после совершения сделок
        """
        billets_requested = sum([tr.delivered for tr in self.transactions if tr.paid])
        billets_left = self.billets_stored + self.billets_produced - billets_requested
        return billets_left

    def store_billets(self) -> None:
        """
        Отправляет заготовки на склад
        """
        self.billets_stored = self.billets_left
        self.billets_produced = 0
        return
