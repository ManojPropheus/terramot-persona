import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

// Available unified analysis types
const UNIFIED_ANALYSIS_TYPES = {
  age: {
    name: 'Age Analysis',
    description: 'Analyze demographics by age ranges',
    color: '#008a89',
    endpoint: '/unified_age_analysis',
    paramKey: 'age_range',
    options: [
      "Under 5 years", "5 to 9 years", "10 to 14 years", "15 to 17 years",
      "18 to 24 years", "25 to 34 years", "35 to 44 years", "45 to 64 years",
      "65 years and over", "Under 18 years", "18 to 34 years"
    ]
  },
  education: {
    name: 'Education Analysis',
    description: 'Analyze demographics by education level',
    color: '#319dff',
    endpoint: '/unified_education_analysis',
    paramKey: 'education_level',
    options: [
      "Less than 9th grade", "9th to 12th grade, no diploma", 
      "High school graduate", "Some college, no degree", "Associate's degree",
      "Bachelor's degree", "Graduate or professional degree"
    ]
  },
  income: {
    name: 'Income Analysis',
    description: 'Analyze demographics by income range',
    color: '#f97316',
    endpoint: '/unified_income_analysis', 
    paramKey: 'income_range',
    options: [
      "$25,000 to $29,999", "$30,000 to $34,999", "$35,000 to $39,999",
      "$45,000 to $49,999", "$50,000 to $59,999", "$60,000 to $74,999",
      "$75,000 to $99,999", "$100,000 to $124,999", "$150,000 to $199,999"
    ]
  },
  gender: {
    name: 'Gender Analysis',
    description: 'Analyze demographics by gender',
    color: '#06b6d4',
    endpoint: '/unified_gender_analysis',
    paramKey: 'gender',
    options: ["Male", "Female"]
  },
  profession: {
    name: 'Profession Analysis',
    description: 'Analyze demographics by profession/occupation',
    color: '#8b5cf6',
    endpoint: '/unified_profession_analysis',
    paramKey: 'profession',
    options: [
      "Management, business, science, and arts occupations",
      "Service occupations",
      "Sales and office occupations",
      "Natural resources, construction, and maintenance occupations",
      "Production, transportation, and material moving occupations",
      "Management, business, and financial occupations",
      "Professional and related occupations",
      "Healthcare practitioners and technical occupations"
    ]
  },
  race: {
    name: 'Race/Ethnicity Analysis',
    description: 'Analyze demographics by race/ethnicity',
    color: '#ec4899',
    endpoint: '/unified_race_analysis',
    paramKey: 'race',
    options: [
      "White alone", "Black or African American alone", "Asian alone",
      "American Indian and Alaska Native alone", "Native Hawaiian and Other Pacific Islander alone",
      "Hispanic or Latino", "Two or more races", "White alone, not Hispanic or Latino"
    ]
  }
};

// Colors for different distribution types
const DISTRIBUTION_COLORS = {
  age: '#008a89',
  gender: '#f97316',
  sex: '#f97316', 
  education: '#319dff',
  income: '#06b6d4',
  race: '#10b981',
  profession: '#8b5cf6'
};

const getStatusColor = (status) => {
  switch (status) {
    case 'success': return '#10b981';
    case 'no_data': return '#6b7280';
    case 'no_match': return '#f59e0b';
    case 'error': return '#ef4444';
    default: return '#6b7280';
  }
};

const getStatusText = (status) => {
  switch (status) {
    case 'success': return '✓ Available';
    case 'no_data': return '⚠ No Data';
    case 'no_match': return '⚠ No Match';
    case 'error': return '✗ Error';
    default: return '? Unknown';
  }
};

const getSimilarityIndicator = (score) => {
  if (score >= 0.95) return { text: "Perfect Match", color: "#10b981" };
  if (score >= 0.8) return { text: "Very Good", color: "#059669" };
  if (score >= 0.5) return { text: "Good Match", color: "#fbbf24" };
  if (score >= 0.3) return { text: "Partial", color: "#f59e0b" };
  return { text: "Limited", color: "#ef4444" };
};

