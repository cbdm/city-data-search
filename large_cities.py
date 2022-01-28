import os.path
from heapq import heappush, heappushpop
from pickle import load
from geopy.distance import distance
from geopy.geocoders import Nominatim

location_app = Nominatim(user_agent="query")

class City(object):
    '''Object to store city data we use to find closest largest cities.'''
    def __init__(self, displayname, citystate, population, coordinates):
        self.displayname = displayname
        self.citystate = citystate
        self.population = population
        self.coordinates = coordinates

    def __hash__(self):
        return str.__hash__(f'{self.coordinates}')

    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):
        return f'{self.displayname} ({self.citystate}), {self.population}, {self.coordinates}'

    def __eq__(self, o):
        if not isinstance(o, City): return False
        return self.displayname == o.displayname

    def __gt__(self, o):
        # Compare state before city name.
        if not isinstance(o, City): return False
        city, state = self.displayname.split(', ')
        ocity, ostate = o.displayname.split(', ')

        if state > ostate:
            return True
        elif state < ostate:
            return False

        if city > ocity:
            return True
        else:
            return False

    @staticmethod
    def from_str(s):
        data = s.split(', ')
        displayname = data[0] + ', ' + data[1][:data[1].find(' ')]
        citystate = data[1][data[1].find('(') + 1:-1]
        population = int(data[2])
        coordinates = (float(data[3][data[3].find('(') + 1:]), float(data[4][:data[4].find(')')]))
        return City(displayname, citystate, population, coordinates)


_data = None  # Store the list of large cities.
def _load_data():
    '''Load the preprocessed data into memory.'''
    global _data
    if _data: return
    # Using a csv instead of pickle data because of heroku's storage.
    root_dir = os.path.dirname(os.path.realpath(__file__))
    filepath = os.path.join(root_dir, 'large_cities.csv')
    _data = []
    with open(filepath) as file_in:
        for row in file_in:
            _data.append(City.from_str(row))


def find_close_large_cities(citystate, k=3, max_dist=100):
    '''Find the k closest large cities (100k+ for US, 50k+ for Canada) for the given citystate.
    Also returns the number of large cities within the max_dist (km).
        Data sources:
            US: https://www2.census.gov/programs-surveys/popest/datasets/2010-2020/cities/
            Canada: https://canadapopulation.org/largest-cities-in-canada-by-population/'''
    assert isinstance(k, int)
    assert k <= 20

    # Load data if it hasn't been loaded yet.    
    if _data is None:
        _load_data()

    # Find coordinates of given city.
    loc = location_app.geocode(citystate)
    coordinates = (loc.latitude, loc.longitude)

    # Initialize counter and result list.
    count = 0
    distances = []

    for city in _data:
        # We don't want to include the city itself here.
        if city.coordinates == coordinates:
            continue

        # Calculate the distance.
        dist = distance(city.coordinates, coordinates)

        # Check it it's within max_dist.
        if dist.km <= max_dist:
            count += 1
 
        # Populate the list of k closest ones as a heap.
        if len(distances) < k:
            heappush(distances, (-dist, city.displayname))
        else:
            heappushpop(distances, (-dist, city.displayname))

    return ', '.join([f'{city} ({abs(distance.km):.0f}km)' for distance, city in sorted(distances, reverse=True)]), f'{count}'


def get_all_large_cities_within_radius(coordinates, radius=100):
    '''Return a sorted list with all unique cities within the given radius in km.'''
    # Load data if it hasn't been loaded yet.    
    if _data is None: _load_data()
    
    distances = set()
    for city in _data:
        # We don't want to include the city itself here.
        if city.coordinates == coordinates:
            continue

        # Calculate the distance.
        dist = distance(city.coordinates, coordinates)

        # Skip cities further than the given radius.
        if dist.km > radius:
            continue

        distances.add((dist.km, city))

    return [city for _, city in sorted(distances)]


if __name__ == '__main__':
    print(find_close_large_cities('irvine-ca'))
    print(get_all_large_cities_within_radius((33.6856969, -117.8259819)))
