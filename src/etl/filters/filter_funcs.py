import time

from thehive4py.query import Or, Eq
from typing import Optional

from dramatiq_tasks import tasks
from etl.filters import utils, crafter
from etl.logger import get_logger
from objects.ELKConnector import ELKConnector
from objects.NinoxConnector import NinoxConnector
from objects.PortalsConnector import PortalsConnector
from objects.QRadarConnector import QRadarConnector
from objects.TheHiveConnector import TheHiveConnector
from objects.etl_data import ETLData, TargetGroup, Alert
from settings import config

MILLISECONDS_IN_SECONDS = 1000
TWELVE_HOURS = 43200000

elk_connector = ELKConnector(
    url=config.elk_url,
    user=config.elk_user,
    password=config.elk_pass,
    search_size=config.elk_search_size
)

thehive_connector = TheHiveConnector(
    url=config.thehive_url,
    l1_api_key=config.thehive_l1_apikey,
    l2_api_key=config.thehive_l2_apikey,
    lpagetest_api_key=config.lpagetest_api_key,
    cert=config.thehive_check_cert,
    logger=get_logger()
)

qradar_connector = QRadarConnector(
    api_version=config.qradar_api_version,
    api_token=config.qradar_api_token,
    server_ip=config.qradar_server_ip,
    verify_ssl=config.qradar_verify_ssl,
    logger=get_logger()
)

portals_connector = PortalsConnector(
    portals_url=config.portals_url,
    username=config.portals_user,
    password=config.portals_pass,
    obtain_tokens_url=config.portals_obtain_token_url,
    refresh_token_url=config.portals_refresh_token_url
)
portals_connector.auth()

ninox_connector = NinoxConnector(
    url=config.ninox_url,
    username=config.ninox_username,
    password=config.ninox_password,
    team=config.ninox_team,
    database=config.ninox_database
)
ninox_connector.auth()


# TODO Можно перенести get'еры прямо в логику producer filter, чтобы передавать в producer filter сразу методы
# TODO elk_connector.search_docs и utils.craft_etl_data_from_elk (и для радара соответственно)
def get_last_elk_alerts(last_time: Optional[str] = None) -> Optional[ETLData]:
    elk_data = elk_connector.search_docs(
        index=config.elk_index,
        query=elk_connector.get_gte_timestamp_query(last_time)
    )
    if not elk_data:
        return None

    data = ETLData()
    data.relevant = [
        Alert(
            source='ELK',
            use_case=alert.get('_source', {}).get('case.id', ''),
            information_system=alert.get('_source', {}).get('case.is.id', 'null'),
            raw_data=alert,
            source_ref=alert['_id']
        ) for alert in elk_data
    ]
    return data


def get_last_qradar_offenses(last_id: Optional[int] = None) -> Optional[ETLData]:
    qradar_data = qradar_connector.get_offenses(
        filter_=config.qradar_offense_filter.replace('{id}', str(last_id or 0)),
        sort=config.qradar_search_sort,
        fields=config.qradar_offense_fields,
        range_=config.qradar_search_range
    )
    if not qradar_data:
        return None

    data = ETLData()
    data.relevant = [
        Alert(
            source='QRadar',
            raw_data=offense,
            source_ref=str(offense['id'])
        ) for offense in qradar_data
    ]
    return data


def get_last_elk_alert_time(data: ETLData) -> str:
    return data.relevant[-1].raw_data.get('_source', {}).get('timestamp')


def get_last_sh_dm_qradar_offenses(last_id: Optional[int] = None) -> Optional[ETLData]:
    sh_dm_data = qradar_connector.get_offenses(
        filter_=config.qradar_sh_dm_offense_filter.replace('{id}', str(last_id or 0)),
        sort=config.qradar_search_sort,
        fields=config.qradar_sh_dm_offense_fields,
        range_=config.qradar_search_range
    )
    if not sh_dm_data:
        return None

    data = ETLData()
    data.relevant = [
        Alert(
            source='QRadar',
            use_case=config.qradar_sh_dm_offense_type_map.get(offense['offense_type']),
            raw_data=offense,
            source_ref=str(offense['id'])
        ) for offense in sh_dm_data
    ]
    return data


def get_last_sh_vcm_001_qradar_offenses(last_id: Optional[int] = None) -> Optional[ETLData]:
    sh_vcm_data = qradar_connector.get_offenses(
        filter_=config.qradar_sh_vcm_001_offense_filter.replace('{id}', str(last_id or 0)),
        sort=config.qradar_search_sort,
        fields=config.qradar_sh_vcm_001_offense_fields,
        range_=config.qradar_sh_vcm_001_search_range
    )
    if not sh_vcm_data:
        return None

    data = ETLData()
    data.relevant = [
        Alert(
            source='QRadar',
            use_case='SH-VCM-001',
            information_system='INTERNAL',
            raw_data=offense,
            source_ref=str(offense['id'])
        ) for offense in sh_vcm_data
    ]
    return data


