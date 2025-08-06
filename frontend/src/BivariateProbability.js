import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

// Configuration for all joint distributions
const JOINT_DISTRIBUTION_CONFIGS = {
  // Available at block group level
  gender_education: { 
    title: 'Gender × Education',
    variables: ['gender', 'education'],
    color: '#008a89'
  },
  income_gender_new: { 
    title: 'Income × Gender',
    variables: ['income', 'gender'],
    color: '#8b5cf6'
  },
  income_profession: { 
    title: 'Income × Profession',
    variables: ['income', 'profession'],
    color: '#10b981'
  },
  education_race: { 
    title: 'Education × Race',
    variables: ['education', 'race'],
    color: '#06b6d4'
  },
  profession_race: { 
    title: 'Profession × Race',
    variables: ['profession', 'race'],
    color: '#f97316'
  },
  // Existing distributions
  age_income: { 
    title: 'Age × Income',
    variables: ['age', 'income'],
    color: '#319dff'
  },
  age_gender: { 
    title: 'Age × Gender',
    variables: ['age', 'gender'],
    color: '#f97316'
  },
  age_race: { 
    title: 'Age × Race',
    variables: ['age', 'race'],
    color: '#06b6d4'
  },
  age_education: { 
    title: 'Age × Education',
    variables: ['age', 'education'],
    color: '#008a89'
  },
  education_sex: { 
    title: 'Education × Sex',
    variables: ['education', 'sex'],
    color: '#8b5cf6'
  },
  profession_gender: { 
    title: 'Profession × Gender',
    variables: ['profession', 'gender'],
    color: '#10b981'
  }
};

// Unavailable distributions
const UNAVAILABLE_DISTRIBUTIONS = {
  age_profession: 'Age × Profession',
  income_education: 'Income × Education', 
  income_race: 'Income × Race'
};

// Age brackets and income ranges for each distribution type (raw Census data)
const DISTRIBUTION_OPTIONS = {
  age_income: {
    age: [
      "Householder under 25 years",
      "Householder 25 to 44 years", 
      "Householder 45 to 64 years",
      "Householder 65 years and over"
    ],
    income: [
      "Less than $10,000", "$10,000 to $14,999", "$15,000 to $19,999",
      "$20,000 to $24,999", "$25,000 to $29,999", "$30,000 to $34,999", 
      "$35,000 to $39,999", "$40,000 to $44,999", "$45,000 to $49,999",
      "$50,000 to $59,999", "$60,000 to $74,999", "$75,000 to $99,999",
      "$100,000 to $124,999", "$125,000 to $149,999",
      "$150,000 to $199,999", "$200,000 or more"
    ]
  },
  age_education: {
    age: [
      "18 to 24 years", "25 to 34 years", "35 to 44 years", 
      "45 to 64 years", "65 years and over"
    ],
    education: [
      "Less than 9th grade", "9th to 12th grade, no diploma", 
      "High school graduate (includes equivalency)", "Some college, no degree",
      "Associate's degree", "Bachelor's degree", "Graduate or professional degree"
    ]
  },
  education_sex: {
    education: [
      "Less than 9th grade", "9th to 12th grade, no diploma", 
      "High school graduate (includes equivalency)", "Some college, no degree",
      "Associate's degree", "Bachelor's degree", "Graduate or professional degree"
    ],
    sex: ["Male", "Female"]
  },
  // Default for other distributions
  default: {
    age: [
      "18 to 24 years", "25 to 34 years", "35 to 44 years", 
      "45 to 64 years", "65 years and over"
    ],
    income: [
      "$1 to $2,499 or loss", "$2,500 to $4,999", "$5,000 to $7,499", 
      "$7,500 to $9,999", "$10,000 to $12,499", "$12,500 to $14,999",
      "$15,000 to $17,499", "$17,500 to $19,999", "$20,000 to $22,499",
      "$22,500 to $24,999", "$25,000 to $29,999", "$30,000 to $34,999",
      "$35,000 to $39,999", "$40,000 to $44,999", "$45,000 to $49,999",
      "$50,000 to $54,999", "$55,000 to $64,999", "$65,000 to $74,999",
      "$75,000 to $99,999", "$100,000 or more"
    ]
  }
};

