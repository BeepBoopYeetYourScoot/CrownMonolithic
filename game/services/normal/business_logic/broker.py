from game.services.broker import AbstractBroker


class BrokerNormal(AbstractBroker):
    """
    Класс маклера для версии "Нормал"
    """

    def __init__(self, balance):
        self.id = 0
        self.balance = balance
        self.shipment = 0
        self.transactions = []
        self.is_bankrupt = False
        self.status = 'OK'
        self.balance_detail = None

    fixed_costs = 1000

    def add_shipments(self) -> None:
        """
        Отправляет заготовки на транспортировку Короне
        """
        for transaction in self.transactions:
            self.shipment += transaction['terms']['quantity']
        return

    def make_deal(self, deal: dict) -> None:
        """
        Совершает сделку с производителем
        """
        self.transactions.append(deal)
        return

    def count_purchase_costs(self) -> int:
        """Считает затраты маклера на совершение сделок"""
        costs = 0
        for transaction in self.transactions:
            costs += transaction['terms']['quantity'] * transaction['terms']['price']
        return costs

    def count_proceeds(self, market_price) -> float:
        """Считает выручку от продажи заготовок"""
        return self.shipment * market_price

    def count_turn_balance_detail(self, crown_balance=0) -> None:
        """
        Записывает детализацию баланса за ход
        """
        self.balance_detail = {
            'start_turn_balance': self.balance,

            'purchase_blanks': self.count_purchase_costs(),
            'logistics': 1500 if self.shipment > 0 else 0,
            'blanks': self.shipment,
            'fine': 0,
            'crown': crown_balance,

            'end_turn_balance': 0,
        }
        return

    def set_end_turn_balance(self) -> None:
        self.balance_detail['end_turn_balance'] = self.balance
        return


transaction_example = {
    'producer': 0,
    'broker': 0,
    'terms': {
        'quantity': 0,
        'material': 0,
        'machine': ('chinese', 'oak', 3),
        'price': 0
    }
}
