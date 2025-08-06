"""
Census Tables Reference
Documentation of Census ACS tables, their variables, and proper usage patterns.
"""

# Census Table Definitions and Usage Guidelines
CENSUS_TABLES = {
    # Age and Gender Tables
    "B01001": {
        "title": "Sex by Age",
        "description": "Population counts by sex and detailed age groups",
        "has_sex_breakdown": True,
        "total_variable": "001",
        "male_total": "002", 
        "female_total": "026",
        "usage": "Primary table for age distributions and age-sex joint distributions",
        "variable_pattern": "Male vars: 003-025, Female vars: 027-049"
    },
    
    "B01001A": {
        "title": "Sex by Age (White Alone)",
        "description": "Population counts by sex and age for White alone population",
        "has_sex_breakdown": True,
        "race_specific": "White Alone",
        "usage": "For age-race joint distributions"
    },
    
    # Income Tables
    "B19001": {
        "title": "Household Income in the Past 12 Months",
        "description": "Household income distribution in detailed ranges",
        "has_sex_breakdown": False,
        "total_variable": "001",
        "usage": "Primary table for income distributions",
        "variable_range": "002-017 for income ranges"
    },
    
    "B19001A": {
        "title": "Household Income (White Alone Householder)",
        "description": "Household income by race of householder",
        "has_sex_breakdown": False,
        "race_specific": "White Alone",
        "usage": "For income-race joint distributions"
    },
    
    # Occupation Tables
    "C24010": {
        "title": "Sex by Occupation for the Civilian Employed Population 16 Years and Over",
        "description": "Detailed occupation categories by sex",
        "has_sex_breakdown": True,
        "total_variable": "001",
        "male_total": "002",
        "female_total": "038",
        "usage": "Primary table for profession distributions and profession-gender joint distributions",
        "variable_pattern": "Male vars: 003-037, Female vars: 039-073"
    },
    
    "C24010A": {
        "title": "Sex by Occupation (White Alone)",
        "description": "Occupation by sex for White alone population", 
        "has_sex_breakdown": True,
        "race_specific": "White Alone",
        "usage": "For profession-race joint distributions"
    },
    
    # Education Tables
    "B15003": {
        "title": "Educational Attainment for the Population 25 Years and Over",
        "description": "Detailed educational attainment categories",
        "has_sex_breakdown": False,
        "total_variable": "001",
        "usage": "Primary table for education distributions",
        "variable_range": "002-025 for education levels"
    },
    
    "C15002": {
        "title": "Sex by Educational Attainment for the Population 25 Years and Over", 
        "description": "Educational attainment by sex",
        "has_sex_breakdown": True,
        "total_variable": "001",
        "male_total": "002",
        "female_total": "011", 
        "usage": "For education-gender joint distributions",
        "variable_pattern": "Male vars: 003-010, Female vars: 012-019"
    },
    
    # INCORRECT TABLES TO AVOID
    "C24020": {
        "title": "Median Earnings by Occupation", 
        "description": "Median earnings data - NOT population counts",
        "has_sex_breakdown": True,
        "data_type": "median_earnings",
        "usage": "WARNING: Contains median values, not population counts. Do not use for joint distributions requiring population data."
    }
}

# Table Usage Patterns
DISTRIBUTION_TABLE_MAPPING = {
    "age": {
        "primary_table": "B01001",
        "joint_tables": {
            "age_gender": "B01001",
            "age_race": "B01001A-I", 
            "age_income": ["B01001", "B19001"], # Requires cross-tabulation
            "age_education": ["B01001", "B15003"] # Requires cross-tabulation
        }
    },
    
    "income": {
        "primary_table": "B19001",
        "joint_tables": {
            "income_gender": "B19001", # Use with demographic tables
            "income_race": "B19001A-I",
            "income_profession": ["B19001", "C24010"] # Requires cross-tabulation
        }
    },
    
    "profession": {
        "primary_table": "C24010",
        "joint_tables": {
            "profession_gender": "C24010",
            "profession_race": "C24010A-I"
        }
    },
    
    "education": {
        "primary_table": "B15003",
        "joint_tables": {
            "education_gender": "C15002", 
            "education_race": "C15002A-I"
        }
    },
    
    "race": {
        "primary_table": "B01001A-I", # Use race-specific versions
        "joint_tables": {
            "race_age": "B01001A-I",
            "race_profession": "C24010A-I"
        }
    }
}

# Variable Naming Patterns
VARIABLE_PATTERNS = {
    "estimate": "E",  # Estimate value
    "margin_of_error": "M",  # Margin of error
    "annotation": "EA"  # Annotation
}

# Geographic Levels (in order of preference for data availability)
GEOGRAPHIC_LEVELS = [
    "block_group",  # Most detailed, may have data suppression
    "tract",        # Good balance of detail and data availability
    "county",       # Aggregated, always has data
    "state"         # Highest level aggregation
]

# Data Quality Guidelines
DATA_QUALITY_RULES = {
    "minimum_population": 50,  # Minimum population for reliable percentages
    "suppression_threshold": 5,  # Values below this may be suppressed
    "margin_of_error_check": True,  # Always check MOE for small geographies
    "zero_handling": "exclude"  # How to handle zero values in calculations
}

def get_table_info(table_code):
    """Get detailed information about a Census table."""
    return CENSUS_TABLES.get(table_code, {"error": f"Table {table_code} not found in reference"})

def validate_table_usage(distribution_type, table_code):
    """Validate that a table is appropriate for a given distribution type."""
    if distribution_type not in DISTRIBUTION_TABLE_MAPPING:
        return False, f"Distribution type {distribution_type} not recognized"
    
    mapping = DISTRIBUTION_TABLE_MAPPING[distribution_type]
    
    if table_code == mapping.get("primary_table"):
        return True, "Valid primary table"
    
    for joint_type, tables in mapping.get("joint_tables", {}).items():
        if isinstance(tables, list):
            if table_code in tables:
                return True, f"Valid for {joint_type} joint distribution"
        elif table_code == tables or table_code in tables:
            return True, f"Valid for {joint_type} joint distribution"
    
    return False, f"Table {table_code} not recommended for {distribution_type} distributions"

def build_variable_name(table_code, variable_code, data_type="E"):
    """Build a complete Census variable name."""
    return f"{table_code}_{variable_code:0>3d}{data_type}"

def get_sex_breakdown_info(table_code):
    """Get information about sex breakdown for a table."""
    table_info = CENSUS_TABLES.get(table_code, {})
    return {
        "has_sex_breakdown": table_info.get("has_sex_breakdown", False),
        "male_total": table_info.get("male_total"),
        "female_total": table_info.get("female_total"),
        "variable_pattern": table_info.get("variable_pattern")
    }