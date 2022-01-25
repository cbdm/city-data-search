import requests
from geopy.geocoders import Nominatim
from datetime import datetime
from meteostat import Point, Daily

# Parameters for queries.
population_url = 'https://www.areavibes.com/{}/demographics'
livability_url = 'https://www.areavibes.com/{}/livability'
location_app = Nominatim(user_agent="query")
weather_start = datetime(2021, 1, 1)
weather_end = datetime(2021, 12, 31)
weather_format_str = '{:^5.1f}' + ('  |  {:^5.1f}' * 4)

def get_population(citystate):
    '''Find the population for the given city in areavibes.com'''
    r = requests.get(population_url.format(citystate))
    html = r.text
    pop_flag = '<td>Population</td>'
    html = html[html.find(pop_flag) + len(pop_flag) + 1:]
    pop_start = html.find('>') + 1
    pop_end = html.find('<')
    return html[pop_start:pop_end]


def get_livability(city):
    '''Find the livability metrics from areavibes.com for the given city.'''
    r = requests.get(livability_url.format(city))
    html = r.text
    
    # Parse the livability score.
    liv_flag = '<em>Livability</em>'
    html = html[html.find(liv_flag) + len(liv_flag) + 1:]
    liv_start = html.find('>') + 1
    liv_end = html.find('<')
    livability = html[liv_start:liv_end]

    # Parse the amenities score.
    amn_flag = '<em>Amenities</em>'
    html = html[html.find(amn_flag) + len(amn_flag) + 1:]
    amn_start = html.find('>') + 1
    amn_end = html.find('<')
    amenities = html[amn_start:amn_end]

    # Parse the cost of living score.
    col_flag = '<em>Cost of Living</em>'
    html = html[html.find(col_flag) + len(col_flag) + 1:]
    col_start = html.find('>') + 1
    col_end = html.find('<')
    col = html[col_start:col_end]

    # Parse the crime score.
    crm_flag = '<em>Crime</em>'
    html = html[html.find(crm_flag) + len(crm_flag) + 1:]
    crm_start = html.find('>') + 1
    crm_end = html.find('<')
    crime = html[crm_start:crm_end]

    # Parse the employment score.
    emp_flag = '<em>Employment</em>'
    html = html[html.find(emp_flag) + len(emp_flag) + 1:]
    emp_start = html.find('>') + 1
    emp_end = html.find('<')
    employment = html[emp_start:emp_end]
    
    # Parse the housing score.
    hou_flag = '<em>Housing</em>'
    html = html[html.find(hou_flag) + len(hou_flag) + 1:]
    hou_start = html.find('>') + 1
    hou_end = html.find('<')
    housing = html[hou_start:hou_end]
    
    # Parse the schools score.
    sch_flag = '<em>Schools</em>'
    html = html[html.find(sch_flag) + len(sch_flag) + 1:]
    sch_start = html.find('>') + 1
    sch_end = html.find('<')
    schools = html[sch_start:sch_end]
    
    # Parse the user ratings score.
    usr_flag = '<em>User Ratings</em>'
    html = html[html.find(usr_flag) + len(usr_flag) + 1:]
    usr_start = html.find('>') + 1
    usr_end = html.find('<')
    user_ratings = html[usr_start:usr_end]

    return livability, amenities, col, crime, employment, housing, schools, user_ratings


def get_weather(city):
    '''Get information about the 2021 daily temperature for the given city.'''
    geo_location = location_app.geocode(city).raw
    coordinates = Point(lat=float(geo_location['lat']),
                        lon=float(geo_location['lon']))
    data = Daily(coordinates, weather_start, weather_end)
    data = data.normalize()
    data = data.interpolate()
    data = data.fetch()
    lowest = data['tmin'].min()
    low = data['tmin'].median()
    avg = data['tavg'].median()
    high = data['tmax'].median()
    highest = data['tmax'].max()
    return weather_format_str.format(lowest, low, avg, high, highest)
