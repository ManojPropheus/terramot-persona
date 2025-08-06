"""
Unified Age Distribution Analysis
Provides comprehensive age-based conditional analysis by combining multiple bivariate distributions.
Handles different age bracket systems through intelligent range mapping.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from typing import Dict, List, Any, Optional, Tuple
import re
from distribution.age_income_distribution import get_distribution as get_age_income, get_conditional_distribution as get_age_income_conditional
from distribution.age_gender_distribution import get_distribution as get_age_gender, get_conditional_distribution as get_age_gender_conditional  
from distribution.age_education_distribution import get_distribution as get_age_education, get_conditional_distribution as get_age_education_conditional
from distribution.age_race_distribution import get_distribution as get_age_race, get_conditional_distribution as get_age_race_conditional


def extract_age_bounds(age_range: str) -> Tuple[float, float]:
    """Extract numeric age bounds from an age range string."""
    age_range = age_range.lower()
    
    # Handle special cases
    if "under 5" in age_range:
        return (0, 4.99)
    elif "85 years and over" in age_range or "85+" in age_range:
        return (85, 120)
    elif "65 years and over" in age_range or "65+" in age_range:
        return (65, 120)
    elif "householder under 25" in age_range:
        return (0, 24.99)
    elif "householder 65 years and over" in age_range:
        return (65, 120)
    
    # Extract numbers from ranges like "25 to 34 years", "5 to 9 years", etc.
    numbers = re.findall(r'\d+', age_range)
    if len(numbers) >= 2:
        return (float(numbers[0]), float(numbers[1]))
    elif len(numbers) == 1:
        # Handle ranges like "18 and 19 years"
        if "and" in age_range:
            base = float(numbers[0])
            return (base, base + 1)
        # Handle ranges like "householder 25 to 44 years"
        elif "25 to 44" in age_range:
            return (25, 44)
        elif "45 to 64" in age_range:
            return (45, 64)
    
    # Fallback for unrecognized formats
    return (0, 120)


def find_best_age_match(target_age_range: str, available_ranges: List[str]) -> Tuple[str, float, str]:
    """
    Find the best matching age range from available options.
    Returns: (best_match, overlap_score, explanation)
    """
    target_min, target_max = extract_age_bounds(target_age_range)
    best_match = None
    best_overlap = 0
    best_explanation = ""
    
    for available_range in available_ranges:
        avail_min, avail_max = extract_age_bounds(available_range)
        
        # Calculate overlap
        overlap_min = max(target_min, avail_min)
        overlap_max = min(target_max, avail_max)
        
        if overlap_max > overlap_min:
            overlap_size = overlap_max - overlap_min
            target_size = target_max - target_min
            overlap_score = overlap_size / target_size
            
            if overlap_score > best_overlap:
                best_overlap = overlap_score
                best_match = available_range
                
                # Generate explanation
                if overlap_score >= 0.95:
                    best_explanation = f"Exact match"
                elif overlap_score >= 0.8:
                    best_explanation = f"Very close match (covers {overlap_score:.0%} of target range)"
                elif overlap_score >= 0.5:
                    best_explanation = f"Partial match (covers {overlap_score:.0%} of target range)"
                else:
                    best_explanation = f"Limited overlap (covers {overlap_score:.0%} of target range)"
    
    if not best_match:
        # Find the closest range by midpoint
        target_mid = (target_min + target_max) / 2
        closest_distance = float('inf')
        
        for available_range in available_ranges:
            avail_min, avail_max = extract_age_bounds(available_range)
            avail_mid = (avail_min + avail_max) / 2
            distance = abs(target_mid - avail_mid)
            
            if distance < closest_distance:
                closest_distance = distance
                best_match = available_range
                best_explanation = f"Closest available range (no overlap with target)"
    
    return best_match, best_overlap, best_explanation


def get_unified_age_analysis(lat: float, lng: float, target_age_range: str) -> Dict[str, Any]:
    """
    Get unified age analysis showing distributions from all bivariate combinations.
    """
    result = {
        "target_age_range": target_age_range,
        "location": {"lat": lat, "lng": lng},
        "distributions": {},
        "metadata": {
            "total_distributions": 0,
            "successful_retrievals": 0,
            "range_mappings": {}
        }
    }
    
    # Define all available age-based bivariate distributions
    distributions_config = {
        "income": {
            "name": "Income Distribution",
            "get_joint": get_age_income,
            "get_conditional": get_age_income_conditional,
            "variable_name": "income"
        },
        "gender": {
            "name": "Gender Distribution", 
            "get_joint": get_age_gender,
            "get_conditional": get_age_gender_conditional,
            "variable_name": "gender"
        },
        "education": {
            "name": "Education Distribution",
            "get_joint": get_age_education,
            "get_conditional": get_age_education_conditional,
            "variable_name": "education"
        },
        "race": {
            "name": "Race/Ethnicity Distribution",
            "get_joint": get_age_race,
            "get_conditional": get_age_race_conditional,
            "variable_name": "race"
        }
    }
    
    result["metadata"]["total_distributions"] = len(distributions_config)
    
    for dist_key, config in distributions_config.items():
        try:
            # Get joint distribution
            joint_data = config["get_joint"](lat, lng)
            
            if not joint_data or not joint_data.get("age_marginal"):
                result["distributions"][dist_key] = {
                    "name": config["name"],
                    "status": "no_data",
                    "error": "No data available for this location"
                }
                continue
            
            # Extract available age ranges
            available_ages = [item["category"] for item in joint_data["age_marginal"]]
            
            # Find best age match
            best_age, overlap_score, explanation = find_best_age_match(target_age_range, available_ages)
            
            if not best_age:
                result["distributions"][dist_key] = {
                    "name": config["name"],
                    "status": "no_match",
                    "error": "No suitable age range found"
                }
                continue
            
            # Get conditional distribution
            conditional_data = config["get_conditional"](joint_data, "age", best_age)
            
            if "error" in conditional_data:
                result["distributions"][dist_key] = {
                    "name": config["name"],
                    "status": "conditional_error",
                    "error": conditional_data["error"],
                    "matched_age_range": best_age,
                    "range_explanation": explanation
                }
                continue
            
            # Success - store the results
            result["distributions"][dist_key] = {
                "name": config["name"],
                "status": "success",
                "matched_age_range": best_age,
                "overlap_score": overlap_score,
                "range_explanation": explanation,
                "conditional_distribution": conditional_data,
                "data_source": conditional_data.get("data_source", "Unknown"),
                "total_population": conditional_data.get("total_population", 0)
            }
            
            result["metadata"]["successful_retrievals"] += 1
            result["metadata"]["range_mappings"][dist_key] = {
                "target": target_age_range,
                "matched": best_age,
                "overlap": overlap_score,
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
    # Test the unified age analysis
    lat, lon = 37.736509, -122.388028  # San Francisco area
    
    print("=" * 80)
    print("UNIFIED AGE DISTRIBUTION ANALYSIS")
    print("=" * 80)
    
    # Test different age ranges
    test_ages = [
        "5 to 9 years",      # Should match detailed ranges exactly
        "25 to 34 years",    # Should match education/gender ranges exactly  
        "30 to 40 years",    # Should partially match some ranges
        "Under 18 years"     # Should map to appropriate young age ranges
    ]
    
    for test_age in test_ages:
        print(f"\n{'='*60}")
        print(f"ANALYSIS FOR AGE RANGE: {test_age}")
        print(f"{'='*60}")
        
        analysis = get_unified_age_analysis(lat, lon, test_age)
        
        print(f"Target Age: {analysis['target_age_range']}")
        print(f"Successful Retrievals: {analysis['metadata']['successful_retrievals']}/{analysis['metadata']['total_distributions']}")
        
        if analysis.get("location_details"):
            loc = analysis["location_details"]
            print(f"Location: {loc.get('county_name', 'Unknown')}, {loc.get('state_name', 'Unknown')}")
        
        print(f"\nDistributions Found:")
        for dist_key, dist_info in analysis["distributions"].items():
            print(f"\n  {dist_info['name']}:")
            print(f"    Status: {dist_info['status']}")
            
            if dist_info["status"] == "success":
                print(f"    Matched Age Range: {dist_info['matched_age_range']}")
                print(f"    Range Explanation: {dist_info['range_explanation']}")
                print(f"    Population in Age Group: {dist_info['total_population']:,}")
                print(f"    Number of Categories: {len(dist_info['conditional_distribution']['data'])}")
                
                # Show top few categories
                data_sorted = sorted(dist_info['conditional_distribution']['data'], 
                                   key=lambda x: x['percentage'], reverse=True)
                print(f"    Top Categories:")
                for i, item in enumerate(data_sorted[:3]):
                    print(f"      {item['category']}: {item['percentage']:.1f}%")
            else:
                print(f"    Error: {dist_info.get('error', 'Unknown error')}")
        
        print("\n" + "-"*60)