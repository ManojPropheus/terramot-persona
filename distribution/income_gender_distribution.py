"""
Income & Gender Joint Distribution from Census Data
Fetches joint distribution from Census Table B20002 (Median Earnings by Sex) and provides conditional distributions.
Allows conditioning on either income or gender to view corresponding distributions.
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


def get_income_gender_data(state_fips: str, county_fips: str, tract_fips: str = None,
                          block_group_fips: str = None, year: int = 2023, force_tract: bool = False) -> pd.DataFrame:
    """
    Fetches joint income-gender distribution from Census ACS Table B20005 (Sex by Work Experience by Earnings) at block group level.
    """
    base_url = f"https://api.census.gov/data/{year}/acs/acs5"
    table_to_get = "B20005"
    params = {"get": f"NAME,group({table_to_get})"}

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

    print(f"Fetching Income/Gender data for {geo_level}...")
    try:
        resp = requests.get(base_url, params=params)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        print(f"API Request failed: {e}")
        return pd.DataFrame()

    if len(data) < 2: return pd.DataFrame()

    df_full = pd.DataFrame(data[1:], columns=data[0])

    # Income brackets and their variable codes for males and females (in ascending order)
    income_ranges = [
        "$1 to $2,499 or loss", "$2,500 to $4,999", "$5,000 to $7,499", 
        "$7,500 to $9,999", "$10,000 to $12,499", "$12,500 to $14,999",
        "$15,000 to $17,499", "$17,500 to $19,999", "$20,000 to $22,499",
        "$22,500 to $24,999", "$25,000 to $29,999", "$30,000 to $34,999",
        "$35,000 to $39,999", "$40,000 to $44,999", "$45,000 to $49,999",
        "$50,000 to $54,999", "$55,000 to $64,999", "$65,000 to $74,999",
        "$75,000 to $99,999", "$100,000 or more"
    ]
    
    # Male variable codes (B20005_003E to B20005_022E)
    male_codes = [f"B20005_{str(i).zfill(3)}E" for i in range(3, 23)]
    
    # Female variable codes (B20005_026E to B20005_045E)  
    female_codes = [f"B20005_{str(i).zfill(3)}E" for i in range(26, 46)]

    records = []
    for i, income_range in enumerate(income_ranges):
        male_var = male_codes[i]
        female_var = female_codes[i]
        
        male_count = 0
        female_count = 0
        
        if male_var in df_full.columns:
            try: male_count = int(df_full[male_var].iloc[0])
            except (ValueError, TypeError): pass
            
        if female_var in df_full.columns:
            try: female_count = int(df_full[female_var].iloc[0])
            except (ValueError, TypeError): pass
        
        # Add male record
        records.append({
            "income_range": income_range,
            "gender": "Male",
            "population": male_count
        })
        
        # Add female record
        records.append({
            "income_range": income_range,
            "gender": "Female", 
            "population": female_count
        })

    df = pd.DataFrame(records)
    return df


def get_distribution(lat: float, lon: float, year: int = 2023, force_tract: bool = True) -> dict:
    """
    Get joint income-gender distribution for a location at block group level.
    Returns both marginal distributions and joint distribution data.
    """
    geo_info = get_geography(lat, lon)
    if not geo_info.get("state_fips"): return {}

    df = get_income_gender_data(
        state_fips=geo_info["state_fips"], 
        county_fips=geo_info["county_fips"],
        tract_fips=geo_info["tract_fips"], 
        block_group_fips=geo_info["block_group_fips"], 
        year=year, 
        force_tract=True
    )

    if df.empty: return {}

    # Calculate marginal distributions with proper ordering
    income_marginal = df.groupby('income_range')['population'].sum().reset_index()
    gender_marginal = df.groupby('gender')['population'].sum().reset_index()
    
    # Sort marginals in ascending order
    income_order = ["$1 to $2,499 or loss", "$2,500 to $4,999", "$5,000 to $7,499", 
                   "$7,500 to $9,999", "$10,000 to $12,499", "$12,500 to $14,999",
                   "$15,000 to $17,499", "$17,500 to $19,999", "$20,000 to $22,499",
                   "$22,500 to $24,999", "$25,000 to $29,999", "$30,000 to $34,999",
                   "$35,000 to $39,999", "$40,000 to $44,999", "$45,000 to $49,999",
                   "$50,000 to $54,999", "$55,000 to $64,999", "$65,000 to $74,999",
                   "$75,000 to $99,999", "$100,000 or more"]
    gender_order = ["Male", "Female"]
    
    income_marginal['sort_order'] = income_marginal['income_range'].map({v: i for i, v in enumerate(income_order)})
    income_marginal = income_marginal.sort_values('sort_order').drop('sort_order', axis=1)
    
    gender_marginal['sort_order'] = gender_marginal['gender'].map({v: i for i, v in enumerate(gender_order)})
    gender_marginal = gender_marginal.sort_values('sort_order').drop('sort_order', axis=1)
    
    total_population = df['population'].sum()
    
    if total_population == 0:
        return {}
    
    # Add percentages
    income_marginal['percentage'] = (income_marginal['population'] / total_population) * 100
    gender_marginal['percentage'] = (gender_marginal['population'] / total_population) * 100

    return {
        "type": "income_gender_joint",
        "joint_data": [
            {
                "income": row["income_range"],
                "gender": row["gender"],
                "population": int(row["population"]),
                "percentage": float((row["population"] / total_population) * 100)
            }
            for _, row in df.iterrows()
        ],
        "income_marginal": [
            {
                "category": row["income_range"],
                "value": int(row["population"]),
                "percentage": float(row["percentage"])
            }
            for _, row in income_marginal.iterrows()
        ],
        "gender_marginal": [
            {
                "category": row["gender"],
                "value": int(row["population"]),
                "percentage": float(row["percentage"])
            }
            for _, row in gender_marginal.iterrows()
        ],
        "location": {
            "state_name": geo_info["state_name"],
            "county_name": geo_info["county_name"],
            "tract_name": geo_info["tract_name"],
            "block_group_name": geo_info["block_group_name"],
            "block_name": geo_info["block_name"],
            "block_geoid": geo_info["block_geoid"]
        },
        "data_source": "Census ACS Detailed Table B20005",
        "total_population": int(total_population)
    }


def get_conditional_distribution(joint_data: dict, condition_type: str, condition_value: str) -> dict:
    """
    Get conditional distribution from joint data.
    
    Args:
        joint_data: Result from get_distribution()
        condition_type: 'income' or 'gender' - what to condition on
        condition_value: The specific income range or gender to condition on
        
    Returns:
        Conditional distribution data
    """
    if condition_type not in ['income', 'gender']:
        raise ValueError("condition_type must be 'income' or 'gender'")
    
    joint_df = pd.DataFrame(joint_data['joint_data'])
    
    if condition_type == 'income':
        # Given income range, return gender distribution
        filtered_data = joint_df[joint_df['income'] == condition_value]
        if filtered_data.empty:
            return {"error": f"No data found for income range: {condition_value}"}
        
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
            "type": "conditional_gender_given_income",
            "condition": f"Income: {condition_value}",
            "data": result,
            "total_population": int(total_population),
            "data_source": joint_data["data_source"]
        }
    
    else:  # condition_type == 'gender'
        # Given gender, return income distribution
        filtered_data = joint_df[joint_df['gender'] == condition_value]
        if filtered_data.empty:
            return {"error": f"No data found for gender: {condition_value}"}
        
        total_population = filtered_data['population'].sum()
        
        result = [
            {
                "category": row["income"],
                "value": int(row["population"]),
                "percentage": float((row["population"] / total_population) * 100) if total_population > 0 else 0
            }
            for _, row in filtered_data.iterrows()
        ]
        
        return {
            "type": "conditional_income_given_gender",
            "condition": f"Gender: {condition_value}",
            "data": result,
            "total_population": int(total_population),
            "data_source": joint_data["data_source"]
        }


if __name__ == "__main__":
    lat, lon = 37.736509, -122.388028  # San Francisco area

    print("=" * 60 + "\nINCOME-GENDER JOINT DISTRIBUTION\n" + "=" * 60)
    
    joint_data = get_distribution(lat, lon)

    if joint_data:
        location = joint_data['location']
        location_name = location.get("block_group_name") or location.get("tract_name") or location.get("county_name")
        state_name = location.get("state_name")
        
        print(f"\nLocation: {location_name}, {state_name}")
        print(f"Data Source: {joint_data['data_source']}")
        
        # Show summary stats
        total_population = sum(item['population'] for item in joint_data['joint_data'])
        print(f"Total Population: {total_population:,}")
        
        print(f"\nGender Distribution:")
        for item in joint_data['gender_marginal']:
            print(f"  {item['category']}: {item['value']:,} people ({item['percentage']:.1f}%)")
        
        # Example conditional distributions
        print(f"\n" + "=" * 60)
        print("EXAMPLE CONDITIONAL DISTRIBUTIONS")
        print("=" * 60)
        
        # Condition on income
        income_condition = "$50,000 to $54,999"
        print(f"\nGender distribution for people earning {income_condition}:")
        conditional_gender = get_conditional_distribution(joint_data, 'income', income_condition)
        if 'error' not in conditional_gender:
            for item in conditional_gender['data']:
                print(f"  {item['category']}: {item['value']:,} people ({item['percentage']:.1f}%)")
        
        # Condition on gender
        gender_condition = "Female"
        print(f"\nIncome distribution for {gender_condition}s:")
        conditional_income = get_conditional_distribution(joint_data, 'gender', gender_condition)
        if 'error' not in conditional_income:
            for item in conditional_income['data'][:5]:  # Show first 5 income brackets
                if item['value'] > 0:
                    print(f"  {item['category']}: {item['value']:,} people ({item['percentage']:.1f}%)")
    else:
        print("Could not retrieve data for the specified location.")