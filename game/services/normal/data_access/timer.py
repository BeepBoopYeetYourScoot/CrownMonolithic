from . import count_session
from threading import Timer, enumerate
from pytz import UTC
from game.services.normal.data_access.count_session import count_session
from datetime import datetime, timedelta


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
    SessionTimer(session_instance.id, duration, count_session, args=[session_instance]).start()
    turn_time_instance.save()


def next_turn_thread_timer(session_instance):
    """
    Запускает новый тред для таймера
    """
    current_turn_obj = session_instance.turn_time.get(turn=session_instance.current_turn)
    if session_instance.current_turn <= session_instance.turn_count:
        if session_instance.turn_phase == 'negotiation':
            duration = current_turn_obj.negotiation_time * 60
        elif session_instance.turn_phase == 'transaction':
            duration = current_turn_obj.transaction_time * 60
        SessionTimer(session_instance.id, duration, count_session, args=[session_instance]).start()
    current_turn_obj.save()


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
