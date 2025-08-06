"""
Unified Race Distribution Analysis
Provides comprehensive race/ethnicity-based conditional analysis by combining multiple bivariate distributions.
Handles different race/ethnicity classification systems through intelligent mapping.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from typing import Dict, List, Any, Optional, Tuple
from distribution.age_race_distribution import get_distribution as get_age_race, get_conditional_distribution as get_age_race_conditional
from distribution.education_race_distribution import get_distribution as get_education_race, get_conditional_distribution as get_education_race_conditional
from distribution.profession_race_distribution import get_distribution as get_profession_race, get_conditional_distribution as get_profession_race_conditional


def normalize_race_ethnicity(race: str) -> str:
    """Normalize race/ethnicity names to a standard format for comparison."""
    race = race.lower().strip()
    
    # Create mapping from various formats to standardized race/ethnicity categories
    mappings = {
        # White variants
        'white alone': 'white',
        'white': 'white',
        'white, not hispanic or latino': 'white_non_hispanic',
        'white alone, not hispanic or latino': 'white_non_hispanic',
        
        # Black variants
        'black or african american alone': 'black',
        'black alone': 'black',
        'african american': 'black',
        'black or african american': 'black',
        
        # Asian variants
        'asian alone': 'asian',
        'asian': 'asian',
        
        # American Indian variants
        'american indian and alaska native alone': 'american_indian_alaska_native',
        'american indian or alaska native alone': 'american_indian_alaska_native',
        'native american': 'american_indian_alaska_native',
        
        # Native Hawaiian and Pacific Islander variants
        'native hawaiian and other pacific islander alone': 'native_hawaiian_pacific_islander',
        'native hawaiian or other pacific islander alone': 'native_hawaiian_pacific_islander',
        'pacific islander': 'native_hawaiian_pacific_islander',
        
        # Two or more races variants
        'two or more races': 'two_or_more_races',
        'multiracial': 'two_or_more_races',
        'mixed race': 'two_or_more_races',
        
        # Hispanic/Latino variants
        'hispanic or latino': 'hispanic_latino',
        'hispanic': 'hispanic_latino',
        'latino': 'hispanic_latino',
        'spanish': 'hispanic_latino',
        
        # Other race variants
        'some other race alone': 'other_race',
        'other race': 'other_race',
        'some other race': 'other_race'
    }
    
    return mappings.get(race, race)


def find_best_race_match(target_race: str, available_races: List[str]) -> Tuple[str, float, str]:
    """
    Find the best matching race/ethnicity from available options.
    Returns: (best_match, similarity_score, explanation)
    """
    target_norm = normalize_race_ethnicity(target_race)
    best_match = None
    best_score = 0
    best_explanation = ""
    
    # First try exact normalized matches
    for available in available_races:
        available_norm = normalize_race_ethnicity(available)
        
        if target_norm == available_norm:
            return available, 1.0, "Exact race/ethnicity match"
    
    # If no exact match, look for partial matches or closest alternatives
    race_hierarchy = [
        'white', 'white_non_hispanic', 'black', 'asian', 'american_indian_alaska_native',
        'native_hawaiian_pacific_islander', 'hispanic_latino', 'two_or_more_races', 'other_race'
    ]
    
    # Try string similarity matching for key words
    best_substring_score = 0
    for available in available_races:
        # Check for key word matches
        target_words = set(target_race.lower().split())
        available_words = set(available.lower().split())
        
        # Remove common stop words that don't help with matching
        stop_words = {'alone', 'or', 'and', 'other', 'not'}
        target_words -= stop_words
        available_words -= stop_words
        
        # Calculate word overlap
        common_words = target_words.intersection(available_words)
        if common_words:
            overlap_score = len(common_words) / max(len(target_words), len(available_words))
            if overlap_score > best_substring_score:
                best_substring_score = overlap_score
                best_match = available
                
                if overlap_score >= 0.6:
                    best_explanation = f"Strong word overlap match ({overlap_score:.1%})"
                    best_score = overlap_score
                elif overlap_score >= 0.4:
                    best_explanation = f"Moderate word overlap match ({overlap_score:.1%})"
                    best_score = overlap_score * 0.8
                else:
                    best_explanation = f"Weak word overlap match ({overlap_score:.1%})"
                    best_score = overlap_score * 0.6
    
    # Special case handling for common variations
    target_lower = target_race.lower()
    for available in available_races:
        available_lower = available.lower()
        
        # Handle Hispanic/Latino variations
        if any(term in target_lower for term in ['hispanic', 'latino', 'spanish']) and \
           any(term in available_lower for term in ['hispanic', 'latino']):
            if best_score < 0.9:
                best_match = available
                best_score = 0.9
                best_explanation = "Hispanic/Latino variation match"
        
        # Handle White variations
        elif 'white' in target_lower and 'white' in available_lower:
            if best_score < 0.8:
                best_match = available
                best_score = 0.8
                best_explanation = "White variation match"
        
        # Handle Black/African American variations
        elif any(term in target_lower for term in ['black', 'african']) and \
             any(term in available_lower for term in ['black', 'african']):
            if best_score < 0.8:
                best_match = available
                best_score = 0.8
                best_explanation = "Black/African American variation match"
        
        # Handle Asian variations
        elif 'asian' in target_lower and 'asian' in available_lower:
            if best_score < 0.8:
                best_match = available
                best_score = 0.8
                best_explanation = "Asian variation match"
    
    # If still no good match, try hierarchy-based matching
    if not best_match or best_score < 0.5:
        try:
            target_idx = race_hierarchy.index(target_norm)
            closest_distance = float('inf')
            
            for available in available_races:
                available_norm = normalize_race_ethnicity(available)
                try:
                    available_idx = race_hierarchy.index(available_norm)
                    distance = abs(target_idx - available_idx)
                    
                    if distance < closest_distance:
                        closest_distance = distance
                        best_match = available
                        
                        if distance == 0:
                            best_explanation = "Exact hierarchical match"
                            best_score = 1.0
                        elif distance <= 1:
                            best_explanation = f"Similar race/ethnicity category (hierarchy distance: {distance})"
                            best_score = 0.7
                        else:
                            best_explanation = f"Different race/ethnicity category (hierarchy distance: {distance})"
                            best_score = 0.4
                except ValueError:
                    continue
        except ValueError:
            pass
    
    # Final fallback to first available option
    if not best_match:
        best_match = available_races[0] if available_races else None
        best_explanation = "Fallback to first available race/ethnicity"
        best_score = 0.2
    
    return best_match, best_score, best_explanation


def get_unified_race_analysis(lat: float, lng: float, target_race: str) -> Dict[str, Any]:
    """
    Get unified race analysis showing distributions from all bivariate combinations.
    """
    result = {
        "target_race": target_race,
        "location": {"lat": lat, "lng": lng},
        "distributions": {},
        "metadata": {
            "total_distributions": 0,
            "successful_retrievals": 0,
            "race_mappings": {}
        }
    }
    
    # Define all available race-based bivariate distributions
    distributions_config = {
        "age": {
            "name": "Age Distribution",
            "get_joint": get_age_race,
            "get_conditional": get_age_race_conditional,
            "condition_type": "race"
        },
        "education": {
            "name": "Education Distribution", 
            "get_joint": get_education_race,
            "get_conditional": get_education_race_conditional,
            "condition_type": "race"
        },
        "profession": {
            "name": "Profession Distribution",
            "get_joint": get_profession_race,
            "get_conditional": get_profession_race_conditional,
            "condition_type": "race"
        }
    }
    
    result["metadata"]["total_distributions"] = len(distributions_config)
    
    for dist_key, config in distributions_config.items():
        try:
            # Get joint distribution
            joint_data = config["get_joint"](lat, lng)
            
            if not joint_data or not joint_data.get("race_marginal"):
                result["distributions"][dist_key] = {
                    "name": config["name"],
                    "status": "no_data",
                    "error": "No data available for this location"
                }
                continue
            
            # Extract available races
            available_races = [item["category"] for item in joint_data["race_marginal"]]
            
            # Find best race match
            best_race, similarity_score, explanation = find_best_race_match(target_race, available_races)
            
            if not best_race:
                result["distributions"][dist_key] = {
                    "name": config["name"],
                    "status": "no_match",
                    "error": "No suitable race/ethnicity found"
                }
                continue
            
            # Get conditional distribution
            conditional_data = config["get_conditional"](joint_data, config["condition_type"], best_race)
            
            if "error" in conditional_data:
                result["distributions"][dist_key] = {
                    "name": config["name"],
                    "status": "conditional_error",
                    "error": conditional_data["error"],
                    "matched_race": best_race,
                    "race_explanation": explanation
                }
                continue
            
            # Success - store the results
            result["distributions"][dist_key] = {
                "name": config["name"],
                "status": "success",
                "matched_race": best_race,
                "similarity_score": similarity_score,
                "race_explanation": explanation,
                "conditional_distribution": conditional_data,
                "data_source": conditional_data.get("data_source", "Unknown"),
                "total_population": conditional_data.get("total_population", 0)
            }
            
            result["metadata"]["successful_retrievals"] += 1
            result["metadata"]["race_mappings"][dist_key] = {
                "target": target_race,
                "matched": best_race,
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
    # Test the unified race analysis
    lat, lon = 37.736509, -122.388028  # San Francisco area
    
    print("=" * 80)
    print("UNIFIED RACE DISTRIBUTION ANALYSIS")
    print("=" * 80)
    
    # Test different race/ethnicity categories
    test_races = [
        "White alone",
        "Black or African American alone",
        "Asian alone",
        "American Indian and Alaska Native alone",
        "Native Hawaiian and Other Pacific Islander alone",
        "Hispanic or Latino",
        "Two or more races",
        "White, not Hispanic or Latino",  # Test complex matching
        "African American",              # Test alternative terms
        "Latino"                        # Test abbreviations
    ]
    
    for test_race in test_races:
        print(f"\n{'='*60}")
        print(f"ANALYSIS FOR RACE/ETHNICITY: {test_race}")
        print(f"{'='*60}")
        
        analysis = get_unified_race_analysis(lat, lon, test_race)
        
        print(f"Target Race/Ethnicity: {analysis['target_race']}")
        print(f"Successful Retrievals: {analysis['metadata']['successful_retrievals']}/{analysis['metadata']['total_distributions']}")
        
        if analysis.get("location_details"):
            loc = analysis["location_details"]
            print(f"Location: {loc.get('county_name', 'Unknown')}, {loc.get('state_name', 'Unknown')}")
        
        print(f"\nDistributions Found:")
        for dist_key, dist_info in analysis["distributions"].items():
            print(f"\n  {dist_info['name']}:")
            print(f"    Status: {dist_info['status']}")
            
            if dist_info["status"] == "success":
                print(f"    Matched Race/Ethnicity: {dist_info['matched_race']}")
                print(f"    Race Explanation: {dist_info['race_explanation']}")
                print(f"    Population: {dist_info['total_population']:,}")
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