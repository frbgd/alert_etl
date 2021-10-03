from dependency_injector import containers, providers

from objects.RedisStorage import RedisStorage
from objects.state import State
from settings import config


class Container(containers.DeclarativeContainer):
    redis_storage = providers.Singleton(
        RedisStorage,
        config.redis_host
    )

    cache_state = providers.Singleton(
        State,
        redis_storage,
        config.redis_info_ttl
    )
    etl_state = providers.Singleton(
        State,
        redis_storage
    )
