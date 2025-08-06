import React, { useState, useEffect, useMemo, useRef } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

// Configuration for the 6 target distributions - Using Propheus color palette
const DISTRIBUTION_CONFIGS = {
  age: { 
    title: 'Age Distribution', 
    color: '#319dff', // Propheus blue
    type: 'individual',
    dataPath: 'data'
  },
  gender: { 
    title: 'Gender Distribution', 
    color: '#f97316', // Orange accent
    type: 'individual',
    dataPath: 'data'
  },
  education: { 
    title: 'Education Distribution', 
    color: '#008a89', // Propheus teal
    type: 'individual',
    dataPath: 'data'
  },
  income: { 
    title: 'Income Distribution', 
    color: '#8b5cf6', // Purple accent
    type: 'individual',
    dataPath: 'data'
  },
  profession: { 
    title: 'Profession Distribution', 
    color: '#10b981', // Green accent
    type: 'individual',
    dataPath: 'data'
  },
  race_ethnicity: { 
    title: 'Race & Ethnicity Distribution', 
    color: '#06b6d4', // Cyan accent
    type: 'individual',
    dataPath: 'data'
  },
  joint_conditional: {
    title: 'Joint Distribution (Conditional Analysis)',
    color: '#dc2626', // Red accent
    type: 'conditional',
    variables: ['age', 'gender', 'education', 'income', 'profession', 'race_ethnicity']
  }
};

// Conditional value options for each type - synchronized with backend standard categories
const CONDITIONAL_OPTIONS = {
  // Standardized age ranges - matches B01001_AGE_MAPPING in standard_categories.py
  age: [
    "Under 5 years", "5 to 9 years", "10 to 14 years", "15 to 17 years", 
    "18 and 19 years", "20 to 24 years", "25 to 29 years", "30 to 34 years",
    "35 to 44 years", "45 to 54 years", "55 to 64 years", "65 to 74 years",
    "75 to 84 years", "85 years and over",
    // Additional age ranges for age-income distribution (B19037)
    "Under 25 years", "25 to 44 years", "45 to 64 years", "65 years and over"
  ],
  
  // Standardized income ranges - matches B19001_INCOME_MAPPING in standard_categories.py
  income: [
    "$1 to $2,499 or loss", "$2,500 to $4,999", "$5,000 to $7,499", 
    "$7,500 to $9,999", "$10,000 to $12,499", "$12,500 to $14,999",
    "$15,000 to $17,499", "$17,500 to $19,999", "$20,000 to $22,499",
    "$22,500 to $24,999", "$25,000 to $29,999", "$30,000 to $34,999",
    "$35,000 to $39,999", "$40,000 to $44,999", "$45,000 to $49,999",
    "$50,000 to $54,999", "$55,000 to $64,999", "$65,000 to $74,999",
    "$75,000 to $99,999", "$100,000 or more",
    // Additional income ranges for age-income distribution (B19037)
    "Less than $10,000", "$10,000 to $14,999", "$15,000 to $19,999",
    "$20,000 to $24,999", "$25,000 to $29,999", "$30,000 to $34,999",
    "$35,000 to $39,999", "$40,000 to $44,999", "$45,000 to $49,999",
    "$50,000 to $59,999", "$60,000 to $74,999", "$75,000 to $99,999",
    "$100,000 to $124,999", "$125,000 to $149,999",
    "$150,000 to $199,999", "$200,000 or more"
  ],
  
  // Standard gender categories
  gender: ["Male", "Female"],
  
  // Standardized education categories - matches STANDARD_EDUCATION_CATEGORIES
  education: [
    "Less than 9th grade", "9th to 12th grade, no diploma", "High school graduate", 
    "Some college, no degree", "Associate's degree", "Bachelor's degree", 
    "Graduate or professional degree"
  ],
  
  // Standardized profession categories - matches STANDARD_PROFESSION_CATEGORIES
  profession: [
    "Management, business, science, and arts occupations", 
    "Service occupations", 
    "Sales and office occupations", 
    "Natural resources, construction, and maintenance occupations", 
    "Production, transportation, and material moving occupations"
  ],
  
  // Standardized race/ethnicity categories - matches STANDARD_RACE_ETHNICITY_CATEGORIES
  race_ethnicity: [
    "White Alone", "Black or African American Alone", "American Indian and Alaska Native Alone", 
    "Asian Alone", "Native Hawaiian and Other Pacific Islander Alone", "Some Other Race Alone", 
    "Two or More Races", "Hispanic or Latino"
  ],
  
  // Alias for race (same as race_ethnicity for compatibility)
  race: [
    "White Alone", "Black or African American Alone", "American Indian and Alaska Native Alone", 
    "Asian Alone", "Native Hawaiian and Other Pacific Islander Alone", "Some Other Race Alone", 
    "Two or More Races", "Hispanic or Latino"
  ]
};

