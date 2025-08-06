"""
Advanced Census Data Analysis AI Agent
Uses sophisticated tool selection, memory systems, and intelligent reasoning
Based on modern AI agent patterns with strategic decision-making capabilities
"""

import os
import pandas as pd
import sys
import json
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional

# Add parent directory to path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from distribution.age_distribution import get_distribution as get_age_distribution
from distribution.gender_distribution import get_distribution as get_gender_distribution
from distribution.education_distribution import get_distribution as get_education_distribution
from distribution.income_distribution import get_distribution as get_income_distribution
from distribution.profession_distribution import get_distribution as get_profession_distribution
from distribution.race_ethnicity_distribution import get_distribution as get_race_ethnicity_distribution
# Joint distributions
from distribution.age_income_distribution import get_distribution as get_age_income_distribution
from distribution.age_gender_distribution import get_distribution as get_age_gender_distribution
from distribution.age_race_distribution import get_distribution as get_age_race_distribution
from distribution.age_education_distribution import get_distribution as get_age_education_distribution
from distribution.income_gender_distribution import get_distribution as get_income_gender_distribution
# Conditional distributions
from agent_tools import get_age_income_conditional
from agent_tools import get_profession_conditional
from agent_tools import get_age_gender_conditional
from agent_tools import get_age_race_conditional
from agent_tools import get_age_education_conditional
from agent_tools import get_income_gender_conditional

from intelligent_agent import IntelligentAgent

# Load environment variables
load_dotenv()

class LegacyDistributionAnalyzer:
    """Legacy compatibility layer - maintained for backward compatibility"""
    
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
            
            # Fetch individual distributions for the 6 variables
            age_dist = get_age_distribution(lat, lng)
            gender_dist = get_gender_distribution(lat, lng)
            education_dist = get_education_distribution(lat, lng)
            income_dist = get_income_distribution(lat, lng)
            profession_dist = get_profession_distribution(lat, lng)
            race_ethnicity_dist = get_race_ethnicity_distribution(lat, lng)
            
            # Fetch joint distributions for the 6 variables
            age_income_dist = get_age_income_distribution(lat, lng)
            age_gender_dist = get_age_gender_distribution(lat, lng)
            age_race_dist = get_age_race_distribution(lat, lng)
            age_education_dist = get_age_education_distribution(lat, lng)
            income_gender_dist = get_income_gender_distribution(lat, lng)
            
            self.current_distributions = {
                # Individual distributions for the 6 variables
                "age": age_dist,
                "gender": gender_dist,
                "education": education_dist,
                "income": income_dist,
                "profession": profession_dist,
                "race_ethnicity": race_ethnicity_dist,
                
                # Joint distributions for the 6 variables
                "age_income": age_income_dist,
                "age_gender": age_gender_dist,
                "age_race": age_race_dist,
                "age_education": age_education_dist,
                "income_gender": income_gender_dist,
                "profession_gender": profession_dist,  # Profession distribution already includes gender breakdown
                
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
        elif distribution_type == "income_tenure":
            # Special handling for income-tenure joint distribution
            total_households = sum(item['households'] for item in dist_data['joint_data'])
            cost_categories = len(dist_data['cost_marginal'])
            tenure_categories = len(dist_data['tenure_marginal'])
            
            # Find most common cost-tenure combination
            max_combo = max(dist_data['joint_data'], key=lambda x: x['households'])
            
            return {
                "type": "joint_distribution_analysis",
                "total_households": total_households,
                "cost_categories": cost_categories,
                "tenure_categories": tenure_categories,
                "most_common_combination": {
                    "cost_burden": max_combo['cost_burden'],
                    "tenure": max_combo['tenure'],
                    "households": max_combo['households'],
                    "percentage": max_combo['percentage']
                },
                "data_source": dist_data['data_source']
            }
        elif distribution_type == "financial_characteristics":
            # Special handling for financial characteristics
            summary = dist_data['summary']
            return {
                "type": "financial_characteristics_analysis",
                "total_units": summary['total_units'],
                "owner_occupied": summary['owner_occupied'],
                "renter_occupied": summary['renter_occupied'],
                "median_owner_costs": summary['median_owner_costs'],
                "median_rent": summary['median_rent'],
                "median_income": summary['median_income'],
                "cost_burden_analysis": {
                    "owner_burdened": len([item for item in dist_data['cost_burden'] if item['category'] == 'Owner cost-burdened']),
                    "renter_burdened": len([item for item in dist_data['cost_burden'] if item['category'] == 'Renter cost-burdened'])
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
            elif base_distribution == 'income_tenure':
                joint_data = self.current_distributions['income_tenure']
                conditional_data = get_income_tenure_conditional(joint_data, condition_type, condition_value)
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
    """Advanced AI Agent for Census Data Analysis with intelligent tool selection and memory"""
    
    def __init__(self, api_key: str):
        # Initialize the intelligent agent
        self.agent = IntelligentAgent(api_key)
        
        # Legacy compatibility
        self.analyzer = LegacyDistributionAnalyzer()
        self.conversation_history = []
        
        # Migration flag for gradual transition
        self.use_intelligent_agent = True
    
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
        """Process user message using advanced intelligent agent system"""
        try:
            if self.use_intelligent_agent:
                # Use the new intelligent agent system
                result = self.agent.process_query(user_message, lat, lng)
                
                # Store conversation for legacy compatibility
                self.conversation_history.append({
                    "user": user_message,
                    "assistant": result['response'],
                    "location": result.get('location')
                })
                
                # Enhanced response with agent insights
                return {
                    "response": result['response'],
                    "error": result.get('error', False),
                    "has_data": lat is not None and lng is not None,
                    "location": result.get('location'),
                    "agent_insights": {
                        "tools_selected": result['reasoning']['tools_selected'],
                        "intent_detected": result['reasoning']['intent_analysis']['query_type'],
                        "analysis_depth": result['reasoning']['intent_analysis']['analysis_depth'],
                        "memory_utilized": result['reasoning']['memory_used']
                    }
                }
            else:
                # Fallback to legacy system if needed
                return self._legacy_chat(user_message, lat, lng)
                
        except Exception as e:
            return {
                "response": f"I encountered an error while processing your request: {str(e)}",
                "error": True,
                "details": "Please try rephrasing your question or check the location coordinates."
            }
    
    def _legacy_chat(self, user_message: str, lat: Optional[float] = None, lng: Optional[float] = None) -> Dict[str, Any]:
        """Legacy chat method for backward compatibility"""
        # This would contain the old implementation as a fallback
        return {
            "response": "Legacy mode: Please use the intelligent agent system for better results.",
            "error": False,
            "has_data": False,
            "location": None
        }
    
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history"""
        return self.conversation_history
    
    def clear_conversation(self):
        """Clear conversation history and agent session"""
        self.conversation_history = []
        if self.use_intelligent_agent:
            self.agent.clear_session()
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status and analytics"""
        if self.use_intelligent_agent:
            return self.agent.get_agent_status()
        else:
            return {
                "mode": "legacy",
                "conversation_history_length": len(self.conversation_history)
            }
    
    def toggle_agent_mode(self, use_intelligent: bool = True):
        """Toggle between intelligent agent and legacy mode"""
        self.use_intelligent_agent = use_intelligent
        return {
            "mode": "intelligent_agent" if use_intelligent else "legacy",
            "message": f"Switched to {'intelligent agent' if use_intelligent else 'legacy'} mode"
        }


# Initialize chatbot instance (will be used by Flask app)
def create_chatbot():
    """Create chatbot instance with API key from environment"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    return CensusDataChatbot(api_key)