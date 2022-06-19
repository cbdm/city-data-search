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
            if not cached:
                # If it's a new city, create a new entry.
                cached = self._table(geonameid=geonameid, data=data.to_json())
            else:
                # If it's an old city, update the existing entry.
                cached.data = data.to_json()
            self._db.session.add(cached)
            self._db.session.commit()
        else:
            data = City.from_json(cached.data)
        # Adds the query that got this city.
        data.query = query
        return data