def get_last_qradar_offense_id(data: ETLData) -> int:
    last_relevant_offense_id = 0
    last_irrelevant_offense_id = 0
    if data.relevant:
        last_relevant_offense_id = data.relevant[-1].raw_data.get('id')
    if data.irrelevant:
        last_irrelevant_offense_id = data.irrelevant[-1].raw_data.get('id')
    return last_relevant_offense_id \
        if last_relevant_offense_id > last_irrelevant_offense_id \
        else last_irrelevant_offense_id


def sh_vcm_001_qradar_filter(data: ETLData) -> ETLData:
    alerts = data.relevant
    data.relevant = []
    for offense in alerts:
        offense_source = offense.raw_data.get('offense_source', '')
        if not offense_source or offense_source.startswith('Device '):
            data.irrelevant.append(offense)
        else:
            data.relevant.append(offense)

    return data


def sh_dm_qradar_log_source_filter(data: ETLData) -> ETLData:
    current_time = int(time.time() * MILLISECONDS_IN_SECONDS)
    log_sources_dict = dict.fromkeys([offense.raw_data.get('offense_source') for offense in data.relevant])
    if log_sources_dict:
        log_sources = qradar_connector.get_log_sources(
            filter_=QRadarConnector.get_log_source_filter([key for key in log_sources_dict]),
            fields=config.qradar_log_source_fields,
            range_=config.qradar_search_range
        )
        for log_source in log_sources:
            log_sources_dict[log_source.get('name')] = log_source

    offenses = data.relevant
    data.relevant = []
    for offense in offenses:
        last_event_time = \
            log_sources_dict.get(offense.raw_data.get('offense_source')).get('last_event_time', MILLISECONDS_IN_SECONDS)
        if current_time - last_event_time < config.qradar_sh_dm_cooling_time * MILLISECONDS_IN_SECONDS:
            offense.closing_reason = config.qradar_sh_dm_closing_reason
            data.irrelevant.append(offense)
        else:
            data.relevant.append(offense)

    return data


def get_uc_from_qradar(data: ETLData) -> ETLData:
    offense_types = utils.get_cached_values(
        keys_dict=dict.fromkeys([offense.raw_data['offense_type'] for offense in data.relevant]),
        cache_key_prefix=config.redis_offense_type_key_prefix,
        get_func=qradar_connector.get_offense_type,
        get_func_kwargs={
            'fields': config.qradar_offense_type_fields
        }
    )

    for alert in data.relevant:
        offense_type = offense_types.get(alert.raw_data.get('offense_type'))
        if not offense_type:
            continue

        res = re.findall(config.qradar_offense_type_name_regex, offense_type.get('offense_type'))
        if not res:
            continue
        alert.use_case = res[0]

    return data


def get_is_from_qradar(data: ETLData) -> ETLData:
    domains = utils.get_cached_values(
        keys_dict=dict.fromkeys([offense.raw_data['domain_id'] for offense in data.relevant]),
        cache_key_prefix=config.redis_domain_key_prefix,
        get_func=qradar_connector.get_domain,
        get_func_kwargs={
            'fields': config.qradar_domain_fields
        }
    )

    for alert in data.relevant:
        domain = domains.get(alert.raw_data.get('domain_id'))
        if not domain:
            continue
        alert.information_system = domain['name']

    return data


def get_is_from_sh_dm_qradar(data: ETLData) -> ETLData:
    # TODO parallel this:
    for offense in data.relevant:
        search_result = qradar_connector.aql_search(
            query=config.qradar_sh_dm_domain_aql_query
                .replace('{id}', str(offense.raw_data['id']))
                .replace('{start_time}', str(offense.raw_data['start_time'] - 1))
                .replace('{stop_time}', str(offense.raw_data['start_time'] + 1))
        )
        if 'events' in search_result and len(search_result['events']) != 0:
            offense.information_system = search_result['events'][0].get('domain_name', config.qradar_default_domain)
        else:
            offense.information_system = config.qradar_default_domain
    return data


def get_log_source_ip_from_qradar(data: ETLData) -> ETLData:
    if data.relevant:
        log_source_names = [offense.raw_data['offense_source'].replace('::', '@') for offense in data.relevant]
        start_time = min([offense.raw_data['start_time'] for offense in data.relevant]) - TWELVE_HOURS
        stop_time = max([offense.raw_data['start_time'] for offense in data.relevant])

        search_result = qradar_connector.aql_search(
            query=config.qradar_sh_vcm_001_aql_query
                .replace('{start_time}', str(start_time))
                .replace('{stop_time}', str(stop_time))
                .replace('{names}', "', '".join(log_source_names))
        )
        result = {}
        # TODO Not tested!!!
        if 'events' in search_result and len(search_result['events']) != 0:
            for item in search_result['events']:
                result[item['log_source_name']] = item['dev_address']
        log_source_ips = result

        for offense in data.relevant:
            offense.raw_data['log_source_ip'] = \
                log_source_ips.get(offense.raw_data['offense_source'].replace('::', '@'), '')

    return data


