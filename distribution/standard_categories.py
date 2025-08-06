"""
Standard Categories for Census Distribution Analysis
This file defines consistent category names and mappings to be used across all distributions.
"""

# Standard Age Ranges (consistent across all age-related distributions)
STANDARD_AGE_RANGES = [
    "Under 5 years",
    "5 to 9 years", 
    "10 to 14 years",
    "15 to 17 years",
    "18 and 19 years",
    "20 to 24 years",
    "25 to 29 years", 
    "30 to 34 years",
    "35 to 44 years",
    "45 to 54 years",
    "55 to 64 years",
    "65 to 74 years",
    "75 to 84 years",
    "85 years and over"
]

# B01001 Age Variable Mapping (Male + Female for each age group)
B01001_AGE_MAPPING = {
    "Under 5 years": ["003", "027"],  # Male + Female under 5
    "5 to 9 years": ["004", "028"],   # Male + Female 5-9
    "10 to 14 years": ["005", "029"], # Male + Female 10-14
    "15 to 17 years": ["006", "030"], # Male + Female 15-17
    "18 and 19 years": ["007", "031"], # Male + Female 18-19
    "20 to 24 years": ["008", "009", "010", "032", "033", "034"],  # Male 20, 21, 22-24 + Female 20, 21, 22-24
    "25 to 29 years": ["011", "035"], # Male + Female 25-29
    "30 to 34 years": ["012", "036"], # Male + Female 30-34
    "35 to 44 years": ["013", "014", "037", "038"],  # Male 35-39, 40-44 + Female 35-39, 40-44
    "45 to 54 years": ["015", "016", "039", "040"],  # Male 45-49, 50-54 + Female 45-49, 50-54
    "55 to 64 years": ["017", "018", "019", "041", "042", "043"],  # Male 55-59, 60-61, 62-64 + Female 55-59, 60-61, 62-64
    "65 to 74 years": ["020", "021", "022", "044", "045", "046"],  # Male 65-66, 67-69, 70-74 + Female 65-66, 67-69, 70-74
    "75 to 84 years": ["023", "024", "047", "048"],  # Male 75-79, 80-84 + Female 75-79, 80-84
    "85 years and over": ["025", "049"]  # Male + Female 85+
}

# Standard Profession Categories (consistent across all profession-related distributions)
STANDARD_PROFESSION_CATEGORIES = [
    "Management, business, science, and arts occupations",
    "Service occupations", 
    "Sales and office occupations",
    "Natural resources, construction, and maintenance occupations",
    "Production, transportation, and material moving occupations"
]

# C24010 Profession Variable Mapping (Male + Female for each profession)
C24010_PROFESSION_MAPPING = {
    "Management, business, science, and arts occupations": {
        "male": ["003", "004", "005", "006", "007"],
        "female": ["039", "040", "041", "042", "043"]
    },
    "Service occupations": {
        "male": ["008", "009", "010", "011"],
        "female": ["044", "045", "046", "047"]
    },
    "Sales and office occupations": {
        "male": ["012", "013"],
        "female": ["048", "049"]
    },
    "Natural resources, construction, and maintenance occupations": {
        "male": ["014", "015", "016"],
        "female": ["050", "051", "052"]
    },
    "Production, transportation, and material moving occupations": {
        "male": ["017", "018"],
        "female": ["053", "054"]
    }
}

# Standard Race/Ethnicity Categories (consistent with Census naming)
STANDARD_RACE_ETHNICITY_CATEGORIES = [
    "White Alone",
    "Black or African American Alone", 
    "American Indian and Alaska Native Alone",
    "Asian Alone",
    "Native Hawaiian and Other Pacific Islander Alone",
    "Some Other Race Alone",
    "Two or More Races",
    "Hispanic or Latino"
]

