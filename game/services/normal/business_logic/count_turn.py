from typing import List

from .broker import BrokerNormal
from .crown import CrownNormal
from .producer import ProducerNormal
from .transaction import TransactionNormal
from game.services.normal.business_logic import producer_count as producers
from game.services.normal.business_logic import broker_count as brokers


# FIXME проверить стыковку баланса Короны (я поставил int, а там был float)
def count_turn(producer_classes: List[ProducerNormal],
               broker_classes: List[BrokerNormal],
               transaction_classes: List[TransactionNormal],
               crown_balance: int) -> int:
    """
    Принимает на вход массивы объектов производителей и маклеров.
    Изменяет свойства объектов, полученных на входе.
    Возвращает баланс Короны на следующий ход
    """

    for producer in producer_classes:
        producer.transactions = [tr for tr in transaction_classes if tr.producer == producer.id]

    for broker in broker_classes:
        broker.transactions = [tr for tr in transaction_classes if tr.broker == broker.id]
        broker.balance_detail.crown_balance = crown_balance

    producers.count_fixed_costs(producer_classes)
    brokers.count_fixed_costs(broker_classes)

    # Пересчёт переменных затрат
    producers.count_variable_costs(producer_classes)

    # Проверка, могут ли маклеры оплатить свои сделки
    brokers.check_shipments(broker_classes, producer_classes)

    # Проверка производителей на недобросовестность
    producers.check_shipments(producer_classes)

    producers.count_logistics_costs(producer_classes)

    brokers.count_variable_costs(broker_classes)

    # Вычисление рыночной цены 1 заготовки
    crown = CrownNormal(crown_balance)

    market_volume = sum([tr.delivered for tr in transaction_classes if tr.paid])

    market_price = crown.count_market_price(market_volume)

    producers.count_proceeds(producer_classes)

    brokers.count_proceeds(broker_classes, market_price)

    # Расчёт расходов на хранение и отправка на хранение заготовок
    producers.count_storage_costs(producer_classes)

    check_fixed_costs_bankruptcy(producer_classes, broker_classes)

    crown.update_balance(market_volume)

    return crown.balance


def check_fixed_costs_bankruptcy(producer_classes, broker_classes):
    """
    Банкротит игроков, если они не могут оплатить постоянные расходы следующего хода
    """
    for producer in producer_classes:
        if producer.balance - producer.count_fixed_costs() < 0:
            producer.is_bankrupt = True
            producer.status = 'FIXED'

    for broker in broker_classes:
        if broker.balance - broker.fixed_costs < 0:
            broker.is_bankrupt = True
            broker.status = 'FIXED'
