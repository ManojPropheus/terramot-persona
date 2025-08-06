"""
Age & Education Joint Distribution from Census Data
Fetches joint distribution from Census Table B15001 and provides conditional distributions.
Allows conditioning on either age or education to view corresponding distributions.
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

def get_age_education_data(state_fips: str, county_fips: str, tract_fips: str = None,
                            block_group_fips: str = None, year: int = 2023, force_tract: bool = False) -> pd.DataFrame:
    """
    Fetches joint age-education distribution from Census ACS Table B15001.
    """
    base_url = f"https://api.census.gov/data/{year}/acs/acs5"
    table_to_get = "B15001"
    params = {"get": f"NAME,group({table_to_get})"}

    if CENSUS_API_KEY:
        params["key"] = CENSUS_API_KEY


    geo_level, params["in"] = ("County", f"state:{state_fips}")
    # Set geography - prefer block group level
    if block_group_fips and tract_fips and not force_tract:
        print(f"Fetching age data for Block Group...")
        params["for"] = f"block group:{block_group_fips}"
        params["in"] = f"state:{state_fips} county:{county_fips} tract:{tract_fips}"
    elif tract_fips:
        print(f"Fetching age data for Census Tract...")
        params["for"] = f"tract:{tract_fips}"
        params["in"] = f"state:{state_fips} county:{county_fips}"
    else:
        print(f"Fetching age data for County...")
        params["for"] = f"county:{county_fips}"
        params["in"] = f"state:{state_fips}"

    print(f"Fetching Age/Education data for {geo_level}...")
    try:
        resp = requests.get(base_url, params=params)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        print(f"API Request failed: {e}")
        return pd.DataFrame()

    if len(data) < 2: return pd.DataFrame()

    df_full = pd.DataFrame(data[1:], columns=data[0])

    # Age-Sex-Education mapping for B15001 with proper variable codes
    age_sex_education_mapping = {
        # 18 to 24 years
        "18 to 24 years": {
            "Male": {
                "Less than 9th grade": "004",
                "9th to 12th grade, no diploma": "005", 
                "High school graduate (includes equivalency)": "006",
                "Some college, no degree": "007",
                "Associate's degree": "008",
                "Bachelor's degree": "009",
                "Graduate or professional degree": "010"
            },
            "Female": {
                "Less than 9th grade": "045",
                "9th to 12th grade, no diploma": "046",
                "High school graduate (includes equivalency)": "047", 
                "Some college, no degree": "048",
                "Associate's degree": "049",
                "Bachelor's degree": "050",
                "Graduate or professional degree": "051"
            }
        },
        # 25 to 34 years  
        "25 to 34 years": {
            "Male": {
                "Less than 9th grade": "012",
                "9th to 12th grade, no diploma": "013",
                "High school graduate (includes equivalency)": "014",
                "Some college, no degree": "015", 
                "Associate's degree": "016",
                "Bachelor's degree": "017",
                "Graduate or professional degree": "018"
            },
            "Female": {
                "Less than 9th grade": "053",
                "9th to 12th grade, no diploma": "054",
                "High school graduate (includes equivalency)": "055",
                "Some college, no degree": "056",
                "Associate's degree": "057", 
                "Bachelor's degree": "058",
                "Graduate or professional degree": "059"
            }
        },
        # 35 to 44 years
        "35 to 44 years": {
            "Male": {
                "Less than 9th grade": "020",
                "9th to 12th grade, no diploma": "021",
                "High school graduate (includes equivalency)": "022",
                "Some college, no degree": "023",
                "Associate's degree": "024",
                "Bachelor's degree": "025", 
                "Graduate or professional degree": "026"
            },
            "Female": {
                "Less than 9th grade": "061",
                "9th to 12th grade, no diploma": "062",
                "High school graduate (includes equivalency)": "063",
                "Some college, no degree": "064",
                "Associate's degree": "065",
                "Bachelor's degree": "066",
                "Graduate or professional degree": "067"
            }
        },
        # 45 to 64 years
        "45 to 64 years": {
            "Male": {
                "Less than 9th grade": "028",
                "9th to 12th grade, no diploma": "029",
                "High school graduate (includes equivalency)": "030",
                "Some college, no degree": "031",
                "Associate's degree": "032",
                "Bachelor's degree": "033",
                "Graduate or professional degree": "034"
            },
            "Female": {
                "Less than 9th grade": "069", 
                "9th to 12th grade, no diploma": "070",
                "High school graduate (includes equivalency)": "071",
                "Some college, no degree": "072",
                "Associate's degree": "073",
                "Bachelor's degree": "074",
                "Graduate or professional degree": "075"
            }
        },
        # 65 years and over
        "65 years and over": {
            "Male": {
                "Less than 9th grade": "036",
                "9th to 12th grade, no diploma": "037",
                "High school graduate (includes equivalency)": "038", 
                "Some college, no degree": "039",
                "Associate's degree": "040",
                "Bachelor's degree": "041",
                "Graduate or professional degree": "042"
            },
            "Female": {
                "Less than 9th grade": "077",
                "9th to 12th grade, no diploma": "078",
                "High school graduate (includes equivalency)": "079",
                "Some college, no degree": "080",
                "Associate's degree": "081",
                "Bachelor's degree": "082",
                "Graduate or professional degree": "083"
            }
        }
    }

    records = []
    # Define explicit order for sorting  
    age_order = ["18 to 24 years", "25 to 34 years", "35 to 44 years", "45 to 64 years", "65 years and over"]
    sex_order = ["Male", "Female"]
    education_order = ["Less than 9th grade", "9th to 12th grade, no diploma", "High school graduate (includes equivalency)", 
                      "Some college, no degree", "Associate's degree", "Bachelor's degree", 
                      "Graduate or professional degree"]
    
    for age_range in age_order:
        if age_range in age_sex_education_mapping:
            sex_dict = age_sex_education_mapping[age_range]
            for sex in sex_order:
                if sex in sex_dict:
                    education_dict = sex_dict[sex]
                    for education_level in education_order:
                        if education_level in education_dict:
                            var_code = education_dict[education_level]
                            var_name = f"B15001_{var_code}E"
                            
                            count = 0
                            if var_name in df_full.columns:
                                try:
                                    count = int(df_full[var_name].iloc[0])
                                except (ValueError, TypeError):
                                    pass
                            
                            records.append({
                                "age_range": age_range,
                                "sex": sex,
                                "education_level": education_level,
                                "population": count
                            })

    return pd.DataFrame(records)


def get_distribution(lat: float, lon: float, year: int = 2023, force_tract: bool = True) -> dict:
    """
    Get joint age-education distribution for a location.
    Returns both marginal distributions and joint distribution data.
    """
    print(f"DEBUG: age_education get_distribution called with {lat}, {lon}")
    geo_info = get_geography(lat, lon)
    if not geo_info.get("state_fips"): return {}

    df = get_age_education_data(
        state_fips=geo_info["state_fips"],
        county_fips=geo_info["county_fips"],
        tract_fips=geo_info["tract_fips"],
        block_group_fips=geo_info["block_group_fips"],
        year=year,
        force_tract=True
    )

    print(f"DEBUG: Raw data shape: {df.shape}, population sum: {df['population'].sum() if not df.empty else 'EMPTY'}")

    if df.empty: return {}

    # Calculate marginal distributions with proper ordering
    age_marginal = df.groupby('age_range')['population'].sum().reset_index()
    sex_marginal = df.groupby('sex')['population'].sum().reset_index()
    education_marginal = df.groupby('education_level')['population'].sum().reset_index()
    
    # Sort marginals in ascending order
    age_order_marginal = ["18 to 24 years", "25 to 34 years", "35 to 44 years", "45 to 64 years", "65 years and over"]
    sex_order_marginal = ["Male", "Female"]
    education_order_marginal = ["Less than 9th grade", "9th to 12th grade, no diploma", "High school graduate (includes equivalency)", 
                               "Some college, no degree", "Associate's degree", "Bachelor's degree", 
                               "Graduate or professional degree"]
    
    age_marginal['sort_order'] = age_marginal['age_range'].map({v: i for i, v in enumerate(age_order_marginal)})
    age_marginal = age_marginal.sort_values('sort_order').drop('sort_order', axis=1)
    
    sex_marginal['sort_order'] = sex_marginal['sex'].map({v: i for i, v in enumerate(sex_order_marginal)})
    sex_marginal = sex_marginal.sort_values('sort_order').drop('sort_order', axis=1)
    
    education_marginal['sort_order'] = education_marginal['education_level'].map({v: i for i, v in enumerate(education_order_marginal)})
    education_marginal = education_marginal.sort_values('sort_order').drop('sort_order', axis=1)
    
    total_population = df['population'].sum()
    
    if total_population == 0:
        # DEBUG: This should be the return point for empty data
        print(f"DEBUG: age_education returning empty dict - total_population = {total_population}")
        return {}
    
    # Add percentages
    age_marginal['percentage'] = (age_marginal['population'] / total_population) * 100
    sex_marginal['percentage'] = (sex_marginal['population'] / total_population) * 100
    education_marginal['percentage'] = (education_marginal['population'] / total_population) * 100

    # Create initial distribution data
    joint_data_list = [
        {
            "age_range": row["age_range"],
            "sex": row["sex"],
            "education_level": row["education_level"],
            "population": int(row["population"]),
            "percentage": float((row["population"] / total_population) * 100)
        }
        for _, row in df.iterrows()
    ]
    
    print(f"DEBUG: Created {len(joint_data_list)} joint records from {len(df)} raw records")
    
    initial_data = {
        "type": "age_sex_education_joint",
        "joint_data": joint_data_list,
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
        "data_source": "Census ACS Detailed Table B15001"
    }
    
    return initial_data


def get_conditional_distribution(joint_data: dict, condition_type: str, condition_value: str, condition_value2: str = None) -> dict:
    """
    Get conditional distribution from joint data with support for multiple conditions.
    
    Args:
        joint_data: Result from get_distribution()
        condition_type: 'age', 'sex', 'education', 'age_sex', 'age_education', 'sex_education' - what to condition on
        condition_value: The specific value for first condition
        condition_value2: The specific value for second condition (if applicable)
        
    Returns:
        Conditional distribution data  
    """
    valid_single = ['age', 'sex', 'education']
    valid_double = ['age_sex', 'age_education', 'sex_education']
    
    if condition_type not in valid_single + valid_double:
        raise ValueError(f"condition_type must be one of {valid_single + valid_double}")
    
    # Check if joint data exists
    if not joint_data.get('joint_data'):
        return {
            "error": "No joint distribution data available for this location",
            "suggestion": "Try a different location or check if this distribution is available at this geographic level",
            "data_availability": False
        }
    
    joint_df = pd.DataFrame(joint_data['joint_data'])
    
    # Single condition cases
    if condition_type == 'age':
        # Given age range, return education distribution
        filtered_data = joint_df[joint_df['age_range'] == condition_value]
        if filtered_data.empty:
            return {"error": f"No data found for age range: {condition_value}"}
        
        total_population = filtered_data['population'].sum()
        
        # Aggregate by education level (summing across sex)
        education_summary = filtered_data.groupby('education_level')['population'].sum().reset_index()
        
        result = [
            {
                "category": row["education_level"],
                "value": int(row["population"]),
                "percentage": float((row["population"] / total_population) * 100) if total_population > 0 else 0
            }
            for _, row in education_summary.iterrows()
        ]
        
        return {
            "type": "conditional_education_given_age",
            "condition": f"Age: {condition_value}",
            "data": result,
            "total_population": int(total_population),
            "data_source": joint_data["data_source"]
        }
    
    elif condition_type == 'sex':
        # Given sex, return age-education distribution
        filtered_data = joint_df[joint_df['sex'] == condition_value]
        if filtered_data.empty:
            return {"error": f"No data found for sex: {condition_value}"}
        
        total_population = filtered_data['population'].sum()
        
        result = [
            {
                "age_range": row["age_range"],
                "education_level": row["education_level"],
                "value": int(row["population"]),
                "percentage": float((row["population"] / total_population) * 100) if total_population > 0 else 0
            }
            for _, row in filtered_data.iterrows()
        ]
        
        return {
            "type": "conditional_age_education_given_sex", 
            "condition": f"Sex: {condition_value}",
            "data": result,
            "total_population": int(total_population),
            "data_source": joint_data["data_source"]
        }
    
    elif condition_type == 'education':
        # Given education level, return age distribution (aggregated across sex)
        filtered_data = joint_df[joint_df['education_level'] == condition_value]
        if filtered_data.empty:
            return {"error": f"No data found for education level: {condition_value}"}
        
        total_population = filtered_data['population'].sum()
        
        # Aggregate by age_range (summing across sex)
        age_summary = filtered_data.groupby('age_range')['population'].sum().reset_index()
        
        result = [
            {
                "category": row["age_range"],
                "value": int(row["population"]),
                "percentage": float((row["population"] / total_population) * 100) if total_population > 0 else 0
            }
            for _, row in age_summary.iterrows()
        ]
        
        return {
            "type": "conditional_age_given_education",
            "condition": f"Education: {condition_value}",
            "data": result,
            "total_population": int(total_population),
            "data_source": joint_data["data_source"]
        }
    
    # Double condition cases
    elif condition_type == 'age_sex':
        # Given age and sex, return education distribution
        if condition_value2 is None:
            raise ValueError("condition_value2 required for age_sex conditioning")
        
        # Use raw age range as provided
        age_range = condition_value
        if not age_range:
            return {"error": f"Age range is required"}
        
        filtered_data = joint_df[(joint_df['age_range'] == age_range) & (joint_df['sex'] == condition_value2)]
        if filtered_data.empty:
            return {"error": f"No data found for age: {condition_value}, sex: {condition_value2}"}
        
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
            "type": "conditional_education_given_age_sex",
            "condition": f"Age: {condition_value}, Sex: {condition_value2}",
            "data": result,
            "total_population": int(total_population),
            "data_source": joint_data["data_source"]
        }
    
    elif condition_type == 'age_education':
        # Given age and education, return sex distribution
        if condition_value2 is None:
            raise ValueError("condition_value2 required for age_education conditioning")
        
        # Use raw age range as provided
        backend_age_range = condition_value
        if not backend_age_range:
            backend_age_range = condition_value
        
        filtered_data = joint_df[(joint_df['age_range'] == age_range) & (joint_df['education_level'] == condition_value2)]
        if filtered_data.empty:
            return {"error": f"No data found for age: {condition_value}, education: {condition_value2}"}
        
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
            "type": "conditional_sex_given_age_education",
            "condition": f"Age: {condition_value}, Education: {condition_value2}",
            "data": result,
            "total_population": int(total_population),
            "data_source": joint_data["data_source"]
        }
    
    elif condition_type == 'sex_education':
        # Given sex and education, return age distribution
        if condition_value2 is None:
            raise ValueError("condition_value2 required for sex_education conditioning")
        
        filtered_data = joint_df[(joint_df['sex'] == condition_value) & (joint_df['education_level'] == condition_value2)]
        if filtered_data.empty:
            return {"error": f"No data found for sex: {condition_value}, education: {condition_value2}"}
        
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
            "type": "conditional_age_given_sex_education",
            "condition": f"Sex: {condition_value}, Education: {condition_value2}",
            "data": result,
            "total_population": int(total_population),
            "data_source": joint_data["data_source"]
        }


if __name__ == "__main__":
    lat, lon = 37.736509, -122.388028  # San Francisco area

    print("=" * 60 + "\nAGE-SEX-EDUCATION JOINT DISTRIBUTION\n" + "=" * 60)
    
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
        
        print(f"\nSex Distribution:")
        for item in joint_data['sex_marginal']:
            print(f"  {item['category']}: {item['value']:,} people ({item['percentage']:.1f}%)")
        
        print(f"\nEducation Level Distribution:")
        for item in joint_data['education_marginal']:
            print(f"  {item['category']}: {item['value']:,} people ({item['percentage']:.1f}%)")
        
        # Example conditional distributions
        print(f"\n" + "=" * 60)
        print("EXAMPLE CONDITIONAL DISTRIBUTIONS")
        print("=" * 60)
        
        # Condition on age and sex together
        age_condition = "25 to 34 years"
        sex_condition = "Female"
        print(f"\nEducation distribution for {sex_condition}s aged {age_condition}:")
        conditional_education = get_conditional_distribution(joint_data, 'age_sex', age_condition, sex_condition)
        if 'error' not in conditional_education:
            for item in conditional_education['data']:
                if item['value'] > 0:
                    print(f"  {item['category']}: {item['value']:,} people ({item['percentage']:.1f}%)")
        
        # Condition on sex only
        sex_condition = "Male"
        print(f"\nAge-Education distribution for {sex_condition}s (top 10 combinations):")
        conditional_age_edu = get_conditional_distribution(joint_data, 'sex', sex_condition)
        if 'error' not in conditional_age_edu:
            # Sort by population and show top 10
            data_sorted = sorted(conditional_age_edu['data'], key=lambda x: x['value'], reverse=True)
            for item in data_sorted[:10]:
                if item['value'] > 0:
                    print(f"  {item['age_range']}, {item['education_level']}: {item['value']:,} people ({item['percentage']:.1f}%)")
        
        # Condition on education and sex together
        education_condition = "Bachelor's degree"
        sex_condition = "Female"
        print(f"\nAge distribution for {sex_condition}s with {education_condition}:")
        conditional_age = get_conditional_distribution(joint_data, 'sex_education', sex_condition, education_condition)
        if 'error' not in conditional_age:
            for item in conditional_age['data']:
                if item['value'] > 0:
                    print(f"  {item['category']}: {item['value']:,} people ({item['percentage']:.1f}%)")
    else:
        print("Could not retrieve data for the specified location.")