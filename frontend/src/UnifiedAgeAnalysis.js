import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

// Common age ranges that users might want to analyze
const COMMON_AGE_RANGES = [
  "Under 5 years",
  "5 to 9 years", 
  "10 to 14 years",
  "15 to 17 years",
  "18 to 24 years",
  "25 to 34 years",
  "35 to 44 years",
  "45 to 64 years",
  "65 years and over",
  "Under 18 years",
  "18 to 34 years",
  "35 to 64 years"
];

// Colors for different distribution types
const DISTRIBUTION_COLORS = {
  income: '#319dff',
  gender: '#f97316', 
  education: '#008a89',
  race: '#06b6d4'
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

function UnifiedAgeAnalysis({ selectedLocation, locationName }) {
  const [selectedAgeRange, setSelectedAgeRange] = useState('25 to 34 years');
  const [analysisData, setAnalysisData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [customAgeRange, setCustomAgeRange] = useState('');
  const [showCustomInput, setShowCustomInput] = useState(false);

  // Fetch analysis when location or age range changes
  useEffect(() => {
    if (selectedLocation && selectedAgeRange) {
      fetchUnifiedAnalysis();
    }
  }, [selectedLocation, selectedAgeRange]);

  const fetchUnifiedAnalysis = async () => {
    if (!selectedLocation || !selectedAgeRange) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('http://localhost:5001/unified_age_analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lat: selectedLocation.lat,
          lng: selectedLocation.lng,
          age_range: selectedAgeRange
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
      setError('Failed to fetch unified age analysis data');
      setAnalysisData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleCustomAgeSubmit = () => {
    if (customAgeRange.trim()) {
      setSelectedAgeRange(customAgeRange.trim());
      setShowCustomInput(false);
      setCustomAgeRange('');
    }
  };

  const renderDistributionChart = (distributionKey, distributionData) => {
    if (distributionData.status !== 'success') return null;

    const chartData = distributionData.conditional_distribution.data.map(item => ({
      ...item,
      name: item.category
    }));

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
            <div style={{ 
              fontSize: '12px', 
              color: getStatusColor(distributionData.status),
              fontWeight: '500'
            }}>
              {getStatusText(distributionData.status)}
            </div>
          </div>
          
          {/* Age range mapping info */}
          <div style={{ 
            backgroundColor: '#1f2937', 
            padding: '8px 12px', 
            borderRadius: '6px', 
            marginBottom: '16px',
            fontSize: '12px'
          }}>
            <div style={{ color: '#9ca3af', marginBottom: '4px' }}>
              <strong>Age Range Mapping:</strong>
            </div>
            <div style={{ color: '#f9fafb' }}>
              Requested: <span style={{ color: '#319dff' }}>{analysisData.target_age_range}</span>
            </div>
            <div style={{ color: '#f9fafb' }}>
              Matched: <span style={{ color: '#10b981' }}>{distributionData.matched_age_range}</span>
            </div>
            <div style={{ color: '#f59e0b', fontSize: '11px', marginTop: '4px' }}>
              {distributionData.range_explanation}
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
            <span>Population in Age Group: <strong>{distributionData.total_population.toLocaleString()}</strong></span>
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
              <Bar dataKey="percentage" fill={DISTRIBUTION_COLORS[distributionKey] || '#319dff'}>
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={DISTRIBUTION_COLORS[distributionKey] || '#319dff'} />
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
          Unified Age Distribution Analysis
        </h1>
        <p style={{ 
          fontSize: '14px', 
          color: '#9ca3af',
          marginBottom: '8px'
        }}>
          Comprehensive age-based demographic analysis combining multiple bivariate distributions
        </p>
        {locationName && (
          <div style={{ color: '#008a89', fontSize: '14px' }}>
            📍 {locationName}
          </div>
        )}
      </div>

      {/* Age Range Selection */}
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
          Select Age Range to Analyze
        </h2>
        
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', 
          gap: '8px',
          marginBottom: '16px'
        }}>
          {COMMON_AGE_RANGES.map((ageRange) => (
            <button
              key={ageRange}
              onClick={() => setSelectedAgeRange(ageRange)}
              style={{
                backgroundColor: selectedAgeRange === ageRange ? '#008a89' : '#4b5563',
                color: selectedAgeRange === ageRange ? '#ffffff' : '#f9fafb',
                border: `1px solid ${selectedAgeRange === ageRange ? '#008a89' : '#6b7280'}`,
                padding: '10px 12px',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: '500',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
            >
              {ageRange}
            </button>
          ))}
        </div>

        {/* Custom age range input */}
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
            {showCustomInput ? 'Hide Custom' : 'Custom Range'}
          </button>
          
          {showCustomInput && (
            <>
              <input
                type="text"
                value={customAgeRange}
                onChange={(e) => setCustomAgeRange(e.target.value)}
                placeholder="e.g., 30 to 40 years"
                style={{
                  backgroundColor: '#1f2937',
                  border: '1px solid #4b5563',
                  borderRadius: '6px',
                  padding: '8px 12px',
                  color: '#f9fafb',
                  fontSize: '12px',
                  width: '200px'
                }}
              />
              <button
                onClick={handleCustomAgeSubmit}
                disabled={!customAgeRange.trim()}
                style={{
                  backgroundColor: customAgeRange.trim() ? '#008a89' : '#4b5563',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '8px 16px',
                  fontSize: '12px',
                  cursor: customAgeRange.trim() ? 'pointer' : 'not-allowed'
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
              Loading unified age analysis...
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
                    <div style={{ color: '#9ca3af', fontSize: '12px' }}>Target Age Range</div>
                    <div style={{ color: '#319dff', fontSize: '14px', fontWeight: '500' }}>
                      {analysisData.target_age_range}
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
            Click on the map to select a location and analyze age-based demographic distributions
          </p>
        </div>
      )}
    </div>
  );
}

export default UnifiedAgeAnalysis;