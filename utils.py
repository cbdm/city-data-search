import string
import xml.etree.ElementTree as ET
from os import remove

def create_output_xml(citystate, population, weather, livability, closest_large_cities, count_large_cities):
    '''Create a xml that contains the provided data.'''

    # Data validation.
    assert isinstance(population, str)
    assert isinstance(weather, str)
    assert isinstance(livability, tuple)
    assert len(livability) == 8
    for l in livability:
        assert isinstance(l, str)
    assert isinstance(closest_large_cities, str)
    assert isinstance(count_large_cities, str)    
    
    root = ET.Element('data', citystate=citystate)

    p = ET.Element('population')
    p.text = population
    root.append(p)

    w = ET.Element('weather')
    w.text = weather
    root.append(w)

    l = []
    liv_headers = ('livability', 'amenities', 'cost_of_living', 'crime',
                    'employment', 'housing', 'schools', 'user_ratings')
    for h, liv in zip(liv_headers, livability):
        l.append(ET.Element(h))
        l[-1].text = liv
        root.append(l[-1])

    lcl = ET.Element('nearby_large_cities')
    lcl.text = closest_large_cities
    root.append(lcl)

    lcc = ET.Element('count_nearby_large')
    lcc.text = count_large_cities
    root.append(lcc)
    
    return ET.tostring(root)


def validate_city_state(citystate):
    '''Validate the format of the citystate; raises assertionerrors for invalid data.'''
    assert citystate.count(' ') == 0, 'spaces should be replaced with pluses (i.e., "+").'
    assert citystate.count('-') == 1, 'wrong number of hyphens.'
    city, state = citystate.split('-')
    assert city, 'city should be filled.'
    assert state, 'state should be filled.'
    assert set(citystate) <= (set(string.ascii_lowercase) | set("'.+-")), \
        "invalid characters, should have only lowercase letters and '.+-"
