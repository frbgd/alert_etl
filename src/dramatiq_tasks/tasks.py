import logging
from logging import handlers

import dramatiq
from dramatiq.brokers.redis import RedisBroker

from objects.QRadarConnector import QRadarConnector
from objects.TheHiveConnector import TheHiveConnector
from settings import config

MAX_BACKOFF = config.dramatiq_max_backoff
MAX_AGE = config.dramatiq_max_age

logger = logging.getLogger('dramatiq')
file_handler = handlers.RotatingFileHandler(config.log_path + '/dramatiq.log',
                                            'a', 1000000, 10)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s :: %(levelname)s :: %(filename)s.%(funcName)s %(message)s'
))
logger.addHandler(file_handler)

thehive_connector = TheHiveConnector(
    url=config.thehive_url,
    l1_api_key=config.thehive_l1_apikey,
    l2_api_key=config.thehive_l2_apikey,
    lpagetest_api_key=config.lpagetest_api_key,
    cert=config.thehive_check_cert,
    logger=logger
)
qradar_connector = QRadarConnector(
    api_version=config.qradar_api_version,
    api_token=config.qradar_api_token,
    server_ip=config.qradar_server_ip,
    verify_ssl=config.qradar_verify_ssl,
    logger=logger
)

redis_broker = RedisBroker(host=config.redis_host)
dramatiq.set_broker(redis_broker)


@dramatiq.actor(max_backoff=MAX_BACKOFF, max_age=MAX_AGE)
def create_alert(alert_data: dict, organisation: str):
    thehive_connector.create_alert(alert_data, organisation)


@dramatiq.actor(max_backoff=MAX_BACKOFF, max_age=MAX_AGE)
def edit_offense(**kwargs):
    qradar_connector.edit_offense(**kwargs)


@dramatiq.actor(max_backoff=MAX_BACKOFF, max_age=MAX_AGE)
def add_note_to_offense(**kwargs):
    qradar_connector.add_note(**kwargs)
