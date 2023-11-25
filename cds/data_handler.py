from city import City, search
from os import getenv
from utils import convert_from_citystate
from datetime import datetime, timedelta
from sqlalchemy.sql import select, desc


class DataHandler(object):
    UPDATE_RECENT_FREQUENCY = timedelta(days=1)

    def __init__(self, db, table):
        self._db = db
        self._table = table
        self._recent_cities = tuple()
        self._last_recent_check = datetime(1908, 3, 25)

    def get_city_by_geonameid(self, geonameid, *, force=False, query="N/A"):
        cached = self._table.query.get(geonameid)
        if force or not cached:
            data = City(geonameid)
            data.fetch_data()
            assert data._fetched  # make sure the data was fetched before commiting it.
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

    def get_recent_cities(self, n=5):
        if (
            datetime.utcnow() - self._last_recent_check
            >= DataHandler.UPDATE_RECENT_FREQUENCY
        ):
            self._recent_cities = sorted(
                [
                    City.from_json(c[0].data)
                    for c in self._db.session.execute(select(self._table))
                ],
                key=lambda x: x.timestamp,
                reverse=True,
            )[:n]
            self._last_recent_check = datetime.utcnow()
        return self._recent_cities
