import os.path
import csv
import json
from heapq import heappush, heappushpop
from geopy.distance import distance

_data = None  # Store the large cities as a dict(coordinates -> name, pop).
def _load_data():
    '''Load the preprocessed data into memory.'''
    global _data
    if _data: return
    # Using a json instead of pickle data because of heroku's storage.
    root_dir = os.path.dirname(os.path.realpath(__file__))
    filepath = os.path.join(root_dir, 'large_cities.json')
    with open(filepath) as file_in:
        _data = json.load(file_in)
    for city in _data:
        city['coordinates'] = tuple(city['coordinates'])


def find_k_closest_large_cities(coordinates, k=3):
    '''Return a sorted list the k closest large cities for the given coordinates.'''
    assert isinstance(k, int)
    assert k <= 20

    # Load data if it hasn't been loaded yet.    
    if _data is None: _load_data()

    # Initialize counter and result list.
    result = []

    for city in _data:
        city_copy = city.copy()

        # We don't want to include the city itself here.
        if city_copy['coordinates'] == coordinates: continue

        # Calculate the distance.
        city_copy['distance'] = distance(city_copy['coordinates'], coordinates).km

        # Populate the list of k closest ones as a heap.
        if len(result) < k:
            heappush(result, (-city_copy['distance'], city_copy))
        else:
            heappushpop(result, (-city_copy['distance'], city_copy))

    return [city for _, city in sorted(result, reverse=True)]


def find_all_large_cities_within_radius(coordinates, radius=250):
    '''Return a list with all unique cities within the given radius in km.'''
    # Load data if it hasn't been loaded yet.    
    if _data is None: _load_data()
    
    result = set()
    
    for city in _data:
        city_copy = city.copy()
        
        # We don't want to include the city itself here.
        if city_copy['coordinates'] == coordinates: continue

        # Calculate the distance.
        city_copy['distance'] = distance(city['coordinates'], coordinates).km

        # Skip cities further than the given radius.
        if city_copy['distance'] > radius: continue

        # Add current city to the result set.
        result.add(tuple(city_copy.items()))

    return [{x[0]: x[1] for x in city} for city in result]


def find_both_k_closest_and_radius(coordinates, k=3, radius=250):
    '''Return a list containing all unique cities that are within the given radius in km or is one of the k closest.'''
    assert isinstance(k, int)
    assert 0 < k <= 5
    assert isinstance(radius, (int, float))

    # Load data if it hasn't been loaded yet.    
    if _data is None: _load_data()
    
    within_radius = set()
    closest = []
    
    for city in _data:
        city_copy = city.copy()
        
        # We don't want to include the city itself here.
        if city['coordinates'] == coordinates: continue

        # Calculate the distance.
        city_copy['distance'] = distance(city['coordinates'], coordinates).km

        # Update the k-closest cities.
        if len(closest) < k:
            heappush(closest, (-city_copy['distance'], city_copy))
        else:
            heappushpop(closest, (-city_copy['distance'], city_copy))

        # Add the city to the result set if it's within the radius.
        if city_copy['distance'] <= radius:
            within_radius.add(tuple(city_copy.items()))

    within_radius = [{x[0]: x[1] for x in city} for city in within_radius]
    closest = [city for _, city in sorted(closest, reverse=True)]
    return within_radius, closest


if __name__ == '__main__':
    print(find_k_closest_large_cities((33.6856969, -117.8259819)))
    print(find_all_large_cities_within_radius((33.6856969, -117.8259819)))
    print(find_both_k_closest_and_radius((33.6856969, -117.8259819), k=5, radius=100))
