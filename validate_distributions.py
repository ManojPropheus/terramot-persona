#!/usr/bin/env python3
"""
Distribution Validation Script
Tests all distributions for consistency, proper data structures, and functionality.
"""

import sys
import traceback
from typing import Dict, List, Any

# Test coordinates (San Francisco area)
TEST_LAT, TEST_LON = 37.736509, -122.388028

def test_distribution(module_name: str, distribution_name: str) -> Dict[str, Any]:
    """Test a single distribution module."""
    result = {
        "module": module_name,
        "distribution": distribution_name,
        "status": "unknown",
        "data": None,
        "error": None,
        "joint_data_count": 0,
        "marginals": {},
        "conditional_tests": []
    }
    
    try:
        # Import the module
        module = __import__(f"distribution.{module_name}", fromlist=[''])
        get_distribution = getattr(module, 'get_distribution')
        get_conditional_distribution = getattr(module, 'get_conditional_distribution', None)
        
        print(f"Testing {distribution_name}...")
        
        # Test basic distribution
        data = get_distribution(TEST_LAT, TEST_LON)
        
        if not data:
            result["status"] = "no_data"
            result["error"] = "No data returned"
            return result
        
        result["data"] = data
        result["joint_data_count"] = len(data.get("joint_data", []))
        
        # Check for required fields - joint_data is only required for joint distributions
        required_fields = ["location", "data_source"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            result["status"] = "incomplete"
            result["error"] = f"Missing required fields: {missing_fields}"
            return result
        
        # For single-variable distributions, check for 'data' field instead of 'joint_data'
        has_joint_data = "joint_data" in data
        has_single_data = "data" in data
        
        if not has_joint_data and not has_single_data:
            result["status"] = "incomplete"
            result["error"] = "Missing both 'joint_data' and 'data' fields"
            return result
        
        # Check marginal distributions
        marginals = {}
        for key in data.keys():
            if "_marginal" in key:
                marginals[key] = len(data[key])
        result["marginals"] = marginals
        
        # Test conditional distributions if available
        if get_conditional_distribution and result["joint_data_count"] > 0:
            # Try to determine condition types from joint data
            joint_sample = data["joint_data"][0] if data["joint_data"] else {}
            
            for condition_type in joint_sample.keys():
                if condition_type in ["profession", "age_range", "race_ethnicity", "income_range", "gender", "education"]:
                    # Map backend field names to condition types
                    condition_type_mapping = {
                        "age_range": "age",
                        "race_ethnicity": "race",
                        "income_range": "income"
                    }
                    
                    mapped_condition_type = condition_type_mapping.get(condition_type, condition_type)
                    
                    # Get a sample condition value
                    condition_value = joint_sample[condition_type]
                    
                    try:
                        conditional_result = get_conditional_distribution(data, mapped_condition_type, condition_value)
                        
                        conditional_test = {
                            "condition_type": mapped_condition_type,
                            "condition_value": condition_value,
                            "status": "error" if "error" in conditional_result else "success",
                            "data_count": len(conditional_result.get("data", [])),
                            "error": conditional_result.get("error")
                        }
                        
                        result["conditional_tests"].append(conditional_test)
                        
                    except Exception as e:
                        result["conditional_tests"].append({
                            "condition_type": mapped_condition_type,
                            "condition_value": condition_value,
                            "status": "exception",
                            "error": str(e)
                        })
        
        result["status"] = "success"
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = f"{type(e).__name__}: {str(e)}"
        print(f"  ERROR: {result['error']}")
        
    return result

def main():
    """Run validation tests on all distributions."""
    
    # Define distributions to test
    distributions_to_test = [
        ("age_distribution", "Age Distribution"),
        ("gender_distribution", "Gender Distribution"),
        ("income_distribution", "Income Distribution"),
        ("profession_distribution", "Profession Distribution"),
        ("education_distribution", "Education Distribution"),
        ("race_ethnicity_distribution", "Race/Ethnicity Distribution"),
        ("age_gender_distribution", "Age-Gender Joint Distribution"),
        ("age_race_distribution", "Age-Race Joint Distribution"),
        ("income_gender_distribution", "Income-Gender Joint Distribution"),
        ("income_profession_distribution", "Income-Profession Joint Distribution"),
        ("profession_race_distribution", "Profession-Race Joint Distribution"),
        ("gender_education_distribution", "Gender-Education Joint Distribution"),
        ("education_race_distribution", "Education-Race Joint Distribution"),
    ]
    
    print("=" * 80)
    print("CENSUS DISTRIBUTION VALIDATION")
    print("=" * 80)
    print(f"Test Location: {TEST_LAT}, {TEST_LON} (San Francisco area)")
    print()
    
    results = []
    success_count = 0
    total_count = len(distributions_to_test)
    
    for module_name, distribution_name in distributions_to_test:
        result = test_distribution(module_name, distribution_name)
        results.append(result)
        
        if result["status"] == "success":
            success_count += 1
            print(f"  ✓ {distribution_name}")
            if result["joint_data_count"] > 0:
                print(f"    Joint data points: {result['joint_data_count']}")
            if result["marginals"]:
                print(f"    Marginals: {result['marginals']}")
            if result["conditional_tests"]:
                successful_conditionals = sum(1 for test in result["conditional_tests"] if test["status"] == "success")
                print(f"    Conditional tests: {successful_conditionals}/{len(result['conditional_tests'])} passed")
        else:
            print(f"  ✗ {distribution_name}: {result['error']}")
        
        print()
    
    # Summary
    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Total distributions tested: {total_count}")
    print(f"Successful: {success_count}")
    print(f"Failed: {total_count - success_count}")
    print(f"Success rate: {success_count/total_count*100:.1f}%")
    
    # Detailed conditional test results
    print("\\n" + "=" * 80)
    print("CONDITIONAL DISTRIBUTION TESTS")
    print("=" * 80)
    
    for result in results:
        if result["conditional_tests"]:
            print(f"\\n{result['distribution']}:")
            for test in result["conditional_tests"]:
                status_symbol = "✓" if test["status"] == "success" else "✗"
                print(f"  {status_symbol} {test['condition_type']} = '{test['condition_value']}'")
                if test["status"] == "success":
                    print(f"    Data points: {test['data_count']}")
                else:
                    print(f"    Error: {test['error']}")
    
    # Category consistency checks
    print("\\n" + "=" * 80)
    print("CATEGORY CONSISTENCY CHECKS")
    print("=" * 80)
    
    # Check age categories across distributions
    age_categories = {}
    profession_categories = {}
    race_categories = {}
    
    for result in results:
        if result["status"] == "success" and result["data"]:
            data = result["data"]
            
            # Check age categories
            if "age_marginal" in data:
                age_cats = [item["category"] for item in data["age_marginal"]]
                age_categories[result["distribution"]] = age_cats
            
            # Check profession categories
            if "profession_marginal" in data:
                prof_cats = [item["category"] for item in data["profession_marginal"]]
                profession_categories[result["distribution"]] = prof_cats
            
            # Check race categories
            if "race_marginal" in data:
                race_cats = [item["category"] for item in data["race_marginal"]]
                race_categories[result["distribution"]] = race_cats
    
    # Report consistency
    def check_consistency(categories_dict, category_type):
        if not categories_dict:
            print(f"{category_type}: No distributions found")
            return
        
        reference_dist = list(categories_dict.keys())[0]
        reference_cats = set(categories_dict[reference_dist])
        
        consistent = True
        for dist, cats in categories_dict.items():
            if set(cats) != reference_cats:
                consistent = False
                print(f"{category_type} INCONSISTENCY in {dist}:")
                print(f"  Expected: {sorted(reference_cats)}")
                print(f"  Found: {sorted(cats)}")
                print()
        
        if consistent:
            print(f"{category_type}: ✓ All distributions use consistent categories")
    
    check_consistency(age_categories, "Age Categories")
    check_consistency(profession_categories, "Profession Categories") 
    check_consistency(race_categories, "Race Categories")
    
    return success_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)