// Conditional value options 
const CONDITIONAL_OPTIONS = {
  age: [
    "Under 5 years", "5 to 9 years", "10 to 14 years", "15 to 17 years", 
    "18 and 19 years", "20 to 24 years", "25 to 29 years", "30 to 34 years", 
    "35 to 44 years", "45 to 54 years", "55 to 64 years", "65 to 74 years", 
    "75 to 84 years", "85 years and over"
  ],
  income: DISTRIBUTION_OPTIONS.default.income,
  gender: ["Male", "Female"],
  sex: ["Male", "Female"],
  race: [
    "White Alone", "Black or African American Alone", "American Indian and Alaska Native Alone", 
    "Asian Alone", "Native Hawaiian and Other Pacific Islander Alone", "Some Other Race Alone", 
    "Two or More Races", "Hispanic or Latino", "White Alone, Not Hispanic or Latino"
  ],
  education: [
    "Less than high school", "High school graduate", "Some college",
    "Associate degree", "Bachelor's degree", "Graduate degree"
  ],
  profession: [
    "Management, business, science, and arts occupations", 
    "Service occupations", 
    "Sales and office occupations", 
    "Natural resources, construction, and maintenance occupations", 
    "Production, transportation, and material moving occupations"
  ]
};

function BivariateProbability({ selectedLocation, locationName }) {
  const [selectedDistribution, setSelectedDistribution] = useState('gender_education');
  const [jointData, setJointData] = useState(null);
  const [conditionalData, setConditionalData] = useState(null);
  const [conditionType, setConditionType] = useState('');
  const [conditionValue, setConditionValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Reset conditional selections when distribution changes
  useEffect(() => {
    setConditionalData(null);
    setConditionType('');
    setConditionValue('');
    if (selectedLocation) {
      fetchJointDistribution();
    }
  }, [selectedDistribution, selectedLocation]);

  const fetchJointDistribution = async () => {
    if (!selectedLocation) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('http://localhost:5001/joint_probability', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lat: selectedLocation.lat,
          lng: selectedLocation.lng,
          distribution_type: selectedDistribution
        })
      });

      if (response.ok) {
        const data = await response.json();
        setJointData(data.joint_distribution);
        setConditionalData(null);
      } else {
        const errorData = await response.json();
        setError(errorData.message || errorData.error || 'Failed to fetch data');
        setJointData(null);
      }
    } catch (err) {
      setError('Failed to fetch joint distribution data');
      setJointData(null);
    } finally {
      setLoading(false);
    }
  };

  const fetchConditionalDistribution = async () => {
    if (!selectedLocation || !conditionType || !conditionValue || !jointData) return;
    
    setLoading(true);
    
    try {
      const response = await fetch('http://localhost:5001/joint_probability', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lat: selectedLocation.lat,
          lng: selectedLocation.lng,
          distribution_type: selectedDistribution,
          condition_type: conditionType,
          condition_value: conditionValue
        })
      });

      if (response.ok) {
        const data = await response.json();
        setConditionalData(data.conditional_distribution);
      } else {
        const errorData = await response.json();
        setError(errorData.message || errorData.error || 'Failed to fetch conditional data');
      }
    } catch (err) {
      setError('Failed to fetch conditional distribution data');
    } finally {
      setLoading(false);
    }
  };

  const handleConditionSubmit = () => {
    if (conditionType && conditionValue) {
      fetchConditionalDistribution();
    }
  };

  const config = JOINT_DISTRIBUTION_CONFIGS[selectedDistribution];

  return (
    <div style={{ 
      padding: '20px', 
      backgroundColor: '#1f2937', 
      color: '#f9fafb',
      minHeight: '100vh'
    }}>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ 
          fontSize: '24px', 
          fontWeight: 'bold', 
          marginBottom: '8px',
          color: '#319dff'
        }}>
          Bivariate Joint Probability Distributions
        </h1>
        {locationName && (
          <div style={{ color: '#008a89', fontSize: '14px' }}>
            📍 {locationName}
          </div>
        )}
      </div>

      {/* Distribution Selection */}
      <div style={{ marginBottom: '24px' }}>
        <label style={{ 
          display: 'block', 
          fontSize: '14px', 
          fontWeight: '500', 
          marginBottom: '8px',
          color: '#d1d5db'
        }}>
          Select Distribution Type:
        </label>
        
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
          gap: '12px',
          marginBottom: '16px'
        }}>
          {Object.entries(JOINT_DISTRIBUTION_CONFIGS).map(([key, config]) => (
            <button
              key={key}
              onClick={() => setSelectedDistribution(key)}
              style={{
                backgroundColor: selectedDistribution === key ? '#008a89' : '#374151',
                color: selectedDistribution === key ? '#ffffff' : '#f9fafb',
                border: `1px solid ${selectedDistribution === key ? '#008a89' : '#4b5563'}`,
                padding: '12px 16px',
                borderRadius: '8px',
                fontSize: '13px',
                fontWeight: '500',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
            >
              {config.title}
            </button>
          ))}
        </div>

        {/* Unavailable distributions */}
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: '500', marginBottom: '8px', color: '#9ca3af' }}>
            Unavailable (Data Not Available):
          </h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {Object.entries(UNAVAILABLE_DISTRIBUTIONS).map(([key, title]) => (
              <div
                key={key}
                style={{
                  backgroundColor: '#4b5563',
                  color: '#9ca3af',
                  border: '1px solid #6b7280',
                  padding: '8px 12px',  
                  borderRadius: '6px',
                  fontSize: '12px',
                  fontStyle: 'italic'
                }}
              >
                {title}
              </div>
            ))}
          </div>
        </div>
      </div>

      {selectedLocation ? (
        <>
          {loading && (
            <div style={{ 
              textAlign: 'center', 
              padding: '40px',
              color: '#9ca3af'
            }}>
              Loading distribution data...
            </div>
          )}

          {error && (
            <div style={{ 
              backgroundColor: '#7f1d1d', 
              color: '#fecaca', 
              padding: '16px', 
              borderRadius: '8px',
              marginBottom: '20px'
            }}>
              <strong>Error:</strong> {error}
            </div>
          )}

          {jointData && !loading && (
            <>
              {/* Joint Distribution Display */}
              <div style={{ marginBottom: '32px' }}>
                <h2 style={{ 
                  fontSize: '18px', 
                  fontWeight: '600', 
                  marginBottom: '16px',
                  color: config?.color || '#319dff'
                }}>
                  {config?.title} Joint Distribution
                </h2>
                
                {/* Marginal Distributions */}
                <div style={{ 
                  display: 'grid', 
                  gridTemplateColumns: '1fr 1fr', 
                  gap: '20px',
                  marginBottom: '24px'
                }}>
                  {/* First Marginal */}
                  {jointData[`${config?.variables[0]}_marginal`] && (
                    <div style={{ 
                      backgroundColor: '#374151', 
                      padding: '16px', 
                      borderRadius: '8px'
                    }}>
                      <h3 style={{ 
                        fontSize: '14px', 
                        fontWeight: '500', 
                        marginBottom: '12px',
                        color: config?.color || '#319dff'
                      }}>
                        {config?.variables[0].charAt(0).toUpperCase() + config?.variables[0].slice(1)} Distribution
                      </h3>
                      <ResponsiveContainer width="100%" height={200}>
                        <BarChart data={jointData[`${config?.variables[0]}_marginal`]}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#4b5563" />
                          <XAxis 
                            dataKey="category" 
                            stroke="#9ca3af"
                            fontSize={11}
                            angle={-45}
                            textAnchor="end"
                            height={60}
                          />
                          <YAxis stroke="#9ca3af" fontSize={11} />
                          <Tooltip 
                            contentStyle={{ 
                              backgroundColor: '#1f2937', 
                              border: '1px solid #4b5563',
                              borderRadius: '4px'
                            }}
                          />
                          <Bar 
                            dataKey="value" 
                            fill={config?.color || '#319dff'} 
                            opacity={0.8}
                          />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  )}

                  {/* Second Marginal */}
                  {jointData[`${config?.variables[1]}_marginal`] && (
                    <div style={{ 
                      backgroundColor: '#374151', 
                      padding: '16px', 
                      borderRadius: '8px'
                    }}>
                      <h3 style={{ 
                        fontSize: '14px', 
                        fontWeight: '500', 
                        marginBottom: '12px',
                        color: config?.color || '#319dff'
                      }}>
                        {config?.variables[1].charAt(0).toUpperCase() + config?.variables[1].slice(1)} Distribution
                      </h3>
                      <ResponsiveContainer width="100%" height={200}>
                        <BarChart data={jointData[`${config?.variables[1]}_marginal`]}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#4b5563" />
                          <XAxis 
                            dataKey="category" 
                            stroke="#9ca3af"
                            fontSize={11}
                            angle={-45}
                            textAnchor="end"
                            height={60}
                          />
                          <YAxis stroke="#9ca3af" fontSize={11} />
                          <Tooltip 
                            contentStyle={{ 
                              backgroundColor: '#1f2937', 
                              border: '1px solid #4b5563',
                              borderRadius: '4px'
                            }}
                          />
                          <Bar 
                            dataKey="value" 
                            fill={config?.color || '#319dff'} 
                            opacity={0.6}
                          />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  )}
                </div>

                {/* Conditional Distribution Controls */}
                <div style={{ 
                  backgroundColor: '#374151', 
                  padding: '16px', 
                  borderRadius: '8px',
                  marginBottom: '20px'
                }}>
                  <h3 style={{ 
                    fontSize: '16px', 
                    fontWeight: '500', 
                    marginBottom: '16px',
                    color: '#f9fafb'
                  }}>
                    Conditional Distribution
                  </h3>
                  
                  <div style={{ 
                    display: 'grid', 
                    gridTemplateColumns: '1fr 1fr 120px', 
                    gap: '12px',
                    alignItems: 'end'
                  }}>
                    <div>
                      <label style={{ 
                        display: 'block', 
                        fontSize: '12px', 
                        fontWeight: '500', 
                        marginBottom: '6px',
                        color: '#d1d5db'
                      }}>
                        Condition on:
                      </label>
                      <select
                        value={conditionType}
                        onChange={(e) => {
                          setConditionType(e.target.value);
                          setConditionValue('');
                          setConditionalData(null);
                        }}
                        style={{
                          width: '100%',
                          padding: '8px 12px',
                          backgroundColor: '#1f2937',
                          border: '1px solid #4b5563',
                          borderRadius: '6px',
                          color: '#f9fafb',
                          fontSize: '14px'
                        }}
                      >
                        <option value="">Select variable...</option>
                        {config?.variables.map(variable => (
                          <option key={variable} value={variable}>
                            {variable.charAt(0).toUpperCase() + variable.slice(1)}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label style={{ 
                        display: 'block', 
                        fontSize: '12px', 
                        fontWeight: '500', 
                        marginBottom: '6px',
                        color: '#d1d5db'
                      }}>
                        Value:
                      </label>
                      <select
                        value={conditionValue}
                        onChange={(e) => setConditionValue(e.target.value)}
                        disabled={!conditionType}
                        style={{
                          width: '100%',
                          padding: '8px 12px',
                          backgroundColor: conditionType ? '#1f2937' : '#374151',
                          border: '1px solid #4b5563',
                          borderRadius: '6px',
                          color: conditionType ? '#f9fafb' : '#9ca3af',
                          fontSize: '14px'
                        }}
                      >
                        <option value="">Select value...</option>
                        {conditionType && (() => {
                          let options = [];
                          if (selectedDistribution === 'age_income' && DISTRIBUTION_OPTIONS.age_income[conditionType]) {
                            options = DISTRIBUTION_OPTIONS.age_income[conditionType];
                          } else if (selectedDistribution === 'age_education' && DISTRIBUTION_OPTIONS.age_education[conditionType]) {
                            options = DISTRIBUTION_OPTIONS.age_education[conditionType];
                          } else if (selectedDistribution === 'education_sex' && DISTRIBUTION_OPTIONS.education_sex[conditionType]) {
                            options = DISTRIBUTION_OPTIONS.education_sex[conditionType];
                          } else {
                            options = CONDITIONAL_OPTIONS[conditionType] || [];
                          }
                          return options.map(option => (
                            <option key={option} value={option}>
                              {option}
                            </option>
                          ));
                        })()}
                      </select>
                    </div>

                    <button
                      onClick={handleConditionSubmit}
                      disabled={!conditionType || !conditionValue || loading}
                      style={{
                        padding: '8px 16px',
                        backgroundColor: (conditionType && conditionValue && !loading) ? '#008a89' : '#4b5563',
                        color: (conditionType && conditionValue && !loading) ? '#ffffff' : '#9ca3af',
                        border: 'none',
                        borderRadius: '6px',
                        fontSize: '14px',
                        fontWeight: '500',
                        cursor: (conditionType && conditionValue && !loading) ? 'pointer' : 'not-allowed'
                      }}
                    >
                      Calculate
                    </button>
                  </div>
                </div>

                {/* Conditional Distribution Results */}
                {conditionalData && (
                  <div style={{ 
                    backgroundColor: '#374151', 
                    padding: '16px', 
                    borderRadius: '8px'
                  }}>
                    <h3 style={{ 
                      fontSize: '14px', 
                      fontWeight: '500', 
                      marginBottom: '12px',
                      color: config?.color || '#319dff'
                    }}>
                      {conditionalData.condition}
                    </h3>
                    
                    {/* Show special handling for median values */}
                    {conditionalData.data && conditionalData.data.length > 0 && conditionalData.data[0].median_earnings ? (
                      <div style={{ 
                        fontSize: '14px', 
                        color: '#f9fafb', 
                        textAlign: 'center',
                        padding: '20px'
                      }}>
                        <div style={{ marginBottom: '8px' }}>
                          <strong>Median Earnings:</strong>
                        </div>
                        <div style={{ fontSize: '24px', color: config?.color || '#319dff' }}>
                          ${conditionalData.data[0].median_earnings.toLocaleString()}
                        </div>
                      </div>
                    ) : (
                      <ResponsiveContainer width="100%" height={250}>
                        <BarChart data={conditionalData.data}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#4b5563" />
                          <XAxis 
                            dataKey="category" 
                            stroke="#9ca3af"
                            fontSize={10}
                            angle={-45}
                            textAnchor="end"
                            height={80}
                            tickFormatter={(value) => {
                              // Truncate long category names for display
                              return value.length > 20 ? value.substring(0, 20) + '...' : value;
                            }}
                          />
                          <YAxis stroke="#9ca3af" fontSize={11} />
                          <Tooltip 
                            contentStyle={{ 
                              backgroundColor: '#1f2937', 
                              border: '1px solid #4b5563',
                              borderRadius: '4px'
                            }}
                            formatter={(value, name) => {
                              if (name === 'percentage') {
                                return [`${value.toFixed(1)}%`, 'Percentage'];
                              }
                              if (name === 'median_earnings') {
                                return [`$${value.toLocaleString()}`, 'Median Earnings'];
                              }
                              return [value, name];
                            }}
                            labelFormatter={(label) => label} // Show full category name in tooltip
                          />
                          <Bar 
                            dataKey="percentage" 
                            fill={config?.color || '#319dff'} 
                            opacity={0.9}
                          />
                        </BarChart>
                      </ResponsiveContainer>
                    )}
                  </div>
                )}
                
                {/* Data Source */}
                <div style={{ 
                  marginTop: '16px', 
                  fontSize: '12px', 
                  color: '#9ca3af',
                  textAlign: 'center'
                }}>
                  Data Source: {jointData.data_source}
                </div>
              </div>
            </>
          )}
        </>
      ) : (
        <div style={{ 
          textAlign: 'center', 
          padding: '60px 20px',
          color: '#9ca3af'
        }}>
          <h2 style={{ fontSize: '18px', marginBottom: '8px' }}>
            Select a Location
          </h2>
          <p style={{ fontSize: '14px' }}>
            Click on the map to select a location and view bivariate joint probability distributions
          </p>
        </div>
      )}
    </div>
  );
}

export default BivariateProbability;