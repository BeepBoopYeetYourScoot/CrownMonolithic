import random
import threading

from game.models import PlayerModel, TransactionModel, BalanceDetail, \
    BalanceRequest, TurnTime
from .timer import timer
from ..business_logic.count_turn import count_turn
from ..business_logic.producer import ProducerNormal
from ..business_logic.broker import BrokerNormal
from ..business_logic.transaction import TransactionNormal as Transaction
from game.services.model_generator import generate_role_instances
from game.services.role_randomizer import distribute_roles
from game.serializers import ProducerBalanceDetailSerializer, \
    BrokerBalanceDetailSerializer

PLAYER_NUMBER_PRESET = (
    ('12-14', '12-14 Игроков'),
    ('15-20', '15-20 Игроков'),
    ('21-25', '21-25 Игроков'),
    ('26-30', '26-30 Игроков'),
    ('31-35', '31-35 Игроков'),
)


def generate_producer(db_producer_player, producer_class) -> ProducerNormal:
    """
    Генерирует экземпляр класса производителя и возвращает экземпляр
    """
    producer = producer_class(db_producer_player.balance)
    producer.id = db_producer_player.producer.id
    producer.billets_produced = db_producer_player.producer.billets_produced
    producer.billets_stored = db_producer_player.producer.billets_stored
    return producer


def generate_broker(db_broker_player, broker_class) -> BrokerNormal:
    """
    Генерирует экземпляр класса маклера и возвращает экземпляр
    """
    broker = broker_class(db_broker_player.balance)
    broker.id = db_broker_player.broker.id
    return broker


def save_producer(producer_class_instance, db_producer_player) -> None:
    """
    Сохраняет результат пересчёта производителя в БД
    """
    db_producer_player.balance = producer_class_instance.balance
    db_producer_player.is_bankrupt = producer_class_instance.is_bankrupt
    db_producer_player.producer.billets_produced = producer_class_instance.billets_produced
    db_producer_player.producer.billets_stored = producer_class_instance.billets_stored
    db_producer_player.status = producer_class_instance.status

    balance_detail_instance, _ = BalanceDetail.objects.get_or_create(player=db_producer_player)
    detail_serializer = ProducerBalanceDetailSerializer(
        balance_detail_instance, data=producer_class_instance.balance_detail)

    detail_serializer.save() if detail_serializer.is_valid() else print('Проблема с сериализатором производителя')
    db_producer_player.save()
    db_producer_player.producer.save()
    return


def save_broker(broker_class_instance, db_broker_player) -> None:
    """
    Сохраняет результат пересчёта маклера в БД.
    """
    db_broker_player.balance = broker_class_instance.balance
    db_broker_player.is_bankrupt = broker_class_instance.is_bankrupt
    db_broker_player.status = broker_class_instance.status

    balance_detail_instance, _ = BalanceDetail.objects.get_or_create(player=db_broker_player)
    detail_serializer = BrokerBalanceDetailSerializer(
        balance_detail_instance, data=broker_class_instance.balance_detail)
    detail_serializer.save() if detail_serializer.is_valid() else print('Проблема с сериализатором маклера')

    db_broker_player.broker.code = random.randint(111111, 999999)
    db_broker_player.save()
    db_broker_player.broker.save()
    return


