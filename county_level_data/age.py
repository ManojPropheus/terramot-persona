import os
from typing import final

import requests
import pandas as pd

# Your Census API Key
CENSUS_API_KEY = 'f5fddae34f7f6adf93a768ac2589c032d3e2e0cf'


def get_and_process_block_group_age_data(state_fips: str, county_fips: str, year: int = 2023) -> pd.DataFrame:
    """
    Fetches raw age data (Table B01001) for all block groups in a county,
    then processes it into a clean age distribution format.
    """
    print("Step 1: Fetching raw data for all block groups...")

    # Using the ACS 5-Year Detailed Tables endpoint
    base_url = f"https://api.census.gov/data/{year}/acs/acs5"
    params = {
        "get": "group(B01001)",
        "for": "block group:*",
        "in": f"state:{state_fips}+county:{county_fips}",
        "key": CENSUS_API_KEY
    }

    resp = requests.get(base_url, params=params)
    resp.raise_for_status()
    raw_data = resp.json()

    # Convert raw data to a DataFrame
    raw_df = pd.DataFrame(raw_data[1:], columns=raw_data[0])

    # Convert all population columns to numeric, coercing errors to 0
    data_cols = [col for col in raw_df.columns if col.startswith('B01001')]
    for col in data_cols:
        raw_df[col] = pd.to_numeric(raw_df[col], errors='coerce').fillna(0).astype(int)

    print("Step 2: Processing raw data into clean age groups...")

    # Define the age groups you want and map them to the correct Census columns
    # Each entry maps an age group to the Male column and the Female column
    age_group_mappings = {
        "Under 5 years": ("B01001_003E", "B01001_027E"),
        "5 to 9 years": ("B01001_004E", "B01001_028E"),
        "10 to 14 years": ("B01001_005E", "B01001_029E"),
        "15 to 19 years": (("B01001_006E", "B01001_007E"), ("B01001_030E", "B01001_031E")),  # Combines 15-17 and 18-19
        "20 to 24 years": (("B01001_008E", "B01001_009E"), ("B01001_032E", "B01001_033E")),
        # Combines 20, 21, and 22-24
        "25 to 29 years": ("B01001_010E", "B01001_034E"),
        "30 to 34 years": ("B01001_011E", "B01001_035E"),
        "35 to 39 years": ("B01001_012E", "B01001_036E"),
        "40 to 44 years": ("B01001_013E", "B01001_037E"),
        "45 to 49 years": ("B01001_014E", "B01001_038E"),
        "50 to 54 years": ("B01001_015E", "B01001_039E"),
        "55 to 59 years": ("B01001_016E", "B01001_040E"),
        "60 to 64 years": (("B01001_017E", "B01001_018E"), ("B01001_041E", "B01001_042E")),  # Combines 60-61 and 62-64
        "65 to 69 years": (("B01001_019E", "B01001_020E"), ("B01001_043E", "B01001_044E")),  # Combines 65-66 and 67-69
        "70 to 74 years": ("B01001_021E", "B01001_045E"),
        "75 to 79 years": ("B01001_022E", "B01001_046E"),
        "80 to 84 years": ("B01001_023E", "B01001_047E"),
        "85 years and over": ("B01001_024E", "B01001_025E", "B01001_048E", "B01001_049E")
        # Combined male and female columns
    }

    processed_records = []
    # Iterate over each row of the raw data (each row is one block group)
    for index, block_group in raw_df.iterrows():
        total_population = block_group['B01001_001E']
        for age_group, cols in age_group_mappings.items():
            population = 0
            # Flatten the tuple of columns in case there are multiple
            all_cols = []
            for item in cols:
                if isinstance(item, str):
                    all_cols.append(item)
                else:
                    all_cols.extend(item)

            # Sum the population from all specified columns for the age group
            for col in all_cols:
                if col in block_group:
                    population += block_group[col]

            percentage = (population * 100.0 / total_population) if total_population > 0 else 0

            processed_records.append({
                "GEO_ID": block_group["GEO_ID"],
                "block_group_name": block_group["NAME"],
                "total_block_group_population": total_population,
                "age_group": age_group,
                "population": population,
                "percentage": round(percentage, 2)
            })

    result = pd.DataFrame(processed_records)
    if 'GEO_ID' in result.columns:
        # remove everything up to and including 'US'
        result['GEO_ID'] = result['GEO_ID'].astype(str).str.replace(r'.*US', '', regex=True)
    result = result.drop(columns=["block_group_name", "total_block_group_population", "percentage"])
    csv_filename = "san_francisco_block_group_age_distribution.csv"
    result.to_csv(csv_filename, index=False)


if __name__ == "__main__":
    # FIPS codes for San Francisco, California
    sf_state_fips = "06"
    sf_county_fips = "075"

    print("=" * 60)
    print("Creating Age Distribution Summary for all SF Block Groups")
    print("=" * 60)

    try:
        # Get and process the data
        final_df = get_and_process_block_group_age_data(sf_state_fips, sf_county_fips)

        # Save the final, clean DataFrame to a CSV file
        csv_filename = "san_francisco_block_group_age_distribution.csv"
        final_df.to_csv(csv_filename, index=False)

        print(f"\nStep 3: Success! Saved the clean distribution to {csv_filename}")
        print("\nHere's a sample of the final data for the first block group:")
        print(final_df.head(18))  # Show all age groups for the first block group

    except requests.exceptions.RequestException as e:
        print(f"\nAn error occurred while trying to fetch the data from the Census API: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred during processing: {e}")