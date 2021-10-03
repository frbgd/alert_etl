from dependency_injector.wiring import inject, Provide

from etl import etl_schema
from etl.containers import Container
from etl.filters import filter_funcs
from etl.logger import get_logger
from objects.state import State
from settings import config

logger = get_logger()


@inject
def run(
        etl_state: State = Provide[Container.etl_state]
):
    """Запускает пайплайн фильтров для ETL из ELK"""

    logger.info('started')
    loader = etl_schema.loader_filter(
        filter_func=filter_funcs.bulk_create_alerts
    )
    crafter = etl_schema.filter_(
        target=loader,
        filter_func=filter_funcs.craft_elk_alerts
    )
    alert_exist_checker = etl_schema.filter_(
        target=crafter,
        filter_func=filter_funcs.check_alert_existing
    )
    uc_is_checker = etl_schema.filter_(
        target=alert_exist_checker,
        filter_func=filter_funcs.uc_is_check
    )
    etl_schema.producer_filter(
        target=uc_is_checker,
        state=etl_state,
        state_key=config.redis_ELK_etl_key,
        update_state_value_func=filter_funcs.get_last_elk_alert_time,
        filter_func=filter_funcs.get_last_elk_alerts
    )

    logger.info('finished')
