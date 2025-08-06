"""
Race & Ethnicity Distribution from Census Data
Fetches comprehensive race and ethnicity distribution from Census Table B03002 (Hispanic or Latino Origin by Race).
This table provides the most complete race/ethnicity breakdown including Hispanic/Latino cross-tabulation.
"""

import os
import requests
import pandas as pd

# Census API key
CENSUS_API_KEY = 'f5fddae34f7f6adf93a768ac2589c032d3e2e0cf'


def get_geography(lat: float, lon: float) -> dict:
    """
    Get geographic information (state, county, tract, block group, block) from coordinates.
    """
    url = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
    params = {
        "x": lon, "y": lat, "benchmark": "Public_AR_Census2020",
        "vintage": "Census2020_Census2020", "format": "json"
    }
    try:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        geogs = resp.json()["result"]["geographies"]
    except requests.exceptions.RequestException as e:
        print(f"Could not get geography: {e}")
        return {}

    state = geogs.get("States", [{}])[0]
    county = geogs.get("Counties", [{}])[0]
    tracts = geogs.get("Census Tracts", [])
    blocks = geogs.get("Census Blocks", [])

    tract_fips, tract_name = (tracts[0].get("TRACT"), tracts[0].get("NAME")) if tracts else (None, None)
    
    if blocks:
        block = blocks[0]
        block_fips = block.get("BLOCK")
        block_name = block.get("NAME")
        block_geoid = block.get("GEOID")
        # Extract block group info from the block data
        block_group_fips = block.get("BLKGRP")
        if block_group_fips:
            block_group_name = f"Block Group {block_group_fips}"
        else:
            block_group_name = None
    else:
        block_fips = None
        block_name = None
        block_geoid = None
        block_group_fips = None
        block_group_name = None

    return {
        "state_fips": state.get("STATE"), "state_name": state.get("NAME"),
        "county_fips": county.get("COUNTY"), "county_name": county.get("NAME"),
        "tract_fips": tract_fips, "tract_name": tract_name,
        "block_group_fips": block_group_fips, "block_group_name": block_group_name,
        "block_fips": block_fips, "block_name": block_name, "block_geoid": block_geoid
    }


