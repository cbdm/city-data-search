# city-data-search
Flask app that returns a xml with relevant information about a given city.

It gets data from [areavibes.com](areavibes.com) for population and livability, and uses [meteostat](https://github.com/meteostat/meteostat-python) for weather data.  
The weather data shown is in the following format:  
`lowest of the year | median of daily lows | median of daily averages | median of daily highs | highest of the year`

## API
You can use `{URL}/api/citystate/city-state` to get the information.  
For example, to get information for `Irvine, CA`, you'd use `{URL}/api/citystate/irvine-ca`.  
For a city that has a space, replace it with a `+`.

### Multi-city
You can also use `{URL}/api/multi/cs1_cs2_cs3_..._csn` to get data for all city-states in the list.

## Google Sheets Embedding
You can use the following formula to embed this info into google sheets:  
`=IMPORTXML(CONCATENATE({URL}/api/citystate/, {CITY}), "/data")`  
or  
`=IMPORTXML(CONCATENATE({URL}/api/multi/, {LIST}), "/multi/data")`

HINTS:
- if you use `get-headers` as the city-state parameter, you should get a xml that you can use the same formula above to populate the header row;
- you can use the following formula to convert from `City, ST` to `city-st`:  
`=LOWER(SUBSTITUTE(SUBSTITUTE({CITY},", ","-"), " ", "+"))`

## Sample URL
This is hosted on a free heroku dyno, so it might stop at anytime:  
[https://city-data-search.herokuapp.com](https://city-data-search.herokuapp.com)
