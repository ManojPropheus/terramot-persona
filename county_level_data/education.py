import os
import requests
import pandas as pd

# Your Census API Key
CENSUS_API_KEY = 'f5fddae34f7f6adf93a768ac2589c032d3e2e0cf'


def get_and_process_block_group_education_data(state_fips: str, county_fips: str, year: int = 2023) -> pd.DataFrame:
    """
    Fetches raw educational attainment data (Table B15003) for all block groups in a county,
    then processes it into a clean distribution format.
    """
    print("Step 1: Fetching raw educational attainment data for all block groups...")

    # Using the ACS 5-Year Detailed Tables endpoint
    base_url = f"https://api.census.gov/data/{year}/acs/acs5"
    params = {
        "get": "group(B15003)",  # B15003 is the detailed table for Educational Attainment
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
    data_cols = [col for col in raw_df.columns if col.startswith('B15003')]
    for col in data_cols:
        raw_df[col] = pd.to_numeric(raw_df[col], errors='coerce').fillna(0).astype(int)

    print("Step 2: Processing raw data into clean education levels...")

    # Define the education levels and map them to the correct Census columns
    education_level_mappings = {
        "No schooling completed": "B15003_002E",
        "Nursery school": "B15003_003E",
        "Kindergarten": "B15003_004E",
        "1st grade": "B15003_005E",
        "2nd grade": "B15003_006E",
        "3rd grade": "B15003_007E",
        "4th grade": "B15003_008E",
        "5th grade": "B15003_009E",
        "6th grade": "B15003_010E",
        "7th grade": "B15003_011E",
        "8th grade": "B15003_012E",
        "9th grade": "B15003_013E",
        "10th grade": "B15003_014E",
        "11th grade": "B15003_015E",
        "12th grade, no diploma": "B15003_016E",
        "High school graduate (or equivalent)": "B15003_017E",
        "GED or alternative": "B15003_018E",
        "Some college, less than 1 year": "B15003_019E",
        "Some college, 1 or more years, no degree": "B15003_020E",
        "Associate's degree": "B15003_021E",
        "Bachelor's degree": "B15003_022E",
        "Master's degree": "B15003_023E",
        "Professional school degree": "B15003_024E",
        "Doctorate degree": "B15003_025E"
    }

    processed_records = []
    # Iterate over each row of the raw data (each row is one block group)
    for index, block_group in raw_df.iterrows():
        # The total is for the population 25 years and over
        total_pop_25_and_over = block_group['B15003_001E']

        for level_name, column_code in education_level_mappings.items():
            population_count = block_group[column_code]
            percentage = (population_count * 100.0 / total_pop_25_and_over) if total_pop_25_and_over > 0 else 0

            processed_records.append({
                "GEO_ID": block_group["GEO_ID"],
                "block_group_name": block_group["NAME"],
                "total_population_25_and_over": total_pop_25_and_over,
                "education_level": level_name,
                "population_count": population_count,
                "percentage_of_population": round(percentage, 2)
            })

    result = pd.DataFrame(processed_records)
    if 'GEO_ID' in result.columns:
        # remove everything up to and including 'US'
        result['GEO_ID'] = result['GEO_ID'].astype(str).str.replace(r'.*US', '', regex=True)
    result = result.drop(columns=["block_group_name", "total_population_25_and_over", "percentage_of_population"])
    csv_filename = "san_francisco_block_group_education_distribution.csv"
    result.to_csv(csv_filename, index=False)


if __name__ == "__main__":
    # FIPS codes for San Francisco, California
    sf_state_fips = "06"
    sf_county_fips = "075"

    print("=" * 60)
    print("Creating Educational Attainment Summary for all SF Block Groups")
    print("=" * 60)

    try:
        # Get and process the data
        final_df = get_and_process_block_group_education_data(sf_state_fips, sf_county_fips)

        # Save the final, clean DataFrame to a CSV file
        csv_filename = "san_francisco_block_group_education_distribution.csv"
        final_df.to_csv(csv_filename, index=False)

        print(f"\nStep 3: Success! Saved the clean distribution to {csv_filename}")
        print("\nHere's a sample of the final data for the first block group:")
        print(final_df.head(10))

    except requests.exceptions.RequestException as e:
        print(f"\nAn error occurred while trying to fetch the data from the Census API: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred during processing: {e}")