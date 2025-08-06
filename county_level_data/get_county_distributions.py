import pandas as pd
import requests
import os
from age import get_and_process_block_group_age_data
from education import get_and_process_block_group_education_data
from gender import get_and_process_block_group_gender_data
from income import get_and_process_block_group_income_data
from profession import get_and_process_total_occupation_data
from race import get_and_process_block_group_race_ethnicity_data


def get_geography(lat: float, lon: float) -> dict:
    """
    Get geographic information (state, county, tract, block group, block) from coordinates.
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

    # Get Census Tract and Block information
    tracts = geogs.get("Census Tracts", [])
    blocks = geogs.get("Census Blocks", [])

    if tracts:
        tract = tracts[0]
        tract_fips = tract["TRACT"]
        tract_name = tract["NAME"]
    else:
        tract_fips = None
        tract_name = None

    if blocks:
        block = blocks[0]
        block_fips = block["BLOCK"]
        block_name = block["NAME"]
        block_geoid = block["GEOID"]
        # Extract block group info from the block data
        block_group_fips = block.get("BLKGRP")
        if block_group_fips:
            block_group_name = f"Block Group {block_group_fips}"
        else:
            block_group_name = None
    else:
        block_fips = None
        block_name = None
        block_geoid = None
        block_group_fips = None
        block_group_name = None

    return {
        "state_fips": state["STATE"],
        "state_name": state["NAME"],
        "county_fips": county["COUNTY"],
        "county_name": county["NAME"],
        "tract_fips": tract_fips,
        "tract_name": tract_name,
        "block_group_fips": block_group_fips,
        "block_group_name": block_group_name,
        "block_fips": block_fips,
        "block_name": block_name,
        "block_geoid": block_geoid
    }


def concatenate_and_process_data():
    """
    Concatenates multiple CSV files into a single DataFrame, renames the
    categorical column to 'brackets', and adds a 'data_type' column.

    Args:
        file_paths (list): A list of file paths to the CSV files.

    Returns:
        pandas.DataFrame: A single DataFrame containing the combined and
                          processed data from all files.
    """

    # This mapping helps identify the categorical and count columns in each file
    # and assign a 'data_type' for the new column.
    file_paths = [
        'san_francisco_block_group_age_distribution.csv',
        'san_francisco_block_group_education_distribution.csv',
        'san_francisco_block_group_gender_distribution.csv',
        'san_francisco_block_group_income_distribution.csv',
        'san_francisco_block_group_race_ethnicity.csv',
        'san_francisco_tract_profession.csv'
    ]
    file_config = {
        'age_distribution': {'categorical_col': 'age_group', 'count_col': 'population', 'data_type': 'Age'},
        'education_distribution': {'categorical_col': 'education_level', 'count_col': 'population_count',
                                   'data_type': 'Education'},
        'gender_distribution': {'categorical_col': 'gender', 'count_col': 'population', 'data_type': 'Gender'},
        'income_distribution': {'categorical_col': 'income_bracket', 'count_col': 'household_count',
                                'data_type': 'Income'},
        'race_ethnicity': {'categorical_col': 'race_ethnicity_category', 'count_col': 'population_count',
                           'data_type': 'Race/Ethnicity'},
        'profession': {'categorical_col': 'occupation_category', 'count_col': 'population_count',
                       'data_type': 'Profession'}
    }

    all_dataframes = []

    print("Starting data processing...")

    for file_path in file_paths:
        # Extract a unique keyword from the filename to use with our config
        file_key = None
        for key in file_config.keys():
            if key in file_path:
                file_key = key
                break

        if not file_key:
            print(f"Warning: No configuration found for file: {file_path}. Skipping.")
            continue

        try:
            # Read the CSV file into a DataFrame
            df = pd.read_csv(file_path)
            print(f"Successfully read {file_path}")

            config = file_config[file_key]

            # 1. Rename the categorical column to 'brackets'
            df.rename(columns={config['categorical_col']: 'brackets'}, inplace=True)

            # 2. Rename the count column to 'count' for standardization
            df.rename(columns={config['count_col']: 'count'}, inplace=True)

            # 3. Add the new 'data_type' column
            df['data_type'] = config['data_type']

            # Ensure the column order is consistent
            # We will keep GEO_ID, brackets, count, and data_type
            # and drop any other columns if they exist.
            final_cols = ['GEO_ID', 'brackets', 'count', 'data_type']
            # Filter to only keep columns that actually exist in the dataframe
            existing_cols = [col for col in final_cols if col in df.columns]
            df = df[existing_cols]

            all_dataframes.append(df)
            print(f"Processed '{config['data_type']}' data.")

        except FileNotFoundError:
            print(f"Error: The file was not found at {file_path}")
        except Exception as e:
            print(f"An error occurred while processing {file_path}: {e}")

    if not all_dataframes:
        print("No dataframes were processed. Returning an empty DataFrame.")
        return pd.DataFrame()

    # Concatenate all the processed DataFrames
    combined_df = pd.concat(all_dataframes, ignore_index=True)
    combined_df.to_csv("combined_data.csv", index=False)
    print("\nAll files have been processed and concatenated.")

    return combined_df

def get_dist(lat,lon):
    geography = get_geography(lat,lon)
    state_fips = geography["state_fips"]
    county_fips = geography["county_fips"]
    get_and_process_total_occupation_data(state_fips, county_fips)
    get_and_process_block_group_race_ethnicity_data(state_fips, county_fips)
    get_and_process_block_group_gender_data(state_fips, county_fips)
    get_and_process_block_group_income_data(state_fips, county_fips)
    get_and_process_block_group_age_data(state_fips, county_fips)
    get_and_process_block_group_education_data(state_fips, county_fips)
    concatenate_and_process_data()
    os.remove('san_francisco_block_group_education_distribution.csv')
    os.remove('san_francisco_block_group_gender_distribution.csv')
    os.remove('san_francisco_block_group_income_distribution.csv')
    os.remove('san_francisco_block_group_race_ethnicity.csv')
    os.remove('san_francisco_tract_profession.csv')
    os.remove('san_francisco_block_group_age_distribution.csv')

if __name__ == "__main__":
    lat, lon = 37.736509, -122.388028
    get_dist(lat, lon)