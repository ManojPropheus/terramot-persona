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
    Get geographic information (state, county, subdivision) from coordinates.
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
    subs = geogs.get("County Subdivisions", [])

    subdiv_fips, subdiv_name = (subs[0].get("COUSUB"), subs[0].get("NAME")) if subs else (None, None)

    return {
        "state_fips": state.get("STATE"), "state_name": state.get("NAME"),
        "county_fips": county.get("COUNTY"), "county_name": county.get("NAME"),
        "subdivision_fips": subdiv_fips, "subdivision_name": subdiv_name
    }


def get_profession_distribution(state_fips: str, county_fips: str, subdivision_fips: str = None,
                        year: int = 2023, force_county: bool = False) -> pd.DataFrame:
    """
    Fetches profession distribution with gender breakdown from Census ACS Subject Table S2401.
    """
    base_url = f"https://api.census.gov/data/{year}/acs/acs5/subject"
    table_to_get = "S2401"
    params = {"get": f"NAME,group({table_to_get})"}

    if CENSUS_API_KEY:
        params["key"] = CENSUS_API_KEY

    geo_level, params["in"] = ("County", f"state:{state_fips}")
    if subdivision_fips and not force_county:
        geo_level = "County Subdivision"
        params["for"] = f"county subdivision:{subdivision_fips}"
        params["in"] = f"state:{state_fips} county:{county_fips}"
    else:
        params["for"] = f"county:{county_fips}"

    print(f"Fetching Profession/Gender data for {geo_level}...")
    try:
        resp = requests.get(base_url, params=params)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        print(f"API Request failed: {e}")
        return pd.DataFrame()
    df_full = pd.DataFrame([data[1]], columns=data[0])
    profession_levels = ['Management, business, science, and arts occupations',
                         'Service occupations',
                         'Sales and office occupations',
                         'Natural resources, construction, and maintenance occupations',
                         'Production, transportation, and material moving occupations']
    profession_levels_codes = [
        "S2401_C01_002E",  # Management, business, science, and arts occupations
        "S2401_C01_018E",  # Service occupations
        "S2401_C01_026E",  # Sales and office occupations
        "S2401_C01_029E",  # Natural resources, construction, and maintenance occupations
        "S2401_C01_033E",  # Production, transportation, and material moving occupations
    ]

    # Codes for Male Population (C02)
    profession_levels_codes_male = [
        "S2401_C02_002E",
        "S2401_C02_018E",
        "S2401_C02_026E",
        "S2401_C02_029E",
        "S2401_C02_033E",
    ]

    # Codes for Female Population (C03)
    profession_levels_codes_female = [
        "S2401_C04_002E",
        "S2401_C04_018E",
        "S2401_C04_026E",
        "S2401_C04_029E",
        "S2401_C04_033E",
    ]

    total_population = int(df_full["S2401_C01_001E"].iloc[0])
    print(f"Total population: {total_population}")
    records = []
    for i, profession_level in enumerate(profession_levels):
        total_code = profession_levels_codes[i]
        male_code = profession_levels_codes_male[i]
        female_code = profession_levels_codes_female[i]

        if total_code in df_full.columns and male_code in df_full.columns and female_code in df_full.columns:
            total_count = int(df_full[total_code].iloc[0])
            male_count = int(df_full[male_code].iloc[0])
            female_count = int(df_full[female_code].iloc[0])

            percentage = (total_count * 100.0 / total_population) if total_population > 0 else 0

            records.append({
                "profession_level": profession_level,
                "population": total_count,
                "male_population": male_count,
                "female_population": female_count,
                "percentage": percentage
            })
    df = pd.DataFrame(records)
    return df


def get_distribution(lat: float, lon: float, year: int = 2023, force_county: bool = False) -> dict:
    """
    Get profession distribution with gender breakdown for a location.
    Returns profession distribution data and joint profession-gender data.
    """
    geo_info = get_geography(lat, lon)
    if not geo_info.get("state_fips"): 
        return {}

    df = get_profession_distribution(
        state_fips=geo_info["state_fips"], county_fips=geo_info["county_fips"],
        subdivision_fips=geo_info["subdivision_fips"], year=year, force_county=force_county
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
        "location": geo_info,
        "data_source": f"Census ACS 5-Year Subject Table S2401 ({year})",
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