# app.py
import os
import os.path
import redis
from flask import Flask, request, jsonify
from data_fetchers import get_livability, get_population, get_weather
from large_cities import find_close_large_cities
from utils import create_output_xml, validate_city_state
from datetime import datetime
import xml.etree.ElementTree as ET

app = Flask(__name__)
app.debug = True
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


@app.route('/')
def index():
    '''Dummy main page just to show it's online.'''
    return "<h1>App is running :)</h1>"


if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)
