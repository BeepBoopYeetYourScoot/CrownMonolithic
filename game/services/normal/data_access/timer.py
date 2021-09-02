import threading
from . import count_session
from datetime import timedelta


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

        # turn_time_intervals = session_instance.turn_time.filter(turn=session_instance.current_turn).first()
        # if session_instance.turn_phase == 'negotiation':
        #     turn_time = turn_time_intervals.negotiation_time
        # else:
        #     turn_time = turn_time_intervals.transaction_time
        # now = datetime.datetime.now(datetime.timezone.utc)
        # ends = turn_time_intervals.started + turn_time
        # time_left = ends - now