"""
Age & Race Joint Distribution from Census Data
Fetches joint distribution from Census Table B01001A-I series and provides conditional distributions.
Allows conditioning on either age or race to view corresponding distributions.
"""

import os
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

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


def get_age_race_data(state_fips: str, county_fips: str, tract_fips: str = None,
                        block_group_fips: str = None, year: int = 2023, force_tract: bool = False) -> pd.DataFrame:
    """
    Fetches joint age-race distribution from Census ACS Table B01001 series (A-I).
    """
    base_url = f"https://api.census.gov/data/{year}/acs/acs5"
    
    # Race/ethnicity table suffixes and their meanings
    race_tables = {
        "B01001A": "White Alone",
        "B01001B": "Black or African American Alone", 
        "B01001C": "American Indian and Alaska Native Alone",
        "B01001D": "Asian Alone",
        "B01001E": "Native Hawaiian and Other Pacific Islander Alone",
        "B01001F": "Some Other Race Alone",
        "B01001G": "Two or More Races",
        "B01001I": "Hispanic or Latino"
    }

    if CENSUS_API_KEY:
        key_param = f"&key={CENSUS_API_KEY}"
    else:
        key_param = ""

    geo_level, geo_in = ("County", f"state:{state_fips}")

    if block_group_fips and tract_fips and not force_tract:
        geo_level = "Block Group"
        geo_for = f"block group:{block_group_fips}"
        geo_in = f"state:{state_fips} county:{county_fips} tract:{tract_fips}"
    elif tract_fips:
        geo_level = "Census Tract"
        geo_for = f"tract:{tract_fips}"
        geo_in = f"state:{state_fips} county:{county_fips}"
    else:
        geo_level = "County"
        geo_for = f"county:{county_fips}"
        geo_in = f"state:{state_fips}"

    print(f"Fetching Age/Race data for {geo_level}...")

    # Age ranges (simplified to broader categories for better data availability)
    age_ranges = [
        'Under 5 years', '5 to 9 years', '10 to 14 years', '15 to 17 years',
        '18 and 19 years', '20 to 24 years', '25 to 29 years', '30 to 34 years',
        '35 to 44 years', '45 to 54 years', '55 to 64 years', '65 to 74 years',
        '75 to 84 years', '85 years and over'
    ]

    # Variable mapping for age groups - B01001 series includes both male and female for each age group
    # Format: {table_prefix}_003E = Male under 5, {table_prefix}_027E = Female under 5, etc.
    age_var_mapping = {
        'Under 5 years': ['003', '027'],  # Male + Female under 5
        '5 to 9 years': ['004', '028'],   # Male + Female 5-9
        '10 to 14 years': ['005', '029'], # Male + Female 10-14
        '15 to 17 years': ['006', '030'], # Male + Female 15-17
        '18 and 19 years': ['007', '031'], # Male + Female 18-19
        '20 to 24 years': ['008', '009', '010', '032', '033', '034'],  # Male 20, 21, 22-24 + Female 20, 21, 22-24
        '25 to 29 years': ['011', '035'], # Male + Female 25-29
        '30 to 34 years': ['012', '036'], # Male + Female 30-34
        '35 to 44 years': ['013', '014', '037', '038'],  # Male 35-39, 40-44 + Female 35-39, 40-44
        '45 to 54 years': ['015', '016', '039', '040'],  # Male 45-49, 50-54 + Female 45-49, 50-54
        '55 to 64 years': ['017', '018', '019', '041', '042', '043'],  # Male 55-59, 60-61, 62-64 + Female 55-59, 60-61, 62-64
        '65 to 74 years': ['020', '021', '022', '044', '045', '046'],  # Male 65-66, 67-69, 70-74 + Female 65-66, 67-69, 70-74
        '75 to 84 years': ['023', '024', '047', '048'],  # Male 75-79, 80-84 + Female 75-79, 80-84
        '85 years and over': ['025', '049']  # Male + Female 85+
    }

    all_records = []
    
    for table_code, race_name in race_tables.items():
        try:
            # Get all variables for this race table
            params = {"get": f"NAME,group({table_code})"}
            if CENSUS_API_KEY:
                params["key"] = CENSUS_API_KEY
            params["for"] = geo_for
            params["in"] = geo_in

            resp = requests.get(base_url, params=params)
            resp.raise_for_status()
            data = resp.json()
            
            if len(data) < 2:
                continue
                
            df_race = pd.DataFrame(data[1:], columns=data[0])
            
            # Process each age range for this race
            for age_range in age_ranges:
                var_codes = age_var_mapping[age_range]
                total_count = 0
                
                for var_code in var_codes:
                    var_name = f"{table_code}_{var_code}E"
                    if var_name in df_race.columns:
                        try:
                            count = int(float(df_race[var_name].iloc[0]))
                            total_count += count
                        except (ValueError, TypeError):
                            pass
                
                all_records.append({
                    "age_range": age_range,
                    "race_ethnicity": race_name,
                    "population": total_count
                })
        
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch data for {table_code}: {e}")
            continue

    return pd.DataFrame(all_records)


