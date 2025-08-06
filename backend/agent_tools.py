"""
Advanced AI Agent Tools for Census Data Analysis
Individual tool classes that can be selected and used strategically by the agent
"""

import sys
import os
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

# Add parent directory to path to import distribution modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from distribution.age_distribution import get_distribution as get_age_distribution
from distribution.gender_distribution import get_distribution as get_gender_distribution
from distribution.education_distribution import get_distribution as get_education_distribution
from distribution.income_distribution import get_distribution as get_income_distribution
from distribution.profession_distribution import get_distribution as get_profession_distribution
from distribution.race_ethnicity_distribution import get_distribution as get_race_ethnicity_distribution
# Joint distributions
from distribution.age_income_distribution import get_distribution as get_age_income_distribution
from distribution.age_income_distribution import get_conditional_distribution as get_age_income_conditional
from distribution.age_gender_distribution import get_distribution as get_age_gender_distribution
from distribution.age_gender_distribution import get_conditional_distribution as get_age_gender_conditional
from distribution.age_race_distribution import get_distribution as get_age_race_distribution
from distribution.age_race_distribution import get_conditional_distribution as get_age_race_conditional
from distribution.age_education_distribution import get_distribution as get_age_education_distribution
from distribution.age_education_distribution import get_conditional_distribution as get_age_education_conditional
from distribution.income_gender_distribution import get_distribution as get_income_gender_distribution
from distribution.income_gender_distribution import get_conditional_distribution as get_income_gender_conditional
from distribution.profession_distribution import get_conditional_distribution as get_profession_conditional
# New joint distributions  
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