def start_session(session):
    """
    Запускает сессию. Работает только для созданной сессии.
    """
    session_instance = session
    assert session_instance.status == 'initialized'

    number_of_players = session_instance.player.count()
    if 12 <= number_of_players <= 14:
        if not session_instance.number_of_brokers:
            session_instance.number_of_brokers = 3
        if not session_instance.broker_starting_balance:
            session_instance.broker_starting_balance = 8000
        if not session_instance.producer_starting_balance:
            session_instance.producer_starting_balance = 4000
        session_instance.save()
    elif 15 <= number_of_players <= 20:
        if not session_instance.number_of_brokers:
            session_instance.number_of_brokers = 4
        if not session_instance.broker_starting_balance:
            session_instance.broker_starting_balance = 12000
        if not session_instance.producer_starting_balance:
            session_instance.producer_starting_balance = 6000
        session_instance.save()
    elif 21 <= number_of_players <= 25:
        if not session_instance.number_of_brokers:
            session_instance.number_of_brokers = 5
        if not session_instance.broker_starting_balance:
            session_instance.broker_starting_balance = 12000
        if not session_instance.producer_starting_balance:
            session_instance.producer_starting_balance = 6000
        session_instance.save()
    elif 26 <= number_of_players <= 30:
        if not session_instance.number_of_brokers:
            session_instance.number_of_brokers = 6
        if not session_instance.broker_starting_balance:
            session_instance.broker_starting_balance = 12000
        if not session_instance.producer_starting_balance:
            session_instance.producer_starting_balance = 6000
        session_instance.save()
    elif 31 <= number_of_players <= 35:
        if not session_instance.number_of_brokers:
            session_instance.number_of_brokers = 7
        if not session_instance.broker_starting_balance:
            session_instance.broker_starting_balance = 12000
        if not session_instance.producer_starting_balance:
            session_instance.producer_starting_balance = 6000
        session_instance.save()

    distribute_roles(session_instance)
    generate_role_instances(session_instance)
    generate_turn_time(session_instance)
    session_instance.crown_balance = session_instance.broker_starting_balance * session_instance.number_of_brokers / 4

    session_instance.current_turn = 1
    session_instance.status = 'started'
    session_instance.save()
    timer(session_instance).start()


def change_phase(session_instance, phase: str) -> None:
    """
    Меняет фазу хода. Работает только на запущенной сессии
    """
    assert session_instance.pk is not None, 'Session doesn\'t exist'
    assert session_instance.status == 'started'

    session_instance.turn_phase = phase
    session_instance.save()
    [cancel_end_turn(player) for player in session_instance.player.all()]
    timer(session_instance).start()


def count_session(session) -> None:
    """
    Пересчитывает параметры игроков внутри указанной сессии.
    """
    session_instance = session
    assert session_instance.pk is not None
    assert session_instance.status == 'started', 'Session has not started'
    assert session_instance.turn_phase == 'transaction', \
        'Session is in the wrong phase'

    players_queryset = session_instance.player.all()
    db_producers_queryset = players_queryset.filter(role='producer')
    db_broker_queryset = players_queryset.filter(role='broker')

    db_producers, db_brokers = [], []

    for player in db_producers_queryset:
        db_producers.append(player)
    for player in db_broker_queryset:
        db_brokers.append(player)

    db_transactions = session_instance.transaction.filter(
        turn=session_instance.current_turn, status='accepted')

    producers, brokers, transactions = [], [], []

    crown_balance = session_instance.crown_balance

    for transaction in db_transactions:
        terms = {
            'quantity': transaction.quantity,
            'price': transaction.price,
            'transporting_cost': transaction.transporting_cost
        }
        deal = Transaction(transaction.producer.id, transaction.broker.id, terms).form_transaction()
        transactions.append(deal)

    for db_producer in db_producers:
        producer = generate_producer(db_producer, ProducerNormal)
        for transaction in transactions:
            if transaction['producer'] == producer.id:
                producer.make_deal(transaction)
        producers.append(producer)

    for db_broker in db_brokers:
        broker = generate_broker(db_broker, BrokerNormal)
        for transaction in transactions:
            if transaction['broker'] == broker.id:
                broker.make_deal(transaction)
        # TODO: Может стоит перенести в generate_broker
        broker.set_previous_crown_balance(crown_balance=crown_balance)
        brokers.append(broker)

    crown_balance_updated = count_turn(producers, brokers, transactions,
                                       crown_balance)

    for producer in producers:
        for db_producer in db_producers:
            if db_producer.producer.id == producer.id:
                producer.set_end_turn_balance()
                save_producer(producer, db_producer)

    for broker in brokers:
        for db_broker in db_brokers:
            if db_broker.broker.id == broker.id:
                broker.set_end_turn_balance()
                save_broker(broker, db_broker)

    session_instance.crown_balance = crown_balance_updated

    if session_instance.current_turn == session_instance.turn_count:
        session_instance.status = 'finished'
        session_instance.save()
        return

    session_instance.current_turn += 1
    session_instance.turn_phase = 'negotiation'

    for player in session_instance.player.all():
        player.ended_turn = False
        player.save()

    session_instance.save()
    timer(session_instance).start()