def get_race_ethnicity_data(state_fips: str, county_fips: str, tract_fips: str = None,
                           block_group_fips: str = None, year: int = 2023, force_tract: bool = False) -> pd.DataFrame:
    """
    Fetches race and ethnicity distribution from Census ACS Detailed Table B03002.
    This table provides Hispanic or Latino Origin by Race breakdown.
    """
    base_url = f"https://api.census.gov/data/{year}/acs/acs5"
    table_to_get = "B03002"
    
    # Key variables from B03002 table
    race_ethnicity_vars = [
        "B03002_001E",  # Total population
        "B03002_002E",  # Not Hispanic or Latino
        "B03002_003E",  # Not Hispanic or Latino: White alone
        "B03002_004E",  # Not Hispanic or Latino: Black or African American alone
        "B03002_005E",  # Not Hispanic or Latino: American Indian and Alaska Native alone
        "B03002_006E",  # Not Hispanic or Latino: Asian alone
        "B03002_007E",  # Not Hispanic or Latino: Native Hawaiian and Other Pacific Islander alone
        "B03002_008E",  # Not Hispanic or Latino: Some other race alone
        "B03002_009E",  # Not Hispanic or Latino: Two or more races
        "B03002_012E",  # Hispanic or Latino
        "B03002_013E",  # Hispanic or Latino: White alone
        "B03002_014E",  # Hispanic or Latino: Black or African American alone
        "B03002_015E",  # Hispanic or Latino: American Indian and Alaska Native alone
        "B03002_016E",  # Hispanic or Latino: Asian alone
        "B03002_017E",  # Hispanic or Latino: Native Hawaiian and Other Pacific Islander alone
        "B03002_018E",  # Hispanic or Latino: Some other race alone
        "B03002_019E",  # Hispanic or Latino: Two or more races
    ]
    
    params = {"get": f"NAME,{','.join(race_ethnicity_vars)}"}

    if CENSUS_API_KEY:
        params["key"] = CENSUS_API_KEY

    # Set geography - prefer block group level
    if block_group_fips and tract_fips and not force_tract:
        geo_level = "Block Group"
        params["for"] = f"block group:{block_group_fips}"
        params["in"] = f"state:{state_fips} county:{county_fips} tract:{tract_fips}"
    elif tract_fips:
        geo_level = "Census Tract"
        params["for"] = f"tract:{tract_fips}"
        params["in"] = f"state:{state_fips} county:{county_fips}"
    else:
        geo_level = "County"
        params["for"] = f"county:{county_fips}"
        params["in"] = f"state:{state_fips}"

    print(f"Fetching Race/Ethnicity data for {geo_level}...")
    try:
        resp = requests.get(base_url, params=params)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        print(f"API Request failed: {e}")
        return pd.DataFrame()
    
    if len(data) < 2:
        print("No data returned")
        return pd.DataFrame()
        
    df_full = pd.DataFrame([data[1]], columns=data[0])
    
    # Parse the data and create comprehensive race/ethnicity breakdown
    total_population = int(float(df_full["B03002_001E"].iloc[0]))
    print(f"Total population: {total_population}")
    
    records = []
    
    # Non-Hispanic categories - ensure proper int conversion
    non_hispanic_white = int(float(df_full["B03002_003E"].iloc[0]))
    non_hispanic_black = int(float(df_full["B03002_004E"].iloc[0]))
    non_hispanic_native = int(float(df_full["B03002_005E"].iloc[0]))
    non_hispanic_asian = int(float(df_full["B03002_006E"].iloc[0]))
    non_hispanic_pacific = int(float(df_full["B03002_007E"].iloc[0]))
    non_hispanic_other = int(float(df_full["B03002_008E"].iloc[0]))
    non_hispanic_multirace = int(float(df_full["B03002_009E"].iloc[0]))
    
    # Hispanic categories - ensure proper int conversion
    hispanic_total = int(float(df_full["B03002_012E"].iloc[0]))
    hispanic_white = int(float(df_full["B03002_013E"].iloc[0]))
    hispanic_black = int(float(df_full["B03002_014E"].iloc[0]))
    hispanic_native = int(float(df_full["B03002_015E"].iloc[0]))
    hispanic_asian = int(float(df_full["B03002_016E"].iloc[0]))
    hispanic_pacific = int(float(df_full["B03002_017E"].iloc[0]))
    hispanic_other = int(float(df_full["B03002_018E"].iloc[0]))
    hispanic_multirace = int(float(df_full["B03002_019E"].iloc[0]))
    
    # Create simplified race/ethnicity categories
    race_ethnicity_categories = [
        {
            "category": "White (Non-Hispanic)",
            "population": int(non_hispanic_white),
            "percentage": float(non_hispanic_white * 100.0 / total_population) if total_population > 0 else 0.0
        },
        {
            "category": "Hispanic or Latino",
            "population": int(hispanic_total),
            "percentage": float(hispanic_total * 100.0 / total_population) if total_population > 0 else 0.0
        },
        {
            "category": "Black or African American (Non-Hispanic)",
            "population": int(non_hispanic_black),
            "percentage": float(non_hispanic_black * 100.0 / total_population) if total_population > 0 else 0.0
        },
        {
            "category": "Asian (Non-Hispanic)",
            "population": int(non_hispanic_asian),
            "percentage": float(non_hispanic_asian * 100.0 / total_population) if total_population > 0 else 0.0
        },
        {
            "category": "Two or More Races (Non-Hispanic)",
            "population": int(non_hispanic_multirace),
            "percentage": float(non_hispanic_multirace * 100.0 / total_population) if total_population > 0 else 0.0
        },
        {
            "category": "American Indian and Alaska Native (Non-Hispanic)",
            "population": int(non_hispanic_native),
            "percentage": float(non_hispanic_native * 100.0 / total_population) if total_population > 0 else 0.0
        },
        {
            "category": "Native Hawaiian and Pacific Islander (Non-Hispanic)",
            "population": int(non_hispanic_pacific),
            "percentage": float(non_hispanic_pacific * 100.0 / total_population) if total_population > 0 else 0.0
        },
        {
            "category": "Some Other Race (Non-Hispanic)",
            "population": int(non_hispanic_other),
            "percentage": float(non_hispanic_other * 100.0 / total_population) if total_population > 0 else 0.0
        }
    ]
    
    # Filter out categories with 0 population and sort by population
    race_ethnicity_categories = [cat for cat in race_ethnicity_categories if cat["population"] > 0]
    race_ethnicity_categories.sort(key=lambda x: x["population"], reverse=True)
    
    # Also create detailed Hispanic breakdown
    hispanic_breakdown = []
    if hispanic_total > 0:
        hispanic_categories = [
            ("Hispanic White", hispanic_white),
            ("Hispanic Other Race", hispanic_other),
            ("Hispanic Two or More Races", hispanic_multirace),
            ("Hispanic Black", hispanic_black),
            ("Hispanic Asian", hispanic_asian),
            ("Hispanic American Indian", hispanic_native),
            ("Hispanic Pacific Islander", hispanic_pacific)
        ]
        
        for cat_name, count in hispanic_categories:
            if count > 0:
                hispanic_breakdown.append({
                    "category": cat_name,
                    "population": int(count),
                    "percentage": float(count * 100.0 / hispanic_total) if hispanic_total > 0 else 0.0
                })
    
    df = pd.DataFrame({
        "total_population": [total_population],
        "race_ethnicity_data": [race_ethnicity_categories],
        "hispanic_breakdown": [hispanic_breakdown]
    })
    
    return df