class BaseTool(ABC):
    """Base class for all agent tools"""
    
    def __init__(self, name: str, description: str, use_cases: List[str]):
        self.name = name
        self.description = description
        self.use_cases = use_cases
        self.usage_count = 0
        self.last_used = None
    
    @abstractmethod
    def execute(self, lat: float, lng: float, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given parameters"""
        pass
    
    def should_use(self, query: str, context: Dict[str, Any]) -> float:
        """Return confidence score (0-1) for whether this tool should be used for the query"""
        query_lower = query.lower()
        score = 0.0
        
        # Base scoring based on keywords in use cases
        for use_case in self.use_cases:
            use_case_words = use_case.lower().split()
            for word in use_case_words:
                if word in query_lower:
                    score += 0.1
        
        # Boost score if tool name is mentioned
        if self.name.lower() in query_lower:
            score += 0.3
            
        return min(score, 1.0)
    
    def track_usage(self):
        """Track tool usage for analytics"""
        self.usage_count += 1
        import datetime
        self.last_used = datetime.datetime.now()

class AgeDistributionTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="age_distribution",
            description="Get age demographics showing population distribution across age groups",
            use_cases=[
                "age demographics", "age groups", "population age", "elderly population", 
                "young adults", "seniors", "age breakdown", "generational analysis"
            ]
        )
    
    def execute(self, lat: float, lng: float, **kwargs) -> Dict[str, Any]:
        self.track_usage()
        return get_age_distribution(lat, lng)

class GenderDistributionTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="gender_distribution",
            description="Get gender demographics showing male/female population distribution",
            use_cases=[
                "gender demographics", "male female ratio", "gender breakdown",
                "population by gender", "sex distribution"
            ]
        )
    
    def execute(self, lat: float, lng: float, **kwargs) -> Dict[str, Any]:
        self.track_usage()
        return get_gender_distribution(lat, lng)

class EducationDistributionTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="education_distribution",
            description="Get educational attainment levels showing degrees and qualifications",
            use_cases=[
                "education levels", "degree attainment", "college education", "high school",
                "bachelor degree", "graduate education", "educational qualifications"
            ]
        )
    
    def execute(self, lat: float, lng: float, **kwargs) -> Dict[str, Any]:
        self.track_usage()
        return get_education_distribution(lat, lng)

class IncomeDistributionTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="income_distribution",
            description="Get household income distribution across different income brackets",
            use_cases=[
                "income levels", "household income", "salary distribution", "earnings",
                "income brackets", "median income", "poverty", "wealth distribution"
            ]
        )
    
    def execute(self, lat: float, lng: float, **kwargs) -> Dict[str, Any]:
        self.track_usage()
        return get_income_distribution(lat, lng)

class AgeIncomeJointTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="age_income_joint",
            description="Get joint age-income distribution showing how income varies by age groups",
            use_cases=[
                "age income relationship", "income by age", "earnings by age group",
                "young adult income", "senior income", "age income correlation"
            ]
        )
    
    def execute(self, lat: float, lng: float, **kwargs) -> Dict[str, Any]:
        self.track_usage()
        return get_age_income_distribution(lat, lng)


class ProfessionGenderJointTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="profession_gender_joint",
            description="Get profession-gender joint distribution showing occupations by gender",
            use_cases=[
                "jobs by gender", "occupation gender", "profession demographics",
                "career by gender", "workplace gender", "employment by gender"
            ]
        )
    
    def execute(self, lat: float, lng: float, **kwargs) -> Dict[str, Any]:
        self.track_usage()
        return get_profession_distribution(lat, lng)

class GenderEducationJointTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="gender_education_joint",
            description="Get gender-education joint distribution showing educational attainment by gender",
            use_cases=[
                "education by gender", "gender education gap", "educational attainment gender",
                "degree by gender", "male female education", "gender academic achievement"
            ]
        )
    
    def execute(self, lat: float, lng: float, **kwargs) -> Dict[str, Any]:
        self.track_usage()
        return get_gender_education_distribution(lat, lng)

class IncomeGenderNewJointTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="income_gender_new_joint", 
            description="Get income-gender joint distribution showing earnings by gender (new version)",
            use_cases=[
                "income by gender", "gender wage gap", "earnings by sex", "male female income",
                "gender pay inequality", "salary by gender", "income gender difference"
            ]
        )
    
    def execute(self, lat: float, lng: float, **kwargs) -> Dict[str, Any]:
        self.track_usage()
        return get_income_gender_new_distribution(lat, lng)

class IncomeProfessionJointTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="income_profession_joint",
            description="Get income-profession joint distribution showing median earnings by occupation",
            use_cases=[
                "earnings by job", "salary by occupation", "profession income", "career earnings",
                "occupation wages", "job income", "professional compensation"
            ]
        )
    
    def execute(self, lat: float, lng: float, **kwargs) -> Dict[str, Any]:
        self.track_usage()
        return get_income_profession_distribution(lat, lng)

class EducationRaceJointTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="education_race_joint",
            description="Get education-race joint distribution showing educational attainment by race/ethnicity",
            use_cases=[
                "education by race", "racial education gap", "ethnic education levels",
                "minority education", "racial academic achievement", "education ethnicity"
            ]
        )
    
    def execute(self, lat: float, lng: float, **kwargs) -> Dict[str, Any]:
        self.track_usage()
        return get_education_race_distribution(lat, lng)

class ProfessionRaceJointTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="profession_race_joint",
            description="Get profession-race joint distribution showing occupations by race/ethnicity",
            use_cases=[
                "jobs by race", "occupation ethnicity", "racial job distribution",
                "career by race", "workplace diversity", "ethnic occupation patterns"
            ]
        )
    
    def execute(self, lat: float, lng: float, **kwargs) -> Dict[str, Any]:
        self.track_usage()
        return get_profession_race_distribution(lat, lng)

class ProfessionDistributionTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="profession_distribution",
            description="Get profession/occupation distribution showing employment by industry",
            use_cases=[
                "occupation", "profession", "employment", "jobs", "industry",
                "career", "work", "occupation distribution"
            ]
        )
    
    def execute(self, lat: float, lng: float, **kwargs) -> Dict[str, Any]:
        self.track_usage()
        return get_profession_distribution(lat, lng)

class RaceEthnicityTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="race_ethnicity",
            description="Get racial and ethnic demographics of the population",
            use_cases=[
                "race demographics", "ethnicity", "diversity", "racial composition",
                "ethnic breakdown", "minority populations", "racial distribution"
            ]
        )
    
    def execute(self, lat: float, lng: float, **kwargs) -> Dict[str, Any]:
        self.track_usage()
        return get_race_ethnicity_distribution(lat, lng)








class ConditionalAnalysisTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="conditional_analysis",
            description="Get conditional distributions from joint data with unified age bracket support",
            use_cases=[
                "income for age group", "age for income bracket", "conditional probability",
                "specific demographics", "filtered analysis", "subset analysis", "unified age brackets",
                "consistent age ranges", "age demographic analysis", "bivariate conditional analysis"
            ]
        )
    
    def execute(self, lat: float, lng: float, **kwargs) -> Dict[str, Any]:
        self.track_usage()
        base_distribution = kwargs.get('base_distribution', 'age_income')
        condition_type = kwargs.get('condition_type')
        condition_value = kwargs.get('condition_value')
        
        if not condition_type or not condition_value:
            return {
                "error": "Missing condition_type or condition_value for conditional analysis",
                "help": {
                    "available_distributions": [
                        "age_income", "age_gender", "age_race", "age_education",
                        "income_gender", "income_gender_new", "income_profession", 
                        "gender_education", "education_race", "profession_race"
                    ],
                    "example_usage": {
                        "base_distribution": "age_income",
                        "condition_type": "age", 
                        "condition_value": "25 to 34 years"
                    }
                }
            }
        
        # Execute conditional analysis for each supported distribution
        try:
            if base_distribution == 'age_income':
                joint_data = get_age_income_distribution(lat, lng)
                result = get_age_income_conditional(joint_data, condition_type, condition_value)
            elif base_distribution == 'age_gender':
                joint_data = get_age_gender_distribution(lat, lng)
                result = get_age_gender_conditional(joint_data, condition_type, condition_value)
            elif base_distribution == 'age_race':
                joint_data = get_age_race_distribution(lat, lng)
                result = get_age_race_conditional(joint_data, condition_type, condition_value)
            elif base_distribution == 'age_education':
                joint_data = get_age_education_distribution(lat, lng)
                result = get_age_education_conditional(joint_data, condition_type, condition_value)
            elif base_distribution == 'income_gender':
                joint_data = get_income_gender_distribution(lat, lng)
                result = get_income_gender_conditional(joint_data, condition_type, condition_value)
            elif base_distribution == 'gender_education':
                joint_data = get_gender_education_distribution(lat, lng)
                result = get_gender_education_conditional(joint_data, condition_type, condition_value)
            elif base_distribution == 'income_gender_new':
                joint_data = get_income_gender_new_distribution(lat, lng)
                result = get_income_gender_new_conditional(joint_data, condition_type, condition_value)
            elif base_distribution == 'income_profession':
                joint_data = get_income_profession_distribution(lat, lng)
                result = get_income_profession_conditional(joint_data, condition_type, condition_value)
            elif base_distribution == 'education_race':
                joint_data = get_education_race_distribution(lat, lng)
                result = get_education_race_conditional(joint_data, condition_type, condition_value)
            elif base_distribution == 'profession_race':
                joint_data = get_profession_race_distribution(lat, lng)
                result = get_profession_race_conditional(joint_data, condition_type, condition_value)
            else:
                available_dists = [
                    "age_income", "age_gender", "age_race", "age_education",
                    "income_gender", "income_gender_new", "income_profession", 
                    "gender_education", "education_race", "profession_race"
                ]
                return {
                    "error": f"Unsupported base distribution: {base_distribution}",
                    "available_distributions": available_dists
                }
            
            return result
            
        except Exception as e:
            return {
                "error": f"Failed to execute conditional analysis: {str(e)}",
                "base_distribution": base_distribution,
                "condition_type": condition_type,
                "condition_value": condition_value
            }


class ToolRegistry:
    """Registry of all available tools for the agent"""
    
    def __init__(self):
        self.tools = {
            'age_distribution': AgeDistributionTool(),
            'gender_distribution': GenderDistributionTool(),
            'education_distribution': EducationDistributionTool(),
            'income_distribution': IncomeDistributionTool(),
            'age_income_joint': AgeIncomeJointTool(),
            'profession_distribution': ProfessionDistributionTool(),
            'profession_gender_joint': ProfessionGenderJointTool(),
            'race_ethnicity': RaceEthnicityTool(),
            'conditional_analysis': ConditionalAnalysisTool(),
            # Joint distribution tools
            'gender_education_joint': GenderEducationJointTool(),
            'income_gender_new_joint': IncomeGenderNewJointTool(),
            'income_profession_joint': IncomeProfessionJointTool(),
            'education_race_joint': EducationRaceJointTool(),
            'profession_race_joint': ProfessionRaceJointTool()
        }
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a specific tool by name"""
        return self.tools.get(name)
    
    def get_relevant_tools(self, query: str, context: Dict[str, Any], top_k: int = 3) -> List[BaseTool]:
        """Get the most relevant tools for a query"""
        tool_scores = []
        
        for tool in self.tools.values():
            score = tool.should_use(query, context)
            if score > 0:
                tool_scores.append((tool, score))
        
        # Sort by score descending and return top_k
        tool_scores.sort(key=lambda x: x[1], reverse=True)
        return [tool for tool, score in tool_scores[:top_k]]
    
    def get_all_tools(self) -> Dict[str, BaseTool]:
        """Get all available tools"""
        return self.tools
    
    def get_tool_usage_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get usage statistics for all tools"""
        stats = {}
        for name, tool in self.tools.items():
            stats[name] = {
                'usage_count': tool.usage_count,
                'last_used': tool.last_used.isoformat() if tool.last_used else None,
                'description': tool.description
            }
        return stats