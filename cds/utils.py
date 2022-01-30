from city import City
import string
import xml.etree.ElementTree as ET

def create_output_xml(city):
    '''Create a xml that contains the provided data.'''
    assert isinstance(city, City)
    
    root = ET.Element('data', query=city.query)

    fn = ET.Element('full_name')
    fn.text = city.full_name
    root.append(fn)

    pop = ET.Element('population')
    pop.text = city.population
    root.append(pop)

    wtr = ET.Element('weather')
    wtr.text = '  |  '.join([f'{x}' for x in city.weather])
    root.append(wtr)

    liv = ET.Element('city_livability')
    liv.text = city.overall_livability
    root.append(liv)

    col = ET.Element('cost_of_living')
    col.text = city.cost_of_living
    root.append(col)

    hou = ET.Element('housing')
    hou.text = city.housing
    root.append(hou)

    saf = ET.Element('safety')
    saf.text = city.safety
    root.append(saf)

    sch = ET.Element('schools')
    sch.text = city.schools
    root.append(sch)

    cmc = ET.Element('closest_major_cities')
    if isinstance(city.closest_major_cities, str):
        # Check for the "headers city".
        cmc.text = city.closest_major_cities
    else:
        cmc.text = ', '.join([f'{c["name"]} ({c["distance"]:.0f}km)' for c in city.closest_major_cities])
    root.append(cmc)

    cnmc = ET.Element('count_nearby_major_cities')
    if isinstance(city.nearby_major_cities, str):
        # Check for the "headers city".
        cnmc.text = city.nearby_major_cities
    else:
        cnmc.text = f'{len(city.nearby_major_cities)}'
    root.append(cnmc)
    
    uan = ET.Element('urban_area_name')
    uan.text = city.urban_area
    root.append(uan)

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


def convert_to_citystate(city):
    '''Convert from City, ST to city-st.'''
    # TODO: probably need improvements here.
    return city.lower().replace(', ', '-').replace(' ', '+')


def convert_from_citystate(citystate):
    '''Convert from city-st to City, ST.'''
    # TODO: probably need improvements here.
    data = citystate.split('-')
    city = '-'.join(data[:-1])
    city = city.replace('+', ' ').title()
    state = data[-1].upper()
    return f'{city}, {state}'


# Maps states and provinces full names to their abbreviations.
_state_province_abbrev = {
    # US
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
    "District of Columbia": "DC",
    "American Samoa": "AS",
    "Guam": "GU",
    "Northern Mariana Islands": "MP",
    "Puerto Rico": "PR",
    "United States Minor Outlying Islands": "UM",
    "U.S. Virgin Islands": "VI",
    # Canada
    'Alberta': 'AB',
    'British Columbia': 'BC',
    'Manitoba': 'MB',
    'New Brunswick': 'NB',
    'Newfoundland and Labrador': 'NL',
    'Northwest Territories': 'NT',
    'Nova Scotia': 'NS',
    'Nunavut': 'NU',
    'Ontario': 'ON',
    'Prince Edward Island': 'PE',
    'Quebec': 'QC',
    'Saskatchewan': 'SK',
    'Yukon': 'YT'
}
# invert the dictionary for mapping short -> long
_state_province_name = dict(map(reversed, _state_province_abbrev.items()))

def state_province_to_short(long_state_province):
    '''Convert the long name of a state/province to its abbreviation.
        E.g., California -> CA'''
    return _state_province_abbrev.get(long_state_province, long_state_province)


def state_province_to_long(short_state_province):
    '''Convert the abbreviation of a state/province to its full name.
        E.g., CA -> California'''
    return _state_province_name.get(short_state_province, short_state_province)


def convert_score_from_numerical_to_letter(score):
    '''Convert a score ranging from 0~10 into a F~A+.
        Source: http://www.science.smith.edu/~jorourke/Grading.html'''
    assert isinstance(score, float)
    assert 0 <= score <= 10
    
    if score >= 9.75: return 'A+'
    if score >= 9.25: return 'A'
    if score >= 9.00: return 'A-'
    if score >= 8.75: return 'B+'
    if score >= 8.25: return 'B'
    if score >= 8.00: return 'B-'
    if score >= 7.75: return 'C+'
    if score >= 7.25: return 'C'
    if score >= 7.00: return 'C-'
    if score >= 6.75: return 'D+'
    if score >= 6.25: return 'D'
    if score >= 6.00: return 'D-'
    return 'F'
