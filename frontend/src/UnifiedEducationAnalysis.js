import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

// Common education levels that users might want to analyze
const COMMON_EDUCATION_LEVELS = [
  "Less than 9th grade",
  "9th to 12th grade, no diploma", 
  "High school graduate",
  "Some college, no degree",
  "Associate's degree",
  "Bachelor's degree",
  "Graduate or professional degree",
  // Simplified versions
  "Less than high school",
  "High school graduate (includes equivalency)",
  "Some college",
  "Associate degree",
  "Graduate degree"
];

// Colors for different distribution types
const DISTRIBUTION_COLORS = {
  age: '#319dff',
  race: '#06b6d4',
  sex: '#f97316'
};

// Status indicators
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
  if (score >= 0.8) return { text: "Very Good Match", color: "#059669" };
  if (score >= 0.6) return { text: "Good Match", color: "#fbbf24" };
  if (score >= 0.4) return { text: "Moderate Match", color: "#f59e0b" };
  return { text: "Limited Match", color: "#ef4444" };
};

function UnifiedEducationAnalysis({ selectedLocation, locationName }) {
  const [selectedEducation, setSelectedEducation] = useState("Bachelor's degree");
  const [analysisData, setAnalysisData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [customEducation, setCustomEducation] = useState('');
  const [showCustomInput, setShowCustomInput] = useState(false);

  // Fetch analysis when location or education changes
  useEffect(() => {
    if (selectedLocation && selectedEducation) {
      fetchUnifiedAnalysis();
    }
  }, [selectedLocation, selectedEducation]);

  const fetchUnifiedAnalysis = async () => {
    if (!selectedLocation || !selectedEducation) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('http://localhost:5001/unified_education_analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lat: selectedLocation.lat,
          lng: selectedLocation.lng,
          education_level: selectedEducation
        })
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
      setError('Failed to fetch unified education analysis data');
      setAnalysisData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleCustomEducationSubmit = () => {
    if (customEducation.trim()) {
      setSelectedEducation(customEducation.trim());
      setShowCustomInput(false);
      setCustomEducation('');
    }
  };

  const renderDistributionChart = (distributionKey, distributionData) => {
    if (distributionData.status !== 'success') return null;

    const chartData = distributionData.conditional_distribution.data.map(item => ({
      ...item,
      name: item.category
    }));

    const similarity = getSimilarityIndicator(distributionData.similarity_score);

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
                color: similarity.color,
                fontWeight: '500',
                padding: '2px 6px',
                backgroundColor: `${similarity.color}20`,
                borderRadius: '4px'
              }}>
                {similarity.text}
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
          
          {/* Education mapping info */}
          <div style={{ 
            backgroundColor: '#1f2937', 
            padding: '8px 12px', 
            borderRadius: '6px', 
            marginBottom: '16px',
            fontSize: '12px'
          }}>
            <div style={{ color: '#9ca3af', marginBottom: '4px' }}>
              <strong>Education Level Mapping:</strong>
            </div>
            <div style={{ color: '#f9fafb' }}>
              Requested: <span style={{ color: '#008a89' }}>{analysisData.target_education}</span>
            </div>
            <div style={{ color: '#f9fafb' }}>
              Matched: <span style={{ color: '#10b981' }}>{distributionData.matched_education}</span>
            </div>
            <div style={{ color: '#f59e0b', fontSize: '11px', marginTop: '4px' }}>
              {distributionData.education_explanation}
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
            <span>Population with Education: <strong>{distributionData.total_population.toLocaleString()}</strong></span>
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
              <Bar dataKey="percentage" fill={DISTRIBUTION_COLORS[distributionKey] || '#008a89'}>
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={DISTRIBUTION_COLORS[distributionKey] || '#008a89'} />
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
        {distributionData.matched_education && (
          <div style={{ 
            fontSize: '11px', 
            color: '#6b7280',
            marginTop: '4px'
          }}>
            Best match found: {distributionData.matched_education}
          </div>
        )}
      </div>
    );
  };

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
          color: '#008a89'
        }}>
          Unified Education Distribution Analysis
        </h1>
        <p style={{ 
          fontSize: '14px', 
          color: '#9ca3af',
          marginBottom: '8px'
        }}>
          Comprehensive education-based demographic analysis combining multiple bivariate distributions
        </p>
        {locationName && (
          <div style={{ color: '#319dff', fontSize: '14px' }}>
            📍 {locationName}
          </div>
        )}
      </div>

      {/* Education Level Selection */}
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
          Select Education Level to Analyze
        </h2>
        
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', 
          gap: '8px',
          marginBottom: '16px'
        }}>
          {COMMON_EDUCATION_LEVELS.map((education) => (
            <button
              key={education}
              onClick={() => setSelectedEducation(education)}
              style={{
                backgroundColor: selectedEducation === education ? '#008a89' : '#4b5563',
                color: selectedEducation === education ? '#ffffff' : '#f9fafb',
                border: `1px solid ${selectedEducation === education ? '#008a89' : '#6b7280'}`,
                padding: '10px 12px',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: '500',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                textAlign: 'left'
              }}
            >
              {education}
            </button>
          ))}
        </div>

        {/* Custom education input */}
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
            {showCustomInput ? 'Hide Custom' : 'Custom Level'}
          </button>
          
          {showCustomInput && (
            <>
              <input
                type="text"
                value={customEducation}
                onChange={(e) => setCustomEducation(e.target.value)}
                placeholder="e.g., Master's degree"
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
                onClick={handleCustomEducationSubmit}
                disabled={!customEducation.trim()}
                style={{
                  backgroundColor: customEducation.trim() ? '#008a89' : '#4b5563',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '8px 16px',
                  fontSize: '12px',
                  cursor: customEducation.trim() ? 'pointer' : 'not-allowed'
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
              Loading unified education analysis...
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
                    <div style={{ color: '#9ca3af', fontSize: '12px' }}>Target Education Level</div>
                    <div style={{ color: '#008a89', fontSize: '14px', fontWeight: '500' }}>
                      {analysisData.target_education}
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
            Click on the map to select a location and analyze education-based demographic distributions
          </p>
        </div>
      )}
    </div>
  );
}

export default UnifiedEducationAnalysis;