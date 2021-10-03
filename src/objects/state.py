import datetime
from datetime import timedelta
from typing import Any, Optional

from objects.RedisStorage import RedisStorage


class State:
    """
     Класс для хранения состояния при работе с данными, чтобы постоянно
    не перечитывать данные с начала.
    Здесь представлена реализация с сохранением состояния в файл.
    В целом ничего не мешает поменять это поведение на работу с БД или
    распределённым хранилищем.
    """

    def __init__(self, storage: RedisStorage, ttl: Optional[timedelta] = None):
        self.storage = storage
        self.ttl = ttl
        self.state = {}

    def set_state(self, key: str, value: Any) -> None:
        """Установить состояние для определённого ключа"""

        if self.ttl:
            self.state[key] = (datetime.datetime.now() + self.ttl, value)
        else:
            self.state[key] = value
        self.storage.save_value(key, value, self.ttl)

    def get_state(self, key: str) -> Any:
        """Получить состояние по определённому ключу"""

        value = self.state.get(key)
        if value and self.ttl:
            if value[0] > datetime.datetime.now():
                return value[1]
            else:
                del self.state[key]
                return None
        elif value:
            return value

        return self.storage.retrieve_value(key)


use_case_state: State = None
information_system_state: State = None


def get_uc_state() -> State:
    return use_case_state


def get_is_state() -> State:
    return information_system_state
