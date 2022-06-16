from city import City, search
from os import getenv
from utils import convert_from_citystate

class DataHandler(object):
    def __init__(self, db, table):
        self._db = db
        self._table = table


    def get_city_by_geonameid(self, geonameid, *, force=False, query='N/A'):
        cached = self._table.query.get(geonameid)
        if force or not cached:
            data = City(geonameid)
            data.fetch_data()
            new_city = self._table(geonameid=geonameid, data=data.to_json())
            self._db.session.add(new_city)
            self._db.session.commit()
        else:
            data = City.from_json(cached.data)
        # Adds the query that got this city.
        data.query = query
        return data