def get_distribution(lat: float, lon: float, year: int = 2023, force_tract: bool = False) -> dict:
    """
    Get joint age-race distribution for a location.
    Returns both marginal distributions and joint distribution data.
    """
    geo_info = get_geography(lat, lon)
    if not geo_info.get("state_fips"): return {}

    df = get_age_race_data(
        state_fips=geo_info["state_fips"],
        county_fips=geo_info["county_fips"],
        tract_fips=geo_info["tract_fips"],
        block_group_fips=geo_info["block_group_fips"],
        year=year,
        force_tract=True
    )

    if df.empty: return {}

    # Calculate marginal distributions with proper ordering
    age_marginal = df.groupby('age_range')['population'].sum().reset_index()
    race_marginal = df.groupby('race_ethnicity')['population'].sum().reset_index()
    
    # Sort marginals in ascending order
    age_order = ['Under 5 years', '5 to 9 years', '10 to 14 years', '15 to 17 years',
                 '18 and 19 years', '20 to 24 years', '25 to 29 years', '30 to 34 years',
                 '35 to 44 years', '45 to 54 years', '55 to 64 years', '65 to 74 years',
                 '75 to 84 years', '85 years and over']
    race_order = ["White Alone", "Black or African American Alone", "American Indian and Alaska Native Alone", 
                  "Asian Alone", "Native Hawaiian and Other Pacific Islander Alone", "Some Other Race Alone", 
                  "Two or More Races", "Hispanic or Latino"]
    
    age_marginal['sort_order'] = age_marginal['age_range'].map({v: i for i, v in enumerate(age_order)})
    age_marginal = age_marginal.sort_values('sort_order').drop('sort_order', axis=1)
    
    race_marginal['sort_order'] = race_marginal['race_ethnicity'].map({v: i for i, v in enumerate(race_order)})
    race_marginal = race_marginal.sort_values('sort_order').drop('sort_order', axis=1)
    
    total_population = df['population'].sum()
    
    if total_population == 0:
        return {}
    
    # Add percentages
    age_marginal['percentage'] = (age_marginal['population'] / total_population) * 100
    race_marginal['percentage'] = (race_marginal['population'] / total_population) * 100

    # Create initial distribution data
    initial_data = {
        "type": "age_race_joint",
        "joint_data": [
            {
                "age_range": row["age_range"],
                "race_ethnicity": row["race_ethnicity"],
                "population": int(row["population"]),
                "percentage": float((row["population"] / total_population) * 100)
            }
            for _, row in df.iterrows() if row["population"] > 0
        ],
        "age_marginal": [
            {
                "category": row["age_range"],
                "value": int(row["population"]),
                "percentage": float(row["percentage"])
            }
            for _, row in age_marginal.iterrows()
        ],
        "race_marginal": [
            {
                "category": row["race_ethnicity"],
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
        "data_source": "Census ACS Detailed Tables B01001A-I series"
    }
    
    return initial_data


def get_conditional_distribution(joint_data: dict, condition_type: str, condition_value: str) -> dict:
    """
    Get conditional distribution from joint data with unified age bracket support.
    
    Args:
        joint_data: Result from get_distribution()
        condition_type: 'age' or 'race' - what to condition on
        condition_value: The specific age range or race/ethnicity to condition on
        
    Returns:
        Conditional distribution data
    """
    if condition_type not in ['age', 'race']:
        raise ValueError("condition_type must be 'age' or 'race'")
    
    joint_df = pd.DataFrame(joint_data['joint_data'])
    
    if condition_type == 'age':
        # Given age range, return race distribution
        filtered_data = joint_df[joint_df['age_range'] == condition_value]
        if filtered_data.empty:
            return {"error": f"No data found for age range: {condition_value}"}
        
        total_population = filtered_data['population'].sum()
        
        result = [
            {
                "category": row["race_ethnicity"],
                "value": int(row["population"]),
                "percentage": float((row["population"] / total_population) * 100) if total_population > 0 else 0
            }
            for _, row in filtered_data.iterrows()
        ]
        
        return {
            "type": "conditional_race_given_age",
            "condition": f"Age: {condition_value}",
            "data": result,
            "total_population": int(total_population),
            "data_source": joint_data["data_source"]
        }
    
    else:  # condition_type == 'race'
        # Given race, return age distribution
        filtered_data = joint_df[joint_df['race_ethnicity'] == condition_value]
        if filtered_data.empty:
            return {"error": f"No data found for race/ethnicity: {condition_value}"}
        
        total_population = filtered_data['population'].sum()
        
        result = [
            {
                "category": row["age_range"],
                "value": int(row["population"]),
                "percentage": float((row["population"] / total_population) * 100) if total_population > 0 else 0
            }
            for _, row in filtered_data.iterrows()
        ]
        
        return {
            "type": "conditional_age_given_race",
            "condition": f"Race/Ethnicity: {condition_value}",
            "data": result,
            "total_population": int(total_population),
            "data_source": joint_data["data_source"]
        }


if __name__ == "__main__":
    lat, lon = 37.736509, -122.388028  # San Francisco area

    print("=" * 60 + "\nAGE-RACE JOINT DISTRIBUTION\n" + "=" * 60)
    
    joint_data = get_distribution(lat, lon)

    if joint_data:
        location = joint_data['location']
        location_name = location.get("subdivision_name") or location.get("county_name")
        state_name = location.get("state_name")
        
        print(f"\nLocation: {location_name}, {state_name}")
        print(f"Data Source: {joint_data['data_source']}")
        
        # Show summary stats
        total_population = sum(item['population'] for item in joint_data['joint_data'])
        print(f"Total Population: {total_population:,}")
        
        print(f"\nRace/Ethnicity Distribution:")
        for item in joint_data['race_marginal']:
            print(f"  {item['category']}: {item['value']:,} people ({item['percentage']:.1f}%)")
        
        # Example conditional distributions
        print(f"\n" + "=" * 60)
        print("EXAMPLE CONDITIONAL DISTRIBUTIONS")
        print("=" * 60)
        
        # Condition on age
        age_condition = "25 to 29 years"
        print(f"\nRace/Ethnicity distribution for people aged {age_condition}:")
        conditional_race = get_conditional_distribution(joint_data, 'age', age_condition)
        if 'error' not in conditional_race:
            for item in conditional_race['data']:
                if item['value'] > 0:
                    print(f"  {item['category']}: {item['value']:,} people ({item['percentage']:.1f}%)")
        
        # Condition on race
        race_condition = "White Alone"
        print(f"\nAge distribution for {race_condition}:")
        conditional_age = get_conditional_distribution(joint_data, 'race', race_condition)
        if 'error' not in conditional_age:
            for item in conditional_age['data'][:5]:  # Show first 5 age groups
                if item['value'] > 0:
                    print(f"  {item['category']}: {item['value']:,} people ({item['percentage']:.1f}%)")
    else:
        print("Could not retrieve data for the specified location.")