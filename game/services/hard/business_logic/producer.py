from game.services.producer import AbstractProducer


class ProducerHard(AbstractProducer):

    def __init__(self, balance):
        self.balance = balance
        self.billets_produced = (0, 0, 0)
        self.billets_stored = {
            'spruce': (0, 0, 0),
            'oak': (0, 0, 0),
            'redwood': (0, 0, 0)
        }
        self.machinery = {
            'chinese': [],
            'korean': [],
            'german': []
        }
        # Предполагается, что данные транзакции прошли все необходимые проверки, как то:
        # 1) На сумму сделки
        # 2) На наличие заготовок у производителя
        # 3) На наличие денег у маклера
        self.transactions = []

    def count_fixed_costs(self) -> float:
        rent_coefficient = 0.93 ** (self.machine[1] - 1)
        base_fixed_costs = 1000
        # Для китайских станков
        if self.machinery['chinese'][0] == self.machine_quality['chinese']:
            if self.billets_produced[0] <= 10:
                return (base_fixed_costs + 200) * rent_coefficient
            elif self.billets_produced[0] <= 20:
                return (base_fixed_costs + 350) * rent_coefficient
            elif self.billets_produced[0] <= 30:
                return (base_fixed_costs + 500) * rent_coefficient
            elif self.billets_produced[0] <= 50:
                return (base_fixed_costs + 700) * rent_coefficient
            else:
                raise AttributeError
        # Для корейских станков
        elif self.machine[0] == 0.6:
            if self.billets_produced[0] <= 10:
                return (base_fixed_costs + 350) * rent_coefficient
            elif self.billets_produced[0] <= 20:
                return (base_fixed_costs + 600) * rent_coefficient
            elif self.billets_produced[0] <= 30:
                return (base_fixed_costs + 1000) * rent_coefficient
            elif self.billets_produced[0] <= 50:
                return (base_fixed_costs + 1400) * rent_coefficient
            else:
                raise AttributeError
        # Для немецких станков
        elif self.machine[0] == 1:
            if self.billets_produced[0] <= 10:
                return (base_fixed_costs + 500) * rent_coefficient
            elif self.billets_produced[0] <= 20:
                return (base_fixed_costs + 900) * rent_coefficient
            elif self.billets_produced[0] <= 30:
                return (base_fixed_costs + 1300) * rent_coefficient
            elif self.billets_produced[0] <= 50:
                return (base_fixed_costs + 1700) * rent_coefficient
            else:
                raise AttributeError

    def count_variable_costs(self) -> int:
        if self.billets_produced[1] == self.material['spruce']:
            if self.billets_produced[0] <= 10:
                return 80 * self.billets_produced[0]
            elif self.billets_produced[0] <= 20:
                return 75 * self.billets_produced[0]
            elif self.billets_produced[0] <= 30:
                return 70 * self.billets_produced[0]
            elif self.billets_produced[0] <= 50:
                return 65 * self.billets_produced[0]
            else:
                raise AttributeError
        elif self.billets_produced[1] == self.material['oak']:
            if self.billets_produced[0] <= 10:
                return 110 * self.billets_produced[0]
            elif self.billets_produced[0] <= 20:
                return 100 * self.billets_produced[0]
            elif self.billets_produced[0] <= 30:
                return 90 * self.billets_produced[0]
            elif self.billets_produced[0] <= 50:
                return 80 * self.billets_produced[0]
            else:
                raise AttributeError
        elif self.billets_produced[1] == self.material['redwood']:
            if self.billets_produced[0] <= 10:
                return 160 * self.billets_produced[0]
            elif self.billets_produced[0] <= 20:
                return 150 * self.billets_produced[0]
            elif self.billets_produced[0] <= 30:
                return 135 * self.billets_produced[0]
            elif self.billets_produced[0] <= 50:
                return 110 * self.billets_produced[0]
            else:
                raise AttributeError

    def count_logistics_costs(self) -> int:
        costs = 0
        for transaction in self.transactions:
            costs += transaction['terms']['billets'][0] * transaction['terms']['transporting_cost']
        return costs

    def count_negotiation_costs(self) -> int:
        return len(self.transactions) * 20

    def count_storage_costs(self) -> int:
        return len(self.transactions)

    def count_proceeds(self) -> int:
        proceeds = 0
        for transaction in self.transactions:
            proceeds += transaction['terms']['billets'][0] * transaction['terms']['price']
        return proceeds

    def make_deal(self, deal: dict) -> None:
        self.transactions.append(deal)
        return

    @property
    def billets_left(self) -> int:
        spruce_available = [x for x in self.billets_stored if x[1] == self.material['spruce']]
        oak_available = [x for x in self.billets_stored if x[1] == self.material['oak']]
        redwood_available = [x for x in self.billets_stored if x[1] == self.material['redwood']]
        for transaction in self.transactions:
            spruce_requested = []
            oak_requested = []
            redwood_requested = []
        return 0

    def produce(self, billet_amount, quality) -> None:
        self.billets_produced = (billet_amount, quality, self.machine[0])
        if billet_amount > 0:
            self.billets_stored.append(self.billets_produced)
        return

    def update_machine(self, machine_quality, rent_duration) -> None:
        self.machine = (machine_quality, rent_duration)
        return
