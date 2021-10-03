from typing import List, Optional, Callable

from dependency_injector.wiring import inject, Provide

from etl.containers import Container
from objects.NinoxConnector import NinoxConnector
from objects.etl_data import Alert, ETLData, TargetGroup, Status
from objects.state import State
from settings import config


def enrich_alerts_by_is(alerts: List[Alert], information_systems: dict):
    for alert in alerts:
        information_system = information_systems.get(alert.information_system, {})
        if not information_system:
            continue

        # FIXME 05.08.21 костыль для совместимости со старым кэшом, удалить через день
        if isinstance(information_system, list):
            information_system = information_system[0]

        information_system_status = information_system.get('Статус')
        if not information_system_status:
            continue

        if information_system_status == 'Prod':
            alert.information_system_status = Status.prod
        elif information_system_status == 'Pilot':
            alert.information_system_status = Status.pilot

        is_uc_mapping = information_system.get(config.ninox_IS_UC_table)
        if is_uc_mapping:
            is_uc = [x for x in is_uc_mapping if x.get('UC') == alert.use_case]
            if is_uc:
                is_uc = is_uc[0]
                is_uc_status = is_uc.get('Status')
                if is_uc_status and is_uc_status == 'Prod':
                    alert.use_case_status = Status.prod
                elif is_uc_status and is_uc_status == 'Pilot':
                    alert.use_case_status = Status.pilot
                else:
                    alert.use_case_status = Status.no_import
            else:
                alert.use_case_status = Status.no_import


def enrich_alerts_by_uc(alerts: List[Alert], use_cases: dict):
    for alert in alerts:
        use_case_info = use_cases.get(alert.use_case)
        if not use_case_info:
            continue
        alert.playbook_links = use_case_info.get('links', '')

        if alert.use_case_status != Status.empty:
            continue

        alert.incident_category = use_case_info.get('incident_category', {}).get('name', '')
        use_case_status = \
            use_case_info.get(config.scenario_source_status_map[alert.source], {}).get('status', {}).get('name', '')
        alert.priority = use_case_info.get('priority', {}).get('name', '')
        alert.use_case_title = use_case_info.get('name', '')

        if use_case_status == 'Готов':
            alert.use_case_status = Status.prod
        elif use_case_status == 'Тестируется':
            alert.use_case_status = Status.pilot


def filter_alerts(data: ETLData):
    alerts = data.relevant
    data.relevant = []

    for alert in alerts:
        if alert.information_system_status == Status.prod and alert.use_case_status == Status.prod:
            alert.target_group = TargetGroup.first_line
            data.relevant.append(alert)
        elif alert.information_system_status == Status.prod and alert.use_case_status == Status.pilot:
            alert.target_group = TargetGroup.second_line
            data.relevant.append(alert)
        elif alert.information_system_status == Status.pilot and alert.use_case_status == Status.prod:
            alert.target_group = TargetGroup.second_line
            data.relevant.append(alert)
        else:
            data.irrelevant.append(alert)


@inject
def get_cached_values(
        keys_dict: dict,
        cache_key_prefix: str,
        get_func: Callable,
        get_func_kwargs: Optional[dict] = None,
        cache: State = Provide[Container.cache_state],

) -> dict:
    for key in keys_dict:
        value = cache.get_state(f'{cache_key_prefix}{key}')
        if not value:
            value = get_func(key, **get_func_kwargs) if get_func_kwargs else get_func(key)
            cache.set_state(f'{cache_key_prefix}{key}', value)
        keys_dict[key] = value
    return keys_dict


@inject
def get_all_information_systems(
        alerts: List[Alert],
        ninox_connector: NinoxConnector,
        is_cache: State = Provide[Container.cache_state],
) -> dict:
    information_systems = dict.fromkeys([alert.information_system for alert in alerts if alert.information_system])
    for key in information_systems:
        information_system_info = is_cache.get_state(f'{config.redis_IS_key_prefix}{key}')
        if not information_system_info:
            information_system_info = ninox_connector.find_by_string(config.ninox_IS_table, key)
            if not information_system_info:
                continue
            information_system_info = information_system_info[0]

            is_uc_mapping = information_system_info.get(config.ninox_IS_UC_table)
            if is_uc_mapping:
                information_system_info[config.ninox_IS_UC_table] = \
                    [ninox_connector.get_by_row_id(config.ninox_IS_UC_table, row_id) for row_id in is_uc_mapping]
                information_system_info[config.ninox_IS_UC_table] = \
                    [x for x in information_system_info[config.ninox_IS_UC_table] if x]

            is_cache.set_state(f'{config.redis_IS_key_prefix}{key}', information_system_info)

        information_systems[key] = information_system_info

    return information_systems
