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


def get_education_data_from_census(state_fips: str, county_fips: str, subdivision_fips: str = None, 
                                  year: int = 2023, force_county: bool = False) -> pd.DataFrame:
    """
    Fetch educational attainment distribution from Census ACS Subject Table S1501.
    Pure Census data - no modifications.
    """
    base_url = f"https://api.census.gov/data/{year}/acs/acs5/subject"
    params = {"get": "NAME,group(S1501)"}
    
    if CENSUS_API_KEY:
        params["key"] = CENSUS_API_KEY

    # Set geography
    if subdivision_fips and not force_county:
        print(f"Fetching education data for County Subdivision...")
        params["for"] = f"county subdivision:{subdivision_fips}"
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

    # Education levels and their corresponding variable codes in S1501
    education_levels = [
        "Less than 9th grade",
        "9th to 12th grade, no diploma", 
        "High school graduate (includes equivalency)",
        "Some college, no degree",
        "Associate's degree",
        "Bachelor's degree",
        "Graduate or professional degree"
    ]
    
    # Variable codes for educational attainment in S1501 (population 25 years and over)
    education_var_codes = [
        "S1501_C01_007E",  # Less than 9th grade
        "S1501_C01_008E",  # 9th to 12th grade, no diploma
        "S1501_C01_009E",  # High school graduate
        "S1501_C01_010E",  # Some college, no degree
        "S1501_C01_011E",  # Associate's degree
        "S1501_C01_012E",  # Bachelor's degree
        "S1501_C01_013E"   # Graduate or professional degree
    ]
    
    # Total population 25 years and over
    total_population = int(df_full["S1501_C01_006E"].iloc[0])
    
    # Extract education distribution data
    records = []
    for education_level, var_code in zip(education_levels, education_var_codes):
        if var_code in df_full.columns:
            population = int(df_full[var_code].iloc[0])
            percentage = (population * 100.0 / total_population) if total_population > 0 else 0
            
            records.append({
                "education_level": education_level,
                "population": population,
                "percentage": percentage
            })

    return pd.DataFrame(records)


def get_distribution(lat: float, lon: float, year: int = 2023, force_county: bool = False) -> dict:
    """
    Get educational attainment distribution for a location.
    
    Args:
        lat: Latitude
        lon: Longitude
        year: ACS year (default 2023)
        force_county: Use county data instead of subdivision (default False)
        
    Returns:
        DataFrame with education levels, population counts, and percentages
    """
    # Get geographic information
    geo_info = get_geography(lat, lon)
    
    # Fetch education data from Census
    education_df = get_education_data_from_census(
        state_fips=geo_info["state_fips"],
        county_fips=geo_info["county_fips"],
        subdivision_fips=geo_info["subdivision_fips"],
        year=year,
        force_county=force_county
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
            "subdivision_name": geo_info["subdivision_name"]
        },
        "data_source": "Census ACS Subject Table S1501"
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
    
    df = education_distribution(lat, lon)
    
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