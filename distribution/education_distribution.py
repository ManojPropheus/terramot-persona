"""
Education Distribution from Census Data
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


def get_geography(lat: float, lon: float) -> dict | None:
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


def get_education_data_from_census(state_fips: str, county_fips: str, tract_fips: str = None, 
                                  block_group_fips: str = None, year: int = 2023, force_tract: bool = False) -> pd.DataFrame:
    """
    Fetch educational attainment distribution from Census ACS Detailed Table B15003 at block group level.
    Pure Census data - no modifications.
    """
    base_url = f"https://api.census.gov/data/{year}/acs/acs5"
    params = {"get": "NAME,group(B15003)"}
    
    if CENSUS_API_KEY:
        params["key"] = CENSUS_API_KEY

    # Set geography - prefer block group level
    if block_group_fips and tract_fips and not force_tract:
        print(f"Fetching education data for Block Group...")
        params["for"] = f"block group:{block_group_fips}"
        params["in"] = f"state:{state_fips} county:{county_fips} tract:{tract_fips}"
    elif tract_fips:
        print(f"Fetching education data for Census Tract...")
        params["for"] = f"tract:{tract_fips}"
        params["in"] = f"state:{state_fips} county:{county_fips}"
    else:
        print(f"Fetching education data for County...")
        params["for"] = f"county:{county_fips}"
        params["in"] = f"state:{state_fips}"

    resp = requests.get(base_url, params=params)
    resp.raise_for_status()
    data = resp.json()

    # Convert to DataFrame
    df_full = pd.DataFrame([data[1]], columns=data[0])

    # Education levels from B15003 table - aggregated for meaningful analysis
    education_levels_mapping = [
        ("Less than 9th grade", ["B15003_002E", "B15003_003E", "B15003_004E", "B15003_005E", "B15003_006E", "B15003_007E", "B15003_008E", "B15003_009E"]),
        ("9th to 12th grade, no diploma", ["B15003_010E", "B15003_011E", "B15003_012E", "B15003_013E", "B15003_014E", "B15003_015E"]),
        ("High school graduate (includes equivalency)", ["B15003_016E", "B15003_017E"]),
        ("Some college, no degree", ["B15003_018E", "B15003_019E", "B15003_020E"]),
        ("Associate's degree", ["B15003_021E"]),
        ("Bachelor's degree", ["B15003_022E"]),
        ("Graduate or professional degree", ["B15003_023E", "B15003_024E", "B15003_025E"])
    ]
    
    # Total population 25 years and over
    total_population = int(df_full["B15003_001E"].iloc[0])
    
    # Extract education distribution data
    records = []
    for education_level, var_codes in education_levels_mapping:
        population = 0
        for var_code in var_codes:
            if var_code in df_full.columns:
                try:
                    population += int(df_full[var_code].iloc[0])
                except (ValueError, TypeError):
                    pass  # Skip if data not available
        
        percentage = (population * 100.0 / total_population) if total_population > 0 else 0
        
        records.append({
            "education_level": education_level,
            "population": population,
            "percentage": percentage
        })

    return pd.DataFrame(records)


def get_distribution(lat: float, lon: float, year: int = 2023, force_tract: bool = False) -> dict:
    """
    Get educational attainment distribution for a location at block group level.
    
    Args:
        lat: Latitude
        lon: Longitude
        year: ACS year (default 2023)
        force_tract: Use tract data instead of block group (default False)
        
    Returns:
        Dict with education levels, population counts, and percentages
    """
    # Get geographic information
    geo_info = get_geography(lat, lon)
    
    # Fetch education data from Census
    education_df = get_education_data_from_census(
        state_fips=geo_info["state_fips"],
        county_fips=geo_info["county_fips"],
        tract_fips=geo_info["tract_fips"],
        block_group_fips=geo_info["block_group_fips"],
        year=year,
        force_tract=force_tract
    )
    
    # Return as JSON-serializable dict
    return {
        "type": "education",
        "data": [
            {
                "category": row["education_level"],
                "value": int(row["population"]),
                "percentage": float(row["percentage"])
            }
            for _, row in education_df.iterrows()
        ],
        "location": {
            "state_name": geo_info["state_name"],
            "county_name": geo_info["county_name"],
            "tract_name": geo_info["tract_name"],
            "block_group_name": geo_info["block_group_name"],
            "block_name": geo_info["block_name"],
            "block_geoid": geo_info["block_geoid"]
        },
        "data_source": "Census ACS Detailed Table B15003"
    }


def plot_education_distribution(df: pd.DataFrame, save_path: str = None) -> None:
    """
    Create visualizations for education distribution data.
    
    Args:
        df: DataFrame from education_distribution() function
        save_path: Optional path to save the plot
    """
    location = df["subdivision_name"].iloc[0] or df["county_name"].iloc[0]
    state = df["state_name"].iloc[0]
    
    # Set up the plot style
    plt.style.use('default')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))
    
    # Education-appropriate colors (blue gradient for knowledge/learning)
    colors = plt.cm.Blues(np.linspace(0.3, 1.0, len(df)))
    
    # Plot 1: Horizontal bar chart for better education level readability
    bars = ax1.barh(range(len(df)), df['population'], color=colors)
    ax1.set_xlabel('Population (25+ years)', fontsize=12)
    ax1.set_ylabel('Education Level', fontsize=12)
    ax1.set_title(f'Population by Education Level\n{location}, {state}', fontsize=14, fontweight='bold')
    ax1.set_yticks(range(len(df)))
    ax1.set_yticklabels(df['education_level'])
    
    # Add value labels on bars
    for bar, pop in zip(bars, df['population']):
        width = bar.get_width()
        ax1.text(width + width*0.01, bar.get_y() + bar.get_height()/2.,
                f'{pop:,}', ha='left', va='center', fontsize=10)
    
    # Plot 2: Pie chart of education percentages
    # Group small categories for better visualization
    threshold = 3.0  # Show only slices > 3%
    large_slices = df[df['percentage'] >= threshold]
    small_slices = df[df['percentage'] < threshold]
    
    if len(small_slices) > 0:
        # Combine small slices
        other_population = small_slices['population'].sum()
        other_percentage = small_slices['percentage'].sum()
        
        plot_data = large_slices.copy()
        plot_data = pd.concat([plot_data, pd.DataFrame({
            'education_level': ['Other (< 3%)'],
            'population': [other_population],
            'percentage': [other_percentage]
        })], ignore_index=True)
    else:
        plot_data = df
    
    # Create pie chart with better labels
    wedges, texts, autotexts = ax2.pie(plot_data['percentage'], 
                                      labels=[label[:25] + '...' if len(label) > 25 else label 
                                             for label in plot_data['education_level']], 
                                      autopct='%1.1f%%',
                                      startangle=90, 
                                      colors=plt.cm.Blues(np.linspace(0.3, 1.0, len(plot_data))))
    
    ax2.set_title(f'Education Distribution\n{location}, {state}', 
                  fontsize=14, fontweight='bold')
    
    # Adjust text properties for better readability
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    # Add data source information
    total_pop = df['population'].sum()
    fig.suptitle(f'Total Population (25+ years): {total_pop:,} | Data Source: {df["data_source"].iloc[0]}', 
                 fontsize=11, y=0.02, ha='center')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Plot saved to: {save_path}")
    
    plt.show()


if __name__ == "__main__":
    # Test the function
    lat, lon = 37.736509, -122.388028  # San Francisco area
    
    print("=" * 60)
    print("EDUCATION DISTRIBUTION TEST")
    print("=" * 60)
    
    df = get_distribution(lat, lon)
    
    location = df["subdivision_name"].iloc[0] or df["county_name"].iloc[0]
    state = df["state_name"].iloc[0]
    
    print(f"\nLocation: {location}, {state}")
    print(f"Data Source: {df['data_source'].iloc[0]}")
    print(f"Total Population (25+ years): {df['population'].sum():,}")
    
    print(f"\nEducational Attainment Distribution:")
    print(f"{'Education Level':<35} {'Population':<12} {'Percentage':<10}")
    print("-" * 60)
    
    for _, row in df.iterrows():
        print(f"{row['education_level']:<35} {row['population']:<12,} {row['percentage']:<10.2f}%")
    
    print(f"\nTop 3 Education Levels:")
    top_education = df.nlargest(3, 'population')
    for _, row in top_education.iterrows():
        print(f"  {row['education_level']}: {row['population']:,} ({row['percentage']:.1f}%)")
    
    # Higher education analysis
    higher_ed = df[df['education_level'].isin([
        "Associate's degree", "Bachelor's degree", "Graduate or professional degree"
    ])]
    
    if len(higher_ed) > 0:
        higher_ed_pop = higher_ed['population'].sum()
        higher_ed_pct = higher_ed_pop * 100.0 / df['population'].sum()
        print(f"\nHigher Education (Associate's+): {higher_ed_pop:,} ({higher_ed_pct:.1f}%)")
    
    # Bachelor's degree or higher
    bachelors_plus = df[df['education_level'].isin([
        "Bachelor's degree", "Graduate or professional degree"
    ])]
    
    if len(bachelors_plus) > 0:
        bachelors_pop = bachelors_plus['population'].sum()
        bachelors_pct = bachelors_pop * 100.0 / df['population'].sum()
        print(f"Bachelor's Degree or Higher: {bachelors_pop:,} ({bachelors_pct:.1f}%)")
    
    # Create visualization
    print(f"\nCreating visualization...")
    plot_education_distribution(df)