function UnifiedDemographicAnalysis({ selectedLocation, locationName }) {
  const [selectedAnalysisType, setSelectedAnalysisType] = useState('age');
  const [selectedValue, setSelectedValue] = useState('25 to 34 years');
  const [analysisData, setAnalysisData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [customValue, setCustomValue] = useState('');
  const [showCustomInput, setShowCustomInput] = useState(false);

  // Update default value when analysis type changes
  useEffect(() => {
    const analysisConfig = UNIFIED_ANALYSIS_TYPES[selectedAnalysisType];
    if (analysisConfig && analysisConfig.options.length > 0) {
      setSelectedValue(analysisConfig.options[0]);
    }
    setAnalysisData(null);
  }, [selectedAnalysisType]);

  // Fetch analysis when location, type, or value changes
  useEffect(() => {
    if (selectedLocation && selectedAnalysisType && selectedValue) {
      fetchUnifiedAnalysis();
    }
  }, [selectedLocation, selectedAnalysisType, selectedValue]);

  const fetchUnifiedAnalysis = async () => {
    if (!selectedLocation || !selectedAnalysisType || !selectedValue) return;
    
    setLoading(true);
    setError(null);
    
    const analysisConfig = UNIFIED_ANALYSIS_TYPES[selectedAnalysisType];
    
    try {
      const requestBody = {
        lat: selectedLocation.lat,
        lng: selectedLocation.lng,
        [analysisConfig.paramKey]: selectedValue
      };

      const response = await fetch(`http://localhost:5001${analysisConfig.endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });

      if (response.ok) {
        const data = await response.json();
        setAnalysisData(data);
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to fetch analysis');
        setAnalysisData(null);
      }
    } catch (err) {
      setError(`Failed to fetch ${analysisConfig.name.toLowerCase()} analysis data`);
      setAnalysisData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleCustomValueSubmit = () => {
    if (customValue.trim()) {
      setSelectedValue(customValue.trim());
      setShowCustomInput(false);
      setCustomValue('');
    }
  };

  const renderDistributionChart = (distributionKey, distributionData) => {
    if (distributionData.status !== 'success') return null;

    const chartData = distributionData.conditional_distribution.data.map(item => ({
      ...item,
      name: item.category
    }));

    // Get similarity/overlap indicator
    const score = distributionData.similarity_score || distributionData.overlap_score || 1.0;
    const indicator = getSimilarityIndicator(score);

    return (
      <div key={distributionKey} style={{ marginBottom: '32px' }}>
        <div style={{ 
          backgroundColor: '#374151', 
          padding: '16px', 
          borderRadius: '8px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h3 style={{ 
              fontSize: '16px', 
              fontWeight: '500', 
              color: DISTRIBUTION_COLORS[distributionKey] || '#f9fafb',
              margin: 0
            }}>
              {distributionData.name}
            </h3>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <div style={{ 
                fontSize: '11px', 
                color: indicator.color,
                fontWeight: '500',
                padding: '2px 6px',
                backgroundColor: `${indicator.color}20`,
                borderRadius: '4px'
              }}>
                {indicator.text}
              </div>
              <div style={{ 
                fontSize: '12px', 
                color: getStatusColor(distributionData.status),
                fontWeight: '500'
              }}>
                {getStatusText(distributionData.status)}
              </div>
            </div>
          </div>
          
          {/* Mapping info */}
          <div style={{ 
            backgroundColor: '#1f2937', 
            padding: '8px 12px', 
            borderRadius: '6px', 
            marginBottom: '16px',
            fontSize: '12px'
          }}>
            <div style={{ color: '#9ca3af', marginBottom: '4px' }}>
              <strong>Mapping:</strong>
            </div>
            <div style={{ color: '#f9fafb' }}>
              Requested: <span style={{ color: UNIFIED_ANALYSIS_TYPES[selectedAnalysisType].color }}>
                {analysisData[`target_${selectedAnalysisType}`] || selectedValue}
              </span>
            </div>
            <div style={{ color: '#f9fafb' }}>
              Matched: <span style={{ color: '#10b981' }}>
                {distributionData[`matched_${selectedAnalysisType}`] || distributionData.matched_gender || distributionData.matched_income || distributionData.matched_education || distributionData.matched_age_range || 'Unknown'}
              </span>
            </div>
            <div style={{ color: '#f59e0b', fontSize: '11px', marginTop: '4px' }}>
              {distributionData[`${selectedAnalysisType}_explanation`] || distributionData.gender_explanation || distributionData.income_explanation || distributionData.education_explanation || distributionData.range_explanation || 'Matched'}
            </div>
          </div>

          {/* Population info */}
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            marginBottom: '16px',
            fontSize: '14px',
            color: '#d1d5db'
          }}>
            <span>Population: <strong>{distributionData.total_population.toLocaleString()}</strong></span>
            <span>Categories: <strong>{chartData.length}</strong></span>
          </div>

          {/* Chart */}
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 80 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#4b5563" />
              <XAxis 
                dataKey="name" 
                stroke="#9ca3af"
                fontSize={10}
                angle={-45}
                textAnchor="end"
                height={80}
                tickFormatter={(value) => {
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
                  return [value, name];
                }}
                labelFormatter={(label) => label}
              />
              <Bar dataKey="percentage" fill={DISTRIBUTION_COLORS[distributionKey] || UNIFIED_ANALYSIS_TYPES[selectedAnalysisType].color}>
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={DISTRIBUTION_COLORS[distributionKey] || UNIFIED_ANALYSIS_TYPES[selectedAnalysisType].color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>

          {/* Data source */}
          <div style={{ 
            fontSize: '11px', 
            color: '#6b7280',
            textAlign: 'center',
            marginTop: '8px'
          }}>
            Source: {distributionData.data_source || 'Unknown'}
          </div>
        </div>
      </div>
    );
  };

  const renderFailedDistribution = (distributionKey, distributionData) => {
    return (
      <div key={distributionKey} style={{ 
        backgroundColor: '#374151', 
        padding: '16px', 
        borderRadius: '8px',
        marginBottom: '16px',
        opacity: 0.7
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ 
            fontSize: '16px', 
            fontWeight: '500', 
            color: '#9ca3af',
            margin: 0
          }}>
            {distributionData.name}
          </h3>
          <div style={{ 
            fontSize: '12px', 
            color: getStatusColor(distributionData.status),
            fontWeight: '500'
          }}>
            {getStatusText(distributionData.status)}
          </div>
        </div>
        <div style={{ 
          fontSize: '12px', 
          color: '#ef4444',
          marginTop: '8px'
        }}>
          {distributionData.error || 'Unable to retrieve data'}
        </div>
      </div>
    );
  };

  const analysisConfig = UNIFIED_ANALYSIS_TYPES[selectedAnalysisType];

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
          color: '#f9fafb'
        }}>
          Unified Demographic Analysis
        </h1>
        <p style={{ 
          fontSize: '14px', 
          color: '#9ca3af',
          marginBottom: '8px'
        }}>
          Comprehensive demographic analysis combining multiple bivariate distributions
        </p>
        {locationName && (
          <div style={{ color: analysisConfig.color, fontSize: '14px' }}>
            📍 {locationName}
          </div>
        )}
      </div>

      {/* Analysis Type Selection */}
      <div style={{ 
        backgroundColor: '#374151', 
        padding: '20px', 
        borderRadius: '8px',
        marginBottom: '24px'
      }}>
        <h2 style={{ 
          fontSize: '18px', 
          fontWeight: '500', 
          marginBottom: '16px',
          color: '#f9fafb'
        }}>
          Select Analysis Type
        </h2>
        
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
          gap: '12px',
          marginBottom: '24px'
        }}>
          {Object.entries(UNIFIED_ANALYSIS_TYPES).map(([key, config]) => (
            <button
              key={key}
              onClick={() => setSelectedAnalysisType(key)}
              style={{
                backgroundColor: selectedAnalysisType === key ? config.color : '#4b5563',
                color: '#ffffff',
                border: `2px solid ${selectedAnalysisType === key ? config.color : '#6b7280'}`,
                padding: '16px',
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                textAlign: 'left'
              }}
            >
              <div style={{ fontSize: '16px', marginBottom: '4px' }}>{config.name}</div>
              <div style={{ fontSize: '12px', opacity: 0.9 }}>{config.description}</div>
            </button>
          ))}
        </div>

        <h3 style={{ 
          fontSize: '16px', 
          fontWeight: '500', 
          marginBottom: '12px',
          color: analysisConfig.color
        }}>
          Select {analysisConfig.name.replace(' Analysis', '')} Value
        </h3>
        
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', 
          gap: '8px',
          marginBottom: '16px'
        }}>
          {analysisConfig.options.map((option) => (
            <button
              key={option}
              onClick={() => setSelectedValue(option)}
              style={{
                backgroundColor: selectedValue === option ? analysisConfig.color : '#4b5563',
                color: '#ffffff',
                border: `1px solid ${selectedValue === option ? analysisConfig.color : '#6b7280'}`,
                padding: '10px 12px',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: '500',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                textAlign: 'left'
              }}
            >
              {option}
            </button>
          ))}
        </div>

        {/* Custom value input */}
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button
            onClick={() => setShowCustomInput(!showCustomInput)}
            style={{
              backgroundColor: '#4b5563',
              color: '#f9fafb',
              border: '1px solid #6b7280',
              padding: '8px 12px',
              borderRadius: '6px',
              fontSize: '12px',
              cursor: 'pointer'
            }}
          >
            {showCustomInput ? 'Hide Custom' : 'Custom Value'}
          </button>
          
          {showCustomInput && (
            <>
              <input
                type="text"
                value={customValue}
                onChange={(e) => setCustomValue(e.target.value)}
                placeholder={`e.g., ${analysisConfig.options[Math.floor(Math.random() * analysisConfig.options.length)]}`}
                style={{
                  backgroundColor: '#1f2937',
                  border: '1px solid #4b5563',
                  borderRadius: '6px',
                  padding: '8px 12px',
                  color: '#f9fafb',
                  fontSize: '12px',
                  width: '250px'
                }}
              />
              <button
                onClick={handleCustomValueSubmit}
                disabled={!customValue.trim()}
                style={{
                  backgroundColor: customValue.trim() ? analysisConfig.color : '#4b5563',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '8px 16px',
                  fontSize: '12px',
                  cursor: customValue.trim() ? 'pointer' : 'not-allowed'
                }}
              >
                Analyze
              </button>
            </>
          )}
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
              <div style={{ color: analysisConfig.color, fontSize: '18px', marginBottom: '8px' }}>
                Loading {analysisConfig.name.toLowerCase()}...
              </div>
              <div style={{ fontSize: '14px' }}>
                Analyzing {selectedValue}
              </div>
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

          {analysisData && !loading && (
            <>
              {/* Summary */}
              <div style={{ 
                backgroundColor: '#374151', 
                padding: '16px', 
                borderRadius: '8px',
                marginBottom: '24px'
              }}>
                <h2 style={{ 
                  fontSize: '18px', 
                  fontWeight: '500', 
                  marginBottom: '12px',
                  color: '#f9fafb'
                }}>
                  Analysis Summary
                </h2>
                <div style={{ 
                  display: 'grid', 
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
                  gap: '16px'
                }}>
                  <div>
                    <div style={{ color: '#9ca3af', fontSize: '12px' }}>Target {analysisConfig.name.replace(' Analysis', '')}</div>
                    <div style={{ color: analysisConfig.color, fontSize: '14px', fontWeight: '500' }}>
                      {selectedValue}
                    </div>
                  </div>
                  <div>
                    <div style={{ color: '#9ca3af', fontSize: '12px' }}>Available Distributions</div>
                    <div style={{ color: '#10b981', fontSize: '14px', fontWeight: '500' }}>
                      {analysisData.metadata.successful_retrievals} of {analysisData.metadata.total_distributions}
                    </div>
                  </div>
                  <div>
                    <div style={{ color: '#9ca3af', fontSize: '12px' }}>Location</div>
                    <div style={{ color: '#f9fafb', fontSize: '14px' }}>
                      {analysisData.location_details?.county_name || 'Unknown'}, {analysisData.location_details?.state_name || 'Unknown'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Distribution Charts */}
              <div>
                {Object.entries(analysisData.distributions).map(([key, data]) => {
                  if (data.status === 'success') {
                    return renderDistributionChart(key, data);
                  } else {
                    return renderFailedDistribution(key, data);
                  }
                })}
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
            Click on the map to select a location and analyze comprehensive demographic distributions
          </p>
        </div>
      )}
    </div>
  );
}

export default UnifiedDemographicAnalysis;