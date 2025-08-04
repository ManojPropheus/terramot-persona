"""
Gender Distribution from Census Data
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
    Get geographic information (state, county, subdivision) from coordinates.
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
    subs = geogs.get("County Subdivisions", [])
    
    if subs:
        subdiv = subs[0]
        subdiv_fips = subdiv["COUSUB"]
        subdiv_name = subdiv["NAME"]
    else:
        subdiv_fips = None
        subdiv_name = None

    return {
        "state_fips": state["STATE"],
        "state_name": state["NAME"],
        "county_fips": county["COUNTY"],
        "county_name": county["NAME"],
        "subdivision_fips": subdiv_fips,
        "subdivision_name": subdiv_name
    }


def get_gender_data_from_census(state_fips: str, county_fips: str, subdivision_fips: str = None, 
                               year: int = 2023, force_county: bool = False) -> pd.DataFrame:
    """
    Fetch gender distribution from Census ACS Subject Table S0101.
    Pure Census data - no modifications.
    """
    base_url = f"https://api.census.gov/data/{year}/acs/acs5/subject"
    params = {"get": "NAME,S0101_C01_001E,S0101_C03_001E,S0101_C05_001E"}
    
    if CENSUS_API_KEY:
        params["key"] = CENSUS_API_KEY

    # Set geography
    if subdivision_fips and not force_county:
        print(f"Fetching gender data for County Subdivision...")
        params["for"] = f"county subdivision:{subdivision_fips}"
        params["in"] = f"state:{state_fips} county:{county_fips}"
    else:
        print(f"Fetching gender data for County...")
        params["for"] = f"county:{county_fips}"
        params["in"] = f"state:{state_fips}"

    resp = requests.get(base_url, params=params)
    resp.raise_for_status()
    data = resp.json()

    # Convert to DataFrame
    df_full = pd.DataFrame([data[1]], columns=data[0])

    # Extract gender data
    total_population = int(df_full["S0101_C01_001E"].iloc[0])
    male_population = int(df_full["S0101_C03_001E"].iloc[0])
    female_population = int(df_full["S0101_C05_001E"].iloc[0])
    
    # Calculate percentages
    male_percentage = (male_population * 100.0 / total_population) if total_population > 0 else 0
    female_percentage = (female_population * 100.0 / total_population) if total_population > 0 else 0
    
    records = [
        {
            "gender": "Male",
            "population": male_population,
            "percentage": male_percentage
        },
        {
            "gender": "Female", 
            "population": female_population,
            "percentage": female_percentage
        },
        {
            "gender": "Total",
            "population": total_population,
            "percentage": 100.0
        }
    ]

    return pd.DataFrame(records)


def get_distribution(lat: float, lon: float, year: int = 2023, force_county: bool = False) -> dict:
    """
    Get gender distribution for a location.
    
    Args:
        lat: Latitude
        lon: Longitude
        year: ACS year (default 2023)
        force_county: Use county data instead of subdivision (default False)
        
    Returns:
        DataFrame with gender, population counts, and percentages
    """
    # Get geographic information
    geo_info = get_geography(lat, lon)
    
    # Fetch gender data from Census
    gender_df = get_gender_data_from_census(
        state_fips=geo_info["state_fips"],
        county_fips=geo_info["county_fips"],
        subdivision_fips=geo_info["subdivision_fips"],
        year=year,
        force_county=force_county
    )
    
    # Filter out 'Total' for API response
    data_df = gender_df[gender_df['gender'] != 'Total']
    
    # Return as JSON-serializable dict
    return {
        "type": "gender",
        "data": [
            {
                "category": row["gender"],
                "value": int(row["population"]),
                "percentage": float(row["percentage"])
            }
            for _, row in data_df.iterrows()
        ],
        "location": {
            "state_name": geo_info["state_name"],
            "county_name": geo_info["county_name"],
            "subdivision_name": geo_info["subdivision_name"]
        },
        "data_source": "Census ACS Subject Table S0101"
    }


def plot_gender_distribution(df: pd.DataFrame, save_path: str = None) -> None:
    """
    Create visualizations for gender distribution data.
    
    Args:
        df: DataFrame from gender_distribution() function
        save_path: Optional path to save the plot
    """
    location = df["subdivision_name"].iloc[0] or df["county_name"].iloc[0]
    state = df["state_name"].iloc[0]
    
    # Filter out 'Total' for visualization
    gender_data = df[df['gender'] != 'Total'].copy()
    
    # Set up the plot style
    plt.style.use('default')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Gender-appropriate colors
    colors = ['#4472C4', '#E15759']  # Blue for Male, Red/Pink for Female
    
    # Plot 1: Bar chart
    bars = ax1.bar(gender_data['gender'], gender_data['population'], color=colors)
    ax1.set_xlabel('Gender', fontsize=12)
    ax1.set_ylabel('Population', fontsize=12)
    ax1.set_title(f'Population by Gender\n{location}, {state}', fontsize=14, fontweight='bold')
    
    # Add value labels on bars
    for bar, pop in zip(bars, gender_data['population']):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                f'{pop:,}', ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    # Add percentage labels
    for bar, pct in zip(bars, gender_data['percentage']):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height*0.5,
                f'{pct:.1f}%', ha='center', va='center', fontsize=11, 
                color='white', fontweight='bold')
    
    # Plot 2: Pie chart
    ax2.pie(gender_data['percentage'], labels=gender_data['gender'], autopct='%1.1f%%',
            colors=colors, startangle=90, textprops={'fontsize': 12, 'fontweight': 'bold'})
    ax2.set_title(f'Gender Distribution\n{location}, {state}', 
                  fontsize=14, fontweight='bold')
    
    # Add total population info
    total_pop = df[df['gender'] == 'Total']['population'].iloc[0]
    fig.suptitle(f'Total Population: {total_pop:,} | Data Source: {df["data_source"].iloc[0]}', 
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
    print("GENDER DISTRIBUTION TEST")
    print("=" * 60)
    
    df = gender_distribution(lat, lon)
    
    location = df["subdivision_name"].iloc[0] or df["county_name"].iloc[0]
    state = df["state_name"].iloc[0]
    
    print(f"\nLocation: {location}, {state}")
    print(f"Data Source: {df['data_source'].iloc[0]}")
    
    print(f"\nGender Distribution:")
    print(f"{'Gender':<10} {'Population':<12} {'Percentage':<10}")
    print("-" * 35)
    
    for _, row in df.iterrows():
        print(f"{row['gender']:<10} {row['population']:<12,} {row['percentage']:<10.2f}%")
    
    # Gender ratio analysis
    male_pop = df[df['gender'] == 'Male']['population'].iloc[0]
    female_pop = df[df['gender'] == 'Female']['population'].iloc[0]
    
    if female_pop > 0:
        gender_ratio = male_pop / female_pop
        print(f"\nGender Ratio (Males per Female): {gender_ratio:.3f}")
        
        if gender_ratio > 1:
            print(f"There are {gender_ratio:.0f} males for every female")
        else:
            print(f"There are {1/gender_ratio:.0f} females for every male")
    
    # Create visualization
    print(f"\nCreating visualization...")
    plot_gender_distribution(df)