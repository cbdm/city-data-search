# app.py
import os
import os.path
import redis
from flask import Flask, request, render_template, flash, redirect, url_for
from data_fetchers import location_app, get_livability, get_population, get_weather, weather_start
from large_cities import find_close_large_cities, get_all_large_cities_within_radius
from utils import create_output_xml, validate_city_state, convert_city_name
from datetime import datetime
import xml.etree.ElementTree as ET
import xmltodict

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'abc')
db = redis.Redis(
    host=os.getenv('REDIS_ENDPOINT_URI', '127.0.0.1'),
    port=os.getenv('REDIS_PORT', '6379'), 
    password=os.getenv('REDIS_PASSWORD', None)
    )


def get_single_city_data(citystate, force=False):
    '''Main function that creates a response xml for a single citystate.'''
    # Check citystate has the correct format.
    validate_city_state(citystate)
   
    if citystate == 'get-headers':   # Check special case for returning headers.
        xml = create_output_xml(citystate,
                                population='Population',
                                weather=f'{datetime.now().year - 1} Weather (ºC)',
                                livability=('Overall Livability', 'Amenities', 'Cost of Living', 'Crime',
                                                'Employment', 'Housing', 'Schools', 'User Ratings'),
                                closest_large_cities='Closest Large Cities',
                                count_large_cities='# of Large Cities Nearby'
                                )
    else:
        # Check if we already have fetched data for this citystate.
        # TODO: add some freshness (e.g., update if after a month?) to this file.
        xml = db.get(citystate)  # If we have this data cached, load it.
        if force or not xml:
            # If we don't, fetch it.
            closest_large_cities, count_large_cities = find_close_large_cities(citystate)
            xml = create_output_xml(citystate=citystate,
                                    population=get_population(citystate),
                                    weather=get_weather(citystate),
                                    livability=get_livability(citystate),
                                    closest_large_cities=closest_large_cities,
                                    count_large_cities=count_large_cities
                                    )
            # Update redis with the data.
            db.set(citystate, xml)

    return xml


@app.route('/api/citystate/<citystate>/')
def single_city(citystate, force=False):
    '''API to get data for a single given city-state.'''
    return app.response_class(get_single_city_data(citystate, force), mimetype='application/xml')


@app.route('/api/force/citystate/<citystate>/')
def force_single_city(citystate):
    '''API to force fetching the data for the given city-state.'''
    return single_city(citystate, force=True)


@app.route('/api/multi/<citystatelist>/')
def multi_city(citystatelist, force=False):
    '''API to fetch data for all cities in the given city-state list.'''
    response = ET.Element('multi', citystatelist=citystatelist)
    for citystate in citystatelist.split('_'):
        new_data = get_single_city_data(citystate, force)
        response.append(ET.XML(new_data.decode("utf8")))
    return app.response_class(ET.tostring(response), mimetype='application/xml')


# Disabled because a large enough query was causing server errors.
# Only queries for single citystates are allowed to force an update now.
# @app.route('/api/force/multi/<citystatelist>/')
# def force_multi_city(citystatelist):
#     '''API to force fetching the data for the given city-state list.'''
#     return multi_city(citystatelist, force=True)


@app.route('/', methods=('GET', 'POST'))
def index():
    '''Homepage to allow the user to search for a city.'''
    if request.method == 'POST':
        city = request.form['city']
        if not city:
            flash('You must enter a city in the search box!')
        else:
            citystate = convert_city_name(city)
            # Only passes both citystate and city if they are different.
            # If they are the same, the url looks cleaner with only citystate.
            if citystate != city:
                return redirect(url_for('web', citystate=citystate,  cityname=city))
            else:
                return redirect(url_for('web', citystate=citystate))
    return render_template('index.html')


@app.route('/about/')
def about():
    '''Return the about page.'''
    return render_template('about.html')


@app.route('/api/info/')
def api_info():
    ''''Return the api-info page.'''
    return render_template('api.html')


@app.route('/web/<citystate>/')
def web(citystate):
    '''Page to serve the data in a easy to understand GUI.'''
    cityname = request.args.get('cityname', citystate)
    xml = get_single_city_data(citystate)
    data = xmltodict.parse(xml)['data']
    del data['@citystate']
    data['citystate'] = citystate
    data['weather'] = [x.strip() for x in data['weather'].split('|')]
    loc = location_app.geocode(citystate)
    coordinates = (loc.latitude, loc.longitude)
    return render_template('city.html', cityname=cityname, **data, weather_year=weather_start.year,
                    coordinates=coordinates, all_large_cities=get_all_large_cities_within_radius(coordinates))


if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)
