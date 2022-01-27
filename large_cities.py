from heapq import heappush, heappushpop
from pickle import load
from geopy.distance import distance
from geopy.geocoders import Nominatim

location_app = Nominatim(user_agent="query")

class City(object):
    '''Object to store city data we use to find closest largest cities.'''
    def __init__(self, citystate, displayname, population, coordinates):
        self.citystate = citystate
        self.displayname = displayname
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


_data = None  # Store the list of large cities.
def _load_data():
    global _data
    with open('large_cities.bin', 'rb') as file_in:
        _data = load(file_in)


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
        # Calculate the distance.
        dist = distance(city.coordinates, coordinates)

        # Check it it's within max_dis.
        if dist.km <= max_dist:
            count += 1
 
        # Populate the list of k closest ones as a heap.
        if len(distances) < k:
            heappush(distances, (-dist, city.displayname))
        else:
            heappushpop(distances, (-dist, city.displayname))

    return [f'{city} ({abs(distance.km):.0f}km)' for distance, city in sorted(distances, reverse=True)], count


if __name__ == '__main__':
    print(find_close_large_cities('irvine-ca'))
