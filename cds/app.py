# app.py
from os import getenv
from flask import Flask, request, render_template, flash, redirect, url_for
from utils import create_output_xml
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from city import search as city_search, City
from data_handler import DataHandler
from flask_sqlalchemy import SQLAlchemy
from pymysql import install_as_MySQLdb

install_as_MySQLdb()

app = Flask(__name__)
app.debug = True
app.config["SECRET_KEY"] = getenv("FLASK_SECRET_KEY", "abc")
# Connect to the DB.
db_config = {
    "host": getenv("DB_HOST", "localhost"),
    "port": getenv("DB_PORT", "3306"),
    "user": getenv("DB_USER", "user"),
    "passwd": getenv("DB_PASS", "pass"),
    "database": getenv("DB_NAME", "db"),
}
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "mysql://{user}:{passwd}@{host}:{port}/{database}".format(**db_config)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Configure DB table to store data.
class CachedCity(db.Model):
    geonameid = db.Column(db.String(100), primary_key=True)
    data = db.Column(db.JSON)

    def __repr__(self):
        return f"<CachedCity {self.geonameid}>"


# Pass the instantiated DB to our data handler.
dh = DataHandler(db=db, table=CachedCity)

# Define the min/max wait time to refresh the data.
# Data over this limit *can* be updated by user's request.
min_data_refresh = timedelta(weeks=12)
# Data over this limit *should* be updated due to its freshness.
max_data_refresh = timedelta(weeks=52)

##
## Webapp routes
##
@app.route("/", methods=("GET", "POST"))
def index():
    """Homepage to allow the user to search for a city."""
    if request.method == "POST":
        query_value = request.form.get("query_value", "")
        if not query_value:
            flash("You must enter a value in the search box!")
        else:
            action = request.form.get("action", "")
            if action == "Search":
                return redirect(url_for("search", query=query_value))
            elif action == "Go":
                option_list = city_search(query_value, max_results=1)
                if not option_list:
                    flash(f'No cities found for "{query_value}"!')
                else:
                    return redirect(url_for("web", geonameid=option_list[0].geonameid))
    return render_template("index.html")


@app.route("/search/<query>", methods=("GET", "POST"))
def search(query):
    """Page for users to select which city they want to view."""
    if request.method == "POST":
        return redirect(url_for("web", geonameid=list(request.form)[0]))

    options = city_search(query, max_results=10)
    if not options:
        flash(f'No cities found for "{query}"!')
        return redirect(url_for("index"))

    return render_template("options.html", option_list=options)


@app.route("/about/")
def about():
    """Return the about page."""
    return render_template("about.html")


@app.route("/api/info/")
def api_info():
    """'Return the api-info page."""
    return render_template("api.html")


@app.route("/api/example/")
def api_example():
    """Redirect to google sheet example."""
    return redirect("https://caio.link/city-data-search-example")


@app.route("/web/<geonameid>/")
def web(geonameid):
    """Page to serve the data in a easy to understand GUI."""
    city = dh.get_city_by_geonameid(geonameid)
    now = datetime.utcnow()
    ts = datetime.fromisoformat(city.timestamp)
    diff = now - ts
    if diff >= max_data_refresh:
        # Data is too old, should refresh.
        return redirect(url_for("refresh", geonameid=geonameid))
    return render_template(
        "city.html",
        city=city,
        geonameid=geonameid,
        show_refresh=(diff >= min_data_refresh),
    )


@app.route("/refresh/<geonameid>/")
def refresh(geonameid):
    city = dh.get_city_by_geonameid(geonameid)
    now = datetime.utcnow()
    ts = datetime.fromisoformat(city.timestamp)
    diff = now - ts
    assert diff >= min_data_refresh, "Data is still fresh, no need to update."
    dh.get_city_by_geonameid(geonameid, force=True)
    return redirect(url_for("web", geonameid=geonameid))


##
## Active API endpoints
##
@app.route("/api/single/<city>/")
def single_city(city, force=False):
    """API to get data for a single given city."""
    return app.response_class(
        get_single_city_data(city, force=force), mimetype="application/xml"
    )


@app.route("/api/force/<city>/")
def force_single_city(city):
    """API to force fetching the data for the given city."""
    return single_city(city, force=True)


@app.route("/api/multi/<citylist>/")
def multi_city(citylist, force=False):
    """API to fetch data for all cities in the given city list."""
    response = ET.Element("multi", citylist=citylist)
    for city in citylist.split("&"):
        new_data = get_single_city_data(city, force)
        response.append(ET.XML(new_data.decode("utf8")))
    return app.response_class(ET.tostring(response), mimetype="application/xml")


def get_single_city_data(city, force=False):
    """Main function that creates a response xml for a single city."""
    assert city
    if city == "get-headers":
        city_obj = City.create_headers_city()
    else:
        city_info = city_search(city, max_results=1)
        if city_info:
            # If we found a result for this query, get the data for it.
            city_obj = dh.get_city_by_geonameid(city_info[0].geonameid, query=city)
        else:
            # If not, we create a special City object to include in the response.
            city_obj = City.create_invalid_query_city(city)
    return create_output_xml(city_obj)


##
## Old API endpoints
##
@app.route("/api/citystate/<citystate>/")
@app.route("/api/force/citystate/<citystate>/")
def old_api(citystate):
    """Rerouting old api endpoints."""
    return f"Invalid endpoint, please check {url_for('api_info', _external=True, _scheme='https')} for up-to-date API info."


if __name__ == "__main__":
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)
