"""
Flask API for Census Distribution Data
Provides a /distribution endpoint that returns all 4 distribution types
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, request, jsonify
from flask_cors import CORS
import concurrent.futures
import logging

from distribution.age_distribution import get_distribution as get_age_distribution
from distribution.gender_distribution import get_distribution as get_gender_distribution  
from distribution.education_distribution import get_distribution as get_education_distribution
from distribution.income_distribution import get_distribution as get_income_distribution
from distribution.profession_distribution import get_distribution as get_profession_distribution
from distribution.race_ethnicity_distribution import get_distribution as get_race_ethnicity_distribution
# Joint distributions - Old
from distribution.age_income_distribution import get_distribution as get_age_income_distribution
from distribution.age_income_distribution import get_conditional_distribution as get_age_income_conditional
from distribution.age_gender_distribution import get_distribution as get_age_gender_distribution
from distribution.age_gender_distribution import get_conditional_distribution as get_age_gender_conditional
from distribution.age_race_distribution import get_distribution as get_age_race_distribution
from distribution.age_race_distribution import get_conditional_distribution as get_age_race_conditional
from distribution.age_education_distribution import get_distribution as get_age_education_distribution
from distribution.age_education_distribution import get_conditional_distribution as get_age_education_conditional
from distribution.education_sex_distribution import get_distribution as get_education_sex_distribution
from distribution.education_sex_distribution import get_conditional_distribution as get_education_sex_conditional_distribution
from distribution.income_gender_distribution import get_distribution as get_income_gender_distribution
from distribution.income_gender_distribution import get_conditional_distribution as get_income_gender_conditional
from distribution.profession_distribution import get_conditional_distribution as get_profession_conditional
# Joint distributions - New
from distribution.gender_education_distribution import get_distribution as get_gender_education_distribution
from distribution.gender_education_distribution import get_conditional_distribution as get_gender_education_conditional
from distribution.income_gender_distribution_new import get_distribution as get_income_gender_new_distribution
from distribution.income_gender_distribution_new import get_conditional_distribution as get_income_gender_new_conditional
from distribution.income_profession_distribution import get_distribution as get_income_profession_distribution
from distribution.income_profession_distribution import get_conditional_distribution as get_income_profession_conditional
from distribution.education_race_distribution import get_distribution as get_education_race_distribution
from distribution.education_race_distribution import get_conditional_distribution as get_education_race_conditional
from distribution.profession_race_distribution import get_distribution as get_profession_race_distribution
from distribution.profession_race_distribution import get_conditional_distribution as get_profession_race_conditional
from distribution.age_distribution import get_geography
from chatbot_service import create_chatbot
from utils import get_geoid

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize chatbot
try:
    chatbot = create_chatbot()
    logger.info("Chatbot initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize chatbot: {e}")
    chatbot = None

@app.route('/distribution', methods=['POST'])
def get_distributions():
    """
    Get all 4 distribution types for given coordinates
    
    Expected JSON body: {"lat": float, "lng": float}
    Returns: JSON with age, gender, education, and income distributions
    """
    try:
        data = request.get_json()
        
        if not data or 'lat' not in data or 'lng' not in data:
            return jsonify({
                "error": "Missing required fields: lat, lng"
            }), 400
            
        lat = float(data['lat'])
        lng = float(data['lng'])
        
        logger.info(f"Fetching distributions for coordinates: {lat}, {lng}")
        
        # Fetch all distributions concurrently for better performance
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
            # Individual distributions for the 6 variables
            future_age = executor.submit(get_age_distribution, lat, lng)
            future_gender = executor.submit(get_gender_distribution, lat, lng)
            future_education = executor.submit(get_education_distribution, lat, lng)
            future_income = executor.submit(get_income_distribution, lat, lng)
            future_profession = executor.submit(get_profession_distribution, lat, lng)
            future_race_ethnicity = executor.submit(get_race_ethnicity_distribution, lat, lng)
            
            # Joint distributions for the 6 variables
            future_age_income = executor.submit(get_age_income_distribution, lat, lng)
            future_age_gender = executor.submit(get_age_gender_distribution, lat, lng)
            future_age_race = executor.submit(get_age_race_distribution, lat, lng)
            future_age_education = executor.submit(get_age_education_distribution, lat, lng)
            future_income_gender = executor.submit(get_income_gender_distribution, lat, lng)
            future_profession_gender = executor.submit(get_profession_distribution, lat, lng)  # Already includes gender breakdown
            
            # Wait for all to complete and get results
            age_result = future_age.result()
            gender_result = future_gender.result()
            education_result = future_education.result()
            income_result = future_income.result()
            profession_result = future_profession.result()
            race_ethnicity_result = future_race_ethnicity.result()
            
            age_income_result = future_age_income.result()
            age_gender_result = future_age_gender.result()
            age_race_result = future_age_race.result()
            age_education_result = future_age_education.result()
            income_gender_result = future_income_gender.result()
            profession_gender_result = future_profession_gender.result()
        
        # Combine all results
        response = {
            "coordinates": {"lat": lat, "lng": lng},
            "location": age_result.get("location", {}),  # All should have same location
            "distributions": {
                # Individual distributions for the 6 variables
                "age": age_result,
                "gender": gender_result,
                "education": education_result,
                "income": income_result,
                "profession": profession_result,
                "race_ethnicity": race_ethnicity_result,
                
                # Joint distributions for the 6 variables
                "age_income": age_income_result,
                "age_gender": age_gender_result,
                "age_race": age_race_result,
                "age_education": age_education_result,
                "income_gender": income_gender_result,
                "profession_gender": profession_gender_result
            }
        }
        
        logger.info(f"Successfully fetched all distributions for {lat}, {lng}")
        return jsonify(response)
        
    except ValueError as e:
        logger.error(f"Invalid coordinates: {e}")
        return jsonify({
            "error": "Invalid coordinates provided"
        }), 400
        
    except Exception as e:
        logger.error(f"Error fetching distributions: {e}")
        return jsonify({
            "error": "Failed to fetch distribution data",
            "details": str(e)
        }), 500

@app.route('/conditional_distribution', methods=['POST'])
def get_conditional_distributions():
    """
    Get conditional distribution from joint age-income data
    
    Expected JSON body: 
    {
        "lat": float, 
        "lng": float, 
        "condition_type": "age" or "income",
        "condition_value": string (age range or income range)
    }
    Returns: JSON with conditional distribution
    """
    try:
        data = request.get_json()
        
        required_fields = ['lat', 'lng', 'condition_type', 'condition_value']
        if not data or not all(field in data for field in required_fields):
            return jsonify({
                "error": f"Missing required fields: {', '.join(required_fields)}"
            }), 400
            
        lat = float(data['lat'])
        lng = float(data['lng'])
        condition_type = data['condition_type']
        condition_value = data['condition_value']
        
        if condition_type not in ['age', 'income']:
            return jsonify({
                "error": "condition_type must be 'age' or 'income'"
            }), 400
        
        logger.info(f"Fetching conditional distribution for {lat}, {lng}, condition: {condition_type}={condition_value}")
        
        # First get the joint distribution
        joint_data = get_age_income_distribution(lat, lng)
        
        if not joint_data:
            return jsonify({
                "error": "Could not fetch joint distribution data"
            }), 500
        
        # Get conditional distribution
        conditional_result = get_age_income_conditional(joint_data, condition_type, condition_value)
        
        if 'error' in conditional_result:
            return jsonify(conditional_result), 404
        
        response = {
            "coordinates": {"lat": lat, "lng": lng},
            "location": joint_data["location"],
            "conditional_distribution": conditional_result
        }
        
        logger.info(f"Successfully fetched conditional distribution")
        return jsonify(response)
        
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        return jsonify({
            "error": "Invalid input provided"
        }), 400
        
    except Exception as e:
        logger.error(f"Error fetching conditional distribution: {e}")
        return jsonify({
            "error": "Failed to fetch conditional distribution data",
            "details": str(e)
        }), 500


@app.route('/unified_conditional', methods=['POST'])
def get_unified_conditional_distribution():
    """
    Get conditional distribution from any joint distribution data
    
    Expected JSON body:
    {
        "lat": float,
        "lng": float,
        "base_distribution": "age_income" or "profession", 
        "condition_type": depends on base_distribution,
        "condition_value": string
    }
    Returns: JSON with conditional distribution
    """
    try:
        data = request.get_json()
        
        required_fields = ['lat', 'lng', 'base_distribution', 'condition_type', 'condition_value']
        if not data or not all(field in data for field in required_fields):
            return jsonify({
                "error": f"Missing required fields: {', '.join(required_fields)}"
            }), 400
        
        lat = float(data['lat'])
        lng = float(data['lng'])
        base_distribution = data['base_distribution']
        condition_type = data['condition_type']
        condition_value = data['condition_value']
        
        logger.info(f"Fetching unified conditional distribution for {lat}, {lng}, base: {base_distribution}, condition: {condition_type}={condition_value}")
        
        # Handle different base distributions
        if base_distribution == 'age_income':
            if condition_type not in ['age', 'income']:
                return jsonify({"error": "For age_income base, condition_type must be 'age' or 'income'"}), 400
            
            joint_data = get_age_income_distribution(lat, lng)
            if not joint_data:
                return jsonify({"error": "Could not fetch age-income distribution data"}), 500
            
            conditional_result = get_age_income_conditional(joint_data, condition_type, condition_value)
            
        elif base_distribution == 'age_gender':
            if condition_type not in ['age', 'gender']:
                return jsonify({"error": "For age_gender base, condition_type must be 'age' or 'gender'"}), 400
            
            joint_data = get_age_gender_distribution(lat, lng)
            if not joint_data:
                return jsonify({"error": "Could not fetch age-gender distribution data"}), 500
            
            conditional_result = get_age_gender_conditional(joint_data, condition_type, condition_value)
            
        elif base_distribution == 'age_race':
            if condition_type not in ['age', 'race']:
                return jsonify({"error": "For age_race base, condition_type must be 'age' or 'race'"}), 400
            
            joint_data = get_age_race_distribution(lat, lng)
            if not joint_data:
                return jsonify({"error": "Could not fetch age-race distribution data"}), 500
            
            conditional_result = get_age_race_conditional(joint_data, condition_type, condition_value)
            
        elif base_distribution == 'age_education':
            if condition_type not in ['age', 'education']:
                return jsonify({"error": "For age_education base, condition_type must be 'age' or 'education'"}), 400
            
            joint_data = get_age_education_distribution(lat, lng)
            if not joint_data:
                return jsonify({"error": "Could not fetch age-education distribution data"}), 500
            
            conditional_result = get_age_education_conditional(joint_data, condition_type, condition_value)
            
        elif base_distribution == 'income_gender':
            if condition_type not in ['income', 'gender']:
                return jsonify({"error": "For income_gender base, condition_type must be 'income' or 'gender'"}), 400
            
            joint_data = get_income_gender_distribution(lat, lng)
            if not joint_data:
                return jsonify({"error": "Could not fetch income-gender distribution data"}), 500
            
            conditional_result = get_income_gender_conditional(joint_data, condition_type, condition_value)
            
        elif base_distribution == 'profession_gender':
            if condition_type not in ['profession', 'gender']:
                return jsonify({"error": "For profession_gender base, condition_type must be 'profession' or 'gender'"}), 400
            
            joint_data = get_profession_distribution(lat, lng)
            if not joint_data:
                return jsonify({"error": "Could not fetch profession distribution data"}), 500
            
            conditional_result = get_profession_conditional(joint_data, condition_type, condition_value)
            
        else:
            return jsonify({"error": f"Unsupported base_distribution: {base_distribution}"}), 400
        
        if 'error' in conditional_result:
            return jsonify(conditional_result), 404
        
        response = {
            "coordinates": {"lat": lat, "lng": lng},
            "location": joint_data.get("location", {}),
            "base_distribution": base_distribution,
            "conditional_distribution": conditional_result
        }
        
        logger.info(f"Successfully fetched unified conditional distribution")
        return jsonify(response)
        
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        return jsonify({"error": "Invalid input provided"}), 400
        
    except Exception as e:
        logger.error(f"Error fetching unified conditional distribution: {e}")
        return jsonify({
            "error": "Failed to fetch unified conditional distribution data",
            "details": str(e)
        }), 500


@app.route('/geography', methods=['POST'])
def get_geography_from_lat_long():
    try:
        data = request.get_json()
        if not data or 'lat' not in data or 'lng' not in data:
            return jsonify({
                "error": "Missing required fields: lat, lng"
            }), 400

        lat = float(data['lat'])
        lng = float(data['lng'])

        logger.info(f"Fetching geography for coordinates: {lat}, {lng}")

        geography_result = get_geography(lat, lng)
        
        if not geography_result:
            return jsonify({
                "error": "Could not fetch geography data for these coordinates"
            }), 404

        response = {
            "coordinates": {"lat": lat, "lng": lng},
            "location": geography_result
        }

        return jsonify(response)

    except ValueError as e:
        logger.error(f"Invalid coordinates: {e}")
        return jsonify({
            "error": "Invalid coordinates provided"
        }), 400

    except Exception as e:
        logger.error(f"Error fetching geography: {e}")
        return jsonify({
            "error": "Failed to fetch geography data",
            "details": str(e)
        }), 500



@app.route('/chat', methods=['POST'])
def chat_endpoint():
    """
    Chat with the Census Data Analysis AI Assistant
    
    Expected JSON body:
    {
        "message": "Your question about census data",
        "lat": float (optional),
        "lng": float (optional)
    }
    Returns: JSON with AI response and metadata
    """
    if not chatbot:
        return jsonify({
            "error": "Chatbot service is not available. Please check API key configuration."
        }), 503
    
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                "error": "Missing required field: message"
            }), 400
        
        message = data['message']
        lat = data.get('lat')
        lng = data.get('lng')
        
        logger.info(f"Chat request: {message[:100]}...")
        
        # Process chat request
        response = chatbot.chat(message, lat=lat, lng=lng)
        
        logger.info(f"Chat response generated successfully")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return jsonify({
            "error": "Failed to process chat request",
            "details": str(e)
        }), 500


@app.route('/chat/history', methods=['GET'])
def get_chat_history():
    """Get conversation history"""
    if not chatbot:
        return jsonify({
            "error": "Chatbot service is not available"
        }), 503
    
    try:
        history = chatbot.get_conversation_history()
        return jsonify({
            "history": history,
            "count": len(history)
        })
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        return jsonify({
            "error": "Failed to get chat history",
            "details": str(e)
        }), 500


@app.route('/chat/clear', methods=['POST'])
def clear_chat_history():
    """Clear conversation history"""
    if not chatbot:
        return jsonify({
            "error": "Chatbot service is not available"
        }), 503
    
    try:
        chatbot.clear_conversation()
        return jsonify({
            "message": "Conversation history cleared successfully"
        })
    except Exception as e:
        logger.error(f"Error clearing chat history: {e}")
        return jsonify({
            "error": "Failed to clear chat history",
            "details": str(e)
        }), 500


@app.route('/agent/status', methods=['GET'])
def get_agent_status():
    """Get comprehensive agent status and analytics"""
    if not chatbot:
        return jsonify({
            "error": "Chatbot service is not available"
        }), 503
    
    try:
        status = chatbot.get_agent_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        return jsonify({
            "error": "Failed to get agent status",
            "details": str(e)
        }), 500


@app.route('/agent/mode', methods=['POST'])
def toggle_agent_mode():
    """Toggle between intelligent agent and legacy mode"""
    if not chatbot:
        return jsonify({
            "error": "Chatbot service is not available"
        }), 503
    
    try:
        data = request.get_json()
        use_intelligent = data.get('use_intelligent_agent', True)
        
        result = chatbot.toggle_agent_mode(use_intelligent)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error toggling agent mode: {e}")
        return jsonify({
            "error": "Failed to toggle agent mode",
            "details": str(e)
        }), 500


@app.route('/joint_probability', methods=['POST'])
def get_joint_probability():
    """
    Unified joint probability endpoint with conditional distributions.
    
    Expected JSON body:
    {
        "lat": float,
        "lng": float,
        "distribution_type": "gender_education" | "income_gender_new" | "income_profession" | 
                           "education_race" | "profession_race" | "age_income" | "age_gender" | 
                           "age_race" | "age_education" | "education_sex" | "income_gender" | 
                           "profession_gender",
        "condition_type": string (optional),
        "condition_value": string (optional)
    }
    """
    try:
        data = request.get_json()
        
        required_fields = ['lat', 'lng', 'distribution_type']
        if not data or not all(field in data for field in required_fields):
            return jsonify({
                "error": f"Missing required fields: {', '.join(required_fields)}"
            }), 400
            
        lat = float(data['lat'])
        lng = float(data['lng'])
        distribution_type = data['distribution_type']
        condition_type = data.get('condition_type')
        condition_value = data.get('condition_value')
        
        logger.info(f"Fetching joint probability for {lat}, {lng}, distribution: {distribution_type}")
        
        # Distribution mapping
        distribution_map = {
            # New distributions (block group level)
            "gender_education": get_gender_education_distribution,
            "income_gender_new": get_income_gender_new_distribution,
            "income_profession": get_income_profession_distribution,
            "education_race": get_education_race_distribution,
            "profession_race": get_profession_race_distribution,
            # Existing distributions
            "age_income": get_age_income_distribution,
            "age_gender": get_age_gender_distribution,
            "age_race": get_age_race_distribution,
            "age_education": get_age_education_distribution,
            "education_sex": get_education_sex_distribution,
            "income_gender": get_income_gender_distribution,
            "profession_gender": get_profession_distribution
        }
        
        conditional_map = {
            # New distributions
            "gender_education": get_gender_education_conditional,
            "income_gender_new": get_income_gender_new_conditional,
            "income_profession": get_income_profession_conditional,
            "education_race": get_education_race_conditional,
            "profession_race": get_profession_race_conditional,
            # Existing distributions
            "age_income": get_age_income_conditional,
            "age_gender": get_age_gender_conditional,
            "age_race": get_age_race_conditional,
            "age_education": get_age_education_conditional,
            "education_sex": get_education_sex_conditional_distribution,
            "income_gender": get_income_gender_conditional,
            "profession_gender": get_profession_conditional
        }
        
        # Handle unavailable distributions
        unavailable_distributions = {"age_profession", "income_education", "income_race"}
        
        if distribution_type in unavailable_distributions:
            return jsonify({
                "error": "Data not available",
                "message": f"The {distribution_type} distribution is not available at block group level",
                "available_distributions": list(distribution_map.keys())
            }), 404
        
        if distribution_type not in distribution_map:
            return jsonify({
                "error": f"Unsupported distribution type: {distribution_type}",
                "available_distributions": list(distribution_map.keys())
            }), 400
        
        # Get joint distribution
        joint_data = distribution_map[distribution_type](lat, lng)
        
        if not joint_data:
            return jsonify({
                "error": "Could not fetch joint distribution data"
            }), 500
        
        response = {
            "coordinates": {"lat": lat, "lng": lng},
            "location": joint_data.get("location", {}),
            "distribution_type": distribution_type,
            "joint_distribution": joint_data
        }
        
        # Get conditional distribution if requested
        if condition_type and condition_value:
            conditional_result = conditional_map[distribution_type](joint_data, condition_type, condition_value)
            response["conditional_distribution"] = conditional_result
        
        logger.info(f"Successfully fetched joint probability for {distribution_type}")
        return jsonify(response)
        
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        return jsonify({
            "error": "Invalid input provided"
        }), 400
        
    except Exception as e:
        logger.error(f"Error fetching joint probability: {e}")
        return jsonify({
            "error": "Failed to fetch joint probability data",
            "details": str(e)
        }), 500


import os
import io
import csv
from flask import current_app, jsonify, request, Response


@app.route('/export_csv', methods=['POST'])
def export_distributions_csv():
    """
    Export individual distributions to CSV format,
    save to disk, and return it as a file download.

    Expected JSON body: {"lat": float, "lng": float}
    Returns: CSV data with columns: GEOID, bucket, populationCount, type_of_data
    """
    try:
        data = request.get_json()
        if not data or 'lat' not in data or 'lng' not in data:
            return jsonify({"error": "Missing required fields: lat, lng"}), 400

        lat = float(data['lat'])
        lng = float(data['lng'])
        logger.info(f"Exporting CSV for coordinates: {lat}, {lng}")

        # ... fetch distributions as before ...
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            future_age = executor.submit(get_age_distribution, lat, lng)
            future_gender = executor.submit(get_gender_distribution, lat, lng)
            future_education = executor.submit(get_education_distribution, lat, lng)
            future_income = executor.submit(get_income_distribution, lat, lng)
            future_profession = executor.submit(get_profession_distribution, lat, lng)
            future_race_ethnicity = executor.submit(get_race_ethnicity_distribution, lat, lng)

            distributions = {
                'age': future_age.result(),
                'gender': future_gender.result(),
                'education': future_education.result(),
                'income': future_income.result(),
                'profession': future_profession.result(),
                'race_ethnicity': future_race_ethnicity.result()
            }

        csv_rows = []
        geoid = None

        for dist_type, dist_data in distributions.items():
            if not dist_data or 'data' not in dist_data:
                continue
            if geoid is None and 'location' in dist_data:
                geoid = get_geoid(lat, lng)
            for item in dist_data['data']:
                csv_rows.append({
                    'GEOID': geoid or 'Unknown',
                    'bucket': item['category'],
                    'populationCount': item['value'],
                    'type_of_data': dist_type
                })


        if not csv_rows:
            return jsonify({"error": "No distribution data available for this location"}), 404

        # --- NEW: save to disk ---
        export_folder = current_app.config.get('EXPORT_FOLDER', 'csv_exports')
        os.makedirs(export_folder, exist_ok=True)

        filename = f"distributions_{lat}_{lng}.csv"
        file_path = os.path.join(export_folder, filename)
        logger.info(f"Writing CSV to {file_path}")

        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['GEOID', 'bucket', 'populationCount', 'type_of_data'])
            writer.writeheader()
            writer.writerows(csv_rows)
        logger.info(f"Saved CSV to {file_path}")
        # --- END NEW ---

        # Convert to CSV string for response
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=['GEOID', 'bucket', 'populationCount', 'type_of_data'])
        writer.writeheader()
        writer.writerows(csv_rows)
        csv_content = output.getvalue()
        output.close()

        return Response(
            csv_content,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename={filename}'
            }
        )

    except ValueError as e:
        logger.error(f"Invalid coordinates: {e}")
        return jsonify({"error": "Invalid coordinates provided"}), 400

    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        return jsonify({
            "error": "Failed to export CSV data",
            "details": str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy", 
        "service": "census-distribution-api",
        "chatbot_available": chatbot is not None
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)