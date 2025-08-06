import requests
from flask import current_app


def get_geoid(lat: float, lng: float) -> str:
    """
    Reverse-geocode latitude/longitude to a Census GEOID.
    Tries Census Blocks first, then Block Groups, then Tracts.
    Returns the GEOID string or raises an exception on failure.
    """
    url = 'https://geocoding.geo.census.gov/geocoder/geographies/coordinates'
    params = {
        'x': lng,
        'y': lat,
        'benchmark': current_app.config.get('CENSUS_BENCHMARK', 'Public_AR_Census2020'),
        'vintage': current_app.config.get('CENSUS_VINTAGE', 'Census2020_Census2020'),
        'format': 'json'
    }
    resp = requests.get(url, params=params, timeout=5)
    resp.raise_for_status()
    data = resp.json().get('result', {}).get('geographies', {})

    # Order of precision
    for geo_key in ('Census Blocks', 'Census Block Groups', 'Census Tracts'):
        items = data.get(geo_key)
        if items:
            return items[0]['GEOID']

    raise ValueError("No GEOID found in Census response")
