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
        self.transactions = []
        self.is_bankrupt = False
        self.status = 'OK'

    def count_fixed_costs(self) -> float:
        """
        Считает постоянные затраты производителя в зависимости от числа производимых заготовок
        """
        if self.billets_produced <= 10:
            return 600
        elif self.billets_produced <= 20:
            return 1000
        elif self.billets_produced <= 30:
            return 1400
        elif self.billets_produced <= 50:
            return 2000
        elif self.billets_produced <= 100:
            return 4000
        else:
            return 15000

    def count_variable_costs(self) -> int:
        """
        Считает переменные затраты в зависимости от числа производимых заготовок
        """
        if self.billets_produced <= 10:
            return 110 * self.billets_produced
        elif self.billets_produced <= 20:
            return 100 * self.billets_produced
        elif self.billets_produced <= 30:
            return 85 * self.billets_produced
        elif self.billets_produced <= 50:
            return 70 * self.billets_produced
        elif self.billets_produced <= 100:
            return 60 * self.billets_produced

    def count_storage_costs(self) -> int:
        """
        Считает затраты на хранение заготовок
        """
        return self.billets_stored * 50

    def count_logistics_costs(self) -> int:
        """
        Считает затраты на доставку заготовок
        """
        costs = 0
        for transaction in self.transactions:
            costs += transaction['terms']['quantity'] * transaction['terms']['transporting_cost']
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
        return

    def turn_balance_detail(self) -> dict:
        """
        Показывает детализацию баланса производителя за предыдущий ход
        """
        return {
            'fixed_costs': self.count_fixed_costs(),
            'operational_costs': self.count_variable_costs(),
            'negotiation_costs': self.count_negotiation_costs(),
            'transporting_costs': self.count_logistics_costs(),
            'storage_costs': self.count_storage_costs(),
            'proceeds': self.count_proceeds()
        }

"""
+ Создание сделок по ключу маклера
+ Результаты игры
Роутинг для таймера
Админка
"""