def finish_session(session_instance):
    """
    Завершает запущенную сессию
    """
    assert session_instance.status == 'started', 'Сессия не запущена'
    session_instance.status = 'finished'
    players = session_instance.player.all().order_by('-balance')
    for place, player in enumerate(players):
        player.position = place + 1
        player.save()
    session_instance.save()
    # ws_services.notify_finish(session_instance.id)
    return


# def return_started_status(session_instance):
# 	assert session_instance.pk is not None
# 	return session_instance.status


def create_player(session_instance, nickname):
    """
    Создаёт модель игрока при подключении к лобби
    """
    player = PlayerModel.objects.create(session_id=session_instance.id, nickname=nickname)
    player.save()
    return


def produce_billets(producer, quantity):
    """
    Отправляет заявку на производство заготовок
    """
    producer.billets_produced = quantity
    producer.save()
    return


def send_trade(producer, broker, terms):
    """
    Отправляет сделку маклеру
    """
    if TransactionModel.objects.filter(
            producer_id=producer.id,
            broker_id=broker.id,
            turn=producer.player.session.current_turn
    ).exists():
        raise ValueError('You\'ve already have deal with this broker!')

    TransactionModel.objects.create(
        session_id=producer.player.session_id,
        producer_id=producer.id,
        broker_id=broker.id,
        quantity=terms['quantity'],
        price=terms['price'],
    ).save()
    return


def cancel_trade(producer, broker):
    """
    Отменяет сделку с маклером
    """
    TransactionModel.objects.get(
        producer_id=producer.id,
        broker_id=broker.id,
    ).delete()
    return


def end_turn(player):
    """
    Завершает ход
    """
    player.ended_turn = True
    player.save()
    return


def cancel_end_turn(player):
    """
    Отменяет завершение хода
    """
    player.ended_turn = False
    player.save()
    return


def accept_transaction(producer, broker):
    """
    Одобряет сделку маклера с производителем
    """
    transaction = TransactionModel.objects.get(
        producer_id=producer.id,
        broker_id=broker.id,
        turn=broker.player.session.current_turn
    )
    if not transaction.status == 'active':
        raise ValueError('Сделка уже рассмотренна!')
    transaction.status = 'accepted'
    transaction.save()


def deny_transaction(producer, broker):
    """
    Отклоняет сделку
    """
    transaction = TransactionModel.objects.get(
        producer_id=producer.id,
        broker_id=broker.id,
        turn=broker.player.session.current_turn
    )
    if not transaction.status == 'active':
        raise ValueError('Сделка уже рассмотренна!')
    transaction.status = 'denied'
    transaction.save()


def create_balance_request(producer, broker) -> None:
    """
    Создает запрос на просмотр баланса
    :param producer: PlayerModel
    :param broker: PlayerModel
    """
    BalanceRequest.objects.create(
        producer=producer,
        broker=broker,
        turn=broker.player.session.current_turn
    )
    return


def accept_balance_request(producer, broker) -> None:
    """
    Согласует запрос на просмотр баланса
    :param producer: PlayerModel
    :param broker: PlayerModel
    """
    requests = BalanceRequest.objects.filter(
        producer=producer,
        broker=broker,
        turn=broker.player.session.current_turn,
        status='active'
    )
    # Цикл для ситуации, в которой маклер несколько раз отправил заявку
    for request in requests:
        request.status = 'accepted'
        request.save()
    return


def deny_balance_request(producer, broker) -> None:
    """
    Отклоняет запрос на просмотр баланса
    :param producer: PlayerModel
    :param broker: PlayerModel
    """
    requests = BalanceRequest.objects.filter(
        producer=producer,
        broker=broker,
        turn=broker.player.session.current_turn,
        status='active'
    )
    # Цикл для ситуации, в которой маклер несколько раз отправил заявку
    for request in requests:
        request.status = 'denied'
        request.save()
    return


def generate_code() -> int:
    """
    Генерирует шестизначный код маклера
    """
    return random.randint(111111, 999999)


def generate_turn_time(session_instance):
    turn = 1
    while turn <= session_instance.turn_count:
        TurnTime.objects.create(session=session_instance, turn=turn)
        turn += 1
