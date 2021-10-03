from datetime import timedelta

from pydantic import BaseSettings, Field


class Config(BaseSettings):
    log_path: str = Field(env='LOG_PATH', default='/var/log/alert_etl')

    backoff_max_time: int = Field(env='BACKOFF_MAX_TIME', default=1800000)

    etl_sleep_time: int = Field(env='ETL_SLEEP_TIME', default=60)

    priority_to_severity_map = Field(default={
        'Критический': 3,
        'Высокий': 3,
        'Средний': 2,
        'Низкий': 1
    })
    scenario_source_status_map = Field(default={
        'ELK': 'tip',
        'QRadar': 'qradar'
    })

    redis_host: str = Field(env='REDIS_HOST', default='redis')
    redis_info_ttl: timedelta = Field(default=timedelta(hours=3))
    redis_offense_type_key_prefix: str = Field(env='REDIS_DOMAIN_KEY_PREFIX', default='qradar_offense_type:')
    redis_domain_key_prefix: str = Field(env='REDIS_DOMAIN_KEY_PREFIX', default='qradar_domain:')
    redis_use_case_key_prefix: str = Field(env='REDIS_USE_CASE_KEY_PREFIX', default='UC:')
    redis_IS_key_prefix: str = Field(env='REDIS_IS_KEY_PREFIX', default='IS:')
    redis_ELK_etl_key: str = Field(env='REDIS_ELK_ETL_KEY', default='ETL:elk')
    redis_qradar_etl_key: str = Field(env='REDIS_QRADAR_ETL_KEY', default='ETL:qradar')
    redis_sh_dm_qradar_etl_key: str = Field(env='REDIS_SH_DM_QRADAR_ETL_KEY', default='ETL:sh_dm_qradar')
    redis_sh_vcm_001_qradar_etl_key: str = Field(env='REDIS_SH_VCM_001_QRADAR_ETL_KEY', default='ETL:sh_vcm_001_qradar')

    thehive_url: str = Field(env='THEHIVE_URL')
    thehive_l1_apikey: str = Field(env='THEHIVE_L1_APIKEY')
    thehive_l2_apikey: str = Field(env='THEHIVE_L2_APIKEY')
    lpagetest_api_key: str = Field(env='THEHIVE_LPAGETEST_APIKEY')
    thehive_check_cert: bool = Field(env='THEHIVE_CHECK_CERT', default=False)

    elk_url: str = Field(env='ELK_URL')
    elk_user: str = Field(env='ELK_USER')
    elk_pass: str = Field(env='ELK_PASS')
    elk_index: str = Field(env='ELK_INDEX', default='.alerts')
    elk_search_size: str = Field(env='ELK_SEARCH_SIZE', default=50)

    portals_url: str = Field(env='P_URL')
    portals_obtain_token_url: str = Field(env='P_OBTAIN_TOKEN_URL')
    portals_refresh_token_url: str = Field(env='P_REFRESH_TOKEN_URL')
    portals_user: str = Field(env='P_USER')
    portals_pass: str = Field(env='P_PASS')

    dramatiq_max_backoff: int = Field(env='DEAMATIQ_MAX_BACKOFF', default=1800000)
    dramatiq_max_age: int = Field(env='DRAMATIQ_MAX_AGE', default=86400000)

    ninox_url: str = Field(env='NINOX_URL')
    ninox_username: str = Field(env='NINOX_USERNAME')
    ninox_password: str = Field(env='NINOX_PASSWORD')
    ninox_team: str = Field(env='NINOX_TEAM', default='Test')
    ninox_database: str = Field(env='NINOX_DATABASE')
    ninox_IS_table: str = Field(env='NINOX_IS_TABLE')
    ninox_IS_UC_table: str = Field(env='NINOX_IS_UC_table')

    qradar_api_version: str = Field(env='QRADAR_API_VERSION', default='12.1')
    qradar_api_token: str = Field(env='QRADAR_API_TOKEN')
    qradar_server_ip: str = Field(env='QRADAR_SERVER_IP')
    qradar_verify_ssl: bool = Field(env='QRADAR_VERIFY_SSL')
    qradar_irp_integration_closing_reason: str = Field(default='54')
    qradar_closed_offense_status: str = Field(default='CLOSED')
    qradar_search_sort: str = Field(env='QRADAR_SEARCH_SORT', default='+id')
    qradar_search_range: str = Field(env='QRADAR_SEARCH_RANGE', default='items=0-49')
    qradar_sh_vcm_001_search_range: str = Field(env='QRADAR_SH_VCM_001_SEARCH_RANGE', default='items=0-4')
    qradar_log_source_fields: str = Field(env='QRADAR_LOG_SOURCE_FIELDS', default='name,last_event_time')
    qradar_inactive_closing_reason: str = Field(env='QRADAR_INACTIVE_CLOSE_REASON', default='Inactive')
    qradar_offense_filter: str = Field(
        env='QRADAR_OFFENSE_FILTER',
        default='id>{id} and status=OPEN and follow_up=false and not '
                '(offense_type=92 or offense_type=228 or offense_type=176)'
    )
    qradar_sh_dm_offense_filter: str = Field(
        env='QRADAR_SH_DM_OFFENSE_FILTER',
        default='id>{id} and status=OPEN and follow_up=false and (offense_type=92 or offense_type=228)'
    )
    qradar_sh_vcm_001_offense_filter: str = Field(
        env='QRADAR_SN_VCM_001_OFFENSE_FILTER',
        default='id>{id} and status=OPEN and follow_up=false and offense_type=176'
    )
    qradar_offense_fields: str = Field(
        env='QRADAR_OFFENSE_FIELDS',
        default='description,start_time,last_updated_time,id,offense_type,offense_source,source_address_ids,'
                'local_destination_address_ids,log_sources'
    )
    qradar_sh_dm_offense_fields: str = Field(
        env='QRADAR_SH_DM_OFFENSE_FIELDS',
        default='description,start_time,last_updated_time,id,offense_type,offense_source'
    )
    qradar_sh_vcm_001_offense_fields: str = Field(
        env='QRADAR_SH_VCM_001_OFFENSE_FIELDS',
        default='description,start_time,last_updated_time,id,offense_type,offense_source'
    )
    qradar_offense_type_fields: str = Field(
        env='QRADAR_OFFENSE_TYPE_FIELDS',
        default='id,name'
    )
    qradar_domain_fields: str = Field(
            env='QRADAR_DOMAIN_FIELDS',
        default='id,name'
    )
    qradar_offense_type_name_regex: str = Field(
        env='QRADAR_OFFENSE_TYPE_NAME_REGEX',
        default=r'^([A-Z]{2,3}-[A-Z]{1,3}-\d{3})'
    )
    qradar_sh_dm_domain_aql_query: str = Field(
        env='QRADAR_SH_DM_DOMAIN_AQL_QUERY',
        default='SELECT "SH-DM-003-Domain" as domain_name '
                'FROM events '
                'WHERE INOFFENSE({id}) LIMIT 1 '
                'START {start_time} STOP {stop_time};'
    )
    qradar_sh_vcm_001_aql_query: str = Field(
        env='QRADAR_SH_VCM_001_AQL_QUERY',
        default='SELECT "dev_address","group_name","log_source_name", QIDNAME(qid) '
                'FROM events '
                "WHERE log_source_name IN ('{names}') "
                'START {start_time} STOP {stop_time};'
    )
    qradar_sh_dm_cooling_time: int = Field(env='QRADAR_SH_DM_COOLING_TIME', default=15 * 65)  # 15 minutes
    qradar_sh_dm_closing_reason: str = Field(env='QRADAR_SH_DM_CLOSING_REASON', default='Host started emitting events')
    qradar_sh_dm_offense_type_map: dict = Field(default={
        92: 'SH-DM-003',
        228: 'SH-DM-010'
    })
    qradar_default_domain: str = Field(env='QRADAR_DEFAULT_DOMAIN', default='UNKNOWN DOMAIN')

    link_smp_is: str = Field(env='LINK_SMP_IS')
    link_ucp_uc: str = Field(env='LINK_UCP_UC')
    link_qradar_from_vdi = Field(env='LINK_QRADAR_FROM_VDI')
    link_qradar_from_kspd: str = Field(env='LINK_QRADAR_FROM_KSPD')


config = Config(_env_file=None)
