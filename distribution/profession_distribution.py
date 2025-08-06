"""
Profession & Gender Joint Distribution from Census Data
Fetches joint distribution from Census Table S2401 and provides conditional distributions.
Allows conditioning on either profession or gender to view corresponding distributions.
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


def get_profession_distribution(state_fips: str, county_fips: str, tract_fips: str = None,
                        block_group_fips: str = None, year: int = 2023, force_tract: bool = False) -> pd.DataFrame:
    """
    Fetches profession distribution with gender breakdown from Census ACS Detailed Table C24010 at block group level.
    """
    base_url = f"https://api.census.gov/data/{year}/acs/acs5"
    params = {"get": "NAME,group(C24010)"}

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

    print(f"Fetching Profession/Gender data for {geo_level}...")
    try:
        resp = requests.get(base_url, params=params)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        print(f"API Request failed: {e}")
        return pd.DataFrame()
    
    df_full = pd.DataFrame([data[1]], columns=data[0])
    
    # Profession categories from C24010 table - aggregated for meaningful analysis
    profession_categories_mapping = [
        ("Management, business, science, and arts occupations", {
            "male": ["C24010_003E", "C24010_004E", "C24010_005E", "C24010_006E", "C24010_007E"],
            "female": ["C24010_039E", "C24010_040E", "C24010_041E", "C24010_042E", "C24010_043E"]
        }),
        ("Service occupations", {
            "male": ["C24010_008E", "C24010_009E", "C24010_010E", "C24010_011E"],
            "female": ["C24010_044E", "C24010_045E", "C24010_046E", "C24010_047E"]
        }),
        ("Sales and office occupations", {
            "male": ["C24010_012E", "C24010_013E"],
            "female": ["C24010_048E", "C24010_049E"]
        }),
        ("Natural resources, construction, and maintenance occupations", {
            "male": ["C24010_014E", "C24010_015E", "C24010_016E"],
            "female": ["C24010_050E", "C24010_051E", "C24010_052E"]
        }),
        ("Production, transportation, and material moving occupations", {
            "male": ["C24010_017E", "C24010_018E"],
            "female": ["C24010_053E", "C24010_054E"]
        })
    ]

    records = []
    for profession, gender_codes in profession_categories_mapping:
        male_pop = 0
        female_pop = 0
        
        # Sum male populations
        for var_code in gender_codes["male"]:
            if var_code in df_full.columns:
                try:
                    male_pop += int(df_full[var_code].iloc[0])
                except (ValueError, TypeError):
                    pass  # Skip if data not available
        
        # Sum female populations  
        for var_code in gender_codes["female"]:
            if var_code in df_full.columns:
                try:
                    female_pop += int(df_full[var_code].iloc[0])
                except (ValueError, TypeError):
                    pass  # Skip if data not available
        
        total_pop = male_pop + female_pop
        total_working_pop = int(df_full["C24010_001E"].iloc[0]) if "C24010_001E" in df_full.columns else 1
        percentage = (total_pop * 100.0 / total_working_pop) if total_working_pop > 0 else 0
        
        records.append({
            "profession_level": profession,
            "population": total_pop,
            "male_population": male_pop,
            "female_population": female_pop,
            "percentage": percentage
        })
    
    return pd.DataFrame(records)


def get_distribution(lat: float, lon: float, year: int = 2023, force_tract: bool = False) -> dict:
    """
    Get profession distribution with gender breakdown for a location at block group level.
    Returns profession distribution data and joint profession-gender data.
    """
    geo_info = get_geography(lat, lon)
    if not geo_info.get("state_fips"): 
        return {}

    df = get_profession_distribution(
        state_fips=geo_info["state_fips"], county_fips=geo_info["county_fips"],
        tract_fips=geo_info["tract_fips"], block_group_fips=geo_info["block_group_fips"], 
        year=year, force_tract=force_tract
    )
    
    if df.empty:
        return {}

    # Prepare main profession distribution data
    profession_data = []
    for _, row in df.iterrows():
        profession_data.append({
            "category": row["profession_level"],
            "value": int(row["population"]),
            "percentage": round(row["percentage"], 2)
        })

    # Prepare joint profession-gender distribution data
    joint_data = []
    for _, row in df.iterrows():
        # Male data
        joint_data.append({
            "profession": row["profession_level"],
            "gender": "Male",
            "population": int(row["male_population"]),
            "percentage": round((row["male_population"] * 100.0 / df["population"].sum()) if df["population"].sum() > 0 else 0, 2)
        })
        # Female data
        joint_data.append({
            "profession": row["profession_level"],
            "gender": "Female", 
            "population": int(row["female_population"]),
            "percentage": round((row["female_population"] * 100.0 / df["population"].sum()) if df["population"].sum() > 0 else 0, 2)
        })

    # Prepare marginal distributions
    profession_marginal = []
    for _, row in df.iterrows():
        profession_marginal.append({
            "category": row["profession_level"],
            "value": int(row["population"]),
            "percentage": round(row["percentage"], 2)
        })

    gender_marginal = [
        {
            "category": "Male",
            "value": int(df["male_population"].sum()),
            "percentage": round((df["male_population"].sum() * 100.0 / df["population"].sum()) if df["population"].sum() > 0 else 0, 2)
        },
        {
            "category": "Female", 
            "value": int(df["female_population"].sum()),
            "percentage": round((df["female_population"].sum() * 100.0 / df["population"].sum()) if df["population"].sum() > 0 else 0, 2)
        }
    ]

    return {
        "data": profession_data,
        "joint_data": joint_data,
        "profession_marginal": profession_marginal,
        "gender_marginal": gender_marginal,
        "location": {
            "state_name": geo_info["state_name"],
            "county_name": geo_info["county_name"],
            "tract_name": geo_info["tract_name"],
            "block_group_name": geo_info["block_group_name"],
            "block_name": geo_info["block_name"],
            "block_geoid": geo_info["block_geoid"]
        },
        "data_source": f"Census ACS 5-Year Detailed Table C24010 ({year})",
        "total_population": int(df["population"].sum())
    }


def get_conditional_distribution(joint_data: dict, condition_type: str, condition_value: str) -> dict:
    """
    Get conditional distribution from joint profession-gender data.
    
    Args:
        joint_data: The result from get_distribution()
        condition_type: Either 'profession' or 'gender'
        condition_value: The specific profession or gender to condition on
        
    Returns:
        Conditional distribution data
    """
    if not joint_data or 'joint_data' not in joint_data:
        return {"error": "No joint data available"}
    
    joint_df = pd.DataFrame(joint_data['joint_data'])
    
    if condition_type == 'profession':
        # Given profession, return gender distribution
        filtered_data = joint_df[joint_df['profession'] == condition_value]
        if filtered_data.empty:
            return {"error": f"No data found for profession: {condition_value}"}
        
        total_for_profession = filtered_data['population'].sum()
        
        conditional_data = []
        for _, row in filtered_data.iterrows():
            conditional_percentage = (row['population'] * 100.0 / total_for_profession) if total_for_profession > 0 else 0
            conditional_data.append({
                "category": row["gender"],
                "value": int(row["population"]),
                "percentage": round(conditional_percentage, 2)
            })
        
        return {
            "data": conditional_data,
            "condition": f"Gender distribution for {condition_value}",
            "total_population": int(total_for_profession),
            "type": "gender_given_profession"
        }
    
    elif condition_type == 'gender':
        # Given gender, return profession distribution
        filtered_data = joint_df[joint_df['gender'] == condition_value]
        if filtered_data.empty:
            return {"error": f"No data found for gender: {condition_value}"}
        
        total_for_gender = filtered_data['population'].sum()
        
        conditional_data = []
        for _, row in filtered_data.iterrows():
            conditional_percentage = (row['population'] * 100.0 / total_for_gender) if total_for_gender > 0 else 0
            conditional_data.append({
                "category": row["profession"],
                "value": int(row["population"]),
                "percentage": round(conditional_percentage, 2)
            })
        
        return {
            "data": conditional_data,
            "condition": f"Profession distribution for {condition_value}s",
            "total_population": int(total_for_gender),
            "type": "profession_given_gender"
        }
    
    else:
        return {"error": f"Invalid condition_type: {condition_type}. Must be 'profession' or 'gender'"}





if __name__ == "__main__":
    lat, lon = 37.736509, -122.388028  # San Francisco area

    print("=" * 60 + "\nProfession Distribution\n" + "=" * 60)

    joint_data = get_distribution(lat, lon)
    print(joint_data)