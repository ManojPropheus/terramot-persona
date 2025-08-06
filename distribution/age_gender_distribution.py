"""
Age & Gender Joint Distribution from Census Data
Fetches joint distribution from Census Table B01001 and provides conditional distributions.
Allows conditioning on either age or gender to view corresponding distributions.
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


def get_age_gender_data(state_fips: str, county_fips: str, tract_fips: str = None,
                        block_group_fips: str = None, year: int = 2023, force_tract: bool = False) -> pd.DataFrame:
    """
    Fetches joint age-gender distribution from Census ACS Table B01001 at block group level.
    """
    base_url = f"https://api.census.gov/data/{year}/acs/acs5"
    params = {"get": "NAME,group(B01001)"}

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

    print(f"Fetching Age/Gender data for {geo_level}...")
    try:
        resp = requests.get(base_url, params=params)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        print(f"API Request failed: {e}")
        return pd.DataFrame()

    if len(data) < 2: return pd.DataFrame()

    df_full = pd.DataFrame([data[1]], columns=data[0])

    # Import standard age mapping for consistency across all distributions
    try:
        from .standard_categories import B01001_AGE_MAPPING
    except ImportError:
        from standard_categories import B01001_AGE_MAPPING
    
    # Convert standard age mapping to the male/female format needed for this distribution
    age_groups_mapping = []
    for age_range, var_codes in B01001_AGE_MAPPING.items():
        # Separate male and female codes based on B01001 structure
        # Male codes: 003-025, Female codes: 027-049
        male_codes = [f"B01001_{code}E" for code in var_codes if int(code) <= 25]
        female_codes = [f"B01001_{code}E" for code in var_codes if int(code) >= 27]
        
        age_groups_mapping.append((age_range, {"male": male_codes, "female": female_codes}))
    
    # Get total population for calculating percentages
    total_population = int(df_full["B01001_001E"].iloc[0])
    
    # Process joint distribution data
    joint_data = []
    age_marginal = []
    gender_marginal = {"Male": 0, "Female": 0}
    
    for age_group, gender_codes in age_groups_mapping:
        male_pop = 0
        female_pop = 0
        
        # Sum male populations for this age group
        for var_code in gender_codes["male"]:
            if var_code in df_full.columns:
                try:
                    male_pop += int(df_full[var_code].iloc[0])
                except (ValueError, TypeError):
                    pass
        
        # Sum female populations for this age group
        for var_code in gender_codes["female"]:
            if var_code in df_full.columns:
                try:
                    female_pop += int(df_full[var_code].iloc[0])
                except (ValueError, TypeError):
                    pass
        
        total_age_pop = male_pop + female_pop
        
        # Add to joint distribution data
        joint_data.extend([
            {
                "age": age_group,
                "gender": "Male",
                "population": male_pop,
                "percentage": (male_pop * 100.0 / total_population) if total_population > 0 else 0
            },
            {
                "age": age_group,
                "gender": "Female", 
                "population": female_pop,
                "percentage": (female_pop * 100.0 / total_population) if total_population > 0 else 0
            }
        ])
        
        # Add to age marginal
        age_marginal.append({
            "category": age_group,
            "value": total_age_pop,
            "percentage": (total_age_pop * 100.0 / total_population) if total_population > 0 else 0
        })
        
        # Add to gender totals
        gender_marginal["Male"] += male_pop
        gender_marginal["Female"] += female_pop
    
    # Create gender marginal distribution
    gender_marginal_data = [
        {
            "category": "Male",
            "value": gender_marginal["Male"],
            "percentage": (gender_marginal["Male"] * 100.0 / total_population) if total_population > 0 else 0
        },
        {
            "category": "Female",
            "value": gender_marginal["Female"],
            "percentage": (gender_marginal["Female"] * 100.0 / total_population) if total_population > 0 else 0
        }
    ]
    
    # Return structured data
    result_data = {
        "joint_data": joint_data,
        "age_marginal": age_marginal,
        "gender_marginal": gender_marginal_data,
        "total_population": total_population
    }
    
    return pd.DataFrame([result_data])


def get_distribution(lat: float, lon: float, year: int = 2023, force_tract: bool = False) -> dict:
    """
    Get joint age-gender distribution for a location at block group level.
    Returns both marginal distributions and joint distribution data.
    """
    geo_info = get_geography(lat, lon)
    if not geo_info.get("state_fips"): return {}

    df = get_age_gender_data(
        state_fips=geo_info["state_fips"], 
        county_fips=geo_info["county_fips"],
        tract_fips=geo_info["tract_fips"], 
        block_group_fips=geo_info["block_group_fips"], 
        year=year, 
        force_tract=force_tract
    )

    if df.empty: return {}

    # Extract the structured data from the returned DataFrame
    result_data = df.iloc[0]
    joint_data = result_data["joint_data"]
    age_marginal = result_data["age_marginal"]
    gender_marginal = result_data["gender_marginal"]
    total_population = result_data["total_population"]

    # Create initial distribution data with consistent field names
    initial_data = {
        "type": "age_gender_joint",
        "joint_data": [
            {
                "age_range": item["age"],  # Standardize to age_range
                "gender": item["gender"],
                "population": int(item["population"]),
                "percentage": float(item["percentage"])
            }
            for item in joint_data
        ],
        "age_marginal": [
            {
                "category": item["category"],
                "value": int(item["value"]),
                "percentage": float(item["percentage"])
            }
            for item in age_marginal
        ],
        "gender_marginal": [
            {
                "category": item["category"],
                "value": int(item["value"]),
                "percentage": float(item["percentage"])
            }
            for item in gender_marginal
        ],
        "location": {
            "state_name": geo_info["state_name"],
            "county_name": geo_info["county_name"],
            "tract_name": geo_info["tract_name"],
            "block_group_name": geo_info["block_group_name"],
            "block_name": geo_info["block_name"],
            "block_geoid": geo_info["block_geoid"]
        },
        "data_source": "Census ACS Detailed Table B01001",
        "total_population": int(total_population)
    }
    
    return initial_data


def get_conditional_distribution(joint_data: dict, condition_type: str, condition_value: str) -> dict:
    """
    Get conditional distribution from joint data.
    
    Args:
        joint_data: Result from get_distribution()
        condition_type: 'age' or 'gender' - what to condition on
        condition_value: The specific age range or gender to condition on
        
    Returns:
        Conditional distribution data
    """
    if condition_type not in ['age', 'gender']:
        raise ValueError("condition_type must be 'age' or 'gender'")
    
    joint_df = pd.DataFrame(joint_data['joint_data'])
    
    if condition_type == 'age':
        # Given age range, return gender distribution
        filtered_data = joint_df[joint_df['age_range'] == condition_value]
        if filtered_data.empty:
            return {"error": f"No data found for age range: {condition_value}"}
        
        total_population = filtered_data['population'].sum()
        
        result = [
            {
                "category": row["gender"],
                "value": int(row["population"]),
                "percentage": float((row["population"] / total_population) * 100) if total_population > 0 else 0
            }
            for _, row in filtered_data.iterrows()
        ]
        
        return {
            "type": "conditional_gender_given_age",
            "condition": f"Age: {condition_value}",
            "data": result,
            "total_population": int(total_population),
            "data_source": joint_data["data_source"]
        }
    
    else:  # condition_type == 'gender'
        # Given gender, return age distribution
        filtered_data = joint_df[joint_df['gender'] == condition_value]
        if filtered_data.empty:
            return {"error": f"No data found for gender: {condition_value}"}
        
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
            "type": "conditional_age_given_gender",
            "condition": f"Gender: {condition_value}",
            "data": result,
            "total_population": int(total_population),
            "data_source": joint_data["data_source"]
        }


if __name__ == "__main__":
    lat, lon = 37.736509, -122.388028  # San Francisco area

    print("=" * 60 + "\nAGE-GENDER JOINT DISTRIBUTION\n" + "=" * 60)
    
    joint_data = get_distribution(lat, lon)

    if joint_data:
        location = joint_data['location']
        location_name = location.get("block_group_name") or location.get("tract_name") or location.get("county_name")
        state_name = location.get("state_name")
        
        print(f"\nLocation: {location_name}, {state_name}")
        print(f"Data Source: {joint_data['data_source']}")
        
        # Show summary stats
        total_population = joint_data['total_population']
        print(f"Total Population: {total_population:,}")
        
        print(f"\nAge Ranges Available:")
        for item in joint_data['age_marginal']:
            print(f"  {item['category']}: {item['value']:,} people ({item['percentage']:.1f}%)")
        
        print(f"\nGender Distribution:")
        for item in joint_data['gender_marginal']:
            print(f"  {item['category']}: {item['value']:,} people ({item['percentage']:.1f}%)")
        
        # Example conditional distributions
        print(f"\n" + "=" * 60)
        print("EXAMPLE CONDITIONAL DISTRIBUTIONS")
        print("=" * 60)
        
        # Condition on age
        age_condition = "25 to 34 years"  # Use the age groups from our mapping
        print(f"\nGender distribution for people aged {age_condition}:")
        conditional_gender = get_conditional_distribution(joint_data, 'age', age_condition)
        if 'error' not in conditional_gender:
            for item in conditional_gender['data']:
                print(f"  {item['category']}: {item['value']:,} people ({item['percentage']:.1f}%)")
        else:
            print(f"  {conditional_gender['error']}")
        
        # Condition on gender
        gender_condition = "Female"
        print(f"\nAge distribution for {gender_condition}s:")
        conditional_age = get_conditional_distribution(joint_data, 'gender', gender_condition)
        if 'error' not in conditional_age:
            for item in conditional_age['data'][:5]:  # Show first 5 age groups
                print(f"  {item['category']}: {item['value']:,} people ({item['percentage']:.1f}%)")
        else:
            print(f"  {conditional_age['error']}")
    else:
        print("Could not retrieve data for the specified location.")