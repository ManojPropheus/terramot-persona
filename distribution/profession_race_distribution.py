"""
Profession-Race Distribution from Census Data (C24010A-I series)
Uses proper Census variable mappings with male/female aggregation
"""

import os
import requests
import pandas as pd

try:
    from .standard_categories import (
        STANDARD_PROFESSION_CATEGORIES,
        C24010_PROFESSION_MAPPING,
        STANDARD_RACE_ETHNICITY_CATEGORIES,
        C24010_RACE_TABLE_MAPPING
    )
except ImportError:
    from standard_categories import (
        STANDARD_PROFESSION_CATEGORIES,
        C24010_PROFESSION_MAPPING,
        STANDARD_RACE_ETHNICITY_CATEGORIES,
        C24010_RACE_TABLE_MAPPING
    )

CENSUS_API_KEY = 'f5fddae34f7f6adf93a768ac2589c032d3e2e0cf'

def get_geography(lat: float, lon: float) -> dict:
    """Get geographic information from coordinates."""
    url = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
    params = {"x": lon, "y": lat, "benchmark": "Public_AR_Census2020", "vintage": "Census2020_Census2020", "format": "json"}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    geogs = resp.json()["result"]["geographies"]

    state, county = geogs["States"][0], geogs["Counties"][0]
    tracts, blocks = geogs.get("Census Tracts", []), geogs.get("Census Blocks", [])
    
    tract_fips, tract_name = (tracts[0]["TRACT"], tracts[0]["NAME"]) if tracts else (None, None)
        
    if blocks:
        block = blocks[0]
        block_fips, block_name, block_geoid = block["BLOCK"], block["NAME"], block["GEOID"]
        block_group_fips = block.get("BLKGRP")
        block_group_name = f"Block Group {block_group_fips}" if block_group_fips else None
    else:
        block_fips = block_name = block_geoid = block_group_fips = block_group_name = None

    return {
        "state_fips": state["STATE"], "state_name": state["NAME"], "county_fips": county["COUNTY"], "county_name": county["NAME"],
        "tract_fips": tract_fips, "tract_name": tract_name, "block_group_fips": block_group_fips, "block_group_name": block_group_name,
        "block_fips": block_fips, "block_name": block_name, "block_geoid": block_geoid
    }