def base_enrich_from_qradar(data: ETLData) -> ETLData:
    source_addresses = dict.fromkeys(
        set().union(*[offense.raw_data['source_address_ids'] for offense in data.relevant])
    )
    response = qradar_connector.get_source_addresses(
        fields='id,source_ip',
        filter='id in (%s)'.format(','.join(source_addresses.keys()))
    )
    for address in response:
        source_addresses[address['id']] = address['source_ip']

    local_destination_addresses = dict.fromkeys(
        set().union(*[offense.raw_data['local_destination_address_ids'] for offense in data.relevant])
    )
    response = qradar_connector.get_local_destination_addresses(
        fields='id,local_destination_ip',
        filter='id in (%s)'.format(','.join(local_destination_addresses.keys()))
    )
    for address in response:
        local_destination_addresses[address['id']] = address['local_destination_ip']

    for offense in data.relevant:
        offense.source_ips = [source_addresses[id_] for id_ in offense.raw_data['source_address_ids']]
    for offense in data.relevant:
        offense.destination_ips = \
            [local_destination_addresses[id_] for id_ in offense.raw_data['local_destination_address_ids']]

    return data


def uc_is_check(data: ETLData) -> ETLData:
    information_systems = utils.get_all_information_systems(
        alerts=data.relevant,
        ninox_connector=ninox_connector
    )
    use_cases = utils.get_cached_values(
        keys_dict=dict.fromkeys([alert.use_case for alert in data.relevant if alert.use_case]),
        cache_key_prefix=config.redis_use_case_key_prefix,
        get_func=portals_connector.get_uc_info
    )

    utils.enrich_alerts_by_is(data.relevant, information_systems)
    utils.enrich_alerts_by_uc(data.relevant, use_cases)

    utils.filter_alerts(data)

    return data


def check_alert_existing(data: ETLData) -> ETLData:
    """Проверяет алерты на наличие в TheHive"""
    if not data.relevant:
        return data

    alerts = data.relevant
    data.relevant = []

    existing_alerts = thehive_connector.find_alerts(
        query=Or(
            *[Eq('sourceRef', alert.source_ref) for alert in alerts]
        ),
        organisation=TargetGroup.first_line.value
    )
    existing_alerts += thehive_connector.find_alerts(
        query=Or(
            *[Eq('sourceRef', alert.source_ref) for alert in alerts]
        ),
        organisation=TargetGroup.second_line.value
    )

    existing_alerts_source_refs = {alert.get('sourceRef') for alert in existing_alerts}
    for alert in alerts:
        if alert.source_ref in existing_alerts_source_refs:
            data.imported.append(alert)
        else:
            data.relevant.append(alert)

    return data


def craft_elk_alerts(data: ETLData) -> ETLData:
    for alert in data.relevant:
        crafter.craft_elk_alert(alert)

    return data


def craft_qradar_alerts(data: ETLData) -> ETLData:
    for alert in data.relevant:
        crafter.craft_qradar_alert(alert)

    return data


def craft_qradar_sh_dm_alerts(data: ETLData) -> ETLData:
    for offense in data.relevant:
        crafter.craft_qradar_sh_dm_alert(offense)

    return data


def craft_qradar_sh_vcm_001_alerts(data: ETLData) -> ETLData:
    for offense in data.relevant:
        crafter.craft_qradar_sh_vcm_001_alert(offense)

    return data


def bulk_create_alerts(data: ETLData) -> ETLData:
    alerts = data.relevant
    data.relevant = []
    for alert in alerts:
        tasks.create_alert.send(
            alert_data=alert.data,
            organisation=alert.target_group.value
        )
        data.imported.append(alert)

    return data


def bulk_follow_up_offenses(data: ETLData) -> ETLData:
    for alert in data.imported:
        tasks.edit_offense.send(
            offense_id=alert.source_ref,
            follow_up='true'
        )

    return data


def bulk_close_offenses(data: ETLData) -> ETLData:
    for alert in data.irrelevant:
        tasks.edit_offense.send(
            offense_id=alert.source_ref,
            closing_reason_id=config.qradar_irp_integration_closing_reason,
            status=config.qradar_closed_offense_status
        )
        tasks.add_note_to_offense.send(
            offense_id=alert.source_ref,
            note_text=alert.closing_reason
        )

    return data
