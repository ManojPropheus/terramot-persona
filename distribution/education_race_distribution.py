"""
Education-Race Distribution from Census Data
Uses C15002A-I series - Sex by Educational Attainment by Race/Ethnicity
Provides education x race cross-tabulation with sex breakdown included
"""

import os
import requests
import pandas as pd
import numpy as np

CENSUS_API_KEY = 'f5fddae34f7f6adf93a768ac2589c032d3e2e0cf'

# Race mapping for C15002A-I tables
RACE_TABLE_MAPPING = {
    'C15002A': 'White Alone',
    'C15002B': 'Black or African American Alone',
    'C15002C': 'American Indian and Alaska Native Alone',
    'C15002D': 'Asian Alone',
    'C15002E': 'Native Hawaiian and Other Pacific Islander Alone',
    'C15002F': 'Some Other Race Alone',
    'C15002G': 'Two or More Races',
    'C15002H': 'Hispanic or Latino',
    'C15002I': 'White Alone, Not Hispanic or Latino'
}

# Education level mapping for C15002 variables (same structure across A-I)
EDUCATION_MAPPING = {
    # Male education levels (002-009)
    'C15002_002E': 'Less than high school',  # Male: Less than 9th grade + 9th to 12th grade, no diploma
    'C15002_003E': 'Less than high school',  # Male: Less than 9th grade
    'C15002_004E': 'Less than high school',  # Male: 9th to 12th grade, no diploma
    'C15002_005E': 'High school graduate',  # Male: High school graduate (includes equivalency)
    'C15002_006E': 'Some college',  # Male: Some college, no degree
    'C15002_007E': 'Associate degree',  # Male: Associate’s degree
    'C15002_008E': 'Bachelor\'s degree',  # Male: Bachelor’s degree
    'C15002_009E': 'Graduate degree',  # Male: Graduate or professional degree

    # Female education levels (011-018)
    'C15002_011E': 'Less than high school',  # Female: Less than 9th grade + 9th to 12th grade, no diploma
    'C15002_012E': 'Less than high school',  # Female: Less than 9th grade
    'C15002_013E': 'Less than high school',  # Female: 9th to 12th grade, no diploma
    'C15002_014E': 'High school graduate',  # Female: High school graduate (includes equivalency)
    'C15002_015E': 'Some college',  # Female: Some college, no degree
    'C15002_016E': 'Associate degree',  # Female: Associate’s degree
    'C15002_017E': 'Bachelor\'s degree',  # Female: Bachelor’s degree
    'C15002_018E': 'Graduate degree'  # Female: Graduate or professional degree
}

# Standard education categories for output
STANDARD_EDUCATION_CATEGORIES = [
    'Less than high school',
    'High school graduate', 
    'Some college',
    'Associate degree',
    'Bachelor\'s degree',
    'Graduate degree'
]


def get_geography(lat: float, lon: float) -> dict:
    """Get geographic information from coordinates."""
    url = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
    params = {"x": lon, "y": lat, "benchmark": "Public_AR_Census2020", "vintage": "Census2020_Census2020", "format": "json"}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    geogs = resp.json()["result"]["geographies"]

    state = geogs["States"][0]
    county = geogs["Counties"][0]
    tracts = geogs.get("Census Tracts", [])
    blocks = geogs.get("Census Blocks", [])
    
    tract_fips = tracts[0]["TRACT"] if tracts else None
    tract_name = tracts[0]["NAME"] if tracts else None
        
    if blocks:
        block = blocks[0]
        block_fips, block_name, block_geoid = block["BLOCK"], block["NAME"], block["GEOID"]
        block_group_fips = block.get("BLKGRP")
        block_group_name = f"Block Group {block_group_fips}" if block_group_fips else None
    else:
        block_fips = block_name = block_geoid = block_group_fips = block_group_name = None

    return {
        "state_fips": state["STATE"], "state_name": state["NAME"],
        "county_fips": county["COUNTY"], "county_name": county["NAME"],
        "tract_fips": tract_fips, "tract_name": tract_name,
        "block_group_fips": block_group_fips, "block_group_name": block_group_name,
        "block_fips": block_fips, "block_name": block_name, "block_geoid": block_geoid
    }


