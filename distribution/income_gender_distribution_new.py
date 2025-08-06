"""
Income-Gender Distribution from Census Data (B20001)
Pure Census API data - no assumptions or synthesis
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
        "x": lon,
        "y": lat,
        "benchmark": "Public_AR_Census2020",
        "vintage": "Census2020_Census2020",
        "format": "json"
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    geogs = resp.json()["result"]["geographies"]

    state = geogs["States"][0]
    county = geogs["Counties"][0]
    
    # Get Census Tract and Block information
    tracts = geogs.get("Census Tracts", [])
    blocks = geogs.get("Census Blocks", [])
    
    if tracts:
        tract = tracts[0]
        tract_fips = tract["TRACT"]
        tract_name = tract["NAME"]
    else:
        tract_fips = None
        tract_name = None
        
    if blocks:
        block = blocks[0]
        block_fips = block["BLOCK"]
        block_name = block["NAME"]
        block_geoid = block["GEOID"]
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
        "state_fips": state["STATE"],
        "state_name": state["NAME"],
        "county_fips": county["COUNTY"],
        "county_name": county["NAME"],
        "tract_fips": tract_fips,
        "tract_name": tract_name,
        "block_group_fips": block_group_fips,
        "block_group_name": block_group_name,
        "block_fips": block_fips,
        "block_name": block_name,
        "block_geoid": block_geoid
    }


def get_income_gender_data_new(state_fips: str, county_fips: str, tract_fips: str = None, 
                              block_group_fips: str = None, year: int = 2023, force_tract: bool = False) -> pd.DataFrame:
    """
    Fetch income-gender distribution from Census ACS Table B20001 at block group level.
    """
    base_url = f"https://api.census.gov/data/{year}/acs/acs5"
    table_to_get = "B20001"
    params = {"get": f"NAME,group({table_to_get})"}
    
    if CENSUS_API_KEY:
        params["key"] = CENSUS_API_KEY

    # Set geography - prefer block group level
    if block_group_fips and tract_fips and not force_tract:
        print(f"Fetching Income/Gender data (B20001) for Block Group...")
        params["for"] = f"block group:{block_group_fips}"
        params["in"] = f"state:{state_fips} county:{county_fips} tract:{tract_fips}"
    elif tract_fips:
        print(f"Fetching Income/Gender data (B20001) for Census Tract...")
        params["for"] = f"tract:{tract_fips}"
        params["in"] = f"state:{state_fips} county:{county_fips}"
    else:
        print(f"Fetching Income/Gender data (B20001) for County...")
        params["for"] = f"county:{county_fips}"
        params["in"] = f"state:{state_fips}"

    resp = requests.get(base_url, params=params)
    resp.raise_for_status()
    data = resp.json()

    # Convert to DataFrame
    df_full = pd.DataFrame([data[1]], columns=data[0])
    
    # Income ranges mapping for B20001
    income_mapping = {
        "$1 to $2,499 or loss": ["003", "024"],  # Male, Female
        "$2,500 to $4,999": ["004", "025"],
        "$5,000 to $7,499": ["005", "026"], 
        "$7,500 to $9,999": ["006", "027"],
        "$10,000 to $12,499": ["007", "028"],
        "$12,500 to $14,999": ["008", "029"],
        "$15,000 to $17,499": ["009", "030"],
        "$17,500 to $19,999": ["010", "031"],
        "$20,000 to $22,499": ["011", "032"],
        "$22,500 to $24,999": ["012", "033"],
        "$25,000 to $29,999": ["013", "034"],
        "$30,000 to $34,999": ["014", "035"],
        "$35,000 to $39,999": ["015", "036"],
        "$40,000 to $44,999": ["016", "037"],
        "$45,000 to $49,999": ["017", "038"],
        "$50,000 to $54,999": ["018", "039"],
        "$55,000 to $64,999": ["019", "040"],
        "$65,000 to $74,999": ["020", "041"],
        "$75,000 to $99,999": ["021", "042"],
        "$100,000 or more": ["022", "043"]
    }
    
    # Process joint distribution
    records = []
    for income_range, var_codes in income_mapping.items():
        male_count = 0
        female_count = 0
        
        for i, var_code in enumerate(var_codes):
            col_name = f"B20001_{var_code}E"
            if col_name in df_full.columns:
                value = int(df_full[col_name].iloc[0]) if df_full[col_name].iloc[0] is not None else 0
                if i == 0:  # First code is male
                    male_count = value
                else:  # Second code is female
                    female_count = value
        
        # Add records for both genders
        records.append({
            "gender": "Male", 
            "income_range": income_range,
            "population": male_count
        })
        records.append({
            "gender": "Female", 
            "income_range": income_range,
            "population": female_count
        })

    return pd.DataFrame(records)


def get_distribution(lat: float, lon: float, year: int = 2023, force_tract: bool = False) -> dict:
    """
    Get income-gender joint distribution for a location.
    """
    geo_info = get_geography(lat, lon)
    if not geo_info.get("state_fips"): 
        return {}

    df = get_income_gender_data_new(
        state_fips=geo_info["state_fips"],
        county_fips=geo_info["county_fips"],
        tract_fips=geo_info["tract_fips"],
        block_group_fips=geo_info["block_group_fips"],
        year=year,
        force_tract=force_tract
    )

    if df.empty: 
        return {}

    # Calculate marginal distributions
    gender_marginal = df.groupby('gender')['population'].sum().reset_index()
    income_marginal = df.groupby('income_range')['population'].sum().reset_index()
    
    # Sort income ranges
    income_order = ["$1 to $2,499 or loss", "$2,500 to $4,999", "$5,000 to $7,499", "$7,500 to $9,999",
                   "$10,000 to $12,499", "$12,500 to $14,999", "$15,000 to $17,499", "$17,500 to $19,999",
                   "$20,000 to $22,499", "$22,500 to $24,999", "$25,000 to $29,999", "$30,000 to $34,999",
                   "$35,000 to $39,999", "$40,000 to $44,999", "$45,000 to $49,999", "$50,000 to $54,999",
                   "$55,000 to $64,999", "$65,000 to $74,999", "$75,000 to $99,999", "$100,000 or more"]
    
    income_marginal['sort_order'] = income_marginal['income_range'].map({v: i for i, v in enumerate(income_order)})
    income_marginal = income_marginal.sort_values('sort_order').drop('sort_order', axis=1)
    
    # Calculate percentages
    total_pop = df['population'].sum()
    if total_pop > 0:
        gender_marginal['percentage'] = (gender_marginal['population'] * 100.0 / total_pop)
        income_marginal['percentage'] = (income_marginal['population'] * 100.0 / total_pop)
        df['percentage'] = (df['population'] * 100.0 / total_pop)
    else:
        gender_marginal['percentage'] = 0
        income_marginal['percentage'] = 0
        df['percentage'] = 0

    return {
        "type": "income_gender_new",
        "joint_data": [
            {
                "gender": row["gender"],
                "income_range": row["income_range"], 
                "value": int(row["population"]),
                "percentage": float(row["percentage"])
            }
            for _, row in df.iterrows()
        ],
        "gender_marginal": [
            {
                "category": row["gender"],
                "value": int(row["population"]),
                "percentage": float(row["percentage"])
            }
            for _, row in gender_marginal.iterrows()
        ],
        "income_marginal": [
            {
                "category": row["income_range"],
                "value": int(row["population"]),
                "percentage": float(row["percentage"])
            }
            for _, row in income_marginal.iterrows()
        ],
        "location": {
            "state_name": geo_info["state_name"],
            "county_name": geo_info["county_name"],
            "tract_name": geo_info["tract_name"],
            "block_group_name": geo_info["block_group_name"],
            "block_name": geo_info["block_name"],
            "block_geoid": geo_info["block_geoid"]
        },
        "data_source": "Census ACS Detailed Table B20001"
    }


def get_conditional_distribution(joint_data: dict, condition_type: str, condition_value: str) -> dict:
    """
    Get conditional distribution from joint income-gender data.
    """
    if not joint_data or "joint_data" not in joint_data:
        return {"error": "No joint distribution data available"}
    
    joint_df = pd.DataFrame(joint_data["joint_data"])
    
    if condition_type == "gender":
        # Filter by gender, return income distribution
        filtered_data = joint_df[joint_df["gender"] == condition_value]
        if filtered_data.empty:
            return {"error": f"No data found for gender: {condition_value}"}
        
        total = filtered_data["value"].sum()
        result_data = []
        for _, row in filtered_data.iterrows():
            percentage = (row["value"] * 100.0 / total) if total > 0 else 0
            result_data.append({
                "category": row["income_range"],
                "value": int(row["value"]),
                "percentage": float(percentage)
            })
        
        return {
            "type": "conditional_income_given_gender",
            "condition": f"Gender = {condition_value}",
            "data": result_data
        }
    
    elif condition_type == "income":
        # Filter by income, return gender distribution
        filtered_data = joint_df[joint_df["income_range"] == condition_value]
        if filtered_data.empty:
            return {"error": f"No data found for income range: {condition_value}"}
        
        total = filtered_data["value"].sum()
        result_data = []
        for _, row in filtered_data.iterrows():
            percentage = (row["value"] * 100.0 / total) if total > 0 else 0
            result_data.append({
                "category": row["gender"],
                "value": int(row["value"]),
                "percentage": float(percentage)
            })
        
        return {
            "type": "conditional_gender_given_income",
            "condition": f"Income = {condition_value}",
            "data": result_data
        }
    
    else:
        return {"error": f"Invalid condition_type: {condition_type}. Must be 'gender' or 'income'"}


if __name__ == "__main__":
    # Test the function
    lat, lon = 37.736509, -122.388028  # San Francisco area
    
    print("=" * 60)
    print("INCOME-GENDER DISTRIBUTION TEST (B20001)")
    print("=" * 60)
    
    result = get_distribution(lat, lon)
    print(f"Joint data count: {len(result.get('joint_data', []))}")
    print(f"Gender marginal count: {len(result.get('gender_marginal', []))}")
    print(f"Income marginal count: {len(result.get('income_marginal', []))}")