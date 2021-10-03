from typing import Optional

from requests import HTTPError
from thehive4py.api import TheHiveApi
from thehive4py.models import Alert, CustomFieldHelper


class TheHiveConnector:
    def __init__(self, **kwargs):
        self.url = kwargs.get('url')
        self.l1_api_key = kwargs.get('l1_api_key')
        self.l2_api_key = kwargs.get('l2_api_key')
        self.lpagetest_api_key = kwargs.get('lpagetest_api_key')
        self.cert = kwargs.get('cert', True)
        self.logger = kwargs.get('logger')

        self.apis = {
            'L1': TheHiveApi(self.url, self.l1_api_key, cert=self.cert),
            'L2': TheHiveApi(self.url, self.l2_api_key, cert=self.cert),
            'LPageTest': TheHiveApi(self.url, self.lpagetest_api_key, cert=self.cert),
        }

    def _get_api(self, organisation: str) -> TheHiveApi:
        api = self.apis.get(organisation)
        if not api:
            raise ValueError(f'invalid organisation {organisation}')
        return api

    def create_alert(self, alert_data: dict, organisation: str) -> Optional[dict]:
        alert_object = Alert(**alert_data)

        if 'customFields' in alert_data:
            alert_object.customFields = self.craft_custom_fields(
                alert_data['customFields'])

        api = self._get_api(organisation)

        response = api.create_alert(alert_object)

        try:
            response.raise_for_status()
        except HTTPError as e:
            if response.status_code == 400 and 'already exist in organisation' in response.text:
                self.logger.info('alert %s already exists', alert_object.sourceRef)
                return
            self.logger.error('create alert returned %s - %s', response.status_code, response.text)
            raise e

        self.logger.info('alert %s created', alert_object.sourceRef)
        return response.json()

    def craft_custom_fields(self, custom_fields_dict: dict) -> dict:
        """
            Create custom fields as objects
        """
        custom_fields = CustomFieldHelper()

        for key in custom_fields_dict:
            if 'date' in custom_fields_dict[key]:
                custom_fields.add_date(key,
                                       custom_fields_dict[key]['date'])
            elif 'boolean' in custom_fields_dict[key]:
                custom_fields.add_boolean(
                    key, custom_fields_dict[key]['boolean'])
            elif 'string' in custom_fields_dict[key]:
                custom_fields.add_string(key,
                                         custom_fields_dict[key]['string'])
            elif 'integer' in custom_fields_dict[key]:
                custom_fields.add_integer(key,
                                          custom_fields_dict[key]['integer'])
            elif 'float' in custom_fields_dict[key]:
                custom_fields.add_float(key,
                                        custom_fields_dict[key]['float'])
            else:
                continue

        return custom_fields.build()

    def find_alerts(self, query, organisation: str) -> list:
        api = self._get_api(organisation)

        response = api.find_alerts(query=query)

        try:
            response.raise_for_status()
        except HTTPError as e:
            self.logger.error('find alerts returned %s - %s', response.status_code, response.text)
            raise e

        return response.json()
