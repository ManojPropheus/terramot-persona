"""
Census Data Analysis Chatbot using Gemini 2.5 Pro
Provides RAG-like capabilities with tools to analyze distribution data
"""

import os
import sys
import json
import google.generativeai as genai
from dotenv import load_dotenv
import pandas as pd
from typing import Dict, List, Any, Optional

# Add parent directory to path to import distribution modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from distribution.age_distribution import get_distribution as get_age_distribution
from distribution.gender_distribution import get_distribution as get_gender_distribution
from distribution.education_distribution import get_distribution as get_education_distribution
from distribution.income_distribution import get_distribution as get_income_distribution
from distribution.age_income_distribution import get_distribution as get_age_income_distribution
from distribution.age_income_distribution import get_conditional_distribution as get_age_income_conditional
from distribution.profession_distribution import get_distribution as get_profession_distribution
from distribution.profession_distribution import get_conditional_distribution as get_profession_conditional

# Load environment variables
load_dotenv()

class DistributionAnalyzer:
    """Tools for analyzing census distribution data"""
    
    def __init__(self):
        self.current_location = None
        self.current_distributions = None
        self.location_history = []
        self.user_preferences = {
            "preferred_distributions": [],
            "frequent_conditions": []
        }
        
    def fetch_all_distributions(self, lat: float, lng: float) -> Dict[str, Any]:
        """Fetch all distribution types for a location"""
        try:
            self.current_location = {"lat": lat, "lng": lng}
            
            # Add to location history
            location_key = f"{lat:.4f},{lng:.4f}"
            if location_key not in [loc.get("key") for loc in self.location_history]:
                self.location_history.append({
                    "key": location_key,
                    "lat": lat,
                    "lng": lng,
                    "timestamp": pd.Timestamp.now().isoformat()
                })
                # Keep only last 10 locations
                if len(self.location_history) > 10:
                    self.location_history = self.location_history[-10:]
            
            # Fetch all distributions
            age_dist = get_age_distribution(lat, lng)
            gender_dist = get_gender_distribution(lat, lng)
            education_dist = get_education_distribution(lat, lng)
            income_dist = get_income_distribution(lat, lng)
            age_income_dist = get_age_income_distribution(lat, lng)
            profession_dist = get_profession_distribution(lat, lng)
            
            self.current_distributions = {
                "age": age_dist,
                "gender": gender_dist,
                "education": education_dist,
                "income": income_dist,
                "age_income": age_income_dist,
                "profession": profession_dist,
                "location": age_dist.get("location", {}),
                "coordinates": {"lat": lat, "lng": lng}
            }
            
            return self.current_distributions
            
        except Exception as e:
            return {"error": f"Failed to fetch distributions: {str(e)}"}
    
    def analyze_distribution(self, distribution_type: str) -> Dict[str, Any]:
        """Analyze a specific distribution type"""
        if not self.current_distributions:
            return {"error": "No distribution data available. Please fetch distributions first."}
        
        if distribution_type not in self.current_distributions:
            return {"error": f"Distribution type '{distribution_type}' not found."}
        
        dist_data = self.current_distributions[distribution_type]
        
        if distribution_type == "age_income":
            # Special handling for age-income joint distribution
            total_households = sum(item['households'] for item in dist_data['joint_data'])
            age_categories = len(dist_data['age_marginal'])
            income_categories = len(dist_data['income_marginal'])
            
            # Find most common age-income combination
            max_combo = max(dist_data['joint_data'], key=lambda x: x['households'])
            
            return {
                "type": "joint_distribution_analysis",
                "total_households": total_households,
                "age_categories": age_categories,
                "income_categories": income_categories,
                "most_common_combination": {
                    "age_range": max_combo['age_range'],
                    "income_range": max_combo['income_range'],
                    "households": max_combo['households'],
                    "percentage": max_combo['percentage']
                },
                "data_source": dist_data['data_source']
            }
        elif distribution_type == "profession":
            # Special handling for profession-gender joint distribution
            total_population = sum(item['population'] for item in dist_data['joint_data'])
            profession_categories = len(dist_data['profession_marginal'])
            gender_categories = len(dist_data['gender_marginal'])
            
            # Find most common profession-gender combination
            max_combo = max(dist_data['joint_data'], key=lambda x: x['population'])
            
            return {
                "type": "joint_distribution_analysis",
                "total_population": total_population,
                "profession_categories": profession_categories,
                "gender_categories": gender_categories,
                "most_common_combination": {
                    "profession": max_combo['profession'],
                    "gender": max_combo['gender'],
                    "population": max_combo['population'],
                    "percentage": max_combo['percentage']
                },
                "data_source": dist_data['data_source']
            }
        else:
            # Regular distribution analysis
            data = dist_data['data']
            total = sum(item['value'] for item in data)
            
            # Find top categories
            top_categories = sorted(data, key=lambda x: x['value'], reverse=True)[:3]
            
            return {
                "type": f"{distribution_type}_analysis",
                "total_count": total,
                "categories_count": len(data),
                "top_categories": top_categories,
                "data_source": dist_data['data_source']
            }
    
    def get_conditional_analysis(self, condition_type: str, condition_value: str) -> Dict[str, Any]:
        """Get conditional distribution analysis (age-income only, kept for compatibility)"""
        if not self.current_distributions or not self.current_location:
            return {"error": "No distribution data or location available."}
        
        try:
            joint_data = self.current_distributions['age_income']
            conditional_data = get_age_income_conditional(joint_data, condition_type, condition_value)
            
            if 'error' in conditional_data:
                return conditional_data
            
            # Track user preferences
            if condition_type not in self.user_preferences["frequent_conditions"]:
                self.user_preferences["frequent_conditions"].append(condition_type)
            
            # Analyze the conditional distribution
            data = conditional_data['data']
            total = sum(item['value'] for item in data)
            top_categories = sorted(data, key=lambda x: x['value'], reverse=True)[:3]
            
            return {
                "type": "conditional_analysis",
                "condition": conditional_data['condition'],
                "total_households": conditional_data['total_households'],
                "categories_analyzed": len(data),
                "top_categories": top_categories,
                "distribution_type": conditional_data['type']
            }
            
        except Exception as e:
            return {"error": f"Failed to get conditional analysis: {str(e)}"}
    
    def get_unified_conditional_analysis(self, base_distribution: str, condition_type: str, condition_value: str) -> Dict[str, Any]:
        """Get conditional analysis from any joint distribution"""
        if not self.current_distributions or not self.current_location:
            return {"error": "No distribution data or location available."}
        
        try:
            # Track user preferences
            if condition_type not in self.user_preferences["frequent_conditions"]:
                self.user_preferences["frequent_conditions"].append(condition_type)
            
            if base_distribution == 'age_income':
                joint_data = self.current_distributions['age_income']
                conditional_data = get_age_income_conditional(joint_data, condition_type, condition_value)
            elif base_distribution == 'profession':
                joint_data = self.current_distributions['profession']
                conditional_data = get_profession_conditional(joint_data, condition_type, condition_value)
            else:
                return {"error": f"Unsupported base distribution: {base_distribution}"}
            
            if 'error' in conditional_data:
                return conditional_data
            
            # Analyze the conditional distribution
            data = conditional_data['data']
            total = sum(item['value'] for item in data)
            top_categories = sorted(data, key=lambda x: x['value'], reverse=True)[:3]
            
            return {
                "type": "unified_conditional_analysis",
                "base_distribution": base_distribution,
                "condition": conditional_data['condition'],
                "total_count": conditional_data.get('total_households') or conditional_data.get('total_population'),
                "categories_analyzed": len(data),
                "top_categories": top_categories,
                "distribution_type": conditional_data['type']
            }
            
        except Exception as e:
            return {"error": f"Failed to get unified conditional analysis: {str(e)}"}
    
    def compare_distributions(self, dist_type1: str, dist_type2: str) -> Dict[str, Any]:
        """Compare two distribution types"""
        if not self.current_distributions:
            return {"error": "No distribution data available."}
        
        if dist_type1 not in self.current_distributions or dist_type2 not in self.current_distributions:
            return {"error": "One or both distribution types not found."}
        
        # Skip age_income for comparison as it has different structure
        if dist_type1 == "age_income" or dist_type2 == "age_income":
            return {"error": "Cannot compare joint distribution with individual distributions."}
        
        dist1_data = self.current_distributions[dist_type1]['data']
        dist2_data = self.current_distributions[dist_type2]['data']
        
        return {
            "type": "distribution_comparison",
            "distribution_1": {
                "type": dist_type1,
                "categories": len(dist1_data),
                "total": sum(item['value'] for item in dist1_data),
                "top_category": max(dist1_data, key=lambda x: x['value'])
            },
            "distribution_2": {
                "type": dist_type2,
                "categories": len(dist2_data),
                "total": sum(item['value'] for item in dist2_data),
                "top_category": max(dist2_data, key=lambda x: x['value'])
            }
        }
    
    def get_location_summary(self) -> Dict[str, Any]:
        """Get summary of current location and data"""
        if not self.current_distributions:
            return {"error": "No distribution data available."}
        
        location = self.current_distributions['location']
        location_name = location.get('subdivision_name') or location.get('county_name')
        
        # Calculate totals for each distribution type
        totals = {}
        for dist_type in ['age', 'gender', 'education', 'income']:
            if dist_type in self.current_distributions:
                totals[dist_type] = sum(item['value'] for item in self.current_distributions[dist_type]['data'])
        
        # Special handling for age_income
        if 'age_income' in self.current_distributions:
            totals['age_income_households'] = sum(item['households'] for item in self.current_distributions['age_income']['joint_data'])
        
        return {
            "type": "location_summary",
            "location_name": location_name,
            "state": location.get('state_name'),
            "coordinates": self.current_distributions['coordinates'],
            "totals": totals,
            "available_distributions": list(self.current_distributions.keys())
        }
    
    def get_user_context(self) -> Dict[str, Any]:
        """Get user context including preferences and history"""
        return {
            "location_history": self.location_history,
            "user_preferences": self.user_preferences,
            "current_location": self.current_location,
            "has_current_data": self.current_distributions is not None
        }
    
    def update_user_preferences(self, distribution_type: str) -> None:
        """Update user preferences based on usage"""
        if distribution_type not in self.user_preferences["preferred_distributions"]:
            self.user_preferences["preferred_distributions"].append(distribution_type)
        # Keep only top 5 preferred distributions
        if len(self.user_preferences["preferred_distributions"]) > 5:
            self.user_preferences["preferred_distributions"] = self.user_preferences["preferred_distributions"][-5:]


