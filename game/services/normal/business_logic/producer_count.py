from typing import List

from game.services.normal.business_logic.producer import ProducerNormal


def count_fixed_costs(producer_classes: List[ProducerNormal]):
    for producer in producer_classes:
        if producer.is_bankrupt:
            continue
        producer.balance -= producer.count_fixed_costs()
        producer.balance_detail.fixed = producer.count_fixed_costs()
        if producer.balance < 0:
            producer.status = 'FIXED'
            producer.is_bankrupt = True


def count_variable_costs(producer_classes: List[ProducerNormal]):
    for producer in producer_classes:
        if producer.is_bankrupt:
            continue

        producer.balance -= producer.count_variable_costs()
        producer.balance -= producer.billets_cost * producer.billets_produced
        producer.balance_detail.variable = producer.count_variable_costs()
        producer.balance_detail.materials = producer.billets_cost * producer.billets_produced
        if producer.balance < 0:
            producer.status = 'VARIABLE'
            producer.is_bankrupt = True


def check_shipments(producer_classes: List[ProducerNormal]):
    """
    Проверяет, сколько заготовок может довезти производитель и сколько заготовок ему нужно довезти.
    На данном этапе нужно устанавливать штрафы за недобросовестность
    и отдавать маклерам то количество заготовок, которое произвёл производитель
    """
    for producer in producer_classes:
        if producer.is_bankrupt:
            continue

        billets_count = producer.billets_produced + producer.billets_stored

        for transaction in producer.transactions:
            if transaction.paid:
                billets_count -= transaction.quantity
                # Если производителю не хватает доставить все заготовки,
                # он доставляет последние оставшиеся
                if billets_count < 0:
                    producer.is_bankrupt = True
                    producer.status = 'UNTRUSTED'
                    producer.is_bankrupt = True
                    # Доставляю столько, сколько имеется
                    transaction.delivered = billets_count + transaction.quantity
                    break
                transaction.delivered = transaction.quantity


def count_logistics_costs(producer_classes: List[ProducerNormal]):
    for producer in producer_classes:
        if producer.is_bankrupt:
            continue
        negotiation_costs, logistics_costs, = 0, 0

        for transaction in producer.transactions:
            # Расходы на переговоры
            producer.balance -= 20
            # Расходы на доставку
            producer.balance -= transaction.quantity * transaction.transporting_cost
            if producer.balance < 0:
                producer.status = 'LOGISTICS'
                producer.is_bankrupt = True
                break
            transaction.delivered = transaction.quantity

        producer.balance_detail.negotiation = negotiation_costs
        producer.balance_detail.logistics = logistics_costs


def count_proceeds(producer_classes: List[ProducerNormal]):
    # Расчёт выручки
    for producer in producer_classes:
        if producer.is_bankrupt:
            continue
        producer.balance += producer.count_proceeds()
        producer.balance_detail.proceeds = producer.count_proceeds()
    print([pr.balance for pr in producer_classes])


def count_storage_costs(producer_classes: List[ProducerNormal]):
    for producer in producer_classes:
        if producer.is_bankrupt:
            continue
        producer.store_billets()
        producer.balance -= producer.count_storage_costs()
        producer.balance_detail.storage = producer.count_storage_costs()
        producer.balance_detail.end_turn_balance = producer.balance
        if producer.balance < 0:
            producer.status = 'STORAGE'
            producer.is_bankrupt = True
            continue
