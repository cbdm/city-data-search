import xml.etree.ElementTree as ET
from os import remove

def create_output_xml(population, weather, livability):
    '''Create a xml that contains the provided data.'''

    # Data validation.
    assert isinstance(population, str)
    assert isinstance(weather, str)
    assert isinstance(livability, tuple)
    assert len(livability) == 8
    for l in livability:
        assert isinstance(l, str)
    
    root = ET.Element('root')

    p = ET.Element('data')
    p.text = population
    root.append(p)

    w = ET.Element('data')
    w.text = weather
    root.append(w)

    l = []
    for liv in livability:
        l.append(ET.Element('data'))
        l[-1].text = liv
        root.append(l[-1])
    
    return ET.tostring(root)


def check_delete(filepath, xml):
    '''Check if the xml was correctly written to disk, otherwise deletes it.'''
    with open(filepath, 'rb') as file_in:
        xml2 = file_in.read()
    
    if xml != xml2:
        remove(filepath)
