from .crown import CrownNormal


def count_turn(producer_list: list, broker_list: list, transaction_list: list, crown_balance: float) -> float:
    """
    Принимает на вход массивы объектов производителей и маклеров.
    Изменяет свойства объектов, полученных на входе.
    Возвращает баланс Короны на следующий ход
    """
    crown = CrownNormal()
    crown.balance = crown_balance
    market_volume = 0
    for transaction in transaction_list:
        market_volume += transaction['terms']['quantity']
    market_price = crown.count_market_price(market_volume)

    # Пересчёт постоянных затрат
    for producer in producer_list:
        if producer.is_bankrupt:
            continue
        producer.balance -= producer.count_fixed_costs()
        if producer.balance < 0:
            producer.status = 'FIXED'
            producer.is_bankrupt = True
    for broker in broker_list:
        if broker.is_bankrupt:
            continue
        broker.balance -= broker.fixed_costs
        if broker.balance < 0:
            broker.status = 'FIXED'
            broker.is_bankrupt = True

    # Пересчёт переменных затрат
    for producer in producer_list:
        if producer.is_bankrupt:
            continue

        variable_costs_summarized = producer.count_variable_costs() + producer.count_negotiation_costs() \
                                    + producer.count_logistics_costs()
        producer.balance -= variable_costs_summarized
        if producer.balance < 0:
            producer.status = 'VARIABLE'
            producer.is_bankrupt = True

    for broker in broker_list:
        if broker.is_bankrupt:
            continue
        for prod in producer_list:
            broker.disrupt_transaction(prod)
        broker.balance -= broker.count_purchase_costs()
        if broker.balance < 0:
            broker.status = 'VARIABLE'
            broker.is_bankrupt = True
        broker.add_shipments()

    # Расчёт прибыли
    for producer in producer_list:
        if producer.is_bankrupt:
            continue
        producer.balance += producer.count_proceeds()

    for broker in broker_list:
        if broker.is_bankrupt:
            continue
        broker.balance += broker.count_proceeds(market_price)

    # Расчёт расходов на хранение и отправка на хранение заготовок
    for producer in producer_list:
        if producer.is_bankrupt:
            continue
        producer.store_billets()
        if producer.billets_stored < 0:
            producer.status = 'UNTRUSTED'
            producer.is_bankrupt = True
        producer.balance -= producer.count_storage_costs()
        if producer.balance < 0:
            producer.status = 'STORAGE'
            producer.is_bankrupt = True
            continue

    crown.update_balance(market_volume)

    return crown.balance
