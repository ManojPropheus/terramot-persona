"""
Unified Education Distribution Analysis
Provides comprehensive education-based conditional analysis by combining multiple bivariate distributions.
Handles different education classification systems through intelligent mapping.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from typing import Dict, List, Any, Optional, Tuple
from distribution.age_education_distribution import get_distribution as get_age_education, get_conditional_distribution as get_age_education_conditional
from distribution.education_race_distribution import get_distribution as get_education_race, get_conditional_distribution as get_education_race_conditional  
from distribution.education_sex_distribution import get_distribution as get_education_sex, get_conditional_distribution as get_education_sex_conditional


def normalize_education_level(education: str) -> str:
    """Normalize education levels to a standard format for comparison."""
    education = education.lower().strip()
    
    # Create mapping from various formats to standardized levels
    mappings = {
        # Less than high school variants
        'less than 9th grade': 'less_than_hs',
        '9th to 12th grade, no diploma': 'less_than_hs', 
        'less than high school': 'less_than_hs',
        
        # High school variants
        'high school graduate (includes equivalency)': 'high_school',
        'high school graduate': 'high_school',
        
        # Some college variants  
        'some college, no degree': 'some_college',
        'some college': 'some_college',
        
        # Associate degree variants
        'associate\'s degree': 'associate',
        'associate degree': 'associate',
        
        # Bachelor's degree variants
        'bachelor\'s degree': 'bachelor',
        'bachelor\'s degree': 'bachelor',
        
        # Graduate degree variants
        'graduate or professional degree': 'graduate',
        'graduate degree': 'graduate'
    }
    
    return mappings.get(education, education)


def find_best_education_match(target_education: str, available_educations: List[str]) -> Tuple[str, float, str]:
    """
    Find the best matching education level from available options.
    Returns: (best_match, similarity_score, explanation)
    """
    target_norm = normalize_education_level(target_education)
    best_match = None
    best_score = 0
    best_explanation = ""
    
    # First try exact normalized matches
    for available in available_educations:
        available_norm = normalize_education_level(available)
        
        if target_norm == available_norm:
            return available, 1.0, "Exact match"
    
    # If no exact match, look for partial matches or closest alternatives
    education_hierarchy = [
        'less_than_hs', 'high_school', 'some_college', 
        'associate', 'bachelor', 'graduate'
    ]
    
    try:
        target_idx = education_hierarchy.index(target_norm)
    except ValueError:
        # Target not in standard hierarchy, find closest by string similarity
        for available in available_educations:
            if target_education.lower() in available.lower() or available.lower() in target_education.lower():
                return available, 0.7, "Partial string match"
        return available_educations[0], 0.3, "Fallback to first available option"
    
    # Find closest in hierarchy
    closest_distance = float('inf')
    for available in available_educations:
        available_norm = normalize_education_level(available)
        try:
            available_idx = education_hierarchy.index(available_norm)
            distance = abs(target_idx - available_idx)
            
            if distance < closest_distance:
                closest_distance = distance
                best_match = available
                
                if distance == 0:
                    best_explanation = "Exact educational level match"
                    best_score = 1.0
                elif distance == 1:
                    best_explanation = "Adjacent educational level (very close match)"
                    best_score = 0.8
                elif distance == 2:
                    best_explanation = "Similar educational level (moderate match)"
                    best_score = 0.6
                else:
                    best_explanation = f"Different educational level ({distance} levels apart)"
                    best_score = 0.4
        except ValueError:
            continue
    
    return best_match or available_educations[0], best_score, best_explanation


def get_unified_education_analysis(lat: float, lng: float, target_education: str) -> Dict[str, Any]:
    """
    Get unified education analysis showing distributions from all bivariate combinations.
    """
    result = {
        "target_education": target_education,
        "location": {"lat": lat, "lng": lng},
        "distributions": {},
        "metadata": {
            "total_distributions": 0,
            "successful_retrievals": 0,
            "education_mappings": {}
        }
    }
    
    # Define all available education-based bivariate distributions
    distributions_config = {
        "age": {
            "name": "Age Distribution",
            "get_joint": get_age_education,
            "get_conditional": get_age_education_conditional,
            "condition_type": "education"
        },
        "race": {
            "name": "Race/Ethnicity Distribution", 
            "get_joint": get_education_race,
            "get_conditional": get_education_race_conditional,
            "condition_type": "education"
        },
        "sex": {
            "name": "Sex/Gender Distribution",
            "get_joint": get_education_sex,
            "get_conditional": get_education_sex_conditional,
            "condition_type": "education"
        }
    }
    
    result["metadata"]["total_distributions"] = len(distributions_config)
    
    for dist_key, config in distributions_config.items():
        try:
            # Get joint distribution
            joint_data = config["get_joint"](lat, lng)
            
            if not joint_data or not joint_data.get("education_marginal"):
                result["distributions"][dist_key] = {
                    "name": config["name"],
                    "status": "no_data",
                    "error": "No data available for this location"
                }
                continue
            
            # Extract available education levels
            available_educations = [item["category"] for item in joint_data["education_marginal"]]
            
            # Find best education match
            best_education, similarity_score, explanation = find_best_education_match(target_education, available_educations)
            
            if not best_education:
                result["distributions"][dist_key] = {
                    "name": config["name"],
                    "status": "no_match",
                    "error": "No suitable education level found"
                }
                continue
            
            # Get conditional distribution
            conditional_data = config["get_conditional"](joint_data, config["condition_type"], best_education)
            
            if "error" in conditional_data:
                result["distributions"][dist_key] = {
                    "name": config["name"],
                    "status": "conditional_error",
                    "error": conditional_data["error"],
                    "matched_education": best_education,
                    "education_explanation": explanation
                }
                continue
            
            # Success - store the results
            result["distributions"][dist_key] = {
                "name": config["name"],
                "status": "success",
                "matched_education": best_education,
                "similarity_score": similarity_score,
                "education_explanation": explanation,
                "conditional_distribution": conditional_data,
                "data_source": conditional_data.get("data_source", "Unknown"),
                "total_population": conditional_data.get("total_population", 0)
            }
            
            result["metadata"]["successful_retrievals"] += 1
            result["metadata"]["education_mappings"][dist_key] = {
                "target": target_education,
                "matched": best_education,
                "similarity": similarity_score,
                "explanation": explanation
            }
            
            # Store location info from first successful distribution
            if "location_details" not in result and joint_data.get("location"):
                result["location_details"] = joint_data["location"]
        
        except Exception as e:
            result["distributions"][dist_key] = {
                "name": config["name"],
                "status": "error",
                "error": str(e)
            }
    
    return result


if __name__ == "__main__":
    # Test the unified education analysis
    lat, lon = 37.736509, -122.388028  # San Francisco area
    
    print("=" * 80)
    print("UNIFIED EDUCATION DISTRIBUTION ANALYSIS")
    print("=" * 80)
    
    # Test different education levels
    test_educations = [
        "High school graduate",           # Should match across systems
        "Bachelor's degree",             # Should match exactly
        "Less than 9th grade",          # Should map between detailed/condensed
        "Some college",                  # Should handle variants
        "Graduate degree"                # Should map to "Graduate or professional degree"
    ]
    
    for test_education in test_educations:
        print(f"\n{'='*60}")
        print(f"ANALYSIS FOR EDUCATION LEVEL: {test_education}")
        print(f"{'='*60}")
        
        analysis = get_unified_education_analysis(lat, lon, test_education)
        
        print(f"Target Education: {analysis['target_education']}")
        print(f"Successful Retrievals: {analysis['metadata']['successful_retrievals']}/{analysis['metadata']['total_distributions']}")
        
        if analysis.get("location_details"):
            loc = analysis["location_details"]
            print(f"Location: {loc.get('county_name', 'Unknown')}, {loc.get('state_name', 'Unknown')}")
        
        print(f"\nDistributions Found:")
        for dist_key, dist_info in analysis["distributions"].items():
            print(f"\n  {dist_info['name']}:")
            print(f"    Status: {dist_info['status']}")
            
            if dist_info["status"] == "success":
                print(f"    Matched Education: {dist_info['matched_education']}")
                print(f"    Education Explanation: {dist_info['education_explanation']}")
                print(f"    Population with Education: {dist_info['total_population']:,}")
                print(f"    Number of Categories: {len(dist_info['conditional_distribution']['data'])}")
                
                # Show top few categories
                data_sorted = sorted(dist_info['conditional_distribution']['data'], 
                                   key=lambda x: x.get('percentage', 0), reverse=True)
                print(f"    Top Categories:")
                for i, item in enumerate(data_sorted[:3]):
                    print(f"      {item['category']}: {item.get('percentage', 0):.1f}%")
            else:
                print(f"    Error: {dist_info.get('error', 'Unknown error')}")
        
        print("\n" + "-"*60)