"""
Unified Income Distribution Analysis
Provides comprehensive income-based conditional analysis by combining multiple bivariate distributions.
Handles different income bracket systems through intelligent range mapping.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from typing import Dict, List, Any, Optional, Tuple
import re
from distribution.age_income_distribution import get_distribution as get_age_income, get_conditional_distribution as get_age_income_conditional
from distribution.income_gender_distribution import get_distribution as get_income_gender, get_conditional_distribution as get_income_gender_conditional
from distribution.income_profession_distribution import get_distribution as get_income_profession, get_conditional_distribution as get_income_profession_conditional


def extract_income_bounds(income_range: str) -> Tuple[float, float]:
    """Extract numeric income bounds from an income range string."""
    income_range = income_range.lower().strip()
    
    # Handle special cases
    if "loss" in income_range or "negative" in income_range:
        return (0, 0)  # Loss/negative income treated as 0
    elif "$200,000 or more" in income_range or "$200,000+" in income_range:
        return (200000, 500000)  # Upper bound estimate for highest bracket
    elif "$100,000 or more" in income_range or "$100,000+" in income_range:
        return (100000, 500000)
    
    # Extract numbers from ranges like "$25,000 to $29,999", "$10,000 to $14,999"
    # Remove commas and dollar signs for easier parsing
    cleaned = income_range.replace(',', '').replace('$', '')
    
    # Look for patterns like "10000 to 14999"
    numbers = re.findall(r'\d+', cleaned)
    
    if len(numbers) >= 2:
        return (float(numbers[0]), float(numbers[1]))
    elif len(numbers) == 1:
        # Single number cases like "$1 to $2,499" 
        base = float(numbers[0])
        if "to" in income_range:
            # Estimate range based on common patterns
            if base < 10000:
                return (base, base + 2499)  # Small ranges
            elif base < 100000:
                return (base, base + 4999)  # Medium ranges
            else:
                return (base, base + 24999)  # Large ranges
        else:
            return (base, base)
    
    # Fallback for unrecognized formats
    return (0, 100000)


def find_best_income_match(target_income: str, available_incomes: List[str]) -> Tuple[str, float, str]:
    """
    Find the best matching income range from available options.
    Returns: (best_match, overlap_score, explanation)
    """
    target_min, target_max = extract_income_bounds(target_income)
    best_match = None
    best_overlap = 0
    best_explanation = ""
    
    for available_range in available_incomes:
        avail_min, avail_max = extract_income_bounds(available_range)
        
        # Calculate overlap
        overlap_min = max(target_min, avail_min)
        overlap_max = min(target_max, avail_max)
        
        if overlap_max > overlap_min:
            overlap_size = overlap_max - overlap_min
            target_size = target_max - target_min
            
            if target_size > 0:
                overlap_score = overlap_size / target_size
                
                if overlap_score > best_overlap:
                    best_overlap = overlap_score
                    best_match = available_range
                    
                    # Generate explanation
                    if overlap_score >= 0.95:
                        best_explanation = "Exact income range match"
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
        
        for available_range in available_incomes:
            avail_min, avail_max = extract_income_bounds(available_range)
            avail_mid = (avail_min + avail_max) / 2
            distance = abs(target_mid - avail_mid)
            
            if distance < closest_distance:
                closest_distance = distance
                best_match = available_range
                best_explanation = f"Closest available range (no overlap with target)"
    
    return best_match, best_overlap, best_explanation


def get_unified_income_analysis(lat: float, lng: float, target_income: str) -> Dict[str, Any]:
    """
    Get unified income analysis showing distributions from all bivariate combinations.
    """
    result = {
        "target_income": target_income,
        "location": {"lat": lat, "lng": lng},
        "distributions": {},
        "metadata": {
            "total_distributions": 0,
            "successful_retrievals": 0,
            "income_mappings": {}
        }
    }
    
    # Define all available income-based bivariate distributions
    distributions_config = {
        "age": {
            "name": "Age Distribution",
            "get_joint": get_age_income,
            "get_conditional": get_age_income_conditional,
            "condition_type": "income"
        },
        "gender": {
            "name": "Gender Distribution",
            "get_joint": get_income_gender,
            "get_conditional": get_income_gender_conditional,
            "condition_type": "income"
        },
        "profession": {
            "name": "Profession Distribution",
            "get_joint": get_income_profession,
            "get_conditional": get_income_profession_conditional,
            "condition_type": "income"
        }
    }
    
    result["metadata"]["total_distributions"] = len(distributions_config)
    
    for dist_key, config in distributions_config.items():
        try:
            # Get joint distribution
            joint_data = config["get_joint"](lat, lng)
            
            if not joint_data or not joint_data.get("income_marginal"):
                result["distributions"][dist_key] = {
                    "name": config["name"],
                    "status": "no_data",
                    "error": "No data available for this location"
                }
                continue
            
            # Extract available income ranges
            available_incomes = [item["category"] for item in joint_data["income_marginal"]]
            
            # Find best income match
            best_income, overlap_score, explanation = find_best_income_match(target_income, available_incomes)
            
            if not best_income:
                result["distributions"][dist_key] = {
                    "name": config["name"],
                    "status": "no_match",
                    "error": "No suitable income range found"
                }
                continue
            
            # Get conditional distribution
            conditional_data = config["get_conditional"](joint_data, config["condition_type"], best_income)
            
            if "error" in conditional_data:
                result["distributions"][dist_key] = {
                    "name": config["name"],
                    "status": "conditional_error",
                    "error": conditional_data["error"],
                    "matched_income": best_income,
                    "income_explanation": explanation
                }
                continue
            
            # Success - store the results
            result["distributions"][dist_key] = {
                "name": config["name"],
                "status": "success",
                "matched_income": best_income,
                "overlap_score": overlap_score,
                "income_explanation": explanation,
                "conditional_distribution": conditional_data,
                "data_source": conditional_data.get("data_source", "Unknown"),
                "total_population": conditional_data.get("total_population", 0)
            }
            
            result["metadata"]["successful_retrievals"] += 1
            result["metadata"]["income_mappings"][dist_key] = {
                "target": target_income,
                "matched": best_income,
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
    # Test the unified income analysis
    lat, lon = 37.736509, -122.388028  # San Francisco area
    
    print("=" * 80)
    print("UNIFIED INCOME DISTRIBUTION ANALYSIS")
    print("=" * 80)
    
    # Test different income ranges
    test_incomes = [
        "$50,000 to $59,999",           # Should match age×income exactly
        "$25,000 to $29,999",           # Should match both systems
        "$75,000 to $99,999",           # Should match both systems  
        "$45,000 to $49,999",           # Should match age×income exactly
        "$100,000 or more",             # Should map to different brackets in each
        "$10,000 to $15,000"            # Should partially overlap with multiple brackets
    ]
    
    for test_income in test_incomes:
        print(f"\n{'='*60}")
        print(f"ANALYSIS FOR INCOME RANGE: {test_income}")
        print(f"{'='*60}")
        
        analysis = get_unified_income_analysis(lat, lon, test_income)
        
        print(f"Target Income: {analysis['target_income']}")
        print(f"Successful Retrievals: {analysis['metadata']['successful_retrievals']}/{analysis['metadata']['total_distributions']}")
        
        if analysis.get("location_details"):
            loc = analysis["location_details"]
            print(f"Location: {loc.get('county_name', 'Unknown')}, {loc.get('state_name', 'Unknown')}")
        
        print(f"\nDistributions Found:")
        for dist_key, dist_info in analysis["distributions"].items():
            print(f"\n  {dist_info['name']}:")
            print(f"    Status: {dist_info['status']}")
            
            if dist_info["status"] == "success":
                print(f"    Matched Income Range: {dist_info['matched_income']}")
                print(f"    Income Explanation: {dist_info['income_explanation']}")
                print(f"    Population in Income Group: {dist_info['total_population']:,}")
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