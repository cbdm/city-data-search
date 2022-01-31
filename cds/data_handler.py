from city import City, search
from os import getenv
from redis import Redis
from utils import convert_from_citystate
from bcrypt import checkpw

class DataHandler(object):
    def __init__(self, redis_host, redis_port, redis_password):
        self._db = Redis(
            host=redis_host,
            port=redis_port, 
            password=redis_password
        )


    def get_city_by_geonameid(self, geonameid, *, force=False, query='N/A'):
        cached = self._db.get(geonameid)
        if force or not cached:
            data = City(geonameid)
            data.fetch_data()
            self._db.set(geonameid, data.to_json())
        else:
            data = City.from_json(cached)
        # Adds the query that got this city.
        data.query = query
        return data


    def flush_db(self, password):
        assert isinstance(password, bytes)
        assert checkpw(password, getenv('REDIS_DROP_DB_PASSWORD', '').encode('utf8'))
        self._db.flushall()
