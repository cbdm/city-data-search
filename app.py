# app.py
import os.path
import string
from flask import Flask, request, jsonify
from data_fetchers import get_livability, get_population, get_weather
from utils import create_output_xml, check_delete

app = Flask(__name__)
app.debug = True
data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')

@app.route('/<citystate>/')
def get_data(citystate):
    '''Return gathered information for the given citystate in a xml format that gSheets can parse.'''
    # Data validation.
    assert citystate.count(' ') == 0, 'spaces should be replaced with pluses (i.e., "+").'
    assert citystate.count('-') == 1, 'too many hyphens.'
    city, state = citystate.split('-')
    assert city, 'city should be filled.'
    assert state, 'state should be filled.'
    assert set(citystate) <= (set(string.ascii_lowercase) | set("'.+-")), \
        "invalid characters, should have only lowercase letters and '.+-"
   
    if citystate == 'get-headers':   # Check special case for returning headers.
        xml = create_output_xml(population='Population',
                                weather='2021 Weather\nlowest | median daily low | median daily avg | median daily high | highest',
                                livability=('Overall Libavility', 'Amenities', 'Cost of Living', 'Crime',
                                                'Employment', 'Housing', 'Schools', 'User Ratings')
                                )
    else:
        # Check if we already have looked for this citystate.
        # TODO: add some freshness (e.g., update if after a month?) to this file.
        filepath = os.path.join(data_dir, f'{citystate}.data')
        if os.path.exists(filepath):
            with open(filepath, 'rb') as file_in:
                xml = file_in.read()
        else:
            xml = create_output_xml(population=get_population(citystate),
                                    weather=get_weather(citystate),
                                    livability=get_livability(citystate)
                                    )
            with open(filepath, 'wb') as file_out:
                file_out.write(xml)
            
            # Check if file was created correctly.
            check_delete(filepath, xml)

    # Put data into a xml and serve it.
    return app.response_class(xml, mimetype='application/xml')


@app.route('/')
def index():
    return "<h1>App is running :)</h1>"


if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)