// Helper function to sort distribution data based on type
function sortDistributionData(data, distributionType) {
  if (!data || data.length === 0) return data;
  
  const sortOrder = CONDITIONAL_OPTIONS[distributionType];
  if (!sortOrder) return data;
  
  return [...data].sort((a, b) => {
    const indexA = sortOrder.indexOf(a.category);
    const indexB = sortOrder.indexOf(b.category);
    
    // If category not found in sort order, put it at the end
    if (indexA === -1 && indexB === -1) return 0;
    if (indexA === -1) return 1;
    if (indexB === -1) return -1;
    
    return indexA - indexB;
  });
}

function UnifiedDistributionChart({ data, title, color, type }) {
  if (!data || data.length === 0) return null;
  
  const sortedData = sortDistributionData(data, type);

  const formatCategory = (category) => {
    if (type === 'age') {
      return category.replace(' years', '').replace(' and over', '+');
    }
    if (type === 'education') {
      return category.length > 15 ? category.substring(0, 15) + '...' : category;
    }
    if (type === 'income') {
      return category.replace('$', '').replace(',000', 'K').replace(' or more', '+');
    }
    if (type === 'profession') {
      return category.length > 20 ? category.substring(0, 20) + '...' : category;
    }
    return category;
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const dataPoint = payload[0].payload;
      return (
        <div style={{
          backgroundColor: '#111827',
          border: '1px solid #374151',
          borderRadius: '8px',
          padding: '12px',
          fontSize: '13px',
          color: '#f9fafb',
          boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.3)'
        }}>
          <p style={{ margin: '0 0 6px 0', fontWeight: '600', color: '#f9fafb' }}>{dataPoint.category}</p>
          <p style={{ margin: '0 0 4px 0', color: '#d1d5db' }}>
            Count: {payload[0].value.toLocaleString()}
          </p>
          <p style={{ margin: '0', color: '#319dff', fontWeight: '600' }}>
            {dataPoint.percentage?.toFixed(1)}%
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div style={{ marginBottom: '24px' }}>
      <h3 style={{ 
        margin: '0 0 16px 0', 
        fontSize: '16px', 
        fontWeight: '600', 
        color: '#ffffff' 
      }}>
        {title}
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={sortedData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
          <CartesianGrid strokeDasharray="2 2" stroke="#374151" strokeOpacity={0.3} />
          <XAxis
            dataKey="category"
            tick={{ fontSize: 11, fill: '#d1d5db' }}
            angle={-45}
            textAnchor="end"
            height={60}
            tickFormatter={formatCategory}
            axisLine={{ stroke: '#4b5563' }}
          />
          <YAxis 
            tick={{ fontSize: 11, fill: '#d1d5db' }} 
            axisLine={{ stroke: '#4b5563' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar
            dataKey="value"
            fill={color}
            radius={[6, 6, 0, 0]}
            animationDuration={1000}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}




function MarginalDistributions({ distributionData, baseDistribution }) {
  const config = DISTRIBUTION_CONFIGS[baseDistribution];
  
  if (!config.marginals || !distributionData) return null;

  return (
    <div style={{ 
      display: 'grid', 
      gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', 
      gap: '20px', 
      marginBottom: '24px' 
    }}>
      {config.marginals.map((marginalKey, index) => {
        const marginalData = distributionData[marginalKey];
        if (!marginalData) return null;

        // Determine the distribution type from the marginal key
        const distributionType = marginalKey.includes('income') ? 'income'
          : marginalKey.includes('age') ? 'age'
          : marginalKey.includes('education') ? 'education'
          : marginalKey.includes('profession') ? 'profession'
          : marginalKey.includes('gender') ? 'gender'
          : marginalKey.includes('race') ? 'race'
          : null;
        
        const sortedData = sortDistributionData(marginalData, distributionType);

        return (
          <div key={marginalKey}>
            <h4 style={{ 
              margin: '0 0 12px 0', 
              fontSize: '14px', 
              fontWeight: '500', 
              color: '#d1d5db' 
            }}>
              {marginalKey.replace('_marginal', '').replace('_', ' ').toUpperCase()} Distribution (Marginal)
            </h4>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={sortedData} margin={{ top: 10, right: 10, left: 10, bottom: 40 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2a2e36" />
                <XAxis
                  dataKey="category"
                  tick={{ fontSize: 8, fill: '#9ca3af' }}
                  angle={-45}
                  textAnchor="end"
                  height={40}
                  tickFormatter={(value) => {
                    if (distributionType === 'income') {
                      return value.replace('$', '').replace(',000', 'K').replace(' or more', '+');
                    }
                    if (distributionType === 'age') {
                      return value.replace(' years', '').replace(' and over', '+');
                    }
                    if (distributionType === 'education') {
                      return value.length > 15 ? value.substring(0, 15) + '...' : value;
                    }
                    if (distributionType === 'profession') {
                      return value.length > 20 ? value.substring(0, 20) + '...' : value;
                    }
                    return value.length > 15 ? value.substring(0, 15) + '...' : value;
                  }}
                />
                <YAxis tick={{ fontSize: 8, fill: '#9ca3af' }} />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: '#1a1e26',
                    border: '1px solid #2a2e36',
                    borderRadius: '6px',
                    fontSize: '12px'
                  }}
                />
                <Bar 
                  dataKey="value" 
                  fill={index === 0 ? '#3b82f6' : '#ef4444'} 
                  radius={[2, 2, 0, 0]} 
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        );
      })}
    </div>
  );
}

export default function UnifiedDistributionSystem({ distributionData, selectedLocation }) {
  const [baseDistribution, setBaseDistribution] = useState('age');
  
  // New state for joint conditional analysis
  const [jointConditionVariable, setJointConditionVariable] = useState('age');
  const [jointConditionValue, setJointConditionValue] = useState('');
  const [jointConditionalResults, setJointConditionalResults] = useState({});
  const [jointLoading, setJointLoading] = useState(false);

  const currentConfig = DISTRIBUTION_CONFIGS[baseDistribution];
  const currentData = distributionData?.distributions?.[baseDistribution];

  // Joint conditional analysis function
  const handleJointConditionalAnalysis = async () => {
    if (!jointConditionValue || !selectedLocation) return;
    
    setJointLoading(true);
    setJointConditionalResults({});
    
    // Define which distributions to fetch for each condition variable
    // Only fetch from distributions that actually contain the condition variable
    const distributionMappings = {
      age: ['age_income', 'age_gender', 'age_race', 'age_education'],
      gender: ['gender_education', 'income_gender_new', 'age_gender', 'profession_gender'],
      income: ['income_gender_new', 'age_income', 'income_profession'],
      education: ['gender_education', 'education_race', 'age_education', 'education_sex'],
      profession: ['profession_race', 'profession_gender', 'income_profession'],
      race_ethnicity: ['education_race', 'profession_race', 'age_race']
    };
    
    const distributionsToFetch = distributionMappings[jointConditionVariable] || [];
    const results = {};
    
    for (const distType of distributionsToFetch) {
      try {
        // Map condition types for backend compatibility
        const backendConditionType = jointConditionVariable === 'race_ethnicity' ? 'race' : jointConditionVariable;
        
        const response = await fetch('http://localhost:5001/joint_probability', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            lat: selectedLocation.lat,
            lng: selectedLocation.lng,
            distribution_type: distType,
            condition_type: backendConditionType,
            condition_value: jointConditionValue
          })
        });
        
        if (response.ok) {
          const data = await response.json();
          if (data.conditional_distribution && !data.conditional_distribution.error) {
            results[distType] = {
              ...data.conditional_distribution,
              displayName: getDistributionDisplayName(distType, jointConditionVariable)
            };
          } else {
            results[distType] = { error: 'Data not available' };
          }
        } else {
          results[distType] = { error: 'Data not available' };
        }
      } catch (error) {
        results[distType] = { error: 'Network error' };
      }
    }
    
    setJointConditionalResults(results);
    setJointLoading(false);
  };

  // Helper function to get display name for distributions
  const getDistributionDisplayName = (distType, conditionVariable) => {
    const mapping = {
      gender_education: 'Education Distribution',
      income_gender_new: 'Income Distribution', 
      education_race: 'Race Distribution',
      profession_race: 'Race Distribution',
      age_gender: 'Age Distribution',
      profession_gender: 'Profession Distribution',
      age_income: 'Income Distribution',
      age_education: 'Education Distribution',
      education_sex: 'Sex Distribution',
      age_race: 'Race Distribution'
    };

    // Return the other variable name based on condition
    if (distType.includes('gender') && conditionVariable !== 'gender') return 'Gender Distribution';
    if (distType.includes('income') && conditionVariable !== 'income') return 'Income Distribution';
    if (distType.includes('education') && conditionVariable !== 'education') return 'Education Distribution';
    if (distType.includes('profession') && conditionVariable !== 'profession') return 'Profession Distribution';
    if (distType.includes('race') && conditionVariable !== 'race_ethnicity') return 'Race Distribution';
    if (distType.includes('age') && conditionVariable !== 'age') return 'Age Distribution';
    
    return mapping[distType] || distType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  if (!distributionData) return null;

  return (
    <div style={{ padding: '20px' }}>
      {/* Distribution Selection */}
      <div style={{ marginBottom: '24px' }}>
        <h3 style={{ 
          margin: '0 0 16px 0', 
          fontSize: '18px', 
          fontWeight: '600', 
          color: '#ffffff' 
        }}>
          Select Distribution Type
        </h3>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', 
          gap: '12px' 
        }}>
          {Object.entries(DISTRIBUTION_CONFIGS).map(([key, config]) => {
            const isAvailable = key === 'joint_conditional' || (distributionData?.distributions?.[key]);
            return (
              <button
                key={key}
                onClick={() => setBaseDistribution(key)}
                disabled={!isAvailable}
                style={{
                  backgroundColor: baseDistribution === key ? '#008a89' : '#1f2937',
                  color: baseDistribution === key ? '#ffffff' : isAvailable ? '#f9fafb' : '#6b7280',
                  border: `1px solid ${baseDistribution === key ? '#008a89' : '#374151'}`,
                  padding: '12px 16px',
                  borderRadius: '8px',
                  fontSize: '13px',
                  fontWeight: '600',
                  cursor: isAvailable ? 'pointer' : 'not-allowed',
                  transition: 'all 0.2s ease',
                  opacity: isAvailable ? 1 : 0.5,
                  boxShadow: baseDistribution === key ? '0 0 0 2px rgba(0, 138, 137, 0.2)' : 'none'
                }}
              >
                {config.title}
              </button>
            );
          })}
        </div>
      </div>

      {/* Joint Conditional Analysis Section */}
      {baseDistribution === 'joint_conditional' && (
        <div style={{ 
          marginBottom: '24px',
          padding: '20px',
          backgroundColor: '#111827',
          borderRadius: '12px',
          border: '1px solid #dc2626'
        }}>
          <h3 style={{ 
            margin: '0 0 16px 0', 
            fontSize: '16px', 
            fontWeight: '600', 
            color: '#dc2626' 
          }}>
            Joint Conditional Analysis
          </h3>
          <p style={{ 
            margin: '0 0 16px 0', 
            fontSize: '14px', 
            color: '#9ca3af' 
          }}>
            Condition on one variable to see distributions of all other variables
          </p>
          
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: '1fr 1fr auto', 
            gap: '12px', 
            alignItems: 'end',
            marginBottom: '20px'
          }}>
            <div>
              <label style={{ 
                display: 'block', 
                marginBottom: '4px', 
                fontSize: '12px', 
                color: '#9ca3af' 
              }}>
                Condition Variable
              </label>
              <select
                value={jointConditionVariable}
                onChange={(e) => {
                  setJointConditionVariable(e.target.value);
                  setJointConditionValue('');
                  setJointConditionalResults({});
                }}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  backgroundColor: '#1f2937',
                  border: '1px solid #374151',
                  borderRadius: '6px',
                  color: '#ffffff',
                  fontSize: '14px'
                }}
              >
                <option value="age">Age</option>
                <option value="gender">Gender</option>
                <option value="income">Income</option>
                <option value="education">Education</option>
                <option value="profession">Profession</option>
                <option value="race_ethnicity">Race/Ethnicity</option>
              </select>
            </div>

            <div>
              <label style={{ 
                display: 'block', 
                marginBottom: '4px', 
                fontSize: '12px', 
                color: '#9ca3af' 
              }}>
                Condition Value
              </label>
              <select
                value={jointConditionValue}
                onChange={(e) => setJointConditionValue(e.target.value)}
                disabled={!jointConditionVariable}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  backgroundColor: jointConditionVariable ? '#1f2937' : '#374151',
                  border: '1px solid #374151',
                  borderRadius: '6px',
                  color: jointConditionVariable ? '#ffffff' : '#6b7280',
                  fontSize: '14px'
                }}
              >
                <option value="">Select value...</option>
                {jointConditionVariable && CONDITIONAL_OPTIONS[jointConditionVariable]?.map(option => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={handleJointConditionalAnalysis}
              disabled={!jointConditionValue || jointLoading}
              style={{
                padding: '8px 16px',
                backgroundColor: (jointConditionValue && !jointLoading) ? '#dc2626' : '#4b5563',
                color: (jointConditionValue && !jointLoading) ? '#ffffff' : '#9ca3af',
                border: 'none',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: '500',
                cursor: (jointConditionValue && !jointLoading) ? 'pointer' : 'not-allowed'
              }}
            >
              {jointLoading ? 'Loading...' : 'Analyze'}
            </button>
          </div>

          {/* Results Display */}
          {Object.keys(jointConditionalResults).length > 0 && (
            <div>
              <h4 style={{ 
                margin: '0 0 16px 0', 
                fontSize: '14px', 
                fontWeight: '600', 
                color: '#ffffff' 
              }}>
                Conditional Distributions: {jointConditionVariable} = "{jointConditionValue}"
              </h4>
              
              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', 
                gap: '16px' 
              }}>
                {Object.entries(jointConditionalResults).map(([distType, result]) => {
                  return (
                    <div key={distType} style={{ 
                      backgroundColor: '#1f2937', 
                      padding: '16px', 
                      borderRadius: '8px',
                      border: '1px solid #374151'
                    }}>
                      <h5 style={{ 
                        margin: '0 0 12px 0', 
                        fontSize: '13px', 
                        fontWeight: '500', 
                        color: '#dc2626' 
                      }}>
                        {result.displayName || distType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </h5>
                      
                      {result.error ? (
                        <div style={{ 
                          color: '#9ca3af', 
                          fontSize: '12px', 
                          fontStyle: 'italic' 
                        }}>
                          Data not available
                        </div>
                      ) : (
                        <>
                          {/* Show special handling for median values */}
                          {result.data && result.data.length > 0 && result.data[0].median_earnings ? (
                            <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '8px' }}>
                              <strong>Median Earnings:</strong> ${result.data[0].median_earnings.toLocaleString()}
                            </div>
                          ) : result.data && result.data.length > 0 ? (
                            <>
                              <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '8px' }}>
                                Data Points: {(result.data || []).length} | Total Population: {result.total_households || result.total_population || 0}
                              </div>
                              <ResponsiveContainer width="100%" height={200}>
                                <BarChart 
                                  data={result.data || []} 
                                  margin={{ top: 5, right: 30, left: 20, bottom: 60 }}
                                >
                                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                                  <XAxis 
                                    dataKey="category" 
                                    stroke="#9ca3af"
                                    fontSize={10}
                                    angle={-45}
                                    textAnchor="end"
                                    height={80}
                                    interval={0}
                                    tickFormatter={(value) => {
                                      // Format different distribution types
                                      if (value.includes('$')) {
                                        return value.replace('$', '').replace(',000', 'K').replace(' or more', '+');
                                      }
                                      if (value.includes(' years')) {
                                        return value.replace(' years', '').replace(' and over', '+');
                                      }
                                      // Truncate long category names
                                      return value.length > 12 ? value.substring(0, 12) + '...' : value;
                                    }}
                                  />
                                  <YAxis 
                                    stroke="#9ca3af" 
                                    fontSize={10}
                                    tickFormatter={(value) => `${value.toFixed(1)}%`}
                                  />
                                  <Tooltip 
                                    contentStyle={{ 
                                      backgroundColor: '#111827', 
                                      border: '1px solid #374151',
                                      borderRadius: '4px',
                                      fontSize: '12px'
                                    }}
                                    formatter={(value, name) => {
                                      if (name === 'percentage') {
                                        return [`${value.toFixed(1)}%`, 'Percentage'];
                                      }
                                      if (name === 'value') {
                                        return [`${value} households`, 'Count'];
                                      }
                                      return [value, name];
                                    }}
                                    labelFormatter={(label) => label}
                                  />
                                  <Bar 
                                    dataKey="percentage" 
                                    fill="#dc2626" 
                                    opacity={0.8}
                                    minPointSize={2}
                                  />
                                </BarChart>
                              </ResponsiveContainer>
                            </>
                          ) : (
                            <div style={{ 
                              color: '#9ca3af', 
                              fontSize: '12px', 
                              fontStyle: 'italic' 
                            }}>
                              No data available
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}


      {/* Distribution Display */}
      {currentConfig.type === 'individual' && currentData && (
        <div>
          {/* Main Distribution Chart */}
          <UnifiedDistributionChart
            data={currentData.data}
            title={currentConfig.title}
            color={currentConfig.color}
            type={baseDistribution}
          />

          {/* Data Source */}
          <div style={{
            marginTop: '20px',
            padding: '16px',
            backgroundColor: '#111827',
            borderRadius: '10px',
            border: '1px solid #374151'
          }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              fontSize: '13px',
              color: '#d1d5db',
              marginBottom: '10px',
              fontWeight: '500'
            }}>
              <span>
                Categories: {currentData.data?.length}
              </span>
              <span>
                Total: {currentData.data?.reduce((sum, item) => sum + item.value, 0).toLocaleString()}
              </span>
            </div>
            <div style={{
              fontSize: '12px',
              color: '#319dff',
              fontFamily: 'JetBrains Mono, monospace'
            }}>
              {currentData.data_source}
            </div>
          </div>
        </div>
      )}

    </div>
  );
}