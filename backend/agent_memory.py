"""
Advanced Memory System for AI Agent
Implements sophisticated memory patterns for contextual awareness and personalization
"""

import json
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import hashlib
from collections import defaultdict, deque

@dataclass
class MemoryEntry:
    """Single memory entry with metadata"""
    id: str
    content: str
    memory_type: str  # 'conversation', 'location', 'preference', 'insight', 'tool_usage'
    timestamp: str
    importance: float  # 0.0 to 1.0
    tags: List[str]
    context: Dict[str, Any]
    access_count: int = 0
    last_accessed: Optional[str] = None

@dataclass
class LocationContext:
    """Context for a specific location"""
    lat: float
    lng: float
    location_name: str
    state: str
    first_visited: str
    last_visited: str
    visit_count: int
    queries_asked: List[str]
    insights_discovered: List[str]
    tools_used: List[str]

@dataclass
class UserPreferences:
    """User preferences and patterns"""
    preferred_distributions: List[str]
    frequent_conditions: List[str]
    interaction_patterns: Dict[str, int]
    preferred_analysis_depth: str  # 'basic', 'detailed', 'expert'
    geographic_interests: List[str]
    topic_interests: List[str]

class AdvancedMemory:
    """Advanced memory system with multiple memory types and intelligent retrieval"""
    
    def __init__(self, max_conversation_history: int = 50, max_location_history: int = 20):
        # Core memory stores
        self.conversation_memory = deque(maxlen=max_conversation_history)
        self.location_contexts = {}  # lat,lng -> LocationContext
        self.user_preferences = UserPreferences(
            preferred_distributions=[],
            frequent_conditions=[],
            interaction_patterns=defaultdict(int),
            preferred_analysis_depth='basic',
            geographic_interests=[],
            topic_interests=[]
        )
        
        # Long-term memory (persistent insights and patterns)
        self.semantic_memory = {}  # topic -> insights
        self.episodic_memory = []  # important events/discoveries
        self.working_memory = {}  # current session context
        
        # Memory management
        self.max_location_history = max_location_history
        self.importance_threshold = 0.3
        
        # Analytics
        self.memory_access_patterns = defaultdict(int)
        self.query_patterns = defaultdict(list)
    
    def _generate_id(self, content: str) -> str:
        """Generate unique ID for memory entry"""
        return hashlib.md5(f"{content}{datetime.now().isoformat()}".encode()).hexdigest()[:12]
    
    def _calculate_importance(self, content: str, memory_type: str, context: Dict[str, Any]) -> float:
        """Calculate importance score for memory entry"""
        base_importance = {
            'conversation': 0.3,
            'location': 0.6,
            'preference': 0.8,
            'insight': 0.9,
            'tool_usage': 0.4
        }.get(memory_type, 0.5)
        
        # Boost importance based on content characteristics
        content_lower = content.lower()
        
        # Important keywords boost
        important_keywords = ['compare', 'analyze', 'trend', 'insight', 'unusual', 'significant']
        for keyword in important_keywords:
            if keyword in content_lower:
                base_importance += 0.1
        
        # Location-specific boosts
        if 'error' in content_lower:
            base_importance -= 0.2
        if 'successful' in content_lower or 'found' in content_lower:
            base_importance += 0.1
            
        return min(base_importance, 1.0)
    
    def add_conversation_memory(self, user_message: str, assistant_response: str, 
                             location: Optional[Dict[str, float]] = None,
                             tools_used: Optional[List[str]] = None) -> str:
        """Add conversation exchange to memory"""
        conversation_data = {
            'user_message': user_message,
            'assistant_response': assistant_response,
            'location': location,
            'tools_used': tools_used or []
        }
        
        memory_id = self._generate_id(user_message)
        importance = self._calculate_importance(user_message, 'conversation', conversation_data)
        
        entry = MemoryEntry(
            id=memory_id,
            content=f"User: {user_message[:200]}... | Assistant: {assistant_response[:200]}...",
            memory_type='conversation',
            timestamp=datetime.now().isoformat(),
            importance=importance,
            tags=self._extract_tags(user_message),
            context=conversation_data
        )
        
        self.conversation_memory.append(entry)
        
        # Update user preferences based on conversation
        self._update_preferences_from_conversation(user_message, tools_used or [])
        
        return memory_id
    
    def add_location_context(self, lat: float, lng: float, location_name: str, 
                           state: str, query: str, tools_used: List[str],
                           insights: Optional[List[str]] = None) -> str:
        """Add or update location context"""
        location_key = f"{lat:.4f},{lng:.4f}"
        
        if location_key in self.location_contexts:
            # Update existing location
            context = self.location_contexts[location_key]
            context.last_visited = datetime.now().isoformat()
            context.visit_count += 1
            context.queries_asked.append(query)
            context.tools_used.extend(tools_used)
            if insights:
                context.insights_discovered.extend(insights)
        else:
            # Create new location context
            context = LocationContext(
                lat=lat,
                lng=lng,
                location_name=location_name,
                state=state,
                first_visited=datetime.now().isoformat(),
                last_visited=datetime.now().isoformat(),
                visit_count=1,
                queries_asked=[query],
                insights_discovered=insights or [],
                tools_used=tools_used
            )
            self.location_contexts[location_key] = context
            
            # Maintain max location limit
            if len(self.location_contexts) > self.max_location_history:
                # Remove oldest location
                oldest_key = min(self.location_contexts.keys(), 
                               key=lambda k: self.location_contexts[k].last_visited)
                del self.location_contexts[oldest_key]
        
        # Add geographic interest
        if state not in self.user_preferences.geographic_interests:
            self.user_preferences.geographic_interests.append(state)
        
        return location_key
    
    def add_insight(self, insight: str, related_data: Dict[str, Any], 
                   importance: Optional[float] = None) -> str:
        """Add analytical insight to long-term memory"""
        memory_id = self._generate_id(insight)
        
        if importance is None:
            importance = self._calculate_importance(insight, 'insight', related_data)
        
        entry = MemoryEntry(
            id=memory_id,
            content=insight,
            memory_type='insight',
            timestamp=datetime.now().isoformat(),
            importance=importance,
            tags=self._extract_tags(insight),
            context=related_data
        )
        
        self.episodic_memory.append(entry)
        
        # Add to semantic memory
        for tag in entry.tags:
            if tag not in self.semantic_memory:
                self.semantic_memory[tag] = []
            self.semantic_memory[tag].append(insight)
        
        return memory_id
    
    def _extract_tags(self, text: str) -> List[str]:
        """Extract relevant tags from text"""
        text_lower = text.lower()
        tags = []
        
        # Distribution types
        distribution_tags = ['age', 'income', 'education', 'gender', 'race', 'ethnicity', 
                           'profession', 'tenure', 'financial', 'language', 'commuting']
        for tag in distribution_tags:
            if tag in text_lower:
                tags.append(tag)
        
        # Analysis types
        analysis_tags = ['compare', 'analyze', 'conditional', 'trend', 'pattern', 'distribution']
        for tag in analysis_tags:
            if tag in text_lower:
                tags.append(tag)
        
        # Geographic terms
        geo_tags = ['location', 'area', 'region', 'state', 'county', 'city']
        for tag in geo_tags:
            if tag in text_lower:
                tags.append(tag)
        
        return list(set(tags))  # Remove duplicates
    
    def _update_preferences_from_conversation(self, user_message: str, tools_used: List[str]):
        """Update user preferences based on conversation patterns"""
        # Track tool usage preferences
        for tool in tools_used:
            if tool not in self.user_preferences.preferred_distributions:
                self.user_preferences.preferred_distributions.append(tool)
        
        # Keep only top 10 preferred distributions
        if len(self.user_preferences.preferred_distributions) > 10:
            self.user_preferences.preferred_distributions = \
                self.user_preferences.preferred_distributions[-10:]
        
        # Track interaction patterns
        message_lower = user_message.lower()
        if len(user_message) > 100:
            self.user_preferences.interaction_patterns['detailed_queries'] += 1
        if any(word in message_lower for word in ['analyze', 'compare', 'insight']):
            self.user_preferences.interaction_patterns['analytical_queries'] += 1
        if any(word in message_lower for word in ['what', 'how many', 'show me']):
            self.user_preferences.interaction_patterns['factual_queries'] += 1
        
        # Infer preferred analysis depth
        total_queries = sum(self.user_preferences.interaction_patterns.values())
        if total_queries > 5:
            analytical_ratio = self.user_preferences.interaction_patterns['analytical_queries'] / total_queries
            if analytical_ratio > 0.6:
                self.user_preferences.preferred_analysis_depth = 'expert'
            elif analytical_ratio > 0.3:
                self.user_preferences.preferred_analysis_depth = 'detailed'
    
    def get_relevant_context(self, current_query: str, location: Optional[Dict[str, float]] = None,
                           max_items: int = 5) -> Dict[str, Any]:
        """Get relevant context for current query"""
        context = {
            'recent_conversations': [],
            'location_history': [],
            'relevant_insights': [],
            'user_patterns': {},
            'suggestions': []
        }
        
        query_tags = self._extract_tags(current_query)
        
        # Get relevant conversation history
        relevant_conversations = []
        for conv in list(self.conversation_memory)[-10:]:  # Last 10 conversations
            conv.access_count += 1
            conv.last_accessed = datetime.now().isoformat()
            
            # Check relevance based on tags
            conv_tags = set(conv.tags)
            query_tag_set = set(query_tags)
            
            if conv_tags.intersection(query_tag_set) or conv.importance > 0.7:
                relevant_conversations.append({
                    'content': conv.content,
                    'importance': conv.importance,
                    'timestamp': conv.timestamp,
                    'tools_used': conv.context.get('tools_used', [])
                })
        
        context['recent_conversations'] = relevant_conversations[:max_items]
        
        # Get location context
        if location:
            location_key = f"{location['lat']:.4f},{location['lng']:.4f}"
            if location_key in self.location_contexts:
                loc_context = self.location_contexts[location_key]
                context['current_location'] = {
                    'name': loc_context.location_name,
                    'state': loc_context.state,
                    'visit_count': loc_context.visit_count,
                    'previous_queries': loc_context.queries_asked[-5:],  # Last 5 queries
                    'insights': loc_context.insights_discovered[-3:]  # Last 3 insights
                }
        
        # Get similar locations
        similar_locations = []
        for loc_key, loc_context in list(self.location_contexts.items())[-5:]:
            if any(tag in ' '.join(loc_context.queries_asked).lower() for tag in query_tags):
                similar_locations.append({
                    'name': loc_context.location_name,
                    'state': loc_context.state,
                    'visit_count': loc_context.visit_count,
                    'relevant_queries': [q for q in loc_context.queries_asked if any(tag in q.lower() for tag in query_tags)]
                })
        
        context['location_history'] = similar_locations
        
        # Get relevant insights
        relevant_insights = []
        for insight_entry in self.episodic_memory:
            if any(tag in insight_entry.tags for tag in query_tags) and insight_entry.importance > 0.6:
                relevant_insights.append({
                    'content': insight_entry.content,
                    'importance': insight_entry.importance,
                    'timestamp': insight_entry.timestamp
                })
        
        context['relevant_insights'] = sorted(relevant_insights, 
                                            key=lambda x: x['importance'], reverse=True)[:max_items]
        
        # User patterns
        context['user_patterns'] = {
            'preferred_distributions': self.user_preferences.preferred_distributions[-5:],
            'analysis_depth': self.user_preferences.preferred_analysis_depth,
            'interaction_style': max(self.user_preferences.interaction_patterns.items(), 
                                   key=lambda x: x[1])[0] if self.user_preferences.interaction_patterns else None,
            'geographic_interests': self.user_preferences.geographic_interests
        }
        
        # Generate suggestions based on patterns
        suggestions = self._generate_suggestions(current_query, query_tags)
        context['suggestions'] = suggestions
        
        return context
    
    def _generate_suggestions(self, current_query: str, query_tags: List[str]) -> List[str]:
        """Generate intelligent suggestions based on memory patterns"""
        suggestions = []
        
        # Based on user preferences
        if self.user_preferences.preferred_distributions:
            most_used = self.user_preferences.preferred_distributions[-1]
            suggestions.append(f"Consider analyzing {most_used} data as you've shown interest in this before")
        
        # Based on location patterns
        if len(self.location_contexts) > 1:
            suggestions.append("You could compare this location with previously analyzed areas")
        
        # Based on analysis depth preference
        if self.user_preferences.preferred_analysis_depth == 'expert':
            suggestions.append("Consider using conditional analysis for deeper insights")
        
        # Based on semantic memory
        for tag in query_tags:
            if tag in self.semantic_memory and len(self.semantic_memory[tag]) > 1:
                suggestions.append(f"Previous insights about {tag} might be relevant to your current query")
        
        return suggestions[:3]  # Return top 3 suggestions
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get comprehensive memory system summary"""
        return {
            'conversation_history_size': len(self.conversation_memory),
            'locations_visited': len(self.location_contexts),
            'insights_stored': len(self.episodic_memory),
            'semantic_topics': len(self.semantic_memory),
            'user_preferences': {
                'preferred_distributions': self.user_preferences.preferred_distributions,
                'frequent_conditions': self.user_preferences.frequent_conditions,
                'interaction_patterns': dict(self.user_preferences.interaction_patterns),
                'preferred_analysis_depth': self.user_preferences.preferred_analysis_depth,
                'geographic_interests': self.user_preferences.geographic_interests,
                'topic_interests': self.user_preferences.topic_interests
            },
            'memory_access_patterns': dict(self.memory_access_patterns),
            'recent_locations': [
                {
                    'name': ctx.location_name,
                    'state': ctx.state,
                    'visit_count': ctx.visit_count,
                    'last_visited': ctx.last_visited
                }
                for ctx in list(self.location_contexts.values())[-5:]
            ]
        }
    
    def clear_working_memory(self):
        """Clear working memory while preserving long-term memories"""
        self.working_memory.clear()
    
    def consolidate_memories(self):
        """Consolidate and optimize memory storage"""
        # Remove low-importance episodic memories if storage is getting full
        if len(self.episodic_memory) > 100:
            important_memories = [m for m in self.episodic_memory if m.importance > self.importance_threshold]
            self.episodic_memory = important_memories
        
        # Consolidate semantic memory
        for topic, insights in self.semantic_memory.items():
            if len(insights) > 10:
                # Keep only the most recent and relevant insights
                self.semantic_memory[topic] = insights[-10:]