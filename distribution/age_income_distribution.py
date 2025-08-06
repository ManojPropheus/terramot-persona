"""
Age & Income Joint Distribution from Census Data
Fetches joint distribution from Census Table B19037 and provides conditional distributions.
Table B19037: "Age of Householder by Household Income in the Past 12 Months (in 2023 Inflation-Adjusted Dollars)"
"""

import os
import requests
import pandas as pd

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


def get_age_income_data(state_fips: str, county_fips: str, tract_fips: str = None,
                        block_group_fips: str = None, year: int = 2023, force_tract: bool = False) -> pd.DataFrame:
    """
    Fetches joint age-income distribution from Census ACS Detailed Table B19037.
    """
    base_url = f"https://api.census.gov/data/{year}/acs/acs5"
    table_to_get = "B19037"
    params = {"get": f"NAME,group({table_to_get})"}

    if CENSUS_API_KEY:
        params["key"] = CENSUS_API_KEY

    geo_level, params["in"] = ("County", f"state:{state_fips}")
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

    print(f"Fetching Age/Income data for {geo_level}...")
    try:
        resp = requests.get(base_url, params=params)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        print(f"API Request failed: {e}")
        return pd.DataFrame()

    if len(data) < 2: return pd.DataFrame()

    df_full = pd.DataFrame(data[1:], columns=data[0])

    # Age ranges exactly as they appear in B19037
    age_ranges = [
        'Householder under 25 years',
        'Householder 25 to 44 years', 
        'Householder 45 to 64 years',
        'Householder 65 years and over'
    ]
    
    # Income ranges exactly as they appear in B19037 
    income_ranges = [
        "Less than $10,000", "$10,000 to $14,999", "$15,000 to $19,999",
        "$20,000 to $24,999", "$25,000 to $29,999", "$30,000 to $34,999", 
        "$35,000 to $39,999", "$40,000 to $44,999", "$45,000 to $49,999",
        "$50,000 to $59,999", "$60,000 to $74,999", "$75,000 to $99,999",
        "$100,000 to $124,999", "$125,000 to $149,999",
        "$150,000 to $199,999", "$200,000 or more"
    ]

    # B19037 Variable mapping based on actual Census structure:
    # B19037_003E to B19037_018E: Under 25 years (16 income brackets)
    # B19037_020E to B19037_035E: 25 to 44 years (16 income brackets) 
    # B19037_037E to B19037_052E: 45 to 64 years (16 income brackets)
    # B19037_054E to B19037_069E: 65 years and over (16 income brackets)
    
    age_start_vars = [3, 20, 37, 54]  # Starting variable numbers for each age group
    
    records = []
    for i_age, age_range in enumerate(age_ranges):
        start_var = age_start_vars[i_age]
        for i_income, income_range in enumerate(income_ranges):
            var_num = start_var + i_income
            var_code = f"{table_to_get}_{str(var_num).zfill(3)}E"
            count = 0
            if var_code in df_full.columns:
                try: 
                    count = int(df_full[var_code].iloc[0])
                except (ValueError, TypeError): 
                    count = 0
            records.append({"age_range": age_range, "income_range": income_range, "households": count})

    return pd.DataFrame(records)


