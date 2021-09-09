import threading
from . import count_session
from threading import Timer, enumerate
from pytz import UTC
from game.services.normal.data_access.count_session import change_phase, count_session
from datetime import datetime, timedelta


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


class SessionTimer(Timer):
    def __init__(self, session_id, *args, **kwargs):
        Timer.__init__(self, *args, **kwargs)
        self.session_id = session_id


def find_session_timer(session_id):
    """
    Возвращает объект таймера для сессии
    """
    timers = [t for t in enumerate() if isinstance(t, SessionTimer)]
    timers.sort(key=lambda x: x.session_id)
    for timer in timers:
        if timer.session_id == session_id:
            return timer


def initialize_thread_timer(session_instance):
    turn_time_instance = session_instance.turn_time.first()
    duration = turn_time_instance.negotiation_time * 60
    SessionTimer(session_instance.id, duration, change_phase, args=[session_instance]).start()
    turn_time_instance.save()

def next_turn_thread_timer(session_instance):
    """
    Запускает новый тред для таймера
    """
    current_turn_obj = session_instance.turn_time.get(turn=session_instance.current_turn)
    if session_instance.current_turn <= session_instance.turn_count:
        duration = current_turn_obj.time * 60
        SessionTimer(session_instance.id, duration, count_session, args=[session_instance]).start()
    current_turn_obj.save()
str.lo

def add_10_minutes(session_instance):
    """
    Добавляет 10 минут на текущий таймер сессии
    """
    turn_obj = session_instance.turn_time.get(turn=session_instance.current_turn)
    timer = find_session_timer(session_instance.id)
    if timer:
        timer.cancel()
    turn_time = turn_obj.time
    timer_started = turn_obj.timer_started
    new_finish = timer_started + timedelta(minutes=10 + turn_time)
    current_time = datetime.now(tz=UTC)
    duration = new_finish - current_time
    duration_in_seconds = int(duration.total_seconds())
    turn_obj.time += 10
    SessionTimer(session_instance.id, duration_in_seconds, count_session, args=[session_instance]).start()
    turn_obj.save(update_fields=['time'])
