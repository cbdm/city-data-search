import requests
import urllib.parse
import json
import utils
import weather
import large_cities
from datetime import datetime
from jsonpickle import encode, decode

class City(object):
    def __init__(self, geonameid, full_name='', *, fetch=False,
                    max_nearby_major_cities=3, radius_nearby_major_cities=250):
        self.geonameid = geonameid
        self.full_name = full_name
        if fetch: self.fetch_data()
        self._max_nearby_major_cities = max_nearby_major_cities
        self.radius_nearby_major_cities = radius_nearby_major_cities
        self._fetched = fetch


    def fetch_data(self):
        # Can add a check here if it's past a threshold from timestamp then refresh the data.
        if self._fetched:
            return

        # Populate the city attributes.
        self._fetch_teleport()
        self._fetch_areavibes()
        self._fetch_city_image()
        self._fetch_weather()
        self._find_nearby_major_cities()

        # Timestamp this data for freshness and mark this city as fetched.
        self.timestamp = datetime.utcnow().isoformat()
        self._fetched = True


    def _fetch_teleport(self):
        '''Fetch city data from teleport.'''

        url = 'https://api.teleport.org/api/cities/' + urllib.parse.quote(f'geonameid:{self.geonameid}')
        resp_city = requests.get(url)
        if resp_city.status_code != 200:
            self.error_code = resp_city.status_code
            return

        # Parse a valid response.
        data = json.loads(resp_city.text)
        self.full_name = data.get('full_name', '')
        self.name = data.get('name', self.full_name)
        self.population = f"{data.get('population', 0):,}"
        self.coordinates = tuple(data.get('location', {}).get('latlon', {}).values())
        self.state = data.get('_links', {}).get('city:admin1_division', {}).get('name', '')
        self.country = data.get('_links', {}).get('city:country', {}).get('name', '')
        self.tz = data.get('_links', {}).get('city:timezone', {}).get('name', '')

        # Try to convert city's name to the old city-state format.
        # Used for the api calls and areavibes requests.
        self.citystate = utils.convert_to_citystate(f'{self.name}, {utils.state_province_to_short(self.state)}')
        
        # Default values for urban area features:
        self.urban_area = 'N/A'
        self.ua_overall_livability = 'N/A'
        self.ua_cost_of_living = 'N/A'
        self.ua_housing = 'N/A'
        self.ua_schools = 'N/A'
        self.ua_safety = 'N/A'
        self.ua_img_url = 'N/A'
        self.ua_weather_type = 'N/A'
        self.ua_avg_num_rainy_days = 'N/A'
        self.ua_currency = 'N/A'
        self.ua_rent_small = 'N/A'
        self.ua_rent_medium = 'N/A'
        self.ua_rent_large = 'N/A'
        
        #
        # Check if the city is part of a teleport urban area.
        #
        urban_area_link = data.get('_links', {}).get('city:urban_area', {}).get('href', '')
        if urban_area_link:
            self._fetch_urban_area(urban_area_link)


    def _fetch_urban_area(self, urban_area_link):
        '''Get data from the given urban area link.'''
        resp_ua = requests.get(urban_area_link)
        data_ua = json.loads(resp_ua.text)
        
        self.urban_area = data_ua.get('name', '')

        details_url = data_ua.get('_links', {}).get('ua:details', {}).get('href', '')
        if details_url:
            resp_details = requests.get(details_url)
            details_data = json.loads(resp_details.text)

            for cat in details_data.get('categories', []):
                category = cat.get('id', '')
                if category == "CLIMATE":
                    for subcat in cat.get('data', []):
                        subcategory = subcat.get('id', '')
                        if subcategory == 'WEATHER-TYPE':
                            self.ua_weather_type = subcat.get('string_value', '')
                        elif subcategory == 'WEATHER-AV-NUMBER-RAINY-DAYS':
                            self.ua_avg_num_rainy_days = int(subcat.get('float_value', 0))
                
                elif category == 'ECONOMY':
                    for subcat in cat.get('data', []):
                        if subcat.get('id', '') == 'CURRENCY-URBAN-AREA':
                            self.ua_currency = subcat.get('string_value', '')
                            break
                
                elif category == 'HOUSING':
                    for subcat in cat.get('data', []):
                        subcategory = subcat.get('id', '')
                        if subcategory == 'APARTMENT-RENT-SMALL':
                            self.ua_rent_small = f'{int(subcat.get("currency_dollar_value", 0)):,}'
                        
                        elif subcategory == 'APARTMENT-RENT-MEDIUM':
                            self.ua_rent_medium = f'{int(subcat.get("currency_dollar_value", 0)):,}'

                        elif subcategory == 'APARTMENT-RENT-LARGE':
                            self.ua_rent_large = f'{int(subcat.get("currency_dollar_value", 0)):,}'

        img_url = data_ua.get('_links', {}).get('ua:images', {}).get('href', '')
        if img_url:
            resp_img = requests.get(img_url)
            img_data = json.loads(resp_img.text)
            self.ua_img_url = img_data.get('photos', [{}])[0].get('image', {}).get('mobile', 'N/A')

        # Get the urban area livability scores if available.
        scores_url = data_ua.get('_links', {}).get('ua:scores', {}).get('href', '')
        if scores_url:
            resp_scores = requests.get(scores_url)
            scores_data = json.loads(resp_scores.text)
                            
            overall = scores_data.get('teleport_city_score', -1)
            if overall >= 0:
                self.ua_overall_livability = f'{overall:.0f}'

            for cat in scores_data.get('categories', []):
                cat_name = cat.get('name', '')
                if cat_name == 'Cost of Living':
                    score = cat.get('score_out_of_10', -1)
                    if score >= 0:
                        self.ua_cost_of_living = utils.convert_score_from_numerical_to_letter(score)
                elif cat_name == 'Education':
                    score = cat.get('score_out_of_10', -1)
                    if score >= 0:
                        self.ua_schools = utils.convert_score_from_numerical_to_letter(score)
                elif cat_name == 'Housing':
                    score = cat.get('score_out_of_10', -1)
                    if score >= 0:
                        self.ua_housing = utils.convert_score_from_numerical_to_letter(score)
                elif cat_name == 'Safety':
                    score = cat.get('score_out_of_10', -1)
                    if score >= 0:
                        self.ua_safety = utils.convert_score_from_numerical_to_letter(score)

    
    def _fetch_areavibes(self):
        '''Fetch city livability data from areavibes.
            Doing this in addition to teleport because, e.g., Irvine, CA != Los Angeles, CA'''
        # Default values:
        self.overall_livability = 'N/A'
        self.cost_of_living = 'N/A'
        self.housing = 'N/A'
        self.schools = 'N/A'
        self.safety = 'N/A'
        
        livability_url = f'https://www.areavibes.com/{self.citystate}/livability'
        resp = requests.get(livability_url)
        if resp.status_code != 200:
            return

        html = resp.text
        
        # Parse the overall livability score.
        liv_flag = '<em>Livability</em>'
        html = html[html.find(liv_flag) + len(liv_flag) + 1:]
        liv_start = html.find('>') + 1
        liv_end = html.find('<')
        livability = html[liv_start:liv_end]
        if livability:
            self.overall_livability = livability

        # Parse the cost of living score.
        col_flag = '<em>Cost of Living</em>'
        html = html[html.find(col_flag) + len(col_flag) + 1:]
        col_start = html.find('>') + 1
        col_end = html.find('<')
        col = html[col_start:col_end]
        if col:
            self.cost_of_living = col

        # Parse the safety score.
        crm_flag = '<em>Crime</em>'
        html = html[html.find(crm_flag) + len(crm_flag) + 1:]
        crm_start = html.find('>') + 1
        crm_end = html.find('<')
        crime = html[crm_start:crm_end]
        if crime:
            self.safety = crime
        
        # Parse the housing score.
        hou_flag = '<em>Housing</em>'
        html = html[html.find(hou_flag) + len(hou_flag) + 1:]
        hou_start = html.find('>') + 1
        hou_end = html.find('<')
        housing = html[hou_start:hou_end]
        if housing:
            self.housing = housing
        
        # Parse the schools score.
        sch_flag = '<em>Schools</em>'
        html = html[html.find(sch_flag) + len(sch_flag) + 1:]
        sch_start = html.find('>') + 1
        sch_end = html.find('<')
        schools = html[sch_start:sch_end]
        if schools:
            self.schools = schools


    def _fetch_city_image(self):
        '''Find an image from this city.'''
        # TODO: look for a city image somewhere.
        # Maybe https://unsplash.com/documentation
        self.img_url = 'N/A'


    def _fetch_weather(self):
        '''Get the weather data from the previous full year.'''
        self.weather_year = datetime.now().year - 1
        self.weather = weather.get_year_round_weather(self.coordinates, self.weather_year)


    def _find_nearby_major_cities(self):
        self.nearby_major_cities, self.closest_major_cities = \
            large_cities.find_both_k_closest_and_radius(coordinates=self.coordinates,
                                                        k=self._max_nearby_major_cities,
                                                        radius=self.radius_nearby_major_cities)


    def get_city_state(self):
        return utils.convert_to_citystate(f'{self.name}, {utils.state_province_to_short(self.state)}')


    def __eq__(self, o):
        if not isinstance(o, City): return False
        return self.geonameid == o.geonameid    


    def __gt__(self, o):
        if not isinstance(o, City): return False
        return self.geonameid > o.geonameid


    def __hash__(self):
        return self.geonameid


    def __str__(self):
        return f'(City:{self.geonameid}, {self.full_name})'


    def __repr__(self):
        return self.__str__()


    def to_json(self):
        '''Serialize the object to a json for storage.'''
        return encode(self)


    @staticmethod
    def from_json(s):
        '''Load a serialized object from storage.'''
        return decode(s)


    @staticmethod
    def create_headers_city():
        headers = City(None)
        headers.population = 'Population'
        headers.weather = ['Year-round Weather']
        headers.overall_livability = 'City Livability'
        headers.cost_of_living = 'Cost of Living'
        headers.housing = 'Housing'
        headers.safety = 'Safety'
        headers.schools = 'Schools'
        headers.closest_major_cities = 'Closest Major Cities'
        headers.nearby_major_cities = 'Nearby Major Cities'
        headers.urban_area = 'Urban Area Name'
        return headers



def search(cityname, max_results=1):
    '''Find the best match results for the given city name.'''
    def _parse_city_result(city_search_result):
        link = city_search_result.get('_links', {}).get('city:item', {}).get('href', '')
        geonameid = link[link.rfind(':') + 1:-1]
        name = city_search_result.get('matching_full_name', 'N/A')
        return geonameid, name

    assert isinstance(cityname, str)
    assert cityname
    assert isinstance(max_results, int)
    if max_results < 1: return []

    url = f'https://api.teleport.org/api/cities/?search={cityname}&limit={max_results}'
    response = requests.get(url)
    data = json.loads(response.text)
    return [City(*_parse_city_result(city_result)) for city_result in data.get('_embedded', {})
                                                                        .get('city:search-results', [])]


if __name__ == '__main__':            
    irv = search('irvine', max_results=5)[0]    
    irv.fetch_data()
    print(irv.__dict__)

    bsb = search('brasilia', max_results=1)[0]
    bsb.fetch_data()
    print(bsb.__dict__)