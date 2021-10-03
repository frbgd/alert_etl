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
    """Запускает пайплайн фильтров для ETL из QRadar только для оффенсов SH-DM"""

    logger.info('started')

    follow_upper = etl_schema.loader_filter(
        filter_func=filter_funcs.bulk_follow_up_offenses
    )
    loader = etl_schema.filter_(
        target=follow_upper,
        filter_func=filter_funcs.bulk_create_alerts
    )
    crafter = etl_schema.filter_(
        target=loader,
        filter_func=filter_funcs.craft_qradar_sh_dm_alerts
    )
    closer = etl_schema.filter_(
        target=crafter,
        filter_func=filter_funcs.bulk_close_offenses
    )
    uc_is_checker = etl_schema.filter_(
        target=closer,
        filter_func=filter_funcs.uc_is_check
    )
    sh_dm_is_getter = etl_schema.filter_(
        target=uc_is_checker,
        filter_func=filter_funcs.get_is_from_sh_dm_qradar
    )
    log_source_filter = etl_schema.filter_(
        target=sh_dm_is_getter,
        filter_func=filter_funcs.sh_dm_qradar_log_source_filter
    )
    alert_exist_checker = etl_schema.filter_(
        target=log_source_filter,
        filter_func=filter_funcs.check_alert_existing
    )
    etl_schema.producer_filter(
        target=alert_exist_checker,
        state=etl_state,
        state_key=config.redis_sh_dm_qradar_etl_key,
        update_state_value_func=filter_funcs.get_last_qradar_offense_id,
        filter_func=filter_funcs.get_last_sh_dm_qradar_offenses
    )

    logger.info('finished')
