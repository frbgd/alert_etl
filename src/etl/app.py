import os
import sys

p = os.path.abspath('.')
sys.path.insert(1, p)

import argparse
import time

from dependency_injector.wiring import inject

from etl.containers import Container
from etl.logger import get_logger
from etl.filters import utils
from etl.workers import etl_elk, etl_sh_dm_qradar, etl_sh_vcm_001_qradar, etl_qradar
from settings import config

logger = get_logger()


@inject
def main(args: argparse.Namespace):
    etl_func = None
    if args.elk:
        etl_func = etl_elk.run
    elif args.sh_dm_qradar:
        etl_func = etl_sh_dm_qradar.run
    elif args.sh_vcm_001_qradar:
        etl_func = etl_sh_vcm_001_qradar.run
    elif args.qradar:
        etl_func = etl_qradar.run
    else:
        logger.error('wrong argument')
        quit()

    logger.info('etl started')
    while True:
        etl_func()
        time.sleep(config.etl_sleep_time)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--elk", help="start alert ETL from ELK")
    parser.add_argument("--sh_dm_qradar", help="start SH-DM alert ETL from QRadar")
    parser.add_argument("--sh_vcm_001_qradar", help="start SH-VCM-001 alert ETL from QRadar")
    parser.add_argument("--qradar", help="start alert ETL from QRadar")
    args = parser.parse_args()

    container = Container()
    container.init_resources()
    container.wire(
        modules=[
            sys.modules[__name__],
            utils,
            etl_elk,
            etl_sh_dm_qradar,
            etl_sh_vcm_001_qradar,
            etl_qradar
        ]
    )

    main(args)