def get_education_race_data(geo_info: dict, year: int = 2023, force_tract: bool = False) -> pd.DataFrame:
    """Get education-race data from C15002A-I tables."""
    base_url = f"https://api.census.gov/data/{year}/acs/acs5"
    
    # Set geography - start with tract level as C15002 detailed tables may not be available at block group level
    if geo_info["tract_fips"] and not force_tract:
        geo_level = "Census Tract"
        geo_params = {"for": f"tract:{geo_info['tract_fips']}", 
                     "in": f"state:{geo_info['state_fips']} county:{geo_info['county_fips']}"}
    else:
        geo_level = "County"
        geo_params = {"for": f"county:{geo_info['county_fips']}", 
                     "in": f"state:{geo_info['state_fips']}"}

    print(f"Fetching Education-Race data from C15002A-I tables for {geo_level}...")
    
    records = []
    
    # Fetch data for each race table
    for table_code, race_name in RACE_TABLE_MAPPING.items():
        try:
            params = {"get": f"NAME,group({table_code})", "key": CENSUS_API_KEY}
            params.update(geo_params)
            
            resp = requests.get(base_url, params=params)
            resp.raise_for_status()
            data = resp.json()
            
            if len(data) < 2:
                continue
                
            df = pd.DataFrame(data[1:], columns=data[0])
            
            # Process education variables for this race
            education_totals = {}
            
            for var_code, education_level in EDUCATION_MAPPING.items():
                # Replace C15002_ with the race-specific table code
                race_var = var_code.replace('C15002_', f'{table_code}_')
                
                if race_var in df.columns:
                    try:
                        value = int(df[race_var].iloc[0])
                        if value < 0:  # Handle Census negative values (N/A)
                            value = 0
                        
                        if education_level in education_totals:
                            education_totals[education_level] += value
                        else:
                            education_totals[education_level] = value
                    except (ValueError, TypeError):
                        pass
            
            # Add records for this race
            for education_level, population in education_totals.items():
                if population > 0:  # Only include non-zero populations
                    records.append({
                        'race': race_name,
                        'education_level': education_level, 
                        'population': population
                    })
                    
        except Exception as e:
            print(f"Error fetching data for {table_code} ({race_name}): {e}")
            continue
    
    result_df = pd.DataFrame(records)
    return result_df


def get_distribution(lat: float, lon: float, year: int = 2023, force_tract: bool = False) -> dict:
    """Get education-race joint distribution."""
    geo_info = get_geography(lat, lon)
    if not geo_info.get("state_fips"): 
        return {}

    df = get_education_race_data(geo_info, year, force_tract)
    if df.empty:
        return {}

    # Calculate total population
    total_population = df['population'].sum()
    
    # Add percentages
    df['percentage'] = (df['population'] / total_population) * 100

    # Calculate marginal distributions
    education_marginal = df.groupby('education_level')['population'].sum().reset_index()
    race_marginal = df.groupby('race')['population'].sum().reset_index()
    
    # Sort education levels in standard order
    education_marginal['sort_order'] = education_marginal['education_level'].map(
        {level: i for i, level in enumerate(STANDARD_EDUCATION_CATEGORIES)}
    )
    education_marginal = education_marginal.sort_values('sort_order').drop('sort_order', axis=1)
    
    # Add percentages to marginals
    education_marginal['percentage'] = (education_marginal['population'] / total_population) * 100
    race_marginal['percentage'] = (race_marginal['population'] / total_population) * 100

    return {
        "type": "education_race",
        "joint_data": [
            {
                "race": row["race"],
                "education_level": row["education_level"], 
                "value": int(row["population"]),
                "percentage": float(row["percentage"])
            }
            for _, row in df.iterrows()
        ],
        "education_marginal": [
            {
                "category": row["education_level"],
                "value": int(row["population"]),
                "percentage": float(row["percentage"])
            }
            for _, row in education_marginal.iterrows()
        ],
        "race_marginal": [
            {
                "category": row["race"],
                "value": int(row["population"]),
                "percentage": float(row["percentage"])
            }
            for _, row in race_marginal.iterrows()
        ],
        "location": {
            "state_name": geo_info["state_name"],
            "county_name": geo_info["county_name"],
            "tract_name": geo_info["tract_name"],
            "block_group_name": geo_info["block_group_name"],
            "block_name": geo_info["block_name"],
            "block_geoid": geo_info["block_geoid"]
        },
        "data_source": "Census ACS Detailed Tables C15002A-I"
    }


