"""
Unified Profession Distribution Analysis
Provides comprehensive profession-based conditional analysis by combining multiple bivariate distributions.
Handles different profession classification systems through intelligent mapping.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from typing import Dict, List, Any, Optional, Tuple
from distribution.income_profession_distribution import get_distribution as get_income_profession, get_conditional_distribution as get_income_profession_conditional
from distribution.profession_race_distribution import get_distribution as get_profession_race, get_conditional_distribution as get_profession_race_conditional
from distribution.profession_distribution import get_distribution as get_profession_distribution, get_conditional_distribution as get_profession_conditional


def normalize_profession(profession: str) -> str:
    """Normalize profession names to a standard format for comparison."""
    profession = profession.lower().strip()
    
    # Create mapping from various formats to standardized professions
    mappings = {
        # Management occupations
        'management, business, science, and arts occupations': 'management_business_science_arts',
        'management, business, and financial occupations': 'management_business_financial',
        'management occupations': 'management',
        
        # Service occupations
        'service occupations': 'service',
        'food preparation and serving related occupations': 'food_service',
        'healthcare support occupations': 'healthcare_support',
        'protective service occupations': 'protective_service',
        
        # Sales and office
        'sales and office occupations': 'sales_office',
        'sales and related occupations': 'sales',
        'office and administrative support occupations': 'office_admin',
        
        # Natural resources, construction, and maintenance
        'natural resources, construction, and maintenance occupations': 'natural_resources_construction_maintenance',
        'farming, fishing, and forestry occupations': 'farming_fishing_forestry',
        'construction and extraction occupations': 'construction_extraction',
        'installation, maintenance, and repair occupations': 'installation_maintenance_repair',
        
        # Production, transportation, and material moving
        'production, transportation, and material moving occupations': 'production_transportation_material',
        'production occupations': 'production',
        'transportation and material moving occupations': 'transportation_material',
        
        # Professional occupations
        'professional, scientific, and technical services': 'professional_scientific_technical',
        'healthcare practitioners and technical occupations': 'healthcare_practitioners',
        'education, training, and library occupations': 'education_training_library',
        'computer and mathematical occupations': 'computer_mathematical',
        'architecture and engineering occupations': 'architecture_engineering',
        'legal occupations': 'legal',
        'arts, design, entertainment, sports, and media occupations': 'arts_design_entertainment'
    }
    
    return mappings.get(profession, profession)


def find_best_profession_match(target_profession: str, available_professions: List[str]) -> Tuple[str, float, str]:
    """
    Find the best matching profession from available options.
    Returns: (best_match, similarity_score, explanation)
    """
    target_norm = normalize_profession(target_profession)
    best_match = None
    best_score = 0
    best_explanation = ""
    
    # First try exact normalized matches
    for available in available_professions:
        available_norm = normalize_profession(available)
        
        if target_norm == available_norm:
            return available, 1.0, "Exact profession match"
    
    # If no exact match, look for partial matches or closest alternatives
    profession_hierarchy = [
        'management_business_science_arts', 'management_business_financial', 'management',
        'professional_scientific_technical', 'computer_mathematical', 'architecture_engineering',
        'healthcare_practitioners', 'healthcare_support', 'education_training_library',
        'legal', 'arts_design_entertainment', 'service', 'food_service', 'protective_service',
        'sales_office', 'sales', 'office_admin', 'natural_resources_construction_maintenance',
        'farming_fishing_forestry', 'construction_extraction', 'installation_maintenance_repair',
        'production_transportation_material', 'production', 'transportation_material'
    ]
    
    # Try string similarity matching
    best_substring_score = 0
    for available in available_professions:
        # Check for key word matches
        target_words = set(target_profession.lower().split())
        available_words = set(available.lower().split())
        
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
                elif overlap_score >= 0.3:
                    best_explanation = f"Moderate word overlap match ({overlap_score:.1%})"
                    best_score = overlap_score * 0.8
                else:
                    best_explanation = f"Weak word overlap match ({overlap_score:.1%})"
                    best_score = overlap_score * 0.6
    
    # If still no good match, try hierarchy-based matching
    if not best_match or best_score < 0.5:
        try:
            target_idx = profession_hierarchy.index(target_norm)
            closest_distance = float('inf')
            
            for available in available_professions:
                available_norm = normalize_profession(available)
                try:
                    available_idx = profession_hierarchy.index(available_norm)
                    distance = abs(target_idx - available_idx)
                    
                    if distance < closest_distance:
                        closest_distance = distance
                        best_match = available
                        
                        if distance == 0:
                            best_explanation = "Exact hierarchical match"
                            best_score = 1.0
                        elif distance <= 2:
                            best_explanation = f"Similar profession category (hierarchy distance: {distance})"
                            best_score = 0.8 - (distance * 0.2)
                        else:
                            best_explanation = f"Different profession category (hierarchy distance: {distance})"
                            best_score = 0.4
                except ValueError:
                    continue
        except ValueError:
            pass
    
    # Final fallback to first available option
    if not best_match:
        best_match = available_professions[0] if available_professions else None
        best_explanation = "Fallback to first available profession"
        best_score = 0.2
    
    return best_match, best_score, best_explanation


def get_unified_profession_analysis(lat: float, lng: float, target_profession: str) -> Dict[str, Any]:
    """
    Get unified profession analysis showing distributions from all bivariate combinations.
    """
    result = {
        "target_profession": target_profession,
        "location": {"lat": lat, "lng": lng},
        "distributions": {},
        "metadata": {
            "total_distributions": 0,
            "successful_retrievals": 0,
            "profession_mappings": {}
        }
    }
    
    # Define all available profession-based bivariate distributions
    distributions_config = {
        "income": {
            "name": "Income Distribution",
            "get_joint": get_income_profession,
            "get_conditional": get_income_profession_conditional,
            "condition_type": "profession"
        },
        "race": {
            "name": "Race/Ethnicity Distribution", 
            "get_joint": get_profession_race,
            "get_conditional": get_profession_race_conditional,
            "condition_type": "profession"
        }
    }
    
    result["metadata"]["total_distributions"] = len(distributions_config)
    
    for dist_key, config in distributions_config.items():
        try:
            # Get joint distribution
            joint_data = config["get_joint"](lat, lng)
            
            if not joint_data or not joint_data.get("profession_marginal"):
                result["distributions"][dist_key] = {
                    "name": config["name"],
                    "status": "no_data",
                    "error": "No data available for this location"
                }
                continue
            
            # Extract available professions
            available_professions = [item["category"] for item in joint_data["profession_marginal"]]
            
            # Find best profession match
            best_profession, similarity_score, explanation = find_best_profession_match(target_profession, available_professions)
            
            if not best_profession:
                result["distributions"][dist_key] = {
                    "name": config["name"],
                    "status": "no_match",
                    "error": "No suitable profession found"
                }
                continue
            
            # Get conditional distribution
            conditional_data = config["get_conditional"](joint_data, config["condition_type"], best_profession)
            
            if "error" in conditional_data:
                result["distributions"][dist_key] = {
                    "name": config["name"],
                    "status": "conditional_error",
                    "error": conditional_data["error"],
                    "matched_profession": best_profession,
                    "profession_explanation": explanation
                }
                continue
            
            # Success - store the results
            result["distributions"][dist_key] = {
                "name": config["name"],
                "status": "success",
                "matched_profession": best_profession,
                "similarity_score": similarity_score,
                "profession_explanation": explanation,
                "conditional_distribution": conditional_data,
                "data_source": conditional_data.get("data_source", "Unknown"),
                "total_population": conditional_data.get("total_population", 0)
            }
            
            result["metadata"]["successful_retrievals"] += 1
            result["metadata"]["profession_mappings"][dist_key] = {
                "target": target_profession,
                "matched": best_profession,
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
    # Test the unified profession analysis
    lat, lon = 37.736509, -122.388028  # San Francisco area
    
    print("=" * 80)
    print("UNIFIED PROFESSION DISTRIBUTION ANALYSIS")
    print("=" * 80)
    
    # Test different profession categories
    test_professions = [
        "Management, business, science, and arts occupations",
        "Service occupations",
        "Sales and office occupations", 
        "Natural resources, construction, and maintenance occupations",
        "Production, transportation, and material moving occupations",
        "Healthcare practitioners",  # Test partial matching
        "Computer and mathematical"   # Test partial matching
    ]
    
    for test_profession in test_professions:
        print(f"\n{'='*60}")
        print(f"ANALYSIS FOR PROFESSION: {test_profession}")
        print(f"{'='*60}")
        
        analysis = get_unified_profession_analysis(lat, lon, test_profession)
        
        print(f"Target Profession: {analysis['target_profession']}")
        print(f"Successful Retrievals: {analysis['metadata']['successful_retrievals']}/{analysis['metadata']['total_distributions']}")
        
        if analysis.get("location_details"):
            loc = analysis["location_details"]
            print(f"Location: {loc.get('county_name', 'Unknown')}, {loc.get('state_name', 'Unknown')}")
        
        print(f"\nDistributions Found:")
        for dist_key, dist_info in analysis["distributions"].items():
            print(f"\n  {dist_info['name']}:")
            print(f"    Status: {dist_info['status']}")
            
            if dist_info["status"] == "success":
                print(f"    Matched Profession: {dist_info['matched_profession']}")
                print(f"    Profession Explanation: {dist_info['profession_explanation']}")
                print(f"    Population in Profession: {dist_info['total_population']:,}")
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