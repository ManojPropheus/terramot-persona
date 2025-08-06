"""
Age Range Mapping System
Maps fine-grained frontend age ranges to backend distribution age ranges.
"""

# Frontend fine-grained age ranges (from standard_categories.py)
FRONTEND_AGE_RANGES = [
    "Under 5 years", "5 to 9 years", "10 to 14 years", "15 to 17 years", 
    "18 and 19 years", "20 to 24 years", "25 to 29 years", "30 to 34 years",
    "35 to 44 years", "45 to 54 years", "55 to 64 years", "65 to 74 years",
    "75 to 84 years", "85 years and over"
]

# Age-Income distribution ranges (from age_income_distribution.py)
AGE_INCOME_RANGES = [
    "Under 25 years", "25 to 44 years", "45 to 64 years", "65 years and over"
]

# Age-Education distribution ranges (from age_education_distribution.py)
AGE_EDUCATION_RANGES = [
    "18 to 24 years", "25 to 34 years", "35 to 44 years", "45 to 64 years", "65 years and over"
]

# Age-Gender distribution ranges (uses fine-grained age ranges same as frontend)
AGE_GENDER_RANGES = [
    "Under 5 years", "5 to 9 years", "10 to 14 years", "15 to 17 years", 
    "18 and 19 years", "20 to 24 years", "25 to 29 years", "30 to 34 years",
    "35 to 44 years", "45 to 54 years", "55 to 64 years", "65 to 74 years",
    "75 to 84 years", "85 years and over"
]

# Age-Race distribution ranges (uses fine-grained age ranges same as frontend)
AGE_RACE_RANGES = [
    "Under 5 years", "5 to 9 years", "10 to 14 years", "15 to 17 years", 
    "18 and 19 years", "20 to 24 years", "25 to 29 years", "30 to 34 years",
    "35 to 44 years", "45 to 54 years", "55 to 64 years", "65 to 74 years",
    "75 to 84 years", "85 years and over"
]

# Mapping from frontend ranges to backend ranges for each distribution type
AGE_RANGE_MAPPINGS = {
    'age_income': {
        # Under 25 years
        "Under 5 years": "Under 25 years",
        "5 to 9 years": "Under 25 years", 
        "10 to 14 years": "Under 25 years",
        "15 to 17 years": "Under 25 years",
        "18 and 19 years": "Under 25 years",
        "20 to 24 years": "Under 25 years",
        
        # 25 to 44 years
        "25 to 29 years": "25 to 44 years",
        "30 to 34 years": "25 to 44 years", 
        "35 to 44 years": "25 to 44 years",
        
        # 45 to 64 years
        "45 to 54 years": "45 to 64 years",
        "55 to 64 years": "45 to 64 years",
        
        # 65 years and over
        "65 to 74 years": "65 years and over",
        "75 to 84 years": "65 years and over",
        "85 years and over": "65 years and over"
    },
    
    'age_education': {
        # 18 to 24 years (note: excludes under 18 as education data starts at 18)
        "18 and 19 years": "18 to 24 years",
        "20 to 24 years": "18 to 24 years",
        
        # 25 to 34 years
        "25 to 29 years": "25 to 34 years",
        "30 to 34 years": "25 to 34 years",
        
        # 35 to 44 years  
        "35 to 44 years": "35 to 44 years",
        
        # 45 to 64 years
        "45 to 54 years": "45 to 64 years", 
        "55 to 64 years": "45 to 64 years",
        
        # 65 years and over
        "65 to 74 years": "65 years and over",
        "75 to 84 years": "65 years and over",
        "85 years and over": "65 years and over"
    },
    
    'age_gender': {
        # Direct 1:1 mapping - age_gender uses same fine-grained ranges as frontend
        "Under 5 years": "Under 5 years",
        "5 to 9 years": "5 to 9 years",
        "10 to 14 years": "10 to 14 years",
        "15 to 17 years": "15 to 17 years",
        "18 and 19 years": "18 and 19 years",
        "20 to 24 years": "20 to 24 years",
        "25 to 29 years": "25 to 29 years",
        "30 to 34 years": "30 to 34 years",
        "35 to 44 years": "35 to 44 years",
        "45 to 54 years": "45 to 54 years",
        "55 to 64 years": "55 to 64 years",
        "65 to 74 years": "65 to 74 years",
        "75 to 84 years": "75 to 84 years",
        "85 years and over": "85 years and over"
    },
    
    'age_race': {
        # Direct 1:1 mapping - age_race uses same fine-grained ranges as frontend
        "Under 5 years": "Under 5 years",
        "5 to 9 years": "5 to 9 years",
        "10 to 14 years": "10 to 14 years",
        "15 to 17 years": "15 to 17 years",
        "18 and 19 years": "18 and 19 years",
        "20 to 24 years": "20 to 24 years",
        "25 to 29 years": "25 to 29 years",
        "30 to 34 years": "30 to 34 years",
        "35 to 44 years": "35 to 44 years",
        "45 to 54 years": "45 to 54 years",
        "55 to 64 years": "55 to 64 years",
        "65 to 74 years": "65 to 74 years",
        "75 to 84 years": "75 to 84 years",
        "85 years and over": "85 years and over"
    }
}

