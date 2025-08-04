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


def get_age_data_from_census(state_fips: str, county_fips: str, subdivision_fips: str = None, 
                            year: int = 2023, force_county: bool = False) -> pd.DataFrame:
    """
    Fetch age distribution from Census ACS Subject Table S0101.
    Pure Census data - no modifications.
    """
    base_url = f"https://api.census.gov/data/{year}/acs/acs5/subject"
    params = {"get": "NAME,group(S0101)"}
    
    if CENSUS_API_KEY:
        params["key"] = CENSUS_API_KEY

    # Set geography
    if subdivision_fips and not force_county:
        print(f"Fetching age data for County Subdivision...")
        params["for"] = f"county subdivision:{subdivision_fips}"
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

    # Age groups and their corresponding variable codes in S0101
    age_groups = [
        "Under 5 years", "5 to 9 years", "10 to 14 years", "15 to 19 years",
        "20 to 24 years", "25 to 29 years", "30 to 34 years", "35 to 39 years",
        "40 to 44 years", "45 to 49 years", "50 to 54 years", "55 to 59 years",
        "60 to 64 years", "65 to 69 years", "70 to 74 years", "75 to 79 years",
        "80 to 84 years", "85 years and over"
    ]
    
    # Total population
    total_population = int(df_full["S0101_C01_001E"].iloc[0])
    
    # Extract age distribution data
    records = []
    for idx, age_group in enumerate(age_groups):
        var_code = f"S0101_C01_{idx+2:03d}E"  # Variables start from S0101_C01_002E
        
        if var_code in df_full.columns:
            population = int(df_full[var_code].iloc[0])
            percentage = (population * 100.0 / total_population) if total_population > 0 else 0
            
            records.append({
                "age_group": age_group,
                "population": population,
                "percentage": percentage
            })

    return pd.DataFrame(records)


def get_distribution(lat: float, lon: float, year: int = 2023, force_county: bool = False) -> dict:
    """
    Get age distribution for a location.
    
    Args:
        lat: Latitude
        lon: Longitude
        year: ACS year (default 2023)
        force_county: Use county data instead of subdivision (default False)
        
    Returns:
        DataFrame with age groups, population counts, and percentages
    """
    # Get geographic information
    geo_info = get_geography(lat, lon)
    
    # Fetch age data from Census
    age_df = get_age_data_from_census(
        state_fips=geo_info["state_fips"],
        county_fips=geo_info["county_fips"],
        subdivision_fips=geo_info["subdivision_fips"],
        year=year,
        force_county=force_county
    )
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
            "subdivision_name": geo_info["subdivision_name"]
        },
        "data_source": "Census ACS Subject Table S0101"
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