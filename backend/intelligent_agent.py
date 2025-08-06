"""
Intelligent Agent System with Strategic Tool Selection and Advanced Reasoning
Uses modern AI agent patterns for sophisticated decision-making
"""

import google.generativeai as genai
from typing import Dict, List, Any, Optional, Tuple
import json
import re
from datetime import datetime

from agent_tools import ToolRegistry, BaseTool
from agent_memory import AdvancedMemory

class ToolSelector:
    """Intelligent tool selection system"""
    
    def __init__(self, tool_registry: ToolRegistry):
        self.tool_registry = tool_registry
        self.selection_history = []
    
    def analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """Analyze user query to understand intent and requirements"""
        query_lower = query.lower()
        
        intent_analysis = {
            'query_type': 'unknown',
            'required_data': [],
            'analysis_depth': 'basic',
            'comparison_requested': False,
            'conditional_analysis': False,
            'geographic_focus': False,
            'specific_demographics': []
        }
        
        # Determine query type
        if any(word in query_lower for word in ['compare', 'versus', 'vs', 'difference']):
            intent_analysis['query_type'] = 'comparison'
            intent_analysis['comparison_requested'] = True
        elif any(word in query_lower for word in ['for age', 'for income', 'given', 'specific']):
            intent_analysis['query_type'] = 'conditional'
            intent_analysis['conditional_analysis'] = True
        elif any(word in query_lower for word in ['analyze', 'breakdown', 'distribution']):
            intent_analysis['query_type'] = 'analysis'
        elif any(word in query_lower for word in ['what', 'show', 'tell me']):
            intent_analysis['query_type'] = 'information'
        
        # Determine analysis depth
        if any(word in query_lower for word in ['detailed', 'comprehensive', 'thorough', 'deep']):
            intent_analysis['analysis_depth'] = 'detailed'
        elif any(word in query_lower for word in ['expert', 'advanced', 'sophisticated']):
            intent_analysis['analysis_depth'] = 'expert'
        
        # Identify required data types
        data_keywords = {
            'age': ['age', 'elderly', 'young', 'senior', 'generational'],
            'income': ['income', 'salary', 'earnings', 'wealth', 'poverty'],
            'education': ['education', 'degree', 'college', 'school', 'qualification'],
            'gender': ['gender', 'male', 'female', 'sex'],
            'race': ['race', 'ethnicity', 'racial', 'ethnic', 'diversity'],
            'profession': ['job', 'occupation', 'career', 'profession', 'employment'],
            'housing': ['housing', 'rent', 'mortgage', 'tenant', 'owner', 'tenure'],
            'language': ['language', 'linguistic', 'english', 'bilingual'],
            'commuting': ['commute', 'transportation', 'travel', 'transit']
        }
        
        for data_type, keywords in data_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                intent_analysis['required_data'].append(data_type)
        
        # Geographic focus
        if any(word in query_lower for word in ['location', 'area', 'region', 'here', 'this place']):
            intent_analysis['geographic_focus'] = True
        
        return intent_analysis
    
    def select_tools(self, query: str, context: Dict[str, Any], 
                    intent_analysis: Dict[str, Any]) -> List[Tuple[BaseTool, float, str]]:
        """Select appropriate tools based on query analysis"""
        selected_tools = []
        
        # Get base tool recommendations
        relevant_tools = self.tool_registry.get_relevant_tools(query, context, top_k=5)
        
        # Refine selection based on intent analysis
        query_type = intent_analysis['query_type']
        required_data = intent_analysis['required_data']
        
        if query_type == 'comparison':
            # For comparisons, we might need multiple distribution tools
            if len(required_data) >= 2:
                for data_type in required_data[:2]:  # Compare top 2 data types
                    tool_name = f"{data_type}_distribution"
                    tool = self.tool_registry.get_tool(tool_name)
                    if tool:
                        selected_tools.append((tool, 0.9, f"Needed for {data_type} comparison"))
            elif len(required_data) == 1:
                # Compare with location history or suggest joint distributions
                data_type = required_data[0]
                if data_type in ['age', 'income']:
                    tool = self.tool_registry.get_tool('age_income_joint')
                    if tool:
                        selected_tools.append((tool, 0.8, "Joint age-income analysis for comparison"))
                elif data_type in ['profession', 'gender']:
                    tool = self.tool_registry.get_tool('profession_gender_joint')
                    if tool:
                        selected_tools.append((tool, 0.8, "Joint profession-gender analysis"))
        
        elif query_type == 'conditional':
            # For conditional analysis, prioritize joint distributions and conditional tool
            conditional_tool = self.tool_registry.get_tool('conditional_analysis')
            if conditional_tool:
                selected_tools.append((conditional_tool, 0.95, "Primary tool for conditional analysis"))
            
            # Add relevant joint distribution tools
            if 'age' in required_data and 'income' in required_data:
                tool = self.tool_registry.get_tool('age_income_joint')
                if tool:
                    selected_tools.append((tool, 0.8, "Base data for age-income conditional analysis"))
            elif 'profession' in required_data or 'gender' in required_data:
                tool = self.tool_registry.get_tool('profession_gender_joint')
                if tool:
                    selected_tools.append((tool, 0.8, "Base data for profession-gender conditional analysis"))
        
        elif query_type == 'analysis' or query_type == 'information':
            # For analysis, select based on specific data requirements
            for data_type in required_data:
                # Choose between individual and joint distributions
                if data_type == 'age' and 'income' in required_data:
                    tool = self.tool_registry.get_tool('age_income_joint')
                    if tool:
                        selected_tools.append((tool, 0.85, f"Joint {data_type}-income analysis"))
                elif data_type == 'age' and 'housing' in required_data:
                    tool = self.tool_registry.get_tool('age_tenure_joint')
                    if tool:
                        selected_tools.append((tool, 0.85, f"Joint age-tenure analysis"))
                elif data_type == 'profession' and 'gender' in required_data:
                    tool = self.tool_registry.get_tool('profession_gender_joint')
                    if tool:
                        selected_tools.append((tool, 0.85, f"Joint profession-gender analysis"))
                elif data_type == 'housing':
                    # For housing, prefer financial characteristics over basic tenure
                    tool = self.tool_registry.get_tool('financial_characteristics')
                    if tool:
                        selected_tools.append((tool, 0.9, "Comprehensive housing financial data"))
                    tool = self.tool_registry.get_tool('income_tenure_joint')
                    if tool:
                        selected_tools.append((tool, 0.8, "Housing costs and tenure analysis"))
                elif data_type == 'language':
                    tool = self.tool_registry.get_tool('language')
                    if tool:
                        selected_tools.append((tool, 0.9, "Language spoken at home analysis"))
                elif data_type == 'commuting':
                    tool = self.tool_registry.get_tool('commuting')
                    if tool:
                        selected_tools.append((tool, 0.9, "Commuting patterns analysis"))
                elif data_type == 'race':
                    tool = self.tool_registry.get_tool('race_ethnicity')
                    if tool:
                        selected_tools.append((tool, 0.9, "Race and ethnicity analysis"))
                else:
                    tool_name = f"{data_type}_distribution"
                    tool = self.tool_registry.get_tool(tool_name)
                    if tool:
                        selected_tools.append((tool, 0.7, f"Basic {data_type} distribution"))
        
        # If no specific tools selected, fall back to most relevant tools
        if not selected_tools:
            for tool in relevant_tools[:2]:  # Take top 2 relevant tools
                selected_tools.append((tool, 0.6, "Fallback relevant tool"))
        
        # Remove duplicates and sort by confidence
        seen_tools = set()
        unique_tools = []
        for tool, confidence, reason in selected_tools:
            if tool.name not in seen_tools:
                seen_tools.add(tool.name)
                unique_tools.append((tool, confidence, reason))
        
        # Sort by confidence score
        unique_tools.sort(key=lambda x: x[1], reverse=True)
        
        # Record selection for learning
        self.selection_history.append({
            'query': query,
            'intent': intent_analysis,
            'selected_tools': [(t.name, c, r) for t, c, r in unique_tools],
            'timestamp': datetime.now().isoformat()
        })
        
        return unique_tools[:3]  # Return top 3 tools

