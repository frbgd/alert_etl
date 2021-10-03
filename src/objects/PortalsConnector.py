from typing import Optional

import backoff
from requests import exceptions

from objects.jwt_auth_module.jwt_session import JWT_Session
from settings import config


class PortalsConnector:
    def __init__(self, **kwargs):
        self.p_url = kwargs.get('portals_url')
        self.username = kwargs.get('username')
        self.password = kwargs.get('password')
        self.obtain_tokens_url = kwargs.get('obtain_tokens_url')
        self.refresh_token_url = kwargs.get('refresh_token_url')
        self.portal_session = None

    @backoff.on_exception(backoff.expo,
                          exceptions.ConnectionError,
                          max_time=config.backoff_max_time)
    def auth(self):
        self.portal_session = JWT_Session(username=self.username,
                                          password=self.password,
                                          obtain_tokens_url=self.obtain_tokens_url,
                                          refresh_token_url=self.refresh_token_url,
                                          auth_field='Authorization',
                                          auth_prefix='Bearer ',
                                          content_type='application/json')

    @backoff.on_exception(backoff.expo,
                          exceptions.ConnectionError,
                          max_time=config.backoff_max_time)
    def get_uc_info(self, use_case_id: str) -> Optional[dict]:
        """
            Get info from UCP about use-case scenario

            :param use_case_id: use-case scenario identifier
            :return: use-case scenario information
        """
        response = self.portal_session.request_with_token(
            method='get', url=f'{self.p_url}/usecases/api/v0/usecases/{use_case_id}/')

        if response.status_code == 404:
            return None

        response.raise_for_status()

        return response.json()


portals_connector: PortalsConnector = None


def get_portals_connector() -> PortalsConnector:
    return portals_connector
