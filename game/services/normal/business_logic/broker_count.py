from typing import List
from game.services.normal.business_logic.broker import BrokerNormal
from game.services.normal.business_logic.producer import ProducerNormal


def count_fixed_costs(broker_classes: List[BrokerNormal]):
    for broker in broker_classes:
        if broker.is_bankrupt:
            continue
        broker.balance -= broker.fixed_costs
        if broker.balance < 0:
            broker.status = 'FIXED'
            broker.is_bankrupt = True


def check_shipments(broker_classes: List[BrokerNormal], producer_classes: List[ProducerNormal]):
    """
    Проверяет, будут ли оплачены сделки маклерами
    """
    for broker in broker_classes:
        initial_balance = broker.balance
        for transaction in broker.transactions:
            # Пропускаю сделку, если Производитель обанкротился на переменных расходах
            # (не смог произвести)
            producer = None
            for prod in producer_classes:
                if prod.id == transaction.producer:
                    producer = prod
            if producer.is_bankrupt:
                continue

            initial_balance -= transaction.quantity * transaction.price
            # Прекращаю проверку оплату сделок, если по ходу какой-то из сделок маклер обранкротится
            if initial_balance < 0:
                break
            transaction.paid = True


def count_variable_costs(broker_classes: List[BrokerNormal], producer_classes: List[ProducerNormal]):
    for broker in broker_classes:
        if broker.is_bankrupt:
            continue

        for transaction in broker.transactions:
            broker.balance -= transaction.delivered * transaction.price
            broker.billets_bought += transaction.quantity
            if broker.balance < 0:
                broker.status = 'VARIABLE'
                broker.is_bankrupt = True
                # Если маклер не смог купить все заготовки,
                # то производитель должен будет доставить ему только то количество заготовок,
                # которое маклер смог купить
                transaction.delivered = (
                                        broker.balance + transaction.delivered * transaction.price) // transaction.price

        broker.balance_detail.billets_sold = broker.billets_bought


def count_proceeds(broker_classes: List[BrokerNormal], market_price):
    for broker in broker_classes:
        broker.balance += broker.count_proceeds(market_price)

