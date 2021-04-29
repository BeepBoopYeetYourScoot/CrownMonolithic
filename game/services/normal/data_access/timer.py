import threading
from . import count_session


def timer(session):
    """
    Запускает таймер и сохраняет модель хода, если таймер истёк. Время вводится в минутах
    """
    if session.status == 'started' and session.turn_phase == 'negotiation':
        negotiation_time = session.turn_time.get(turn=session.current_turn).negotiation_time
        time_in_seconds = negotiation_time * 60
        return threading.Timer(time_in_seconds, count_session.change_phase, args=[session, 'transaction'])
    elif session.status == 'started' and session.turn_phase == 'transaction':
        transaction_time = session.turn_time.get(turn=session.current_turn).transaction_time
        time_in_seconds = transaction_time * 60
        return threading.Timer(time_in_seconds, count_session.count_session, args=[session])
