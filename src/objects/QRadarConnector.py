import json
from typing import Optional, List

import requests
from requests import HTTPError, Request

DEFAULT_AQL_CHECK_PERIOD = 60


class QRadarConnector:
    def __init__(self, **kwargs):
        self.headers = {
            'Accept': 'application/json',
            'Version': kwargs.get('api_version'),
            'SEC': kwargs.get('api_token')
        }
        self.server_ip = kwargs.get('server_ip')
        self.verify_ssl = kwargs.get('verify_ssl')
        self.aql_check_period = kwargs.get('aql_check_period', DEFAULT_AQL_CHECK_PERIOD)

        self.logger = kwargs.get('logger')

    @staticmethod
    def get_log_source_filter(log_source_names: List[str]) -> str:
        return ' or '.join([f'name="{name}"' for name in log_source_names if name])

    def __request(
            self,
            method: str,
            url: str,
            **kwargs
    ):
        headers = dict(self.headers)
        if 'headers' in kwargs and isinstance(kwargs['headers'], dict):
            headers.update(kwargs['headers'])
            kwargs.pop('headers')

        request = Request(
            method=method,
            url=url,
            headers=headers,
            **kwargs
        )
        prepped = request.prepare()

        with requests.Session() as session:
            session.verify = self.verify_ssl
            try:
                response = session.send(prepped)
                response.raise_for_status()
                try:
                    return response.json()
                except json.decoder.JSONDecodeError:
                    return response.text
            except HTTPError as e:
                if e.response.status_code == 404:
                    return None
                raise e

    def __get_rows(
            self,
            url: str,
            fields: Optional[str] = None,
            filter_: Optional[str] = None,
            sort: Optional[str] = None,
            range_: Optional[str] = None
    ) -> List[dict]:
        try:
            params = {}
            if fields:
                params['fields'] = fields
            if filter_:
                params['filter'] = filter_
            if sort:
                params['sort'] = sort
            headers = {}
            if range_:
                headers['Range'] = range_
            return self.__request(method='get', url=url, headers=headers, params=params)
        except Exception as e:
            self.logger.error('(url=\'%s\', fields=\'%s\', filter=\'%s\', sort=\'%s\', range=\'%s\') failed - %s',
                              url, fields, filter_, sort, range_, e)
            raise

    def __get_row(
            self,
            url: str,
            fields: Optional[str] = None
    ):
        try:
            params = None
            if fields:
                params = {'fields': fields}
            return self.__request(method='get', url=url, params=params)
        except Exception as e:
            self.logger.error('(url=\'%s\', fields=\'%s\') failed - %s',
                              url, fields, e)
            raise

    def get_offenses(self, **kwargs) -> List[dict]:
        return self.__get_rows(
            url=f'https://{self.server_ip}/api/siem/offenses',
            **kwargs
        )

    def get_source_addresses(self, **kwargs) -> List[dict]:
        return self.__get_rows(
            url=f'https://{self.server_ip}/api/siem/source_addresses',
            **kwargs
        )

    def get_local_destination_addresses(self, **kwargs) -> List[dict]:
        return self.__get_rows(
            url=f'https://{self.server_ip}/api/siem/local_destination_addresses',
            **kwargs
        )

    def get_log_sources(self, **kwargs) -> List[dict]:
        return self.__get_rows(
            url=f'https://{self.server_ip}/api/config/event_sources/log_source_management/log_sources',
            **kwargs
        )

    def get_offense_types(self, **kwargs) -> List[dict]:
        return self.__get_rows(
            url=f'https://{self.server_ip}/api/siem/offense_types',
            **kwargs
        )

    def get_domains(self, **kwargs) -> List[dict]:
        return self.__get_rows(
            url=f'https://{self.server_ip}/api/config/domain_management/domains',
            **kwargs
        )

    def __create_search(
            self,
            query: str,
    ) -> dict:
        url = f'https://{self.server_ip}/api/ariel/searches'
        params = {'query_expression': query}

        return self.__request(method='post', url=url, params=params)

    def __get_search(
            self,
            search_id: str,
    ) -> dict:
        url = f'https://{self.server_ip}/api/ariel/searches/{search_id}'

        return self.__request(method='get', url=url)

    def __get_search_results(
            self,
            search_id: str,
            range_start: Optional[str] = None,
            range_end: Optional[str] = None,
    ) -> dict:
        headers = {}
        if range_start and range_end:
            headers['Range'] = f'items={range_start}-{range_end}'

        url = f'https://{self.server_ip}/api/ariel/searches/{search_id}/results'

        return self.__request(method='get', url=url, headers=headers)

    def aql_search(
            self,
            query: str
    ) -> dict:
        search = {}
        try:
            search = self.__create_search(query)

            while search['status'] != 'COMPLETED':
                if (search['status'] == 'EXECUTE') | \
                        (search['status'] == 'SORTING') | \
                        (search['status'] == 'WAIT'):
                    search = self.__get_search(search['search_id'])
                    time.sleep(self.aql_check_period)

            return self.__get_search_results(search['search_id'])

        except Exception as e:
            self.logger.error('search_id=\'%s\' query=(%s) failed - %s', search.get('search_id'), query, e)
            raise

    def edit_offense(
            self,
            offense_id: str,
            assigned_to: Optional[str] = None,
            follow_up: Optional[str] = None,
            closing_reason_id: Optional[str] = None,
            status: Optional[str] = None,
    ) -> dict:
        try:
            url = f'https://{self.server_ip}/api/siem/offenses/{offense_id}'
            params = {}
            if assigned_to:
                params['assigned_to'] = assigned_to
            if follow_up:
                params['follow_up'] = follow_up
            if closing_reason_id:
                params['closing_reason_id'] = closing_reason_id
            if status:
                params['status'] = status
            return self.__request(method='post', url=url, params=params)
        except Exception as e:
            self.logger.error(
                '(offense_id="%s", assigned_to="%s", follow_up=%s, closing_reason_id=%s, status=%s) failed - %s',
                offense_id, assigned_to, follow_up, closing_reason_id, status, e
            )
            raise

    def add_note(
            self,
            offense_id: str,
            note_text: str = 'Closed by IRP integration',
            fields: Optional[str] = None,
    ) -> dict:
        try:
            url = f'https://{self.server_ip}/api/siem/offenses/{offense_id}/notes'
            params = {
                'note_text': note_text,
            }
            if fields:
                params['fields'] = fields
            return self.__request(method='post', url=url, params=params)
        except Exception as e:
            self.logger.error('(offense_id="%s", note_text="%s", fields="%s") failed - %s',
                              offense_id, note_text, fields, e)
            raise

    def get_offense_type(
            self,
            offense_type_id: int,
            fields: Optional[str] = None
    ):
        return self.__get_row(
            url=f'https://{self.server_ip}/api/siem/offense_types/{offense_type_id}',
            fields=fields
        )

    def get_domain(
            self,
            domain_id: int,
            fields: Optional[str] = None
    ):
        return self.__get_row(
            url=f'https://{self.server_ip}/api/config/domain_management/domains/{domain_id}',
            fields=fields
        )
