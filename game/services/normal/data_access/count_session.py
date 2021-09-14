import random

from game.models import PlayerModel, TransactionModel, BalanceRequest, TurnTime, SessionModel
from ..business_logic.count_turn import count_turn
from ..business_logic.producer import ProducerNormal
from ..business_logic.broker import BrokerNormal
from ..business_logic.transaction import TransactionNormal as Transaction
from game.services.model_generator import generate_role_instances
from game.services.role_randomizer import distribute_roles


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


def save_producer(producer_class: ProducerNormal, producer_player_model: PlayerModel) -> None:
    """
    Сохраняет результат пересчёта производителя в БД
    """
    producer_player_model.balance = producer_class.balance
    producer_player_model.is_bankrupt = producer_class.is_bankrupt
    producer_player_model.producer.billets_produced = producer_class.billets_produced
    producer_player_model.producer.billets_stored = producer_class.billets_stored
    producer_player_model.status = producer_class.status

    producer_player_model.save()
    producer_player_model.producer.save()
    producer_class.balance_detail.save()
    return


def save_broker(broker_class: BrokerNormal, broker_player_model: PlayerModel) -> None:
    """
    Сохраняет результат пересчёта маклера в БД.
    """
    broker_player_model.balance = broker_class.balance
    broker_player_model.is_bankrupt = broker_class.is_bankrupt
    broker_player_model.status = broker_class.status
    broker_player_model.broker.code = random.randint(111111, 999999)

    broker_player_model.save()
    broker_player_model.broker.save()
    broker_class.balance_detail.save()
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
    elif 15 <= number_of_players <= 20:
        if not session_instance.number_of_brokers:
            session_instance.number_of_brokers = 4
        if not session_instance.broker_starting_balance:
            session_instance.broker_starting_balance = 12000
        if not session_instance.producer_starting_balance:
            session_instance.producer_starting_balance = 6000
    elif 21 <= number_of_players <= 25:
        if not session_instance.number_of_brokers:
            session_instance.number_of_brokers = 5
        if not session_instance.broker_starting_balance:
            session_instance.broker_starting_balance = 12000
        if not session_instance.producer_starting_balance:
            session_instance.producer_starting_balance = 6000
    elif 26 <= number_of_players <= 35:
        if not session_instance.number_of_brokers:
            session_instance.number_of_brokers = 6
        if not session_instance.broker_starting_balance:
            session_instance.broker_starting_balance = 12000
        if not session_instance.producer_starting_balance:
            session_instance.producer_starting_balance = 6000

    distribute_roles(session_instance)
    generate_role_instances(session_instance)
    generate_turn_time(session_instance)
    # Начальный баланс Короны считается от начального баланса Маклеров и количества Маклеров в сессии
    session_instance.crown_balance = session_instance.broker_starting_balance * session_instance.number_of_brokers / 4

    session_instance.current_turn = 1
    session_instance.status = 'started'
    # turn_time.status = 'negotiation'
    session_instance.save()
    # turn_time.save()
    # timer(session_instance).start()


def change_phase(session_instance, phase: str) -> None:
    """
    Меняет фазу хода. Работает только на запущенной сессии
    """
    assert session_instance.pk is not None, 'Session doesn\'t exist'
    assert session_instance.status == 'started'

    session_instance.turn_phase = phase
    session_instance.save()
    [cancel_end_turn(player) for player in session_instance.player.all()]


def count_session(session_instance: SessionModel) -> None:
    """
    Пересчитывает параметры игроков внутри указанной сессии.
    """
    assert session_instance.pk is not None
    assert session_instance.status == 'started', 'Session has not started'
    if session_instance.turn_phase == 'negotiation':
        change_phase(session_instance, 'transaction')
        return

    producer_player_models = session_instance.player.filter(role='producer', is_bankrupt=False)
    broker_player_models = session_instance.player.filter(role='broker', is_bankrupt=False)

    transaction_models = session_instance.transaction.filter(
        turn=session_instance.current_turn,
        status='accepted')

    producer_classes, broker_classes, transaction_classes = [], [], []

    crown_balance = session_instance.crown_balance

    for transaction in transaction_models:
        transaction_classes.append(Transaction(transaction))

    for producer in producer_player_models:
        producer_classes.append(ProducerNormal(producer))

    for broker in broker_player_models:
        broker_classes.append(BrokerNormal(broker))

    crown_balance_updated = count_turn(producer_classes, broker_classes, transaction_classes,
                                       crown_balance)

    for producer_class in producer_classes:
        for producer_player_model in producer_player_models:
            if producer_player_model.id == producer_class.id:
                save_producer(producer_class, producer_player_model)

    for broker_class in broker_classes:
        for broker_player_model in broker_player_models:
            if broker_player_model.id == broker_class.id:
                save_broker(broker_class, broker_player_model)

    session_instance.crown_balance = crown_balance_updated

    if session_instance.current_turn == session_instance.turn_count:
        finish_session(session_instance)
        return

    session_instance.current_turn += 1
    session_instance.turn_phase = 'negotiation'

    session_instance.save()


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
    return


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
        raise ValueError('Сделка уже рассмотрена!')
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
