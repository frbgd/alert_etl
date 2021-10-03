import json

from redis import Redis

redis = Redis(host='localhost')


if __name__ == '__main__':

    key = 'ETL:sh_dm_qradar'
    value = 360000

    redis.set(key, json.dumps(value))
