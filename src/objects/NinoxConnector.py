from typing import List, Optional

import backoff
from PyNinox import NinoxClient
from PyNinox.Exceptions import NinoxError
from requests import exceptions

from settings import config


class NinoxConnector:
    def __init__(self, **kwargs):
        self.team = kwargs.get('team')
        self.database = kwargs.get('database')

        self.api = NinoxClient(
            url=kwargs.get('url'),
            username=kwargs.get('username'),
            password=kwargs.get('password')
        )

    @backoff.on_exception(backoff.expo,
                          (exceptions.ConnectionError, NinoxError),
                          max_time=config.backoff_max_time)
    def auth(self):
        return self.api.auth()

    @backoff.on_exception(backoff.expo,
                          (exceptions.ConnectionError, NinoxError),
                          max_time=config.backoff_max_time)
    def find_by_string(
            self,
            table_name: str,
            filter_string: str
    ) -> List[dict]:
        """Осуществляет поиск в указанной таблице по переданной строке"""

        data = self.api.find_db_record(
            self.team,
            self.database,
            filter_string
        )

        return [row for row in data if row.get('_table') == table_name]

    def get_by_row_id(
            self,
            table_name: str,
            row_id: str
    ) -> Optional[dict]:
        """Осуществляет поиск записи по переданному id"""

        try:
            data = self.api.get_db_record(
                self.team,
                self.database,
                row_id
            )
        except KeyError:
            return None
        if data.get('_table') != table_name:
            return None
        if len(data) < 2:
            return None

        return data


ninox_connector: NinoxConnector = None


def get_ninox_connector() -> NinoxConnector:
    return ninox_connector
