"""
Age Distribution from Census Data
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


def get_age_data_from_census(state_fips: str, county_fips: str, tract_fips: str = None, 
                            block_group_fips: str = None, year: int = 2023, force_tract: bool = False) -> pd.DataFrame:
    """
    Fetch age distribution from Census ACS Detailed Table B01001 at block group level.
    Pure Census data - no modifications.
    """
    base_url = f"https://api.census.gov/data/{year}/acs/acs5"
    params = {"get": "NAME,group(B01001)"}
    
    if CENSUS_API_KEY:
        params["key"] = CENSUS_API_KEY

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

    resp = requests.get(base_url, params=params)
    resp.raise_for_status()
    data = resp.json()

    # Convert to DataFrame
    df_full = pd.DataFrame([data[1]], columns=data[0])

    # Import standard age mapping from reference file
    try:
        from .standard_categories import B01001_AGE_MAPPING
    except ImportError:
        from standard_categories import B01001_AGE_MAPPING
    
    # Use standardized age ranges for consistency across all distributions
    age_groups_mapping = [(age_range, [f"B01001_{code}E" for code in codes]) 
                         for age_range, codes in B01001_AGE_MAPPING.items()]
    
    # Total population
    total_population = int(df_full["B01001_001E"].iloc[0])
    
    # Extract age distribution data
    records = []
    for age_group, var_codes in age_groups_mapping:
        population = 0
        for var_code in var_codes:
            if var_code in df_full.columns:
                try:
                    population += int(df_full[var_code].iloc[0])
                except (ValueError, TypeError):
                    pass  # Skip if data not available
        
        percentage = (population * 100.0 / total_population) if total_population > 0 else 0
        
        records.append({
            "age_group": age_group,
            "population": population,
            "percentage": percentage
        })

    return pd.DataFrame(records)


def get_distribution(lat: float, lon: float, year: int = 2023, force_tract: bool = False) -> dict:
    """
    Get age distribution for a location at block group level.
    
    Args:
        lat: Latitude
        lon: Longitude
        year: ACS year (default 2023)
        force_tract: Use tract data instead of block group (default False)
        
    Returns:
        Dict with age groups, population counts, and percentages
    """
    # Get geographic information
    geo_info = get_geography(lat, lon)
    
    # Fetch age data from Census
    age_df = get_age_data_from_census(
        state_fips=geo_info["state_fips"],
        county_fips=geo_info["county_fips"],
        tract_fips=geo_info["tract_fips"],
        block_group_fips=geo_info["block_group_fips"],
        year=year,
        force_tract=force_tract
    )
    
    # Sort age groups in chronological order
    age_order = [
        "Under 5 years", "5 to 9 years", "10 to 14 years", "15 to 19 years",
        "20 to 24 years", "25 to 34 years", "35 to 44 years", "45 to 54 years",
        "55 to 64 years", "65 to 74 years", "75 to 84 years", "85 years and over"
    ]
    
    # Create mapping and handle any missing values
    age_order_map = {v: i for i, v in enumerate(age_order)}
    age_df['sort_order'] = age_df['age_group'].map(age_order_map)
    
    # Fill any NaN values (age groups not in our order list) with a high number to put them at the end
    age_df['sort_order'] = age_df['sort_order'].fillna(999)
    age_df = age_df.sort_values('sort_order').drop('sort_order', axis=1)
    
    # Return as JSON-serializable dict
    return {
        "type": "age",
        "data": [
            {
                "category": row["age_group"],
                "value": int(row["population"]),
                "percentage": float(row["percentage"])
            }
            for _, row in age_df.iterrows()
        ],
        "location": {
            "state_name": geo_info["state_name"],
            "county_name": geo_info["county_name"],
            "tract_name": geo_info["tract_name"],
            "block_group_name": geo_info["block_group_name"],
            "block_name": geo_info["block_name"],
            "block_geoid": geo_info["block_geoid"]
        },
        "data_source": "Census ACS Detailed Table B01001"
    }


def plot_age_distribution(df: pd.DataFrame, save_path: str = None) -> None:
    """
    Create visualizations for age distribution data.
    
    Args:
        df: DataFrame from age_distribution() function
        save_path: Optional path to save the plot
    """
    location = df["subdivision_name"].iloc[0] or df["county_name"].iloc[0]
    state = df["state_name"].iloc[0]
    
    # Set up the plot style
    plt.style.use('default')
    fig, (ax1) = plt.subplots(1, 1, figsize=(16, 8))
    
    # Color palette
    colors = plt.cm.viridis(np.linspace(0, 1, len(df)))
    
    # Plot 1: Bar chart of population by age group
    bars = ax1.bar(range(len(df)), df['population'], color=colors)
    ax1.set_xlabel('Age Group', fontsize=12)
    ax1.set_ylabel('Population', fontsize=12)
    ax1.set_title(f'Population by Age Group\n{location}, {state}', fontsize=14, fontweight='bold')
    ax1.set_xticks(range(len(df)))
    ax1.set_xticklabels(df['age_group'], rotation=45, ha='right')
    
    # Add value labels on bars
    for bar, pop in zip(bars, df['population']):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                f'{pop:,}', ha='center', va='bottom', fontsize=9)
    
    # # Plot 2: Pie chart of age percentages
    # ax2.pie(df['percentage'], labels=df['age_group'], autopct='%1.1f%%',
    #         colors=colors, startangle=90)
    # ax2.set_title(f'Age Distribution Percentages\n{location}, {state}',
    #               fontsize=14, fontweight='bold')
    
    # Add data source information
    fig.suptitle(f'Data Source: {df["data_source"].iloc[0]}', 
                 fontsize=10, y=0.02, ha='center')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Plot saved to: {save_path}")
    
    plt.show()


if __name__ == "__main__":
    # Test the function
    lat, lon = 37.736509, -122.388028  # San Francisco area
    
    print("=" * 60)
    print("AGE DISTRIBUTION TEST")
    print("=" * 60)
    
    df = get_distribution(lat, lon)