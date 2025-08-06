"""
Education & Gender Joint Distribution from Census Data
Fetches joint distribution from Census Table B15002 (Sex by Educational Attainment for the Population 25 Years and Over) at block group level.
Allows conditioning on either education or gender to view corresponding distributions.
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

    print({
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
    })
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


def get_education_sex_data(state_fips: str, county_fips: str, tract_fips: str = None,
                           block_group_fips: str = None, year: int = 2023, force_tract: bool = False) -> pd.DataFrame:
    """
    Fetches joint education-sex distribution for the population 25 years and over
    from Census ACS Detail Table B15002.
    """
    # The base URL for Detail tables (like B-series) is different from Subject tables
    base_url = f"https://api.census.gov/data/{year}/acs/acs5"
    table_to_get = "B15002"
    params = {"get": f"NAME,group({table_to_get})"}

    if CENSUS_API_KEY:
        params["key"] = CENSUS_API_KEY

    # Determine the geographic level for the API call
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

    print(f"Fetching Education/Sex data (B15002) for {geo_level}...")
    try:
        resp = requests.get(base_url, params=params)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        print(f"API Request failed: {e}")
        return pd.DataFrame()

    if not data or len(data) < 2:
        print("No data returned from API.")
        return pd.DataFrame()

    df_full = pd.DataFrame(data[1:], columns=data[0])

    # Education-Sex mapping for B15002 (Population 25 years and over)
    # Categories are constructed by summing the relevant detailed variables.
    education_sex_mapping = {
        "Male": {
            "Less than 9th grade": [f"B15002_0{i:02d}E" for i in range(3, 11)],
            "9th to 12th grade, no diploma": [f"B15002_0{i:02d}E" for i in range(11, 15)],
            "High school graduate (includes equivalency)": ["B15002_015E"],
            "Some college, no degree": ["B15002_016E", "B15002_017E"],
            "Associate's degree": ["B15002_018E"],
            "Bachelor's degree": ["B15002_019E"],
            "Graduate or professional degree": ["B15002_020E", "B15002_021E", "B15002_022E"]
        },
        "Female": {
            "Less than 9th grade": [f"B15002_0{i:02d}E" for i in range(24, 32)],
            "9th to 12th grade, no diploma": [f"B15002_0{i:02d}E" for i in range(32, 36)],
            "High school graduate (includes equivalency)": ["B15002_036E"],
            "Some college, no degree": ["B15002_037E", "B15002_038E"],
            "Associate's degree": ["B15002_039E"],
            "Bachelor's degree": ["B15002_040E"],
            "Graduate or professional degree": ["B15002_041E", "B15002_042E", "B15002_043E"]
        }
    }

    records = []
    # Define explicit order for the output DataFrame
    sex_order = ["Male", "Female"]
    education_order = [
        "Less than 9th grade", "9th to 12th grade, no diploma",
        "High school graduate (includes equivalency)", "Some college, no degree",
        "Associate's degree", "Bachelor's degree", "Graduate or professional degree"
    ]

    # B15002 only covers "25 years and over", so this is a constant.
    age_range_constant = "25 years and over"

    for sex in sex_order:
        if sex in education_sex_mapping:
            education_dict = education_sex_mapping[sex]
            for education_level in education_order:
                if education_level in education_dict:
                    vars_to_sum = education_dict[education_level]
                    count = 0

                    for var_name in vars_to_sum:
                        if var_name in df_full.columns:
                            try:
                                # Add the population count for this specific variable
                                count += int(df_full[var_name].iloc[0])
                            except (ValueError, TypeError):
                                # Handle cases where the value is not a valid integer
                                pass

                    records.append({
                        "age_range": age_range_constant,
                        "sex": sex,
                        "education_level": education_level,
                        "population": count
                    })

    return pd.DataFrame(records)


def get_distribution(lat: float, lon: float, year: int = 2023, force_tract: bool = False) -> dict:
    """
    Get joint education-sex distribution for a location.
    Returns both marginal distributions and joint distribution data.
    """
    geo_info = get_geography(lat, lon)
    if not geo_info.get("state_fips"): return {}

    df = get_education_sex_data(
        state_fips=geo_info["state_fips"],
        county_fips=geo_info["county_fips"],
        tract_fips=geo_info["tract_fips"],
        block_group_fips=geo_info["block_group_fips"],
        year=year,
        force_tract=force_tract
    )

    if df.empty: return {}

    # Calculate marginal distributions with proper ordering
    age_marginal = df.groupby('age_range')['population'].sum().reset_index()
    sex_marginal = df.groupby('sex')['population'].sum().reset_index()
    education_marginal = df.groupby('education_level')['population'].sum().reset_index()
    
    # Sort marginals in ascending order
    age_order_marginal = ["18 to 24 years", "25 years and over", "25 to 34 years", "35 to 44 years", "45 to 64 years", "65 years and over"]
    sex_order_marginal = ["Male", "Female"]
    education_order_marginal = ["Less than 9th grade", "9th to 12th grade, no diploma", "Less than high school graduate",
                               "High school graduate (includes equivalency)", "High school graduate or higher",
                               "Some college, no degree", "Some college or associate's degree", "Associate's degree", 
                               "Bachelor's degree", "Bachelor's degree or higher", "Graduate or professional degree"]
    
    age_marginal['sort_order'] = age_marginal['age_range'].map({v: i for i, v in enumerate(age_order_marginal)})
    age_marginal = age_marginal.sort_values('sort_order').drop('sort_order', axis=1)
    
    sex_marginal['sort_order'] = sex_marginal['sex'].map({v: i for i, v in enumerate(sex_order_marginal)})
    sex_marginal = sex_marginal.sort_values('sort_order').drop('sort_order', axis=1)
    
    education_marginal['sort_order'] = education_marginal['education_level'].map({v: i for i, v in enumerate(education_order_marginal)})
    education_marginal = education_marginal.sort_values('sort_order').drop('sort_order', axis=1)
    
    total_population = df['population'].sum()
    
    if total_population == 0:
        return {}
    
    # Add percentages
    age_marginal['percentage'] = (age_marginal['population'] / total_population) * 100
    sex_marginal['percentage'] = (sex_marginal['population'] / total_population) * 100
    education_marginal['percentage'] = (education_marginal['population'] / total_population) * 100

    return {
        "type": "education_sex_joint",
        "joint_data": [
            {
                "age_range": row["age_range"],
                "sex": row["sex"],
                "education_level": row["education_level"],
                "population": int(row["population"]),
                "percentage": float((row["population"] / total_population) * 100)
            }
            for _, row in df.iterrows()
        ],
        "age_marginal": [
            {
                "category": row["age_range"],
                "value": int(row["population"]),
                "percentage": float(row["percentage"])
            }
            for _, row in age_marginal.iterrows()
        ],
        "sex_marginal": [
            {
                "category": row["sex"],
                "value": int(row["population"]),
                "percentage": float(row["percentage"])
            }
            for _, row in sex_marginal.iterrows()
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
        "data_source": "Census ACS Subject Table"
    }


def get_conditional_distribution(joint_data: dict, condition_type: str, condition_value: str,
                                 condition_value2: str = None) -> dict:
    """
    Get conditional distribution from joint data.
    NOTE: This function is adapted for data from B15002, which only covers the
    population "25 years and over". Therefore, conditioning by 'age' is not supported.

    Args:
        joint_data: A dictionary containing the 'joint_data' DataFrame.
                    Expected columns: 'age_range', 'sex', 'education_level', 'population'.
        condition_type: What to condition on. Valid options are:
                        'sex', 'education', 'sex_education'.
        condition_value: The specific value for the first condition.
                         (e.g., 'Male' if condition_type is 'sex').
        condition_value2: The specific value for the second condition.
                          (Required only for 'sex_education').

    Returns:
        A dictionary containing the conditional distribution data.
    """
    # Valid conditions have been reduced as 'age' is no longer a variable dimension.
    valid_conditions = ['sex', 'education', 'sex_education']

    if condition_type not in valid_conditions:
        raise ValueError(f"condition_type must be one of {valid_conditions}")

    # Ensure 'joint_data' key exists and is not empty
    if "joint_data" not in joint_data or not joint_data["joint_data"]:
        return {"error": "Input 'joint_data' is empty or invalid."}

    joint_df = pd.DataFrame(joint_data['joint_data'])

    if condition_type == 'sex':
        # Given sex, return the education distribution (age is constant).
        filtered_data = joint_df[joint_df['sex'] == condition_value]
        if filtered_data.empty:
            return {"error": f"No data found for sex: {condition_value}"}

        total_population = filtered_data['population'].sum()

        result = [
            {
                "category": row["education_level"],
                "value": int(row["population"]),
                "percentage": float((row["population"] / total_population) * 100) if total_population > 0 else 0
            }
            for _, row in filtered_data.iterrows()
        ]

        return {
            "type": "conditional_education_given_sex",
            "condition": f"Sex: {condition_value}",
            "data": result,
            "total_population": int(total_population),
            "data_source": joint_data.get("data_source")
        }

    elif condition_type == 'education':
        # Given education level, return the sex distribution (age is constant).
        filtered_data = joint_df[joint_df['education_level'] == condition_value]
        if filtered_data.empty:
            return {"error": f"No data found for education level: {condition_value}"}

        total_population = filtered_data['population'].sum()

        result = [
            {
                "category": row["sex"],
                "value": int(row["population"]),
                "percentage": float((row["population"] / total_population) * 100) if total_population > 0 else 0
            }
            for _, row in filtered_data.iterrows()
        ]

        return {
            "type": "conditional_sex_given_education",
            "condition": f"Education: {condition_value}",
            "data": result,
            "total_population": int(total_population),
            "data_source": joint_data.get("data_source")
        }

    elif condition_type == 'sex_education':
        # Given sex and education, return the age distribution (which will be trivial).
        if condition_value2 is None:
            raise ValueError(
                "For 'sex_education' conditioning, condition_value (sex) and condition_value2 (education_level) are required.")

        filtered_data = joint_df[
            (joint_df['sex'] == condition_value) & (joint_df['education_level'] == condition_value2)]
        if filtered_data.empty:
            return {"error": f"No data found for sex: '{condition_value}' and education: '{condition_value2}'"}

        total_population = filtered_data['population'].sum()

        # The result is a distribution of the last remaining variable: age_range.
        # Since there's only one age group, this list will contain a single element.
        result = [
            {
                "category": row["age_range"],
                "value": int(row["population"]),
                "percentage": float((row["population"] / total_population) * 100) if total_population > 0 else 0
            }
            for _, row in filtered_data.iterrows()
        ]

        return {
            "type": "conditional_age_given_sex_education",
            "condition": f"Sex: {condition_value}, Education: {condition_value2}",
            "data": result,
            "total_population": int(total_population),
            "data_source": joint_data.get("data_source")
        }



if __name__ == "__main__":
    # Example coordinates for a location in San Francisco, CA
    lat, lon = 37.736509, -122.388028

    # The data source is now B15002, which covers the population 25 years and over.
    print("=" * 60 + "\nEDUCATION-SEX JOINT DISTRIBUTION (B15002 - Population 25+)\n" + "=" * 60)

    # This function is assumed to be the main entry point that internally calls
    # geocoding and the data fetching functions we corrected earlier.
    joint_data = get_distribution(lat, lon)

    if joint_data and 'joint_data' in joint_data and joint_data['joint_data']:
        location = joint_data.get('location', {})
        location_name = location.get("subdivision_name") or location.get("county_name", "N/A")
        state_name = location.get("state_name", "N/A")

        print(f"\nLocation: {location_name}, {state_name}")
        print(f"Data Source: {joint_data.get('data_source', 'N/A')}")

        # Show summary stats
        total_population = sum(item['population'] for item in joint_data['joint_data'])
        print(f"Total Population (Age 25+): {total_population:,}")

        print(f"\nSex Distribution (Age 25+):")
        for item in joint_data.get('sex_marginal', []):
            print(f"  {item['category']}: {item['value']:,} people ({item['percentage']:.1f}%)")

        print(f"\nEducation Level Distribution (Age 25+):")
        for item in joint_data.get('education_marginal', []):
            if item['value'] > 0:
                print(f"  {item['category']}: {item['value']:,} people ({item['percentage']:.1f}%)")

        # --- Example Conditional Distributions ---
        print(f"\n" + "=" * 60)
        print("EXAMPLE CONDITIONAL DISTRIBUTIONS")
        print("=" * 60)

        # Condition on sex only
        sex_condition = "Female"
        # Since age is constant, we now get the education distribution for a given sex.
        print(f"\nEducation distribution for {sex_condition}s (Age 25+):")
        conditional_edu_dist = get_conditional_distribution(joint_data, 'sex', sex_condition)

        if 'error' not in conditional_edu_dist:
            # The result from get_conditional_distribution no longer contains 'age_range' for this condition type.
            data_sorted = sorted(conditional_edu_dist['data'], key=lambda x: x['value'], reverse=True)
            for item in data_sorted:
                if item['value'] > 0:
                    print(f"  {item['education_level']}: {item['value']:,} people ({item['percentage']:.1f}%)")
        else:
            print(f"  Error: {conditional_edu_dist['error']}")

        # Condition on education and sex together
        # We must use an exact education level from the B15002 categories.
        education_condition = "Bachelor's degree"
        sex_condition = "Male"
        print(f"\nAge distribution for {sex_condition}s with a {education_condition}:")
        conditional_age_dist = get_conditional_distribution(joint_data, 'sex_education', sex_condition,
                                                            education_condition)

        if 'error' not in conditional_age_dist:
            # This result is a trivial distribution of the single age group "25 years and over"
            for item in conditional_age_dist['data']:
                if item['value'] > 0:
                    print(f"  {item['category']}: {item['value']:,} people ({item['percentage']:.1f}%)")
        else:
            print(f"  Error: {conditional_age_dist['error']}")

    else:
        print("Could not retrieve data for the specified location.")