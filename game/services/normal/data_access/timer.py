from game.services.normal.data_access import count_session
import asyncio
import threading


def timer(session):
    """
    Запускает таймер и сохраняет модель хода, если таймер истёк. Время вводится в минутах
    """
    if session.status == 'started' and session.turn_phase == 'negotiation':
        negotiation_time = session.turn_time.get(turn=session.current_turn).negotiation_time
        time_in_seconds = negotiation_time * 5
        timer_obj = threading.Timer(time_in_seconds, count_session.change_phase, args=[session, 'transaction'])
        timer_obj.name = f'timer_{session.id}_{session.current_turn}_{session.turn_phase}'
        return {
            'timer': timer_obj,
            'thread_id': timer_obj.ident
        }
    elif session.status == 'started' and session.turn_phase == 'transaction':
        transaction_time = session.turn_time.get(turn=session.current_turn).transaction_time
        time_in_seconds = transaction_time * 5
        print(f'Количество потоков: {len(threading.enumerate())}, \n Список потоков: {threading.enumerate()}')
        timer_obj = threading.Timer(time_in_seconds, count_session.count_session, args=[session])
        timer_obj.name = f'timer_{session.id}_{session.current_turn}_{session.turn_phase}'
        return {
            'timer': timer_obj,
            'thread_id': timer_obj.ident
        }