def get_distribution(lat: float, lon: float, year: int = 2023, force_tract: bool = False) -> dict:
    """
    Get race and ethnicity distribution for a location at block group level.
    Returns comprehensive race/ethnicity breakdown with Hispanic detail.
    """
    geo_info = get_geography(lat, lon)
    if not geo_info.get("state_fips"): 
        return {}

    df = get_race_ethnicity_data(
        state_fips=geo_info["state_fips"], 
        county_fips=geo_info["county_fips"],
        tract_fips=geo_info["tract_fips"], 
        block_group_fips=geo_info["block_group_fips"],
        year=year, 
        force_tract=force_tract
    )
    
    if df.empty:
        return {}

    race_ethnicity_data = df["race_ethnicity_data"].iloc[0]
    hispanic_breakdown = df["hispanic_breakdown"].iloc[0]
    total_population = df["total_population"].iloc[0]

    # Prepare main race/ethnicity distribution data
    main_data = []
    for category in race_ethnicity_data:
        main_data.append({
            "category": str(category["category"]),
            "value": int(category["population"]),
            "percentage": float(round(category["percentage"], 2))
        })

    # Prepare Hispanic breakdown data
    hispanic_data = []
    for category in hispanic_breakdown:
        hispanic_data.append({
            "category": str(category["category"]),
            "value": int(category["population"]),
            "percentage": float(round(category["percentage"], 2))
        })

    return {
        "data": main_data,
        "hispanic_breakdown": hispanic_data,
        "location": {
            "state_name": geo_info["state_name"],
            "county_name": geo_info["county_name"],
            "tract_name": geo_info["tract_name"],
            "block_group_name": geo_info["block_group_name"],
            "block_name": geo_info["block_name"],
            "block_geoid": geo_info["block_geoid"]
        },
        "data_source": f"Census ACS 5-Year Detailed Table B03002 ({year})",
        "total_population": int(total_population)
    }


if __name__ == "__main__":
    lat, lon = 37.736509, -122.388028  # San Francisco area

    print("=" * 60 + "\nRace & Ethnicity Distribution\n" + "=" * 60)

    distribution_data = get_distribution(lat, lon)
    
    if distribution_data:
        print(f"\nLocation: {distribution_data['location']}")
        print(f"Total Population: {distribution_data['total_population']:,}")
        print(f"Data Source: {distribution_data['data_source']}")
        
        print("\nMain Race/Ethnicity Breakdown:")
        for item in distribution_data['data']:
            print(f"  {item['category']}: {item['value']:,} ({item['percentage']:.1f}%)")
            
        if distribution_data['hispanic_breakdown']:
            print("\nHispanic/Latino Detailed Breakdown:")
            for item in distribution_data['hispanic_breakdown']:
                print(f"  {item['category']}: {item['value']:,} ({item['percentage']:.1f}%)")
    else:
        print("No data available")