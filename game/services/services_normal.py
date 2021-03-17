from .crown import CrownNormal

# FIXME
#  На данный момент сделка между маклером и производителем обрывается, если маклер обанкротился при проходе
#  сделок с производителями в порядке их перечисления. Как это должно выглядеть на самом деле?


def count_turn(producer_list: list, broker_list: list, transaction_list: list, crown_balance: float) -> dict:
    crown = CrownNormal()
    crown.balance = crown_balance
    market_volume = 0
    for transaction in transaction_list:
        market_volume += transaction['terms']['quantity']
    market_price = crown.count_market_price(market_volume)
    # Пересчёт постоянных затрат
    for producer in producer_list:
        producer.balance -= producer.count_fixed_costs()
        if producer.balance < 0:
            producer.is_bankrupt = True
    for broker in broker_list:
        broker.balance -= broker.fixed_costs
        if broker.balance < 0:
            broker.is_bankrupt = True

    # Пересчёт переменных затрат
    for producer in producer_list:
        variable_costs_summarized = producer.count_variable_costs() + producer.count_negotiation_costs() \
                                    + producer.count_logistics_costs()
        producer.balance -= variable_costs_summarized
        if producer.balance < 0:
            producer.is_bankrupt = True

    for broker in broker_list:
        broker.balance -= broker.count_purchase_costs()
        if broker.balance < 0:
            broker.is_bankrupt = True

    # Расчёт прибыли
    for producer in producer_list:
        producer.balance += producer.count_proceeds()
    for broker in broker_list:
        broker.add_shipments()
        broker.balance += broker.count_proceeds(market_price)

    # Расчёт расходов на хранение и отправка на хранение заготовок
    for producer in producer_list:
        producer.balance -= producer.count_storage_costs()
        if producer.balance < 0:
            producer.is_bankrupt = True
            continue
        producer.store_billets()

    crown.update_balance(market_volume)
    results = {
        'producers': producer_list,
        'brokers': broker_list,
        'crown_balance': crown.balance
    }
    return results
