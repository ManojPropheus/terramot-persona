import os
import requests
import pandas as pd

# Your Census API Key
CENSUS_API_KEY = 'f5fddae34f7f6adf93a768ac2589c032d3e2e0cf'


def get_and_process_total_occupation_data(state_fips: str, county_fips: str, year: int = 2023) -> pd.DataFrame:
    """
    Fetches raw occupation data (Table C24010) for all census tracts, then preprocesses
    it by summing the male and female counts for each broad occupation category.
    """
    print("Step 1: Fetching original data for all census tracts...")

    # The API call to get the raw data group
    base_url = f"https://api.census.gov/data/{year}/acs/acs5"
    params = {
        "get": "group(C24010)",
        "for": "tract:*",  # Data is for census tracts, not block groups
        "in": f"state:{state_fips}+county:{county_fips}",
        "key": CENSUS_API_KEY
    }

    resp = requests.get(base_url, params=params)
    resp.raise_for_status()
    raw_data = resp.json()

    # Convert the original data to a DataFrame
    raw_df = pd.DataFrame(raw_data[1:], columns=raw_data[0])

    # Ensure all data columns are numeric for calculations
    data_cols = [col for col in raw_df.columns if col.startswith('C24010')]
    for col in data_cols:
        raw_df[col] = pd.to_numeric(raw_df[col], errors='coerce').fillna(0).astype(int)

    print("Step 2: Preprocessing by adding male and female counts for each category...")

    # Mapping of categories to their respective Male and Female column codes
    occupation_mappings = {
        "Management, business, science, and arts": ('C24010_003E', 'C24010_039E'),
        "Service occupations": ('C24010_018E', 'C24010_055E'),
        "Sales and office occupations": ('C24010_024E', 'C24010_061E'),
        "Natural resources, construction, and maintenance": ('C24010_030E', 'C24010_067E'),
        "Production, transportation, and material moving": ('C24010_034E', 'C24010_071E')
    }

    processed_records = []
    # Iterate through each row (each row is a census tract)
    for index, tract_data in raw_df.iterrows():
        # Total employed population 16+ in this tract
        total_employed_pop = tract_data['C24010_001E']

        # For each occupation category, sum the male and female counts
        for category_name, (male_col, female_col) in occupation_mappings.items():
            # This is the preprocessing step you requested:
            total_population_count = tract_data[male_col] + tract_data[female_col]

            percentage = (total_population_count * 100.0 / total_employed_pop) if total_employed_pop > 0 else 0

            processed_records.append({
                "GEO_ID": tract_data["GEO_ID"],
                "census_tract_name": tract_data["NAME"],
                "total_employed_population_16_and_over": total_employed_pop,
                "occupation_category": category_name,
                "population_count": total_population_count,
                "percentage_of_employed_population": round(percentage, 2)
            })

    result = pd.DataFrame(processed_records)
    if 'GEO_ID' in result.columns:
        # remove everything up to and including 'US'
        result['GEO_ID'] = result['GEO_ID'].astype(str).str.replace(r'.*US', '', regex=True)
    result = result.drop(columns=["census_tract_name", "total_employed_population_16_and_over", "percentage_of_employed_population"])
    csv_filename = "san_francisco_tract_profession.csv"
    result.to_csv(csv_filename, index=False)


if __name__ == "__main__":
    # FIPS codes for San Francisco, California
    sf_state_fips = "06"
    sf_county_fips = "075"

    print("=" * 60)
    print("Creating Total Occupation Summary for all SF Census Tracts")
    print("=" * 60)

    try:
        final_df = get_and_process_total_occupation_data(sf_state_fips, sf_county_fips)

        csv_filename = "san_francisco_tract_profession.csv"
        final_df.to_csv(csv_filename, index=False)

        print(f"\nStep 3: Success! Saved the final distribution to {csv_filename}")
        print("\nHere's a sample of the final data for the first census tract:")
        print(final_df.head())

    except requests.exceptions.RequestException as e:
        print(f"\nAn error occurred while trying to fetch the data from the Census API: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred during processing: {e}")