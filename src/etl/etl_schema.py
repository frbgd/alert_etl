from functools import wraps
from typing import Coroutine, Callable, Tuple

from objects.state import State


def coroutine(func):
    @wraps(func)
    def inner(*args, **kwargs):
        fn = func(*args, **kwargs)
        next(fn)
        return fn

    return inner


def producer_filter(target: Coroutine,
                    state: State,
                    state_key: str,
                    update_state_value_func: Callable,
                    filter_func: Callable):
    """Описывает алгоритм первого фильтра"""

    state_value = state.get_state(state_key)

    data = filter_func(state_value)

    if data:
        state_value = update_state_value_func(data)
        target.send(data)
        state.set_state(state_key, state_value)


@coroutine
def filter_(target: Coroutine,
            filter_func: Callable):
    """Описывает алгоритм фильтров merger и transformer"""

    while input_data := (yield):
        if input_data:
            data = filter_func(input_data)
            target.send(data)


@coroutine
def loader_filter(filter_func: Callable):
    """Описывает алгоритм фильтра loader"""

    while input_data := (yield):
        if input_data:
            filter_func(input_data)