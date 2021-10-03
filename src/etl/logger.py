import logging
import sys
from logging import handlers

from settings import config

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(filename)s.%(funcName)s() :: %(message)s')

file_handler = handlers.RotatingFileHandler(config.log_path + '/etl.log',
                                            'a', 1000000, 10)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

out_handler = logging.StreamHandler(sys.stdout)
out_handler.setLevel(logging.DEBUG)
out_handler.setFormatter(formatter)

logger.addHandler(out_handler)


def get_logger():
    return logger
