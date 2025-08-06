"""
Age & Income Joint Distribution from Census Data
Fetches joint distribution from Census Table B19037 and provides conditional distributions.
Allows conditioning on either age or income brackets to view corresponding distributions.
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


def get_age_income_data(state_fips: str, county_fips: str, tract_fips: str = None,
                        block_group_fips: str = None, year: int = 2023, force_tract: bool = False)-> pd.DataFrame:
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

    age_ranges = ['Under 25 years', '25 to 44 years', '45 to 64 years', '65 years and over']
    income_ranges = [
        "Less than $10,000", "$10,000 to $14,999", "$15,000 to $19,999",
        "$20,000 to $24,999", "$25,000 to $29,999", "$30,000 to $34,999",
        "$35,000 to $39,999", "$40,000 to $44,999", "$45,000 to $49,999",
        "$50,000 to $59,999", "$60,000 to $74,999", "$75,000 to $99,999",
        "$100,000 to $124,999", "$125,000 to $149,999",
        "$150,000 to $199,999", "$200,000 or more"
    ]

    records = []
    var_start_index = 3
    for i_age, age_range in enumerate(age_ranges):
        for i_income, income_range in enumerate(income_ranges):
            var_num = var_start_index + (i_age * 17) + i_income
            var_code = f"{table_to_get}_{str(var_num).zfill(3)}E"
            count = 0
            if var_code in df_full.columns:
                try: count = int(df_full[var_code].iloc[0])
                except (ValueError, TypeError): pass
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
    
    # Sort marginals in ascending order
    age_order = ["Under 25 years", "25 to 44 years", "45 to 64 years", "65 years and over"]
    income_order = ["Less than $10,000", "$10,000 to $14,999", "$15,000 to $19,999",
                   "$20,000 to $24,999", "$25,000 to $29,999", "$30,000 to $34,999", 
                   "$35,000 to $39,999", "$40,000 to $44,999", "$45,000 to $49,999",
                   "$50,000 to $59,999", "$60,000 to $74,999", "$75,000 to $99,999",
                   "$100,000 to $124,999", "$125,000 to $149,999", "$150,000 to $199,999",
                   "$200,000 or more"]
    
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
                "percentage": float((row["households"] / total_households) * 100)
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
        "data_source": "Census ACS Detailed Table B19037"
    }


def get_conditional_distribution(joint_data: dict, condition_type: str, condition_value: str) -> dict:
    """
    Get conditional distribution from joint data with age range mapping support.
    
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
        # Map frontend age range to backend age range if needed
        from .age_range_mapper import map_frontend_age_to_backend
        
        backend_age_range = map_frontend_age_to_backend(condition_value, 'age_income')
        if backend_age_range is None:
            # Try using the condition_value directly (might already be a backend range)
            backend_age_range = condition_value
        
        # Given age range, return income distribution
        filtered_data = joint_df[joint_df['age_range'] == backend_age_range]
        if filtered_data.empty:
            # Check if this is a valid frontend age range that maps to a backend range
            from .age_range_mapper import get_available_frontend_ages, get_backend_age_ranges
            available_frontend = get_available_frontend_ages('age_income')
            available_backend = get_backend_age_ranges('age_income')
            
            if condition_value in available_frontend:
                return {"error": f"Data not available for age range '{condition_value}'. This age range maps to '{backend_age_range}' but no data found for that range."}
            else:
                return {"error": f"Age range '{condition_value}' not supported for age-income data. Available age ranges: {', '.join(available_backend)}"}
        
        total_households = filtered_data['households'].sum()
        
        result = [
            {
                "category": row["income_range"],
                "value": int(row["households"]),
                "percentage": float((row["households"] / total_households) * 100) if total_households > 0 else 0
            }
            for _, row in filtered_data.iterrows()
        ]
        
        # Use original condition_value in the display
        condition_display = condition_value
        if backend_age_range != condition_value:
            condition_display = f"{condition_value} (grouped as {backend_age_range})"
        
        return {
            "type": "conditional_income_given_age",
            "condition": f"Age: {condition_display}",
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


def plot_joint_distribution(joint_data: dict, save_path: str = None) -> None:
    """
    Create a heatmap visualization of the joint age-income distribution.
    
    Args:
        joint_data: Result from get_distribution()
        save_path: Optional path to save the plot
    """
    df = pd.DataFrame(joint_data['joint_data'])
    location = joint_data['location']
    location_name = location.get("subdivision_name") or location.get("county_name")
    state_name = location.get("state_name")
    
    # Create pivot table for heatmap
    pivot_df = df.pivot(index='age_range', columns='income_range', values='households')
    
    # Set up the plot
    plt.style.use('default')
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Create heatmap
    sns.heatmap(pivot_df, annot=True, fmt='d', cmap='YlOrRd', ax=ax, 
                cbar_kws={'label': 'Number of Households'})
    
    ax.set_title(f'Age-Income Joint Distribution\n{location_name}, {state_name}', 
                 fontsize=14, fontweight='bold')
    ax.set_xlabel('Household Income Range', fontsize=12)
    ax.set_ylabel('Age of Householder', fontsize=12)
    
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    
    # Add data source information
    fig.suptitle(f'Data Source: {joint_data["data_source"]}', 
                 fontsize=10, y=0.02, ha='center')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Plot saved to: {save_path}")
    
    plt.show()


def plot_conditional_distribution(conditional_data: dict, save_path: str = None) -> None:
    """
    Create a bar chart for conditional distribution.
    
    Args:
        conditional_data: Result from get_conditional_distribution()
        save_path: Optional path to save the plot
    """
    if "error" in conditional_data:
        print(f"Error: {conditional_data['error']}")
        return
    
    data = conditional_data['data']
    condition = conditional_data['condition']
    
    # Set up the plot
    plt.style.use('default')
    fig, ax = plt.subplots(figsize=(12, 8))
    
    categories = [item['category'] for item in data]
    values = [item['value'] for item in data]
    percentages = [item['percentage'] for item in data]
    
    # Create color palette
    colors = plt.cm.viridis(np.linspace(0, 1, len(data)))
    
    # Create horizontal bar chart for better readability
    bars = ax.barh(range(len(categories)), values, color=colors)
    
    ax.set_yticks(range(len(categories)))
    ax.set_yticklabels(categories)
    ax.set_xlabel('Number of Households', fontsize=12)
    ax.set_title(f'Distribution Conditioned on {condition}\nTotal Households: {conditional_data["total_households"]:,}', 
                 fontsize=14, fontweight='bold')
    
    # Add value labels on bars
    for i, (bar, value, pct) in enumerate(zip(bars, values, percentages)):
        width = bar.get_width()
        ax.text(width + width*0.01, bar.get_y() + bar.get_height()/2,
                f'{value:,} ({pct:.1f}%)', ha='left', va='center', fontsize=9)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Add data source information
    fig.suptitle(f'Data Source: {conditional_data["data_source"]}', 
                 fontsize=10, y=0.02, ha='center')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Plot saved to: {save_path}")
    
    plt.show()


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
        age_condition = "25 to 44 years"
        print(f"\nIncome distribution for householders aged {age_condition}:")
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
        
        # Create visualizations
        print(f"\nCreating visualizations...")
        plot_joint_distribution(joint_data)
        
        if 'error' not in conditional_income:
            plot_conditional_distribution(conditional_income)
        
        if 'error' not in conditional_age:
            plot_conditional_distribution(conditional_age)
    else:
        print("Could not retrieve data for the specified location.")