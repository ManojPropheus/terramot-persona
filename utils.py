import httpx
import os
import json
import pyproj
from typing import Tuple,Dict

from shapely.geometry import shape
from shapely.geometry import base as shapely_geom
from shapely.ops import transform

Geometry4326 = shapely_geom.BaseGeometry
Geometry3857 = shapely_geom.BaseGeometry

client = httpx.Client(verify=False)

def get_isochrone(location : Dict[str, float]) -> Tuple[Geometry3857, Geometry4326]:
    """
    Generate isochrone geometry in two coordinate reference systems (CRS).'
    
    Example usage for get isochrone
    location = {"lat": 37.7787, "lon": -122.4212}
    print(get_isochrone(location=location))

    Args:
        coords (Dict[str, float]): A dictionary containing geographic coordinates with the following keys:
            - 'lat' (float): Latitude in decimal degrees.
            - 'lon' (float): Longitude in decimal degrees.

    Returns:
        Tuple[BaseGeometry, BaseGeometry]: A tuple containing two Shapely geometries:
            - The first geometry is the isochrone in EPSG:3857 (Web Mercator).
            - The second geometry is the isochrone in EPSG:4326 (WGS 84 - latitude/longitude).
    """


    wgs84 = pyproj.CRS('EPSG:4326') # projection for crs with the distance units in degrees
    utm = pyproj.CRS('EPSG:3857') # projection for crs with distance units in metres

    project = pyproj.Transformer.from_crs(wgs84, utm, always_xy=True).transform
    utm_point = lambda x : transform(project, x) # Transform function given a geometry in 4326 to 3857
    
    VALHALLA_URL = "https://valhalla1.openstreetmap.de/isochrone"  
    costing_model = "auto" 
    contours = [
        {"time": 15, "color": "FF0000"}  
    ]
    polygons = True 

    # Construct the JSON request payload
    request_payload = {
        "locations": [location],
        "costing": costing_model,
        "contours": contours,
        "polygons": polygons
    }

    # Convert the request payload to a JSON string
    json_payload = json.dumps(request_payload)

    # Make the API request
    try:
        response = httpx.get(f"{VALHALLA_URL}?json={json_payload}")
        # Check for successful response (status code 200)
        if response.status_code == 200:
            isochrone_data = response.json()
        else:
            print(f"Error: {response.status_code} - {response.text}")

    except httpx.exceptions.ConnectionError:
        print("Error: Could not connect to Valhalla server. Ensure Valhalla is running and accessible at the specified URL.")
    
    espg_3857 = utm_point(shape(isochrone_data['features'][0]))
    espg_4326 = shape(isochrone_data['features'][0])

    return espg_3857,espg_4326

# Facing issues of SSL Certificate, currently manual
# def retrieve_geoid_geometry(state_id : str,hierarchy_level : str ):

#     assert hierarchy_level.lower() in ['bg','tract'], "Hierarchy must be either bg (Block Group) or tract (Census tract)"
#     file_path = f'data/{state_id}/{hierarchy_level.lower()}'
#     file_name = f"tl_2024_{state_id}_{hierarchy_level.lower()}"
#     os.makedirs(file_path,exist_ok=True)

#     URL = f"https://www2.census.gov/geo/tiger/TIGER2024/{hierarchy_level.upper()}/{file_name}.zip"
#     print(URL)

#     response = httpx.get(URL)
#     response.raise_for_status()

#     with open(file_path, "wb") as f:
#         f.write(response.content)


