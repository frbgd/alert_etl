import json
from datetime import timedelta
from typing import Any, Optional

import backoff
from redis import Redis, exceptions

from settings import config


class RedisStorage:
    def __init__(self, host: str):
        self.redis_adapter = Redis(host=host)

    @backoff.on_exception(backoff.expo,
                          exceptions.ConnectionError,
                          max_time=config.backoff_max_time)
    def save_value(self, key: str, value: Any, ttl: Optional[timedelta] = None):
        if ttl:
            self.redis_adapter.setex(key, ttl, json.dumps(value))
        else:
            self.redis_adapter.set(key, json.dumps(value))

    @backoff.on_exception(backoff.expo,
                          exceptions.ConnectionError,
                          max_time=config.backoff_max_time)
    def retrieve_value(self, key: str) -> Any:
        raw_data = self.redis_adapter.get(key)
        if raw_data is None:
            return None
        return json.loads(raw_data)


redis_storage: RedisStorage = None


def get_redis_storage() -> RedisStorage:
    return redis_storage
