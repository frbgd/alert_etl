from typing import List

import backoff
from elasticsearch import Elasticsearch, exceptions

from settings import config


class ELKConnector:
    def __init__(self, url, user, password, search_size: int, cert=False):
        self.url = url
        self.auth = (user, password)
        self.cert = cert
        self.search_size = search_size

        self.es = Elasticsearch(self.url, http_auth=self.auth, verify_certs=self.cert, ca_certs=self.cert)

    @backoff.on_exception(backoff.expo,
                          exceptions.ConnectionError,
                          max_time=config.backoff_max_time)
    def search_docs(self, index: str, query: dict) -> List[dict]:
        result = self.es.search(
            index=index,
            body=query,
            size=self.search_size,
            sort='timestamp'
        )
        return result.get('hits', {}).get('hits', [])

    def get_gte_timestamp_query(self, timestamp: str):
        return {
            "query": {
                "range": {
                    "timestamp": {
                        "gt": timestamp
                    }
                }
            }
        }
