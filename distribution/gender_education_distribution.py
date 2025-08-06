"""
Gender-Education Distribution from Census Data
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


def get_gender_education_data(state_fips: str, county_fips: str, tract_fips: str = None, 
                             block_group_fips: str = None, year: int = 2023, force_tract: bool = False) -> pd.DataFrame:
    """
    Fetch gender-education distribution from Census ACS Table B15002 at block group level.
    """
    base_url = f"https://api.census.gov/data/{year}/acs/acs5"
    table_to_get = "B15002"
    params = {"get": f"NAME,group({table_to_get})"}
    
    if CENSUS_API_KEY:
        params["key"] = CENSUS_API_KEY

    # Set geography - prefer block group level
    if block_group_fips and tract_fips and not force_tract:
        print(f"Fetching Gender/Education data for Block Group...")
        params["for"] = f"block group:{block_group_fips}"
        params["in"] = f"state:{state_fips} county:{county_fips} tract:{tract_fips}"
    elif tract_fips:
        print(f"Fetching Gender/Education data for Census Tract...")
        params["for"] = f"tract:{tract_fips}"
        params["in"] = f"state:{state_fips} county:{county_fips}"
    else:
        print(f"Fetching Gender/Education data for County...")
        params["for"] = f"county:{county_fips}"
        params["in"] = f"state:{state_fips}"

    resp = requests.get(base_url, params=params)
    resp.raise_for_status()
    data = resp.json()

    # Convert to DataFrame
    df_full = pd.DataFrame([data[1]], columns=data[0])
    
    # Education levels mapping
    education_mapping = {
        "Less than 9th grade": ["003", "004", "020", "021"],  # Male + Female no schooling through 8th grade
        "9th to 12th grade, no diploma": ["005", "006", "007", "008", "009", "010", "022", "023", "024", "025", "026", "027"],  # 9th-12th no diploma
        "High school graduate": ["011", "028"],  # High school diploma
        "Some college, no degree": ["012", "013", "029", "030"],  # Some college
        "Associate's degree": ["014", "031"],  # Associate's
        "Bachelor's degree": ["015", "032"],  # Bachelor's
        "Graduate or professional degree": ["016", "017", "018", "033", "034", "035"]  # Graduate degrees
    }
    
    # Process joint distribution
    records = []
    for education_level, var_codes in education_mapping.items():
        male_count = 0
        female_count = 0
        
        for var_code in var_codes:
            col_name = f"B15002_{var_code}E"
            if col_name in df_full.columns:
                value = int(df_full[col_name].iloc[0]) if df_full[col_name].iloc[0] is not None else 0
                # Male variables are 003-018, female are 020-035
                if int(var_code) <= 18:
                    male_count += value
                else:
                    female_count += value
        
        # Add records for both genders
        records.append({
            "gender": "Male", 
            "education_level": education_level,
            "population": male_count
        })
        records.append({
            "gender": "Female", 
            "education_level": education_level,
            "population": female_count
        })

    return pd.DataFrame(records)


def get_distribution(lat: float, lon: float, year: int = 2023, force_tract: bool = False) -> dict:
    """
    Get gender-education joint distribution for a location.
    """
    geo_info = get_geography(lat, lon)
    if not geo_info.get("state_fips"): 
        return {}

    df = get_gender_education_data(
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
    education_marginal = df.groupby('education_level')['population'].sum().reset_index()
    
    # Sort education levels
    education_order = ["Less than 9th grade", "9th to 12th grade, no diploma", "High school graduate", 
                      "Some college, no degree", "Associate's degree", "Bachelor's degree", 
                      "Graduate or professional degree"]
    
    education_marginal['sort_order'] = education_marginal['education_level'].map({v: i for i, v in enumerate(education_order)})
    education_marginal = education_marginal.sort_values('sort_order').drop('sort_order', axis=1)
    
    # Calculate percentages
    total_pop = df['population'].sum()
    if total_pop > 0:
        gender_marginal['percentage'] = (gender_marginal['population'] * 100.0 / total_pop)
        education_marginal['percentage'] = (education_marginal['population'] * 100.0 / total_pop)
        df['percentage'] = (df['population'] * 100.0 / total_pop)
    else:
        gender_marginal['percentage'] = 0
        education_marginal['percentage'] = 0
        df['percentage'] = 0

    return {
        "type": "gender_education",
        "joint_data": [
            {
                "gender": row["gender"],
                "education_level": row["education_level"], 
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
        "education_marginal": [
            {
                "category": row["education_level"],
                "value": int(row["population"]),
                "percentage": float(row["percentage"])
            }
            for _, row in education_marginal.iterrows()
        ],
        "location": {
            "state_name": geo_info["state_name"],
            "county_name": geo_info["county_name"],
            "tract_name": geo_info["tract_name"],
            "block_group_name": geo_info["block_group_name"],
            "block_name": geo_info["block_name"],
            "block_geoid": geo_info["block_geoid"]
        },
        "data_source": "Census ACS Detailed Table B15002"
    }


def get_conditional_distribution(joint_data: dict, condition_type: str, condition_value: str) -> dict:
    """
    Get conditional distribution from joint gender-education data.
    """
    if not joint_data or "joint_data" not in joint_data:
        return {"error": "No joint distribution data available"}
    
    joint_df = pd.DataFrame(joint_data["joint_data"])
    
    if condition_type == "gender":
        # Filter by gender, return education distribution
        filtered_data = joint_df[joint_df["gender"] == condition_value]
        if filtered_data.empty:
            return {"error": f"No data found for gender: {condition_value}"}
        
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
            "type": "conditional_education_given_gender",
            "condition": f"Gender = {condition_value}",
            "data": result_data
        }
    
    elif condition_type == "education":
        # Filter by education, return gender distribution
        filtered_data = joint_df[joint_df["education_level"] == condition_value]
        if filtered_data.empty:
            return {"error": f"No data found for education level: {condition_value}"}
        
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
            "type": "conditional_gender_given_education",
            "condition": f"Education = {condition_value}",
            "data": result_data
        }
    
    else:
        return {"error": f"Invalid condition_type: {condition_type}. Must be 'gender' or 'education'"}


if __name__ == "__main__":
    # Test the function
    lat, lon = 37.736509, -122.388028  # San Francisco area
    
    print("=" * 60)
    print("GENDER-EDUCATION DISTRIBUTION TEST")
    print("=" * 60)
    
    result = get_distribution(lat, lon)
    print(f"Joint data count: {len(result.get('joint_data', []))}")
    print(f"Gender marginal count: {len(result.get('gender_marginal', []))}")
    print(f"Education marginal count: {len(result.get('education_marginal', []))}")