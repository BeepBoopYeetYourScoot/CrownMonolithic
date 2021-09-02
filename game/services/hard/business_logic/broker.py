from game.services.broker import AbstractBroker


class BrokerHard(AbstractBroker):
    def __init__(self, balance):
        self.balance = balance
        self.shipments_spruce = []
        self.shipments_oak = []
        self.shipments_redwood = []
        self.transactions = []

    def add_shipments(self) -> None:
        """Раскидывает заготовки на отправку согласно материалу"""
        for transaction in self.transactions:
            material = transaction['terms']['material']
            if material == self.material['spruce']:
                self.shipments_spruce.append(transaction['terms'])
            elif material == self.material['oak']:
                self.shipments_oak.append(transaction['terms'])
            elif material == self.material['redwood']:
                self.shipments_redwood.append(transaction['terms'])
        return

    def make_deal(self, deal: dict) -> None:
        """Совершает сделку с производителем"""
        self.transactions.append(deal)
        return

    def count_proceeds(self, market_price: dict) -> float:
        """Считает выручку маклера от продажи заготовок"""
        proceeds = 0
        for shipment in self.shipments_spruce:
            proceeds += shipment['quantity'] * shipment['material'] * shipment['machine'] * market_price['spruce']
        for shipment in self.shipments_oak:
            proceeds += shipment['quantity'] * shipment['material'] * shipment['machine'] * market_price['oak']
        for shipment in self.shipments_redwood:
            proceeds += shipment['quantity'] * shipment['material'] * shipment['machine'] * market_price['redwood']
        return proceeds

    def count_purchase_costs(self) -> int:
        """Считает затраты маклера на покупку заготовок"""
        costs = 0
        spruce_purchased = [x['terms'] for x in self.transactions if x['terms']['material'] == self.material['spruce']]
        oak_purchased = [x['terms'] for x in self.transactions if x['terms']['material'] == self.material['oak']]
        redwood_purchased = [x['terms'] for x in self.transactions if
                             x['terms']['material'] == self.material['redwood']]
        for purchase in spruce_purchased:
            costs += purchase['quantity'] * purchase['price']
        for purchase in oak_purchased:
            costs += purchase['quantity'] * purchase['price']
        for purchase in redwood_purchased:
            costs += purchase['quantity'] * purchase['price']
        return costs
