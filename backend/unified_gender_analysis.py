"""
Unified Gender Distribution Analysis
Provides comprehensive gender-based conditional analysis by combining multiple bivariate distributions.
Gender categories are consistent across distributions (Male/Female) making this simpler than other analyses.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from typing import Dict, List, Any, Optional, Tuple
from distribution.age_gender_distribution import get_distribution as get_age_gender, get_conditional_distribution as get_age_gender_conditional
from distribution.income_gender_distribution import get_distribution as get_income_gender, get_conditional_distribution as get_income_gender_conditional
from distribution.education_sex_distribution import get_distribution as get_education_sex, get_conditional_distribution as get_education_sex_conditional


def find_best_gender_match(target_gender: str, available_genders: List[str]) -> Tuple[str, float, str]:
    """
    Find the best matching gender from available options.
    Gender should be consistent, but handle variations like "Sex" vs "Gender" or case differences.
    Returns: (best_match, similarity_score, explanation)
    """
    target_norm = target_gender.lower().strip()
    
    # Normalize common gender variations
    gender_mappings = {
        'male': 'male',
        'female': 'female', 
        'men': 'male',
        'women': 'female',
        'man': 'male',
        'woman': 'female',
        'm': 'male',
        'f': 'female'
    }
    
    target_standard = gender_mappings.get(target_norm, target_norm)
    
    # Look for exact match first
    for available in available_genders:
        available_norm = available.lower().strip()
        available_standard = gender_mappings.get(available_norm, available_norm)
        
        if target_standard == available_standard:
            return available, 1.0, "Exact gender match"
        elif target_norm == available_norm:
            return available, 1.0, "Exact match"
    
    # If no exact match, try partial matching
    for available in available_genders:
        if target_norm in available.lower() or available.lower() in target_norm:
            return available, 0.8, "Partial gender match"
    
    # Fallback to first available option
    return available_genders[0] if available_genders else None, 0.3, "Fallback to first available gender"


def get_unified_gender_analysis(lat: float, lng: float, target_gender: str) -> Dict[str, Any]:
    """
    Get unified gender analysis showing distributions from all bivariate combinations.
    """
    result = {
        "target_gender": target_gender,
        "location": {"lat": lat, "lng": lng},
        "distributions": {},
        "metadata": {
            "total_distributions": 0,
            "successful_retrievals": 0,
            "gender_mappings": {}
        }
    }
    
    # Define all available gender-based bivariate distributions
    distributions_config = {
        "age": {
            "name": "Age Distribution",
            "get_joint": get_age_gender,
            "get_conditional": get_age_gender_conditional,
            "condition_type": "gender"
        },
        "income": {
            "name": "Income Distribution",
            "get_joint": get_income_gender,
            "get_conditional": get_income_gender_conditional,
            "condition_type": "gender"
        },
        "education": {
            "name": "Education Distribution",
            "get_joint": get_education_sex,
            "get_conditional": get_education_sex_conditional,
            "condition_type": "sex"  # Note: education_sex uses "sex" not "gender"
        }
    }
    
    result["metadata"]["total_distributions"] = len(distributions_config)
    
    for dist_key, config in distributions_config.items():
        try:
            # Get joint distribution
            joint_data = config["get_joint"](lat, lng)
            
            # Check for gender_marginal or sex_marginal depending on distribution
            gender_marginal_key = "sex_marginal" if dist_key == "education" else "gender_marginal"
            
            if not joint_data or not joint_data.get(gender_marginal_key):
                result["distributions"][dist_key] = {
                    "name": config["name"],
                    "status": "no_data",
                    "error": "No data available for this location"
                }
                continue
            
            # Extract available genders
            available_genders = [item["category"] for item in joint_data[gender_marginal_key]]
            
            # Find best gender match
            best_gender, similarity_score, explanation = find_best_gender_match(target_gender, available_genders)
            
            if not best_gender:
                result["distributions"][dist_key] = {
                    "name": config["name"],
                    "status": "no_match",
                    "error": "No suitable gender found"
                }
                continue
            
            # Get conditional distribution
            conditional_data = config["get_conditional"](joint_data, config["condition_type"], best_gender)
            
            if "error" in conditional_data:
                result["distributions"][dist_key] = {
                    "name": config["name"],
                    "status": "conditional_error",
                    "error": conditional_data["error"],
                    "matched_gender": best_gender,
                    "gender_explanation": explanation
                }
                continue
            
            # Success - store the results
            result["distributions"][dist_key] = {
                "name": config["name"],
                "status": "success",
                "matched_gender": best_gender,
                "similarity_score": similarity_score,
                "gender_explanation": explanation,
                "conditional_distribution": conditional_data,
                "data_source": conditional_data.get("data_source", "Unknown"),
                "total_population": conditional_data.get("total_population", 0)
            }
            
            result["metadata"]["successful_retrievals"] += 1
            result["metadata"]["gender_mappings"][dist_key] = {
                "target": target_gender,
                "matched": best_gender,
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
    # Test the unified gender analysis
    lat, lon = 37.736509, -122.388028  # San Francisco area
    
    print("=" * 80)
    print("UNIFIED GENDER DISTRIBUTION ANALYSIS")
    print("=" * 80)
    
    # Test both gender options
    test_genders = [
        "Male",
        "Female",
        "men",    # Test normalization
        "Women"   # Test normalization
    ]
    
    for test_gender in test_genders:
        print(f"\n{'='*60}")
        print(f"ANALYSIS FOR GENDER: {test_gender}")
        print(f"{'='*60}")
        
        analysis = get_unified_gender_analysis(lat, lon, test_gender)
        
        print(f"Target Gender: {analysis['target_gender']}")
        print(f"Successful Retrievals: {analysis['metadata']['successful_retrievals']}/{analysis['metadata']['total_distributions']}")
        
        if analysis.get("location_details"):
            loc = analysis["location_details"]
            print(f"Location: {loc.get('county_name', 'Unknown')}, {loc.get('state_name', 'Unknown')}")
        
        print(f"\nDistributions Found:")
        for dist_key, dist_info in analysis["distributions"].items():
            print(f"\n  {dist_info['name']}:")
            print(f"    Status: {dist_info['status']}")
            
            if dist_info["status"] == "success":
                print(f"    Matched Gender: {dist_info['matched_gender']}")
                print(f"    Gender Explanation: {dist_info['gender_explanation']}")
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