def get_distribution(lat: float, lon: float, year: int = 2023, force_tract: bool = False) -> dict:
    """
    Get joint age-income distribution for a location.
    Returns both marginal distributions and joint distribution data.
    """
    geo_info = get_geography(lat, lon)
    if not geo_info.get("state_fips"): return {}

    df = get_age_income_data(
        state_fips=geo_info["state_fips"],
        county_fips=geo_info["county_fips"],
        tract_fips=geo_info["tract_fips"],
        block_group_fips=geo_info["block_group_fips"],
        year=year,
        force_tract=force_tract
    )

    if df.empty: return {}

    # Calculate marginal distributions with proper ordering
    age_marginal = df.groupby('age_range')['households'].sum().reset_index()
    income_marginal = df.groupby('income_range')['households'].sum().reset_index()
    
    # Sort marginals in the correct order
    age_order = [
        'Householder under 25 years',
        'Householder 25 to 44 years', 
        'Householder 45 to 64 years',
        'Householder 65 years and over'
    ]
    income_order = [
        "Less than $10,000", "$10,000 to $14,999", "$15,000 to $19,999",
        "$20,000 to $24,999", "$25,000 to $29,999", "$30,000 to $34,999", 
        "$35,000 to $39,999", "$40,000 to $44,999", "$45,000 to $49,999",
        "$50,000 to $59,999", "$60,000 to $74,999", "$75,000 to $99,999",
        "$100,000 to $124,999", "$125,000 to $149,999",
        "$150,000 to $199,999", "$200,000 or more"
    ]
    
    age_marginal['sort_order'] = age_marginal['age_range'].map({v: i for i, v in enumerate(age_order)})
    age_marginal = age_marginal.sort_values('sort_order').drop('sort_order', axis=1)
    
    income_marginal['sort_order'] = income_marginal['income_range'].map({v: i for i, v in enumerate(income_order)})
    income_marginal = income_marginal.sort_values('sort_order').drop('sort_order', axis=1)
    
    total_households = df['households'].sum()
    
    # Add percentages
    age_marginal['percentage'] = (age_marginal['households'] / total_households) * 100
    income_marginal['percentage'] = (income_marginal['households'] / total_households) * 100

    return {
        "type": "age_income_joint",
        "joint_data": [
            {
                "age_range": row["age_range"],
                "income_range": row["income_range"],
                "households": int(row["households"]),
                "percentage": float((row["households"] / total_households) * 100) if total_households > 0 else 0
            }
            for _, row in df.iterrows()
        ],
        "age_marginal": [
            {
                "category": row["age_range"],
                "value": int(row["households"]),
                "percentage": float(row["percentage"])
            }
            for _, row in age_marginal.iterrows()
        ],
        "income_marginal": [
            {
                "category": row["income_range"],
                "value": int(row["households"]),
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
        "data_source": "Census ACS Detailed Table B19037: Age of Householder by Household Income in the Past 12 Months (in 2023 Inflation-Adjusted Dollars)"
    }


def get_conditional_distribution(joint_data: dict, condition_type: str, condition_value: str) -> dict:
    """
    Get conditional distribution from joint data.
    
    Args:
        joint_data: Result from get_distribution()
        condition_type: 'age' or 'income' - what to condition on
        condition_value: The specific age range or income range to condition on
        
    Returns:
        Conditional distribution data
    """
    if condition_type not in ['age', 'income']:
        raise ValueError("condition_type must be 'age' or 'income'")
    
    joint_df = pd.DataFrame(joint_data['joint_data'])
    
    if condition_type == 'age':
        # Given age range, return income distribution
        filtered_data = joint_df[joint_df['age_range'] == condition_value]
        if filtered_data.empty:
            return {"error": f"No data found for age range: {condition_value}"}
        
        total_households = filtered_data['households'].sum()
        
        result = [
            {
                "category": row["income_range"],
                "value": int(row["households"]),
                "percentage": float((row["households"] / total_households) * 100) if total_households > 0 else 0
            }
            for _, row in filtered_data.iterrows()
        ]
        
        return {
            "type": "conditional_income_given_age",
            "condition": f"Age: {condition_value}",
            "data": result,
            "total_households": int(total_households),
            "data_source": joint_data["data_source"]
        }
    
    else:  # condition_type == 'income'
        # Given income range, return age distribution
        filtered_data = joint_df[joint_df['income_range'] == condition_value]
        if filtered_data.empty:
            return {"error": f"No data found for income range: {condition_value}"}
        
        total_households = filtered_data['households'].sum()
        
        result = [
            {
                "category": row["age_range"],
                "value": int(row["households"]),
                "percentage": float((row["households"] / total_households) * 100) if total_households > 0 else 0
            }
            for _, row in filtered_data.iterrows()
        ]
        
        return {
            "type": "conditional_age_given_income",
            "condition": f"Income: {condition_value}",
            "data": result,
            "total_households": int(total_households),
            "data_source": joint_data["data_source"]
        }


if __name__ == "__main__":
    lat, lon = 37.736509, -122.388028  # San Francisco area

    print("=" * 60 + "\nAGE-INCOME JOINT DISTRIBUTION\n" + "=" * 60)
    
    joint_data = get_distribution(lat, lon)

    if joint_data:
        location = joint_data['location']
        location_name = location.get("subdivision_name") or location.get("county_name")
        state_name = location.get("state_name")
        
        print(f"\nLocation: {location_name}, {state_name}")
        print(f"Data Source: {joint_data['data_source']}")
        
        # Show summary stats
        total_households = sum(item['households'] for item in joint_data['joint_data'])
        print(f"Total Households: {total_households:,}")
        
        print(f"\nAge Ranges Available:")
        for item in joint_data['age_marginal']:
            print(f"  {item['category']}: {item['value']:,} households ({item['percentage']:.1f}%)")
        
        print(f"\nIncome Ranges Available:")
        for item in joint_data['income_marginal']:
            print(f"  {item['category']}: {item['value']:,} households ({item['percentage']:.1f}%)")
        
        # Example conditional distributions
        print(f"\n" + "=" * 60)
        print("EXAMPLE CONDITIONAL DISTRIBUTIONS")
        print("=" * 60)
        
        # Condition on age
        age_condition = "Householder 25 to 44 years"
        print(f"\nIncome distribution for {age_condition}:")
        conditional_income = get_conditional_distribution(joint_data, 'age', age_condition)
        if 'error' not in conditional_income:
            for item in conditional_income['data']:
                print(f"  {item['category']}: {item['value']:,} households ({item['percentage']:.1f}%)")
        
        # Condition on income
        income_condition = "$50,000 to $59,999"
        print(f"\nAge distribution for households earning {income_condition}:")
        conditional_age = get_conditional_distribution(joint_data, 'income', income_condition)
        if 'error' not in conditional_age:
            for item in conditional_age['data']:
                print(f"  {item['category']}: {item['value']:,} households ({item['percentage']:.1f}%)")
    else:
        print("Could not retrieve data for the specified location.")