import os
import requests
import pandas as pd

# Your Census API Key
CENSUS_API_KEY = 'f5fddae34f7f6adf93a768ac2589c032d3e2e0cf'


def get_and_process_block_group_race_ethnicity_data(state_fips: str, county_fips: str,
                                                    year: int = 2023) -> pd.DataFrame:
    """
    Fetches raw race and ethnicity data (Table B03002) for all block groups in a county,
    then processes it into a clean distribution format.
    """
    print("Step 1: Fetching original data for all block groups...")

    # The API call to get the raw data group for Hispanic or Latino Origin by Race
    base_url = f"https://api.census.gov/data/{year}/acs/acs5"
    params = {
        "get": "group(B03002)",
        "for": "block group:*",  # This data is available at the block group level
        "in": f"state:{state_fips}+county:{county_fips}",
        "key": CENSUS_API_KEY
    }

    resp = requests.get(base_url, params=params)
    resp.raise_for_status()
    raw_data = resp.json()

    # Convert the original data to a DataFrame
    raw_df = pd.DataFrame(raw_data[1:], columns=raw_data[0])

    # Ensure all data columns are numeric for calculations
    data_cols = [col for col in raw_df.columns if col.startswith('B03002')]
    for col in data_cols:
        raw_df[col] = pd.to_numeric(raw_df[col], errors='coerce').fillna(0).astype(int)

    print("Step 2: Preprocessing by mapping columns to race/ethnicity categories...")

    # Mapping of categories to their respective column codes from table B03002
    race_ethnicity_mappings = {
        "Hispanic or Latino": "B03002_012E",
        "Not Hispanic or Latino: White alone": "B03002_003E",
        "Not Hispanic or Latino: Black or African American alone": "B03002_004E",
        "Not Hispanic or Latino: American Indian and Alaska Native alone": "B03002_005E",
        "Not Hispanic or Latino: Asian alone": "B03002_006E",
        "Not Hispanic or Latino: Native Hawaiian and Other Pacific Islander alone": "B03002_007E",
        "Not Hispanic or Latino: Some other race alone": "B03002_008E",
        "Not Hispanic or Latino: Two or more races": "B03002_009E"
    }

    processed_records = []
    # Iterate through each row (each row is a block group)
    for index, block_group_data in raw_df.iterrows():
        # Total population in this block group
        total_population = block_group_data['B03002_001E']

        # For each category, get the count and calculate the percentage
        for category_name, column_code in race_ethnicity_mappings.items():
            population_count = block_group_data[column_code]
            percentage = (population_count * 100.0 / total_population) if total_population > 0 else 0

            processed_records.append({
                "GEO_ID": block_group_data["GEO_ID"],
                "block_group_name": block_group_data["NAME"],
                "total_population": total_population,
                "race_ethnicity_category": category_name,
                "population_count": population_count,
                "percentage_of_total_population": round(percentage, 2)
            })

    result = pd.DataFrame(processed_records)
    if 'GEO_ID' in result.columns:
        # remove everything up to and including 'US'
        result['GEO_ID'] = result['GEO_ID'].astype(str).str.replace(r'.*US', '', regex=True)
    result = result.drop(columns=["block_group_name", "total_population", "percentage_of_total_population"])
    csv_filename = "san_francisco_block_group_race_ethnicity.csv"
    result.to_csv(csv_filename, index=False)


if __name__ == "__main__":
    # FIPS codes for San Francisco, California
    sf_state_fips = "06"
    sf_county_fips = "075"

    print("=" * 60)
    print("Creating Race & Ethnicity Summary for all SF Block Groups")
    print("=" * 60)

    try:
        final_df = get_and_process_block_group_race_ethnicity_data(sf_state_fips, sf_county_fips)

        csv_filename = "san_francisco_block_group_race_ethnicity.csv"
        final_df.to_csv(csv_filename, index=False)

        print(f"\nStep 3: Success! Saved the final distribution to {csv_filename}")
        print("\nHere's a sample of the final data for the first block group:")
        print(final_df.head(8))  # Show all categories for the first block group

    except requests.exceptions.RequestException as e:
        print(f"\nAn error occurred while trying to fetch the data from the Census API: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred during processing: {e}")