# B01001 Race Table Mapping
B01001_RACE_TABLE_MAPPING = {
    "B01001A": "White Alone",
    "B01001B": "Black or African American Alone", 
    "B01001C": "American Indian and Alaska Native Alone",
    "B01001D": "Asian Alone",
    "B01001E": "Native Hawaiian and Other Pacific Islander Alone",
    "B01001F": "Some Other Race Alone",
    "B01001G": "Two or More Races",
    "B01001I": "Hispanic or Latino"
}

# C24010 Race Table Mapping
C24010_RACE_TABLE_MAPPING = {
    "C24010A": "White Alone",
    "C24010B": "Black or African American Alone",
    "C24010C": "American Indian and Alaska Native Alone", 
    "C24010D": "Asian Alone",
    "C24010E": "Native Hawaiian and Other Pacific Islander Alone",
    "C24010F": "Some Other Race Alone",
    "C24010G": "Two or More Races",
    "C24010I": "Hispanic or Latino"
}

# Standard Income Ranges (from Census B19001 table)
STANDARD_INCOME_RANGES = [
    "$1 to $2,499 or loss",
    "$2,500 to $4,999", 
    "$5,000 to $7,499",
    "$7,500 to $9,999",
    "$10,000 to $12,499",
    "$12,500 to $14,999",
    "$15,000 to $17,499",
    "$17,500 to $19,999", 
    "$20,000 to $22,499",
    "$22,500 to $24,999",
    "$25,000 to $29,999",
    "$30,000 to $34,999",
    "$35,000 to $39,999",
    "$40,000 to $44,999",
    "$45,000 to $49,999", 
    "$50,000 to $54,999",
    "$55,000 to $64,999",
    "$65,000 to $74,999",
    "$75,000 to $99,999",
    "$100,000 or more"
]

# B19001 Income Variable Mapping (already includes both male and female)
B19001_INCOME_MAPPING = {
    "$1 to $2,499 or loss": ["002"],
    "$2,500 to $4,999": ["003"], 
    "$5,000 to $7,499": ["004"],
    "$7,500 to $9,999": ["005"],
    "$10,000 to $12,499": ["006"],
    "$12,500 to $14,999": ["007"],
    "$15,000 to $17,499": ["008"],
    "$17,500 to $19,999": ["009"], 
    "$20,000 to $22,499": ["010"],
    "$22,500 to $24,999": ["011"],
    "$25,000 to $29,999": ["012"],
    "$30,000 to $34,999": ["013"],
    "$35,000 to $39,999": ["014"],
    "$40,000 to $44,999": ["015"],
    "$45,000 to $49,999": ["016"], 
    "$50,000 to $54,999": ["017"],
    "$55,000 to $64,999": ["018"],
    "$65,000 to $74,999": ["019"],
    "$75,000 to $99,999": ["020"],
    "$100,000 or more": ["021"]
}

# Standard Education Categories
STANDARD_EDUCATION_CATEGORIES = [
    "Less than 9th grade",
    "9th to 12th grade, no diploma", 
    "High school graduate",
    "Some college, no degree",
    "Associate's degree",
    "Bachelor's degree",
    "Graduate or professional degree"
]

# Standard Gender Categories
STANDARD_GENDER_CATEGORIES = ["Male", "Female"]

# Helper functions to validate category consistency
def validate_age_categories(categories):
    """Validate that age categories match standard."""
    return set(categories) == set(STANDARD_AGE_RANGES)

def validate_profession_categories(categories):
    """Validate that profession categories match standard."""
    return set(categories) == set(STANDARD_PROFESSION_CATEGORIES)

def validate_race_categories(categories):
    """Validate that race/ethnicity categories match standard."""
    return set(categories) == set(STANDARD_RACE_ETHNICITY_CATEGORIES)

def validate_income_categories(categories):
    """Validate that income categories match standard."""
    return set(categories) == set(STANDARD_INCOME_RANGES)

def validate_education_categories(categories):
    """Validate that education categories match standard."""
    return set(categories) == set(STANDARD_EDUCATION_CATEGORIES)