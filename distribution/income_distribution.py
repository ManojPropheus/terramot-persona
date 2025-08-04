"""
Income Distribution from Census Data
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


def get_income_data_from_census(state_fips: str, county_fips: str, subdivision_fips: str = None, 
                               year: int = 2023, force_county: bool = False) -> pd.DataFrame:
    """
    Fetch household income distribution from Census ACS Subject Table S1901.
    Pure Census data - no modifications.
    """
    base_url = f"https://api.census.gov/data/{year}/acs/acs5/subject"
    params = {"get": "NAME,group(S1901)"}
    
    if CENSUS_API_KEY:
        params["key"] = CENSUS_API_KEY

    # Set geography
    if subdivision_fips and not force_county:
        print(f"Fetching income data for County Subdivision...")
        params["for"] = f"county subdivision:{subdivision_fips}"
        params["in"] = f"state:{state_fips} county:{county_fips}"
    else:
        print(f"Fetching income data for County...")
        params["for"] = f"county:{county_fips}"
        params["in"] = f"state:{state_fips}"

    resp = requests.get(base_url, params=params)
    resp.raise_for_status()
    data = resp.json()

    # Convert to DataFrame
    df_full = pd.DataFrame([data[1]], columns=data[0])

    # Income ranges and their corresponding variable codes in S1901
    income_ranges = [
        "Less than $10,000",
        "$10,000 to $14,999", 
        "$15,000 to $24,999",
        "$25,000 to $34,999",
        "$35,000 to $49,999",
        "$50,000 to $74,999",
        "$75,000 to $99,999",
        "$100,000 to $149,999",
        "$150,000 to $199,999",
        "$200,000 or more"
    ]
    
    # Variable codes for household income distribution in S1901
    income_var_codes = [
        "S1901_C01_002E",  # Less than $10,000
        "S1901_C01_003E",  # $10,000 to $14,999
        "S1901_C01_004E",  # $15,000 to $24,999
        "S1901_C01_005E",  # $25,000 to $34,999
        "S1901_C01_006E",  # $35,000 to $49,999
        "S1901_C01_007E",  # $50,000 to $74,999
        "S1901_C01_008E",  # $75,000 to $99,999
        "S1901_C01_009E",  # $100,000 to $149,999
        "S1901_C01_010E",  # $150,000 to $199,999
        "S1901_C01_011E"   # $200,000 or more
    ]
    
    # Total households
    total_households = int(df_full["S1901_C01_001E"].iloc[0])
    
    # Extract income distribution data
    records = []
    for income_range, var_code in zip(income_ranges, income_var_codes):
        if var_code in df_full.columns:
            try:
                # S1901 table contains percentages, not counts
                percentage = float(df_full[var_code].iloc[0])
                households = int((percentage * total_households) / 100.0)
                
                records.append({
                    "income_range": income_range,
                    "households": households,
                    "percentage": percentage
                })
            except (ValueError, TypeError):
                # Skip if data is not available
                pass

    return pd.DataFrame(records)


def get_distribution(lat: float, lon: float, year: int = 2023, force_county: bool = False) -> dict:
    """
    Get household income distribution for a location.
    
    Args:
        lat: Latitude
        lon: Longitude
        year: ACS year (default 2023)
        force_county: Use county data instead of subdivision (default False)
        
    Returns:
        DataFrame with income ranges, household counts, and percentages
    """
    # Get geographic information
    geo_info = get_geography(lat, lon)
    
    # Fetch income data from Census
    income_df = get_income_data_from_census(
        state_fips=geo_info["state_fips"],
        county_fips=geo_info["county_fips"],
        subdivision_fips=geo_info["subdivision_fips"],
        year=year,
        force_county=force_county
    )
    
    # Return as JSON-serializable dict
    return {
        "type": "income",
        "data": [
            {
                "category": row["income_range"],
                "value": int(row["households"]),
                "percentage": float(row["percentage"])
            }
            for _, row in income_df.iterrows()
        ],
        "location": {
            "state_name": geo_info["state_name"],
            "county_name": geo_info["county_name"],
            "subdivision_name": geo_info["subdivision_name"]
        },
        "data_source": "Census ACS Subject Table S1901"
    }


def plot_income_distribution(df: pd.DataFrame, save_path: str = None) -> None:
    """
    Create visualizations for income distribution data.
    
    Args:
        df: DataFrame from income_distribution() function
        save_path: Optional path to save the plot
    """
    location = df["subdivision_name"].iloc[0] or df["county_name"].iloc[0]
    state = df["state_name"].iloc[0]
    
    # Set up the plot style
    plt.style.use('default')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Color palette - use income-appropriate colors (green gradient)
    colors = plt.cm.Greens(np.linspace(0.3, 1.0, len(df)))
    
    # Plot 1: Horizontal bar chart for better income range readability
    bars = ax1.barh(range(len(df)), df['households'], color=colors)
    ax1.set_xlabel('Number of Households', fontsize=12)
    ax1.set_ylabel('Income Range', fontsize=12)
    ax1.set_title(f'Households by Income Range\n{location}, {state}', fontsize=14, fontweight='bold')
    ax1.set_yticks(range(len(df)))
    ax1.set_yticklabels(df['income_range'])
    
    # Add value labels on bars
    for bar, households in zip(bars, df['households']):
        width = bar.get_width()
        ax1.text(width + width*0.01, bar.get_y() + bar.get_height()/2.,
                f'{households:,}', ha='left', va='center', fontsize=9)
    
    # Plot 2: Pie chart of income percentages
    # Only show slices with significant percentages for clarity
    threshold = 2.0  # Show only slices > 2%
    large_slices = df[df['percentage'] >= threshold]
    small_slices = df[df['percentage'] < threshold]
    
    if len(small_slices) > 0:
        # Combine small slices
        other_households = small_slices['households'].sum()
        other_percentage = small_slices['percentage'].sum()
        
        plot_data = large_slices.copy()
        plot_data = pd.concat([plot_data, pd.DataFrame({
            'income_range': ['Other (< 2%)'],
            'households': [other_households],
            'percentage': [other_percentage]
        })], ignore_index=True)
    else:
        plot_data = df
    
    ax2.pie(plot_data['percentage'], labels=plot_data['income_range'], autopct='%1.1f%%',
            startangle=90, colors=plt.cm.Greens(np.linspace(0.3, 1.0, len(plot_data))))
    ax2.set_title(f'Income Distribution Percentages\n{location}, {state}', 
                  fontsize=14, fontweight='bold')
    
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
    print("INCOME DISTRIBUTION TEST")
    print("=" * 60)
    
    df = income_distribution(lat, lon)
    
    location = df["subdivision_name"].iloc[0] or df["county_name"].iloc[0]
    state = df["state_name"].iloc[0]
    
    print(f"\nLocation: {location}, {state}")
    print(f"Data Source: {df['data_source'].iloc[0]}")
    print(f"Total Households: {df['households'].sum():,}")
    
    print(f"\nIncome Distribution:")
    print(f"{'Income Range':<20} {'Households':<12} {'Percentage':<10}")
    print("-" * 45)
    
    for _, row in df.iterrows():
        print(f"{row['income_range']:<20} {row['households']:<12,} {row['percentage']:<10.2f}%")
    
    print(f"\nTop 5 Income Ranges:")
    top_incomes = df.nlargest(5, 'households')
    for _, row in top_incomes.iterrows():
        print(f"  {row['income_range']}: {row['households']:,} ({row['percentage']:.1f}%)")
    
    # Create visualization
    print(f"\nCreating visualization...")
    plot_income_distribution(df)