def get_distribution(lat: float, lon: float, year: int = 2023, force_tract: bool = False) -> dict:
    """Get profession-race joint distribution using proper C24010 variable mappings."""
    geo_info = get_geography(lat, lon)
    if not geo_info.get("state_fips"): 
        return {}

    base_url = f"https://api.census.gov/data/{year}/acs/acs5"
    all_records = []
    
    # Set geography parameters
    geo_params = {}
    if geo_info["block_group_fips"] and geo_info["tract_fips"] and not force_tract:
        geo_level = "Block Group"
        geo_params["for"] = f"block group:{geo_info['block_group_fips']}"
        geo_params["in"] = f"state:{geo_info['state_fips']} county:{geo_info['county_fips']} tract:{geo_info['tract_fips']}"
    elif geo_info["tract_fips"]:
        geo_level = "Census Tract"
        geo_params["for"] = f"tract:{geo_info['tract_fips']}"
        geo_params["in"] = f"state:{geo_info['state_fips']} county:{geo_info['county_fips']}"
    else:
        geo_level = "County"
        geo_params["for"] = f"county:{geo_info['county_fips']}"
        geo_params["in"] = f"state:{geo_info['state_fips']}"

    print(f"Fetching Profession/Race data (C24010A-I) for {geo_level}...")
    
    # Fetch data for each race-specific table
    for table_code, race_name in C24010_RACE_TABLE_MAPPING.items():
        params = {"get": f"NAME,group({table_code})"}
        if CENSUS_API_KEY:
            params["key"] = CENSUS_API_KEY
        params.update(geo_params)
        
        try:
            resp = requests.get(base_url, params=params)
            resp.raise_for_status()
            data = resp.json()
            
            if len(data) < 2:
                continue
                
            df_full = pd.DataFrame([data[1]], columns=data[0])
            
            # Process each profession using standard mapping
            for profession, gender_codes in C24010_PROFESSION_MAPPING.items():
                male_pop = 0
                female_pop = 0
                
                # Sum male populations for this profession
                for var_code in gender_codes["male"]:
                    var_name = f"{table_code}_{var_code}E"
                    if var_name in df_full.columns:
                        try:
                            male_pop += int(float(df_full[var_name].iloc[0] or 0))
                        except (ValueError, TypeError):
                            pass
                
                # Sum female populations for this profession
                for var_code in gender_codes["female"]:
                    var_name = f"{table_code}_{var_code}E"
                    if var_name in df_full.columns:
                        try:
                            female_pop += int(float(df_full[var_name].iloc[0] or 0))
                        except (ValueError, TypeError):
                            pass
                
                total_pop = male_pop + female_pop
                if total_pop > 0:
                    all_records.append({
                        "profession": profession,
                        "race_ethnicity": race_name,
                        "population": total_pop,
                        "male_population": male_pop,
                        "female_population": female_pop
                    })
                    
        except Exception as e:
            print(f"Warning: Could not fetch {table_code} for {race_name}: {e}")
            continue

    if not all_records: 
        print("Warning: No profession-race data available for this location")
        return {}
        
    df = pd.DataFrame(all_records)
    
    # Calculate marginal distributions
    profession_marginal = df.groupby('profession')['population'].sum().reset_index()
    race_marginal = df.groupby('race_ethnicity')['population'].sum().reset_index()
    
    total_pop = df['population'].sum()
    if total_pop > 0:
        profession_marginal['percentage'] = (profession_marginal['population'] * 100.0 / total_pop)
        race_marginal['percentage'] = (race_marginal['population'] * 100.0 / total_pop)
        df['percentage'] = (df['population'] * 100.0 / total_pop)
    else:
        profession_marginal['percentage'] = race_marginal['percentage'] = df['percentage'] = 0

    return {
        "type": "profession_race_joint",
        "joint_data": [
            {
                "profession": row["profession"], 
                "race_ethnicity": row["race_ethnicity"], 
                "value": int(row["population"]), 
                "percentage": float(row["percentage"])
            } 
            for _, row in df.iterrows()
        ],
        "profession_marginal": [
            {
                "category": row["profession"], 
                "value": int(row["population"]), 
                "percentage": float(row["percentage"])
            } 
            for _, row in profession_marginal.iterrows()
        ],
        "race_marginal": [
            {
                "category": row["race_ethnicity"], 
                "value": int(row["population"]), 
                "percentage": float(row["percentage"])
            } 
            for _, row in race_marginal.iterrows()
        ],
        "location": {
            "state_name": geo_info["state_name"], 
            "county_name": geo_info["county_name"], 
            "tract_name": geo_info["tract_name"],
            "block_group_name": geo_info["block_group_name"], 
            "block_name": geo_info["block_name"], 
            "block_geoid": geo_info["block_geoid"]
        },
        "data_source": "Census ACS Detailed Tables C24010A/B/C/D/E/F/G/I - Proper variable mappings",
        "total_population": int(total_pop)
    }

def get_conditional_distribution(joint_data: dict, condition_type: str, condition_value: str) -> dict:
    """Get conditional distribution from joint profession-race data."""
    if not joint_data or "joint_data" not in joint_data:
        return {"error": "No joint distribution data available"}
    
    joint_df = pd.DataFrame(joint_data["joint_data"])
    
    if condition_type == "profession":
        filtered_data = joint_df[joint_df["profession"] == condition_value]
        if filtered_data.empty: 
            return {"error": f"No data found for profession: {condition_value}"}
        
        total_for_profession = filtered_data["value"].sum()
        
        result = [
            {
                "category": row["race_ethnicity"],
                "value": int(row["value"]),
                "percentage": float((row["value"] * 100.0 / total_for_profession) if total_for_profession > 0 else 0)
            }
            for _, row in filtered_data.iterrows()
        ]
        
        return {
            "type": "conditional_race_given_profession",
            "condition": f"Profession: {condition_value}",
            "data": result,
            "total_population": int(total_for_profession),
            "data_source": joint_data.get("data_source", "")
        }
    
    elif condition_type == "race":
        filtered_data = joint_df[joint_df["race_ethnicity"] == condition_value]
        if filtered_data.empty: 
            return {"error": f"No data found for race/ethnicity: {condition_value}"}
        
        total_for_race = filtered_data["value"].sum()
        
        result = [
            {
                "category": row["profession"],
                "value": int(row["value"]),
                "percentage": float((row["value"] * 100.0 / total_for_race) if total_for_race > 0 else 0)
            }
            for _, row in filtered_data.iterrows()
        ]
        
        return {
            "type": "conditional_profession_given_race",
            "condition": f"Race/Ethnicity: {condition_value}",
            "data": result,
            "total_population": int(total_for_race),
            "data_source": joint_data.get("data_source", "")
        }
    
    else:
        return {"error": f"Invalid condition_type: {condition_type}. Must be 'profession' or 'race'"}

if __name__ == "__main__":
    result = get_distribution(37.736509, -122.388028)
    print(f"Profession-Race joint data: {len(result.get('joint_data', []))}")