class CensusDataChatbot:
    """Main chatbot class using Gemini 2.5 Pro with tool calling capabilities"""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        
        # Define the tools that the AI agent can use
        self.tools = [
            genai.protos.Tool(
                function_declarations=[
                    genai.protos.FunctionDeclaration(
                        name="fetch_all_distributions",
                        description="Fetch all census distribution data for a specific location using coordinates",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "lat": genai.protos.Schema(type=genai.protos.Type.NUMBER, description="Latitude coordinate"),
                                "lng": genai.protos.Schema(type=genai.protos.Type.NUMBER, description="Longitude coordinate")
                            },
                            required=["lat", "lng"]
                        )
                    ),
                    genai.protos.FunctionDeclaration(
                        name="analyze_distribution",
                        description="Analyze a specific distribution type (age, gender, education, income, age_income, or profession)",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "distribution_type": genai.protos.Schema(
                                    type=genai.protos.Type.STRING, 
                                    description="Type of distribution to analyze",
                                    enum=["age", "gender", "education", "income", "age_income", "profession"]
                                )
                            },
                            required=["distribution_type"]
                        )
                    ),
                    genai.protos.FunctionDeclaration(
                        name="get_conditional_analysis",
                        description="Get conditional distribution analysis from joint age-income data. Use this to find income distribution for specific age groups or age distribution for specific income brackets.",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "condition_type": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="What to condition on",
                                    enum=["age", "income"]
                                ),
                                "condition_value": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="The specific age range or income range. For age use exactly: 'Under 25 years', '25 to 44 years', '45 to 64 years', '65 years and over'. For income use ranges like '$25,000 to $34,999', '$50,000 to $74,999', etc."
                                )
                            },
                            required=["condition_type", "condition_value"]
                        )
                    ),
                    genai.protos.FunctionDeclaration(
                        name="compare_distributions",
                        description="Compare two different distribution types",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "dist_type1": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="First distribution type to compare",
                                    enum=["age", "gender", "education", "income"]
                                ),
                                "dist_type2": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="Second distribution type to compare",
                                    enum=["age", "gender", "education", "income"]
                                )
                            },
                            required=["dist_type1", "dist_type2"]
                        )
                    ),
                    genai.protos.FunctionDeclaration(
                        name="get_location_summary",
                        description="Get a comprehensive summary of the current location and available demographic data",
                        parameters=genai.protos.Schema(type=genai.protos.Type.OBJECT, properties={})
                    ),
                    genai.protos.FunctionDeclaration(
                        name="get_unified_conditional_analysis",
                        description="Get conditional analysis from any joint distribution (age_income or profession). More flexible than get_conditional_analysis.",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "base_distribution": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="Base distribution type",
                                    enum=["age_income", "profession"]
                                ),
                                "condition_type": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="What to condition on. For age_income: 'age' or 'income'. For profession: 'profession' or 'gender'"
                                ),
                                "condition_value": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="The specific value to condition on"
                                )
                            },
                            required=["base_distribution", "condition_type", "condition_value"]
                        )
                    ),
                    genai.protos.FunctionDeclaration(
                        name="get_user_context",
                        description="Get user context including location history, preferences, and current session state",
                        parameters=genai.protos.Schema(type=genai.protos.Type.OBJECT, properties={})
                    )
                ]
            )
        ]
        
        # Initialize model with tools
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp', tools=self.tools)
        self.analyzer = DistributionAnalyzer()
        self.conversation_history = []
        
        # System prompt
        self.system_prompt = """You are an expert Census data analyst and demographic researcher with advanced AI capabilities. You have access to comprehensive U.S. Census distribution data, analysis tools, and user context memory.

CORE CAPABILITIES:
- Fetch and analyze distribution data for any US location (age, gender, education, income, profession)
- Perform joint distribution analysis (age-income, profession-gender) with conditional analysis
- Compare different demographic aspects across distributions
- Maintain conversation memory and user preferences
- Provide location summaries and historical context

AVAILABLE TOOLS:
- fetch_all_distributions: Get comprehensive data for any location
- analyze_distribution: Analyze specific distribution types (age, gender, education, income, age_income, profession)
- get_unified_conditional_analysis: Flexible conditional analysis for any joint distribution
- get_conditional_analysis: Legacy age-income conditional analysis
- compare_distributions: Compare two distribution types
- get_location_summary: Comprehensive location demographics
- get_user_context: Access user history, preferences, and session state

MEMORY & PERSONALIZATION:
- Remember user's preferred distributions and frequent analysis types
- Track location history and provide comparative insights
- Adapt responses based on user patterns and preferences
- Use context from previous interactions to provide more relevant insights

RESPONSE STYLE:
- Be conversational yet professionally informative
- Use tools strategically - don't over-fetch data
- Provide specific, data-driven insights with clear numbers
- Reference user's previous locations or analyses when relevant
- Keep responses focused and actionable

Always use the most appropriate tools for the user's question and leverage memory to provide personalized, contextual responses."""
    
    def _execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool function"""
        try:
            if tool_name == "fetch_all_distributions":
                return self.analyzer.fetch_all_distributions(kwargs['lat'], kwargs['lng'])
            elif tool_name == "analyze_distribution":
                # Update user preferences
                self.analyzer.update_user_preferences(kwargs['distribution_type'])
                return self.analyzer.analyze_distribution(kwargs['distribution_type'])
            elif tool_name == "get_conditional_analysis":
                return self.analyzer.get_conditional_analysis(kwargs['condition_type'], kwargs['condition_value'])
            elif tool_name == "get_unified_conditional_analysis":
                return self.analyzer.get_unified_conditional_analysis(
                    kwargs['base_distribution'], kwargs['condition_type'], kwargs['condition_value']
                )
            elif tool_name == "compare_distributions":
                return self.analyzer.compare_distributions(kwargs['dist_type1'], kwargs['dist_type2'])
            elif tool_name == "get_location_summary":
                return self.analyzer.get_location_summary()
            elif tool_name == "get_user_context":
                return self.analyzer.get_user_context()
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}
    
    def chat(self, user_message: str, lat: Optional[float] = None, lng: Optional[float] = None) -> Dict[str, Any]:
        """Process user message and return response using AI agent with tools"""
        try:
            # Build enhanced context with user memory and location
            context_parts = [self.system_prompt]
            
            # Add user context for personalization
            user_context = self.analyzer.get_user_context()
            if user_context['user_preferences']['preferred_distributions']:
                context_parts.append(f"User's preferred distributions: {', '.join(user_context['user_preferences']['preferred_distributions'])}")
            
            if user_context['location_history']:
                recent_locations = user_context['location_history'][-3:]  # Last 3 locations
                context_parts.append(f"Recent locations analyzed: {len(recent_locations)} locations")
            
            # Add conversation history context (last 2 exchanges)
            if self.conversation_history:
                recent_history = self.conversation_history[-2:]
                history_text = "Recent conversation context:\n"
                for exchange in recent_history:
                    history_text += f"User: {exchange['user'][:100]}...\n"
                    history_text += f"Assistant: {exchange['assistant'][:100]}...\n"
                context_parts.append(history_text)
            
            if lat is not None and lng is not None:
                # Ensure data is loaded for the location
                if not self.analyzer.current_location or (
                    self.analyzer.current_location.get('lat') != lat or 
                    self.analyzer.current_location.get('lng') != lng
                ):
                    self.analyzer.fetch_all_distributions(lat, lng)
                
                context_parts.append(f"Current location context: Latitude {lat}, Longitude {lng}")
                if self.analyzer.current_distributions:
                    location_info = self.analyzer.current_distributions.get('location', {})
                    location_name = location_info.get('subdivision_name') or location_info.get('county_name')
                    if location_name:
                        context_parts.append(f"Location: {location_name}, {location_info.get('state_name', '')}")
                        # Check if this location was analyzed before
                        location_key = f"{lat:.4f},{lng:.4f}"
                        if any(loc['key'] == location_key for loc in user_context['location_history']):
                            context_parts.append("Note: This location has been analyzed before in this session.")
            
            context_parts.append(f"Current user question: {user_message}")
            full_prompt = "\n\n".join(context_parts)
            
            # Start chat session with tools
            chat = self.model.start_chat()
            response = chat.send_message(full_prompt)
            
            # Process tool calls if any
            response_text = ""
            while True:
                # Check if model wants to use tools
                function_calls = []
                if response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            function_calls.append(part.function_call)
                        elif hasattr(part, 'text') and part.text:
                            response_text += part.text
                
                # If no function calls, we're done
                if not function_calls:
                    if not response_text:
                        response_text = response.text
                    break
                
                # Execute all function calls
                function_responses = []
                for function_call in function_calls:
                    function_name = function_call.name
                    function_args = {k: v for k, v in function_call.args.items()}
                    
                    tool_result = self._execute_tool(function_name, **function_args)
                    
                    function_responses.append(
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=function_name,
                                response={"result": tool_result}
                            )
                        )
                    )
                
                # Send all function responses back to model
                response = chat.send_message(function_responses)
            
            # Store conversation
            self.conversation_history.append({
                "user": user_message,
                "assistant": response_text,
                "location": self.analyzer.current_location
            })
            
            return {
                "response": response_text,
                "error": False,
                "has_data": self.analyzer.current_distributions is not None,
                "location": self.analyzer.current_location
            }
            
        except Exception as e:
            return {
                "response": f"I'm sorry, I encountered an error while processing your request: {str(e)}",
                "error": True
            }
    
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history"""
        return self.conversation_history
    
    def clear_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []


# Initialize chatbot instance (will be used by Flask app)
def create_chatbot():
    """Create chatbot instance with API key from environment"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    return CensusDataChatbot(api_key)