class IntelligentAgent:
    """Main intelligent agent with advanced reasoning capabilities"""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        
        # Initialize components
        self.tool_registry = ToolRegistry()
        self.tool_selector = ToolSelector(self.tool_registry)
        self.memory = AdvancedMemory()
        
        # AI model for reasoning
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Agent state
        self.current_location = None
        self.current_session_context = {}
        self.reasoning_history = []
    
    def process_query(self, user_query: str, lat: Optional[float] = None, 
                     lng: Optional[float] = None) -> Dict[str, Any]:
        """Process user query with intelligent reasoning and tool selection"""
        
        try:
            # Step 1: Analyze query intent
            intent_analysis = self.tool_selector.analyze_query_intent(user_query)
            
            # Step 2: Get relevant context from memory
            location_dict = {'lat': lat, 'lng': lng} if lat and lng else None
            memory_context = self.memory.get_relevant_context(user_query, location_dict)
            
            # Step 3: Select appropriate tools
            selected_tools = self.tool_selector.select_tools(user_query, memory_context, intent_analysis)
            
            # Step 4: Plan execution strategy
            execution_plan = self._create_execution_plan(user_query, selected_tools, intent_analysis)
            
            # Step 5: Execute tools strategically
            tool_results = self._execute_tools_strategically(execution_plan, lat, lng)
            
            # Step 6: Synthesize response using AI reasoning
            response = self._generate_intelligent_response(
                user_query, intent_analysis, tool_results, memory_context
            )
            
            # Step 7: Update memory with new learnings
            self._update_memory(user_query, response, tool_results, lat, lng)
            
            return {
                'response': response,
                'reasoning': {
                    'intent_analysis': intent_analysis,
                    'tools_selected': [(t.name, c, r) for t, c, r in selected_tools],
                    'execution_plan': execution_plan,
                    'memory_used': len(memory_context.get('recent_conversations', [])) > 0
                },
                'error': False,
                'location': {'lat': lat, 'lng': lng} if lat and lng else None
            }
        
        except Exception as e:
            # Return error response with proper structure
            return {
                'response': f"I encountered an error while processing your request: {str(e)}",
                'reasoning': {
                    'intent_analysis': {'query_type': 'error'},
                    'tools_selected': [],
                    'execution_plan': {},
                    'memory_used': False
                },
                'error': True,
                'location': {'lat': lat, 'lng': lng} if lat and lng else None,
                'error_details': str(e)
            }
    
    def _create_execution_plan(self, query: str, selected_tools: List[Tuple[BaseTool, float, str]], 
                             intent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create strategic execution plan for selected tools"""
        plan = {
            'execution_order': [],
            'parallel_execution': [],
            'conditional_execution': [],
            'strategy': 'sequential'
        }
        
        # Determine execution strategy
        query_type = intent_analysis['query_type']
        
        if query_type == 'conditional':
            # For conditional analysis, execute base distribution first, then conditional analysis
            base_tools = [t for t, c, r in selected_tools if 'joint' in t.name]
            conditional_tools = [t for t, c, r in selected_tools if t.name == 'conditional_analysis']
            
            plan['execution_order'] = base_tools + conditional_tools
            plan['strategy'] = 'sequential'
        
        elif query_type == 'comparison':
            # For comparisons, can execute tools in parallel
            plan['parallel_execution'] = [t for t, c, r in selected_tools]
            plan['strategy'] = 'parallel'
        
        else:
            # For analysis/information queries, prioritize by confidence
            sorted_tools = sorted(selected_tools, key=lambda x: x[1], reverse=True)
            plan['execution_order'] = [t for t, c, r in sorted_tools]
            plan['strategy'] = 'priority_sequential'
        
        return plan
    
    def _execute_tools_strategically(self, execution_plan: Dict[str, Any], 
                                   lat: Optional[float], lng: Optional[float]) -> Dict[str, Any]:
        """Execute tools according to the strategic plan"""
        results = {}
        
        if not lat or not lng:
            return {'error': 'Location coordinates required for data analysis'}
        
        strategy = execution_plan['strategy']
        
        try:
            if strategy == 'parallel':
                # Execute tools in parallel for better performance
                import concurrent.futures
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                    future_to_tool = {}
                    for tool in execution_plan['parallel_execution']:
                        future = executor.submit(tool.execute, lat, lng)
                        future_to_tool[future] = tool
                    
                    for future in concurrent.futures.as_completed(future_to_tool):
                        tool = future_to_tool[future]
                        try:
                            result = future.result()
                            results[tool.name] = {
                                'data': result,
                                'success': True,
                                'tool_info': {
                                    'name': tool.name,
                                    'description': tool.description,
                                    'usage_count': tool.usage_count
                                }
                            }
                        except Exception as e:
                            results[tool.name] = {
                                'error': str(e),
                                'success': False,
                                'tool_info': {'name': tool.name, 'description': tool.description}
                            }
            
            elif strategy == 'sequential':
                # Execute tools sequentially, using results from previous tools
                for tool in execution_plan['execution_order']:
                    try:
                        # Check if this is conditional analysis and we have base data
                        if tool.name == 'conditional_analysis':
                            # Need to extract condition parameters from previous results or query
                            # This is a simplified version - in practice, you'd parse the query more carefully
                            base_distribution = 'age_income'  # Default
                            condition_type = 'age'  # Default
                            condition_value = 'Under 25 years'  # Default - should be parsed from query
                            
                            result = tool.execute(lat, lng, 
                                                base_distribution=base_distribution,
                                                condition_type=condition_type,
                                                condition_value=condition_value)
                        else:
                            result = tool.execute(lat, lng)
                        
                        results[tool.name] = {
                            'data': result,
                            'success': True,
                            'tool_info': {
                                'name': tool.name,
                                'description': tool.description,
                                'usage_count': tool.usage_count
                            }
                        }
                    except Exception as e:
                        results[tool.name] = {
                            'error': str(e),
                            'success': False,
                            'tool_info': {'name': tool.name, 'description': tool.description}
                        }
            
            else:  # priority_sequential
                # Execute tools in priority order, but stop if we get sufficient data
                for tool in execution_plan['execution_order']:
                    try:
                        result = tool.execute(lat, lng)
                        results[tool.name] = {
                            'data': result,
                            'success': True,
                            'tool_info': {
                                'name': tool.name,
                                'description': tool.description,
                                'usage_count': tool.usage_count
                            }
                        }
                        
                        # For information queries, one good result might be sufficient
                        if len(results) >= 1 and not any('error' in r.get('data', {}) for r in results.values()):
                            break
                            
                    except Exception as e:
                        results[tool.name] = {
                            'error': str(e),
                            'success': False,
                            'tool_info': {'name': tool.name, 'description': tool.description}
                        }
        
        except Exception as e:
            results['execution_error'] = {'error': f'Tool execution failed: {str(e)}', 'success': False}
        
        return results
    
    def _generate_intelligent_response(self, query: str, intent_analysis: Dict[str, Any], 
                                     tool_results: Dict[str, Any], 
                                     memory_context: Dict[str, Any]) -> str:
        """Generate intelligent response using AI reasoning over tool results"""
        
        # Prepare context for AI model
        context_parts = []
        
        # Add system context
        context_parts.append("""You are an expert Census data analyst with access to comprehensive demographic data and tools. 
You have just executed specific tools based on the user's query and now need to provide an intelligent, contextual response.

INSTRUCTIONS:
- Analyze the tool results and provide insights, not just raw data
- Use the memory context to personalize your response
- Be conversational yet professionally informative
- Focus on answering the user's specific question
- Highlight interesting patterns or insights in the data
- If multiple tools were used, synthesize the information coherently
- Use specific numbers and percentages from the data""")
        
        # Add query and intent analysis
        context_parts.append(f"User Query: {query}")
        context_parts.append(f"Query Intent Analysis: {json.dumps(intent_analysis, indent=2)}")
        
        # Add tool results
        context_parts.append("Tool Results:")
        for tool_name, result_data in tool_results.items():
            if result_data.get('success'):
                context_parts.append(f"\n{tool_name.upper()} RESULTS:")
                context_parts.append(json.dumps(result_data['data'], indent=2)[:2000])  # Limit size
            else:
                context_parts.append(f"\n{tool_name.upper()} ERROR: {result_data.get('error', 'Unknown error')}")
        
        # Add memory context for personalization
        if memory_context.get('user_patterns', {}).get('preferred_distributions'):
            context_parts.append(f"User's Previous Interests: {memory_context['user_patterns']['preferred_distributions']}")
        
        if memory_context.get('current_location'):
            context_parts.append(f"Location History: User has analyzed this location {memory_context['current_location']['visit_count']} times before")
        
        if memory_context.get('suggestions'):
            context_parts.append(f"Contextual Suggestions: {memory_context['suggestions']}")
        
        context_parts.append("\nGenerate a comprehensive, insightful response based on this data. Be specific with numbers and provide meaningful analysis.")
        
        full_context = "\n\n".join(context_parts)
        
        try:
            # Generate response using AI model
            response = self.model.generate_content(full_context)
            return response.text
        except Exception as e:
            # Fallback to basic response if AI generation fails
            return self._generate_fallback_response(tool_results, query)
    
    def _generate_fallback_response(self, tool_results: Dict[str, Any], query: str) -> str:
        """Generate fallback response if AI generation fails"""
        response_parts = []
        
        successful_results = {k: v for k, v in tool_results.items() if v.get('success')}
        
        if not successful_results:
            return "I apologize, but I encountered issues retrieving the data for your query. Please try again or rephrase your question."
        
        response_parts.append(f"Based on your query about {query.lower()}, here's what I found:")
        
        for tool_name, result_data in successful_results.items():
            data = result_data['data']
            if 'data' in data and isinstance(data['data'], list) and data['data']:
                top_item = data['data'][0]
                response_parts.append(f"\n• {tool_name.replace('_', ' ').title()}: {top_item.get('category', 'Top category')} with {top_item.get('value', 'N/A')} people")
        
        return "\n".join(response_parts)
    
    def _update_memory(self, query: str, response: str, tool_results: Dict[str, Any], 
                      lat: Optional[float], lng: Optional[float]):
        """Update memory with new information and learnings"""
        
        # Add conversation to memory
        tools_used = [name for name, result in tool_results.items() if result.get('success')]
        location_dict = {'lat': lat, 'lng': lng} if lat and lng else None
        
        self.memory.add_conversation_memory(
            user_message=query,
            assistant_response=response,
            location=location_dict,
            tools_used=tools_used
        )
        
        # Add location context if applicable
        if lat and lng:
            # Extract location info from tool results
            location_name = "Unknown Location"
            state = "Unknown State"
            
            for result_data in tool_results.values():
                if result_data.get('success') and 'location' in result_data.get('data', {}):
                    location_info = result_data['data']['location']
                    # Check if location_info is a dictionary (not a string)
                    if isinstance(location_info, dict):
                        location_name = location_info.get('subdivision_name') or location_info.get('county_name', location_name)
                        state = location_info.get('state_name', state)
                        break
                    elif isinstance(location_info, str):
                        # If it's a string, use it as location name
                        location_name = location_info
                        break
            
            self.memory.add_location_context(
                lat=lat, lng=lng,
                location_name=location_name,
                state=state,
                query=query,
                tools_used=tools_used
            )
        
        # Extract and store insights
        insights = self._extract_insights_from_response(response, tool_results)
        for insight in insights:
            self.memory.add_insight(
                insight=insight,
                related_data={'query': query, 'tools_used': tools_used, 'location': location_dict}
            )
    
    def _extract_insights_from_response(self, response: str, tool_results: Dict[str, Any]) -> List[str]:
        """Extract key insights from the generated response"""
        insights = []
        
        # Look for numerical insights in the response
        percentage_pattern = r'(\d+(?:\.\d+)?%)'
        number_pattern = r'(\d+(?:,\d+)*)'
        
        percentages = re.findall(percentage_pattern, response)
        numbers = re.findall(number_pattern, response)
        
        if percentages:
            insights.append(f"Key percentages mentioned: {', '.join(percentages[:3])}")
        
        # Look for comparative statements
        if any(word in response.lower() for word in ['higher', 'lower', 'more', 'less', 'compared']):
            insights.append("Comparative analysis performed")
        
        # Look for trend or pattern mentions
        if any(word in response.lower() for word in ['trend', 'pattern', 'increase', 'decrease']):
            insights.append("Demographic trends identified")
        
        return insights[:3]  # Limit to 3 insights
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status and analytics"""
        return {
            'memory_summary': self.memory.get_memory_summary(),
            'tool_usage_stats': self.tool_registry.get_tool_usage_stats(),
            'selection_history': len(self.tool_selector.selection_history),
            'reasoning_history': len(self.reasoning_history),
            'current_session': self.current_session_context
        }
    
    def clear_session(self):
        """Clear current session while preserving long-term memory"""
        self.current_session_context.clear()
        self.memory.clear_working_memory()
        self.reasoning_history.clear()