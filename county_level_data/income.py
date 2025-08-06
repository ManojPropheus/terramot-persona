import os
import requests
import pandas as pd

# Your Census API Key
CENSUS_API_KEY = 'f5fddae34f7f6adf93a768ac2589c032d3e2e0cf'


def get_and_process_block_group_income_data(state_fips: str, county_fips: str, year: int = 2023) -> pd.DataFrame:
    """
    Fetches raw household income data (Table B19001) for all block groups in a county,
    then processes it into a clean income distribution format.
    """
    print("Step 1: Fetching raw income data for all block groups...")

    # Using the ACS 5-Year Detailed Tables endpoint
    base_url = f"https://api.census.gov/data/{year}/acs/acs5"
    params = {
        "get": "group(B19001)",  # B19001 is the detailed table for Household Income
        "for": "block group:*",
        "in": f"state:{state_fips}+county:{county_fips}",
        "key": CENSUS_API_KEY
    }

    resp = requests.get(base_url, params=params)
    resp.raise_for_status()
    raw_data = resp.json()

    # Convert raw data to a DataFrame
    raw_df = pd.DataFrame(raw_data[1:], columns=raw_data[0])

    # Convert all data columns to numeric, coercing errors to 0
    data_cols = [col for col in raw_df.columns if col.startswith('B19001')]
    for col in data_cols:
        raw_df[col] = pd.to_numeric(raw_df[col], errors='coerce').fillna(0).astype(int)

    print("Step 2: Processing raw data into clean income brackets...")

    # Define the income brackets and map them to the correct Census columns
    income_bracket_mappings = {
        "Less than $10,000": "B19001_002E",
        "$10,000 to $14,999": "B19001_003E",
        "$15,000 to $19,999": "B19001_004E",
        "$20,000 to $24,999": "B19001_005E",
        "$25,000 to $29,999": "B19001_006E",
        "$30,000 to $34,999": "B19001_007E",
        "$35,000 to $39,999": "B19001_008E",
        "$40,000 to $44,999": "B19001_009E",
        "$45,000 to $49,999": "B19001_010E",
        "$50,000 to $59,999": "B19001_011E",
        "$60,000 to $74,999": "B19001_012E",
        "$75,000 to $99,999": "B19001_013E",
        "$100,000 to $124,999": "B19001_014E",
        "$125,000 to $149,999": "B19001_015E",
        "$150,000 to $199,999": "B19001_016E",
        "$200,000 or more": "B19001_017E"
    }

    processed_records = []
    # Iterate over each row of the raw data (each row is one block group)
    for index, block_group in raw_df.iterrows():
        total_households = block_group['B19001_001E']

        for bracket_name, column_code in income_bracket_mappings.items():
            household_count = block_group[column_code]
            percentage = (household_count * 100.0 / total_households) if total_households > 0 else 0

            processed_records.append({
                "GEO_ID": block_group["GEO_ID"],
                "block_group_name": block_group["NAME"],
                "total_households_in_block_group": total_households,
                "income_bracket": bracket_name,
                "household_count": household_count,
                "percentage_of_households": round(percentage, 2)
            })

    result = pd.DataFrame(processed_records)
    if 'GEO_ID' in result.columns:
        # remove everything up to and including 'US'
        result['GEO_ID'] = result['GEO_ID'].astype(str).str.replace(r'.*US', '', regex=True)
    result = result.drop(columns=["block_group_name", "total_households_in_block_group", "percentage_of_households"])
    csv_filename = "san_francisco_block_group_income_distribution.csv"
    result.to_csv(csv_filename, index=False)


if __name__ == "__main__":
    # FIPS codes for San Francisco, California
    sf_state_fips = "06"
    sf_county_fips = "075"

    print("=" * 60)
    print("Creating Household Income Distribution Summary for all SF Block Groups")
    print("=" * 60)

    try:
        # Get and process the data
        final_df = get_and_process_block_group_income_data(sf_state_fips, sf_county_fips)

        # Save the final, clean DataFrame to a CSV file
        csv_filename = "san_francisco_block_group_income_distribution.csv"
        final_df.to_csv(csv_filename, index=False)

        print(f"\nStep 3: Success! Saved the clean distribution to {csv_filename}")
        print("\nHere's a sample of the final data for the first block group:")
        print(final_df.head(16))  # Show all income brackets for the first block group

    except requests.exceptions.RequestException as e:
        print(f"\nAn error occurred while trying to fetch the data from the Census API: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred during processing: {e}")