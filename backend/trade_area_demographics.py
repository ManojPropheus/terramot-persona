import os
import sys
import json
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import geopandas as gpd
import pyproj
from shapely.ops import transform
from shapely import to_geojson

from county_level_data.get_county_distributions import get_dist
from utils import get_isochrone


def get_isochrone_response(lat,lon):
        location = {'lat':lat,'lon':lon}

        wgs84 = pyproj.CRS('EPSG:4326') # projection for crs with the distance units in degrees
        utm = pyproj.CRS('EPSG:3857') # projection for crs with distance units in metres

        project = pyproj.Transformer.from_crs(wgs84, utm, always_xy=True).transform
        utm_point = lambda x : transform(project, x)

        data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'../data/')

        if not os.path.isfile(os.path.join(data_path,'combined_data.csv')):
            get_dist(lat,lon)

        geoid_distribution = pd.read_csv(os.path.join(data_path,'combined_data.csv'),dtype={'GEO_ID':'str'})
        geoid_distribution.loc[:,'GEO_ID'] = geoid_distribution.loc[:,'GEO_ID'].str.split('_',expand=True)[0]
        california_block_groups = gpd.read_file(os.path.join(data_path,'california_block_groups/tl_2020_06_bg.shp'))
        california_block_groups.rename(columns={'GEOID':'GEO_ID'},inplace=True)
        california_block_groups = california_block_groups[['GEO_ID','geometry']]
        california_block_groups.loc[:,'geometry_3857'] = california_block_groups['geometry'].apply(utm_point)

        geoid_distribution = geoid_distribution.merge(california_block_groups,on='GEO_ID')
        geometry_3857,geometry_4326 = get_isochrone(location) # Isochrone geometry

        area_of_intersection = lambda x : x.intersection(geometry_3857).area

        geoid_distribution['intersection_area'] = geoid_distribution['geometry_3857'].apply(area_of_intersection)
        geoid_distribution['geoid_area'] = geoid_distribution['geometry_3857'].apply(lambda x : x.area)

        # Pct computed as a % of geoid area
        geoid_distribution['pct_intersection'] = geoid_distribution['intersection_area']/geoid_distribution['geoid_area']
        geoid_distribution['population'] = (geoid_distribution['pct_intersection']*geoid_distribution['count']).apply(lambda x: int(x))

        isochrone_grouped = geoid_distribution[geoid_distribution['pct_intersection']>0].groupby(['data_type','brackets'])\
                .agg(population = ('population','sum'))\
                .reset_index()
        isochrone_grouped['key'] = isochrone_grouped['data_type'] + "_" + isochrone_grouped['brackets']
        isochrone_grouped.set_index('key',inplace=True)

        
        output_dict = {
            "properties" : isochrone_grouped.to_dict()['population'],
            "type" : 'Feature',
            "geometry" : json.loads(to_geojson(geometry_4326))
            }
        
        return output_dict


def get_block_groups_geometry(lat, lon):
    """
    Get block group geometries that intersect with the isochrone.
    Returns GeoJSON FeatureCollection of intersecting block groups.
    """
    location = {'lat': lat, 'lon': lon}

    wgs84 = pyproj.CRS('EPSG:4326')
    utm = pyproj.CRS('EPSG:3857')

    project = pyproj.Transformer.from_crs(wgs84, utm, always_xy=True).transform
    utm_point = lambda x: transform(project, x)

    data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/')

    # Ensure we have the combined data
    if not os.path.isfile(os.path.join(data_path, 'combined_data.csv')):
        get_dist(lat, lon)

    # Load California block groups
    california_block_groups = gpd.read_file(os.path.join(data_path, 'california_block_groups/tl_2020_06_bg.shp'))
    california_block_groups.rename(columns={'GEOID': 'GEO_ID'}, inplace=True)
    california_block_groups = california_block_groups[['GEO_ID', 'geometry']]
    california_block_groups.loc[:, 'geometry_3857'] = california_block_groups['geometry'].apply(utm_point)

    # Get isochrone geometry
    geometry_3857, geometry_4326 = get_isochrone(location)

    # Find intersecting block groups
    area_of_intersection = lambda x: x.intersection(geometry_3857).area
    california_block_groups['intersection_area'] = california_block_groups['geometry_3857'].apply(area_of_intersection)
    california_block_groups['geoid_area'] = california_block_groups['geometry_3857'].apply(lambda x: x.area)
    california_block_groups['pct_intersection'] = california_block_groups['intersection_area'] / california_block_groups['geoid_area']

    # Filter to only intersecting block groups (>1% intersection to avoid tiny slivers)
    intersecting_block_groups = california_block_groups[california_block_groups['pct_intersection'] > 0.01].copy()

    # Convert to GeoJSON format
    features = []
    for _, row in intersecting_block_groups.iterrows():
        feature = {
            "type": "Feature",
            "properties": {
                "GEO_ID": row['GEO_ID'],
                "intersection_pct": round(row['pct_intersection'] * 100, 1)
            },
            "geometry": json.loads(to_geojson(row['geometry']))
        }
        features.append(feature)

    geojson_output = {
        "type": "FeatureCollection",
        "features": features
    }

    return geojson_output
    