# Reverse mappings - get all frontend ranges that map to each backend range
REVERSE_AGE_MAPPINGS = {}
for distribution_type, mapping in AGE_RANGE_MAPPINGS.items():
    REVERSE_AGE_MAPPINGS[distribution_type] = {}
    for frontend_range, backend_range in mapping.items():
        if backend_range not in REVERSE_AGE_MAPPINGS[distribution_type]:
            REVERSE_AGE_MAPPINGS[distribution_type][backend_range] = []
        REVERSE_AGE_MAPPINGS[distribution_type][backend_range].append(frontend_range)


def map_frontend_age_to_backend(frontend_age_range: str, distribution_type: str) -> str:
    """
    Map a frontend age range to the appropriate backend age range for a given distribution type.
    
    Args:
        frontend_age_range: The fine-grained age range from the frontend
        distribution_type: The type of distribution (age_income, age_education, etc.)
        
    Returns:
        The corresponding backend age range, or None if not available
    """
    mapping = AGE_RANGE_MAPPINGS.get(distribution_type, {})
    return mapping.get(frontend_age_range)


def get_available_frontend_ages(distribution_type: str) -> list:
    """
    Get the list of frontend age ranges that are available for a given distribution type.
    
    Args:
        distribution_type: The type of distribution
        
    Returns:
        List of available frontend age ranges
    """
    mapping = AGE_RANGE_MAPPINGS.get(distribution_type, {})
    return list(mapping.keys())


def get_backend_age_ranges(distribution_type: str) -> list:
    """
    Get the backend age ranges for a given distribution type.
    
    Args:
        distribution_type: The type of distribution
        
    Returns:
        List of backend age ranges
    """
    if distribution_type == 'age_income':
        return AGE_INCOME_RANGES.copy()
    elif distribution_type == 'age_education': 
        return AGE_EDUCATION_RANGES.copy()
    elif distribution_type == 'age_gender':
        return AGE_GENDER_RANGES.copy()
    elif distribution_type == 'age_race':
        return AGE_RACE_RANGES.copy()
    else:
        return []


def validate_age_range_compatibility(frontend_age_range: str, distribution_type: str) -> bool:
    """
    Check if a frontend age range is compatible with a given distribution type.
    
    Args:
        frontend_age_range: The fine-grained age range from the frontend
        distribution_type: The type of distribution
        
    Returns:
        True if compatible, False otherwise
    """
    return map_frontend_age_to_backend(frontend_age_range, distribution_type) is not None


def get_age_range_description(distribution_type: str) -> str:
    """
    Get a human-readable description of the age ranges available for a distribution type.
    
    Args:
        distribution_type: The type of distribution
        
    Returns:
        Description string
    """
    backend_ranges = get_backend_age_ranges(distribution_type)
    if not backend_ranges:
        return "No age ranges available"
    
    return f"Available age ranges: {', '.join(backend_ranges)}"


# Distribution-specific mappings for easy lookup
DISTRIBUTION_MAPPINGS = {
    'age_income': AGE_INCOME_RANGES,
    'age_education': AGE_EDUCATION_RANGES,  
    'age_gender': AGE_GENDER_RANGES,
    'age_race': AGE_RACE_RANGES
}