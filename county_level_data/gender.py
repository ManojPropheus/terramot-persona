import os
import requests
import pandas as pd

# Your Census API Key
CENSUS_API_KEY = 'f5fddae34f7f6adf93a768ac2589c032d3e2e0cf'


def get_and_process_block_group_gender_data(state_fips: str, county_fips: str, year: int = 2023) -> pd.DataFrame:
    """
    Fetches raw age and sex data (Table B01001) for all block groups in a county,
    then processes it into a clean gender distribution format.
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

    print("Step 2: Processing raw data into clean gender distribution...")

    processed_records = []
    # Iterate over each row of the raw data (each row is one block group)
    for index, block_group in raw_df.iterrows():
        total_population = block_group['B01001_001E']
        male_population = block_group['B01001_002E']
        female_population = block_group['B01001_026E']

        # Add a record for Males
        processed_records.append({
            "GEO_ID": block_group["GEO_ID"],
            "block_group_name": block_group["NAME"],
            "total_block_group_population": total_population,
            "gender": "Male",
            "population": male_population,
            "percentage": round((male_population * 100.0 / total_population) if total_population > 0 else 0, 2)
        })

        # Add a record for Females
        processed_records.append({
            "GEO_ID": block_group["GEO_ID"],
            "block_group_name": block_group["NAME"],
            "total_block_group_population": total_population,
            "gender": "Female",
            "population": female_population,
            "percentage": round((female_population * 100.0 / total_population) if total_population > 0 else 0, 2)
        })

    result = pd.DataFrame(processed_records)
    if 'GEO_ID' in result.columns:
        # remove everything up to and including 'US'
        result['GEO_ID'] = result['GEO_ID'].astype(str).str.replace(r'.*US', '', regex=True)
    result = result.drop(columns=["block_group_name", "total_block_group_population", "percentage"])
    csv_filename = "san_francisco_block_group_gender_distribution.csv"
    result.to_csv(csv_filename, index=False)


if __name__ == "__main__":
    # FIPS codes for San Francisco, California
    sf_state_fips = "06"
    sf_county_fips = "075"

    print("=" * 60)
    print("Creating Gender Distribution Summary for all SF Block Groups")
    print("=" * 60)

    try:
        # Get and process the data
        final_df = get_and_process_block_group_gender_data(sf_state_fips, sf_county_fips)

        # Save the final, clean DataFrame to a CSV file
        csv_filename = "san_francisco_block_group_gender_distribution.csv"
        final_df.to_csv(csv_filename, index=False)

        print(f"\nStep 3: Success! Saved the clean distribution to {csv_filename}")
        print("\nHere's a sample of the final data for the first block group:")
        print(final_df.head(2))  # Show the male/female summary for the first block group

    except requests.exceptions.RequestException as e:
        print(f"\nAn error occurred while trying to fetch the data from the Census API: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred during processing: {e}")