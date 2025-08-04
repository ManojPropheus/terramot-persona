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
from distribution.age_income_distribution import get_distribution as get_age_income_distribution
from distribution.age_income_distribution import get_conditional_distribution as get_age_income_conditional
from distribution.profession_distribution import get_distribution as get_profession_distribution
from distribution.profession_distribution import get_conditional_distribution as get_profession_conditional
from distribution.age_distribution import get_geography
from chatbot_service import create_chatbot
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
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            future_age = executor.submit(get_age_distribution, lat, lng)
            future_gender = executor.submit(get_gender_distribution, lat, lng)
            future_education = executor.submit(get_education_distribution, lat, lng)
            future_income = executor.submit(get_income_distribution, lat, lng)
            future_age_income = executor.submit(get_age_income_distribution, lat, lng)
            future_profession = executor.submit(get_profession_distribution, lat, lng)
            
            # Wait for all to complete and get results
            age_result = future_age.result()
            gender_result = future_gender.result()
            education_result = future_education.result()
            income_result = future_income.result()
            age_income_result = future_age_income.result()
            profession_result = future_profession.result()
        
        # Combine all results
        response = {
            "coordinates": {"lat": lat, "lng": lng},
            "location": age_result["location"],  # All should have same location
            "distributions": {
                "age": age_result,
                "gender": gender_result,
                "education": education_result,
                "income": income_result,
                "age_income": age_income_result,
                "profession": profession_result
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
            
        elif base_distribution == 'profession':
            if condition_type not in ['profession', 'gender']:
                return jsonify({"error": "For profession base, condition_type must be 'profession' or 'gender'"}), 400
            
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

        logger.info(f"Fetching distributions for coordinates: {lat}, {lng}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            geography = executor.submit(get_geography, lat, lng)

        response = {
            "coordinates": {"lat": lat, "lng": lng},
            "location": geography.result()
        }

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