def get_conditional_distribution(joint_data: dict, condition_type: str, condition_value: str) -> dict:
    """Get conditional distribution from joint education-race data."""
    if not joint_data or "joint_data" not in joint_data:
        return {"error": "No joint distribution data available"}
    
    joint_df = pd.DataFrame(joint_data["joint_data"])
    
    if condition_type == "education":
        # Filter by education level, return race distribution
        filtered_data = joint_df[joint_df["education_level"] == condition_value]
        if filtered_data.empty:
            return {"error": f"No data found for education level: {condition_value}"}
        
        total = filtered_data["value"].sum()
        result_data = []
        for _, row in filtered_data.iterrows():
            percentage = (row["value"] * 100.0 / total) if total > 0 else 0
            result_data.append({
                "category": row["race"],
                "value": int(row["value"]),
                "percentage": float(percentage)
            })
        
        return {
            "type": "conditional_race_given_education",
            "condition": f"Education = {condition_value}",
            "data": result_data,
            "total_population": int(total),
            "data_source": joint_data["data_source"]
        }
    
    elif condition_type == "race":
        # Filter by race, return education distribution
        filtered_data = joint_df[joint_df["race"] == condition_value]
        if filtered_data.empty:
            return {"error": f"No data found for race: {condition_value}"}
        
        total = filtered_data["value"].sum()
        result_data = []
        for _, row in filtered_data.iterrows():
            percentage = (row["value"] * 100.0 / total) if total > 0 else 0
            result_data.append({
                "category": row["education_level"],
                "value": int(row["value"]),
                "percentage": float(percentage)
            })
        
        return {
            "type": "conditional_education_given_race",
            "condition": f"Race = {condition_value}",
            "data": result_data,
            "total_population": int(total),
            "data_source": joint_data["data_source"]
        }
    
    else:
        return {"error": f"Invalid condition_type: {condition_type}. Must be 'education' or 'race'"}


if __name__ == "__main__":
    # Test the function
    lat, lon = 37.736509, -122.388028  # San Francisco area
    
    print("=" * 60)
    print("EDUCATION-RACE DISTRIBUTION TEST (C15002A-I)")
    print("=" * 60)
    
    result = get_distribution(lat, lon)
    
    if result:
        location = result['location']
        location_name = location.get("county_name")
        state_name = location.get("state_name")
        
        print(f"\nLocation: {location_name}, {state_name}")
        print(f"Data Source: {result['data_source']}")
        
        print(f"\nJoint Distribution Sample (first 10):")
        for i, item in enumerate(result['joint_data'][:10]):
            print(f"  {item['race']} × {item['education_level']}: {item['value']:,} people ({item['percentage']:.1f}%)")
        
        print(f"\nEducation Marginals:")
        for item in result['education_marginal']:
            print(f"  {item['category']}: {item['value']:,} people ({item['percentage']:.1f}%)")
        
        print(f"\nRace Marginals:")
        for item in result['race_marginal']:
            print(f"  {item['category']}: {item['value']:,} people ({item['percentage']:.1f}%)")
        
        # Test conditional distribution
        print(f"\n" + "=" * 60)
        print("CONDITIONAL DISTRIBUTION TEST")
        print("=" * 60)
        
        if result['joint_data']:
            test_education = result['joint_data'][0]['education_level']
            conditional_result = get_conditional_distribution(result, 'education', test_education)
            
            if 'error' not in conditional_result:
                print(f"\nRace distribution for {test_education}:")
                for item in conditional_result['data']:
                    print(f"  {item['category']}: {item['value']:,} people ({item['percentage']:.1f}%)")
            else:
                print(f"Error: {conditional_result['error']}")
    else:
        print("Could not retrieve data for the specified location.")