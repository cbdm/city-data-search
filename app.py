# app.py
import os
import os.path
import redis
from flask import Flask, request, jsonify
from data_fetchers import get_livability, get_population, get_weather
from utils import create_output_xml, check_delete, validate_city_state

app = Flask(__name__)
app.debug = True
db = redis.Redis(
    host=os.getenv('REDIS_ENDPOINT_URI', '127.0.0.1'),
    port=os.getenv('REDIS_PORT', '6379'), 
    password=os.getenv('REDIS_PASSWORD', None)
    )

@app.route('/<citystate>/')
def get_data(citystate):
    '''Return gathered information for the given citystate in a xml format that gSheets can parse.'''
    # Data validation.
    validate_city_state(citystate)
   
    if citystate == 'get-headers':   # Check special case for returning headers.
        xml = create_output_xml(population='Population',
                                weather='2021 Weather (ºC)',
                                livability=('Overall Livability', 'Amenities', 'Cost of Living', 'Crime',
                                                'Employment', 'Housing', 'Schools', 'User Ratings')
                                )
    else:
        # Check if we already have fetched data for this citystate.
        # TODO: add some freshness (e.g., update if after a month?) to this file.
        xml = db.get(citystate)  # If we have this data cached, load it.
        if not xml:
            # If we don't, fetch it.
            xml = create_output_xml(population=get_population(citystate),
                                    weather=get_weather(citystate),
                                    livability=get_livability(citystate)
                                    )
            # Update redis with the data.
            db.set(citystate, xml)

    # Serve the xml.
    return app.response_class(xml, mimetype='application/xml')


@app.route('/force/<citystate>/')
def force_get_data(citystate):
    '''API to force fetching the data for the given city-state.'''
    # Data validation.
    validate_city_state(citystate)
   
    if citystate == 'get-headers':   # Check special case for returning headers.
        return 'Please use the regular API.'
    else:
        # Fetch the data.
        xml = create_output_xml(population=get_population(citystate),
                                weather=get_weather(citystate),
                                livability=get_livability(citystate)
                                )
        # Update redis with the data.
        db.set(citystate, xml)
        # Serve the xml.
        return app.response_class(xml, mimetype='application/xml')


@app.route('/')
def index():
    return "<h1>App is running :)</h1>"


if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)
