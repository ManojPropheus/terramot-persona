"""
Income-Profession Distribution from Census Data
Uses B24011 table - Occupation by Median Earnings 
Returns median earnings by profession instead of count distributions.
"""

import os
import requests
import pandas as pd
import numpy as np

# Census API key
CENSUS_API_KEY = 'f5fddae34f7f6adf93a768ac2589c032d3e2e0cf'

# B24011 Variable mapping for main profession categories
B24011_PROFESSION_MAPPING = {
    'B24011_002E': 'Management, business, science, and arts occupations',
    'B24011_018E': 'Service occupations',
    'B24011_026E': 'Sales and office occupations',
    'B24011_029E': 'Natural resources, construction, and maintenance occupations',
    'B24011_033E': 'Production, transportation, and material moving occupations'
}


def get_geography(lat: float, lon: float) -> dict:
    """Get geographic information from coordinates."""
    url = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
    params = {
        "x": lon, "y": lat,
        "benchmark": "Public_AR_Census2020",
        "vintage": "Census2020_Census2020",
        "format": "json"
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
    
    tract_fips = tracts[0].get("TRACT") if tracts else None
    tract_name = tracts[0].get("NAME") if tracts else None
        
    if blocks:
        block = blocks[0]
        block_fips = block.get("BLOCK")
        block_name = block.get("NAME")
        block_geoid = block.get("GEOID")
        block_group_fips = block.get("BLKGRP")
        block_group_name = f"Block Group {block_group_fips}" if block_group_fips else None
    else:
        block_fips = block_name = block_geoid = block_group_fips = block_group_name = None

    return {
        "state_fips": state.get("STATE"), "state_name": state.get("NAME"),
        "county_fips": county.get("COUNTY"), "county_name": county.get("NAME"),
        "tract_fips": tract_fips, "tract_name": tract_name,
        "block_group_fips": block_group_fips, "block_group_name": block_group_name,
        "block_fips": block_fips, "block_name": block_name, "block_geoid": block_geoid
    }


def get_median_earnings_data(geo_info: dict, year: int = 2023, force_tract: bool = False) -> pd.DataFrame:
    """Get median earnings by occupation data from B24011."""
    base_url = f"https://api.census.gov/data/{year}/acs/acs5"
    
    # Get the specific variables we need
    variables = ",".join(["NAME"] + list(B24011_PROFESSION_MAPPING.keys()))
    params = {"get": variables}
    
    if CENSUS_API_KEY:
        params["key"] = CENSUS_API_KEY

    # Set geography - B24011 might not be available at block group level, try tract first
    if geo_info["tract_fips"] and not force_tract:
        geo_level = "Census Tract"
        params["for"] = f"tract:{geo_info['tract_fips']}"
        params["in"] = f"state:{geo_info['state_fips']} county:{geo_info['county_fips']}"
    else:
        geo_level = "County"
        params["for"] = f"county:{geo_info['county_fips']}"
        params["in"] = f"state:{geo_info['state_fips']}"

    print(f"Fetching Median Earnings by Occupation data (B24011) for {geo_level}...")
    
    try:
        resp = requests.get(base_url, params=params)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        print(f"API Request failed: {e}")
        return pd.DataFrame()

    if len(data) < 2:
        return pd.DataFrame()

    df = pd.DataFrame(data[1:], columns=data[0])
    
    # Process the data to extract median earnings by profession
    records = []
    for var_code, profession in B24011_PROFESSION_MAPPING.items():
        median_earnings = 0
        if var_code in df.columns:
            try:
                median_earnings = int(df[var_code].iloc[0])
                # Handle negative values (Census uses -666666666 for N/A)
                if median_earnings < 0:
                    median_earnings = 0
            except (ValueError, TypeError):
                median_earnings = 0
        
        records.append({
            "profession": profession,
            "median_earnings": median_earnings
        })
    
    result_df = pd.DataFrame(records)
    return result_df


def get_distribution(lat: float, lon: float, year: int = 2023, force_tract: bool = False) -> dict:
    """
    Get profession median earnings distribution for a location.
    Returns median earnings by profession instead of count distributions.
    """
    geo_info = get_geography(lat, lon)
    if not geo_info.get("state_fips"):
        return {}

    df = get_median_earnings_data(geo_info, year, force_tract)
    if df.empty:
        return {}

    # Filter out professions with no data (0 median earnings)
    df_filtered = df[df['median_earnings'] > 0].copy()
    
    if df_filtered.empty:
        return {}

    return {
        "type": "income_profession_median",
        "joint_data": [
            {
                "profession": row["profession"],
                "median_earnings": int(row["median_earnings"]),
                # For consistency with other distributions, we include these fields
                "value": int(row["median_earnings"]),  # Use median earnings as "value"
                "percentage": 0  # Not applicable for median earnings
            }
            for _, row in df_filtered.iterrows()
        ],
        "location": {
            "state_name": geo_info["state_name"],
            "county_name": geo_info["county_name"],
            "tract_name": geo_info["tract_name"],
            "block_group_name": geo_info["block_group_name"],
            "block_name": geo_info["block_name"],
            "block_geoid": geo_info["block_geoid"]
        },
        "data_source": "Census ACS Detailed Table B24011",
        "note": "Values represent median earnings in dollars, not population counts"
    }


def get_conditional_distribution(joint_data: dict, condition_type: str, condition_value: str) -> dict:
    """
    Get conditional distribution for median earnings data.
    Since this is median earnings by profession, conditional analysis returns individual profession data.
    """
    if not joint_data or "joint_data" not in joint_data:
        return {"error": "No joint distribution data available"}
    
    if condition_type == "profession":
        # Find the specific profession
        for item in joint_data["joint_data"]:
            if item["profession"] == condition_value:
                return {
                    "type": "median_earnings_for_profession",
                    "condition": f"Profession = {condition_value}",
                    "data": [{
                        "category": f"Median Earnings - {condition_value}",
                        "value": item["median_earnings"],
                        "median_earnings": item["median_earnings"],
                        "percentage": 100.0  # 100% since it's a single value
                    }],
                    "total_population": 1,  # Not applicable but needed for frontend
                    "data_source": joint_data["data_source"],
                    "note": "Median earnings in dollars for this profession"
                }
        
        return {"error": f"No data found for profession: {condition_value}"}
    
    elif condition_type == "income":
        # For income conditioning, return all professions (since we can't filter by income ranges on median data)
        return {
            "type": "all_professions_median_earnings",
            "condition": f"All professions (income condition not applicable for median data)",
            "data": [
                {
                    "category": item["profession"],
                    "value": item["median_earnings"],
                    "median_earnings": item["median_earnings"],
                    "percentage": 0  # Not applicable for median earnings
                }
                for item in joint_data["joint_data"]
            ],
            "total_population": len(joint_data["joint_data"]),
            "data_source": joint_data["data_source"],
            "note": "Median earnings in dollars by profession"
        }
    
    else:
        return {"error": f"Invalid condition_type: {condition_type}. Must be 'profession' or 'income'"}


if __name__ == "__main__":
    # Test the function
    lat, lon = 37.736509, -122.388028  # San Francisco area
    
    print("=" * 60)
    print("INCOME-PROFESSION MEDIAN EARNINGS TEST")
    print("=" * 60)
    
    result = get_distribution(lat, lon)
    
    if result:
        location = result['location']
        location_name = location.get("county_name")
        state_name = location.get("state_name")
        
        print(f"\nLocation: {location_name}, {state_name}")
        print(f"Data Source: {result['data_source']}")
        print(f"Note: {result['note']}")
        
        print(f"\nMedian Earnings by Profession:")
        for item in result['joint_data']:
            print(f"  {item['profession']}: ${item['median_earnings']:,}")
        
        # Test conditional distribution
        print(f"\n" + "=" * 60)
        print("CONDITIONAL DISTRIBUTION TEST")
        print("=" * 60)
        
        if result['joint_data']:
            test_profession = result['joint_data'][0]['profession']
            conditional_result = get_conditional_distribution(result, 'profession', test_profession)
            
            if 'error' not in conditional_result:
                print(f"\nConditional result for {test_profession}:")
                for item in conditional_result['data']:
                    print(f"  {item['category']}: ${item['median_earnings']:,}")
            else:
                print(f"Error: {conditional_result['error']}")
    else:
        print("Could not retrieve data for the specified location.")