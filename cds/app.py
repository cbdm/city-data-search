# app.py
from os import getenv
from flask import Flask, request, render_template, flash, redirect, url_for
from utils import create_output_xml
from datetime import datetime
import xml.etree.ElementTree as ET
from city import search as city_search
from data_handler import DataHandler

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = getenv('FLASK_SECRET_KEY', 'abc')
dh = DataHandler(redis_host=getenv('REDIS_ENDPOINT_URI', '127.0.0.1'),
                    redis_port=getenv('REDIS_PORT', '6379'),
                    redis_password=getenv('REDIS_PASSWORD', None)
                )

##
## Webapp routes
##
@app.route('/', methods=('GET', 'POST'))
def index():
    '''Homepage to allow the user to search for a city.'''
    if request.method == 'POST':
        query_value = request.form.get('query_value', '')
        if not query_value:
            flash('You must enter a value in the search box!')
        else: 
            action = request.form.get('action', '')
            if action == 'Search':
                return redirect(url_for('search', query=query_value))
            elif action == 'Go':
                option_list = city_search(query_value, max_results=1)
                if not option_list:
                    flash(f'No cities found for "{query_value}"!')
                else:
                    return redirect(url_for('web', geonameid=option_list[0].geonameid))
    return render_template('index.html')


@app.route('/search/<query>', methods=('GET', 'POST'))
def search(query):
    '''Page for users to select which city they want to view.'''
    if request.method == 'POST':
        return redirect(url_for('web', geonameid=list(request.form)[0]))

    options = city_search(query, max_results=10)
    if not options:
        flash(f'No cities found for "{query}"!')
        return redirect(url_for('index'))
    
    return render_template('options.html', option_list=options)


@app.route('/about/')
def about():
    '''Return the about page.'''
    return render_template('about.html')


@app.route('/api/info/')
def api_info():
    ''''Return the api-info page.'''
    return render_template('api.html')


@app.route('/web/<geonameid>/')
def web(geonameid):
    '''Page to serve the data in a easy to understand GUI.'''
    return render_template('city.html', city=dh.get_city_by_geonameid(geonameid))


##
## Active API endpoints
##
@app.route('/api/single/<city>/')
def single_city(city, force=False):
    '''API to get data for a single given city.'''
    return app.response_class(get_single_city_data(city, force), mimetype='application/xml')


@app.route('/api/force/<city>/')
def force_single_city(city):
    '''API to force fetching the data for the given city.'''
    return single_city(city, force=True)


@app.route('/api/multi/<citylist>/')
def multi_city(citylist, force=False):
    '''API to fetch data for all cities in the given city list.'''
    response = ET.Element('multi', citylist=citylist)
    for city in citylist.split('_'):
        new_data = get_single_city_data(city, force)
        response.append(ET.XML(new_data.decode("utf8")))
    return app.response_class(ET.tostring(response), mimetype='application/xml')


def get_single_city_data(city, force=False):
    '''Main function that creates a response xml for a single city.'''
    assert city
    if city == 'get-headers':
        return create_output_xml(None, headers=True)
    
    city_info = city_search(city, max_results=1)[0]
    city_obj = dh.get_city_by_geonameid(city_info.geonameid)
    return create_output_xml(city_obj)


##
## Option to flush the db if we make any changes to the data, should be used sparringly!
##
@app.route('/flush-db/<password>')
def clear_db(password):
    dh.flush_db(password)
    return '<h1>DB flushed!<h1>'


##
## Old API endpoints
##
@app.route('/api/citystate/<citystate>/')
@app.route('/api/force/citystate/<citystate>/')
def old_api(citystate):
    '''Rerouting old api endpoints.'''
    return f"Invalid endpoint, please check {url_for('api_info', _external=True)} for up-to-date API info."


if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)