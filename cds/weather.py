from datetime import datetime
from meteostat import Point, Daily

def get_year_round_weather(coordinates, year):
    assert isinstance(coordinates, tuple)
    assert len(coordinates) == 2
    assert isinstance(coordinates[0], float)
    assert isinstance(coordinates[1], float)
    assert isinstance(year, int)
    
    # Define the date range we're analyzing.
    weather_start = datetime(year, 1, 1)
    weather_end = datetime(year, 12, 31)

    # Create a location point for the coordinates.
    location = Point(*coordinates)

    try:
        data = Daily(location, weather_start, weather_end)
        data = data.normalize()
        data = data.interpolate()
        data = data.fetch()
        data.dropna()
        lowest = data['tmin'].min()
        low = data['tmin'].median()
        avg = data['tavg'].median()
        high = data['tmax'].median()
        highest = data['tmax'].max()
    except KeyError:
        lowest = 'N/A'
        low = 'N/A'
        avg = 'N/A'
        high = 'N/A'
        highest = 'N/A'

    return lowest, low, avg, high, highest
