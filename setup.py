#!/usr/bin/env python3
"""
Setup script for Census Distribution Explorer
Validates that all distribution scripts work correctly
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(__file__))

def test_distribution_scripts():
    """Test that all distribution scripts can be imported and work"""
    
    print("🧪 Testing distribution scripts...")
    
    try:
        from distribution.age_distribution import get_distribution as age_dist
        from distribution.gender_distribution import get_distribution as gender_dist
        from distribution.education_distribution import get_distribution as education_dist
        from distribution.income_distribution import get_distribution as income_dist
        
        print("✅ All distribution modules imported successfully")
        
        # Test with sample SF coordinates
        lat, lng = 37.7749, -122.4194
        print(f"🌍 Testing with coordinates: {lat}, {lng}")
        
        # Test age distribution
        print("  - Testing age distribution...")
        age_result = age_dist(lat, lng)
        assert age_result['type'] == 'age'
        assert len(age_result['data']) > 0
        print(f"    ✅ Age: {len(age_result['data'])} categories")
        
        # Test gender distribution
        print("  - Testing gender distribution...")
        gender_result = gender_dist(lat, lng)
        assert gender_result['type'] == 'gender'
        assert len(gender_result['data']) > 0
        print(f"    ✅ Gender: {len(gender_result['data'])} categories")
        
        # Test education distribution
        print("  - Testing education distribution...")
        education_result = education_dist(lat, lng)
        assert education_result['type'] == 'education'
        assert len(education_result['data']) > 0
        print(f"    ✅ Education: {len(education_result['data'])} categories")
        
        # Test income distribution
        print("  - Testing income distribution...")
        income_result = income_dist(lat, lng)
        assert income_result['type'] == 'income'
        assert len(income_result['data']) > 0
        print(f"    ✅ Income: {len(income_result['data'])} categories")
        
        print("\n🎉 All distribution scripts are working correctly!")
        print("\n📍 Sample location data:")
        print(f"   Location: {age_result['location']['subdivision_name'] or age_result['location']['county_name']}")
        print(f"   State: {age_result['location']['state_name']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing distribution scripts: {e}")
        return False

def main():
    print("🚀 Census Distribution Explorer Setup")
    print("=" * 50)
    
    if test_distribution_scripts():
        print("\n✨ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Start the backend: cd backend && python app.py")  
        print("2. Start the frontend: cd frontend && npm install && npm start")
        print("3. Open http://localhost:3000 in your browser")
    else:
        print("\n❌ Setup failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()