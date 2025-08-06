import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

// Common income ranges that users might want to analyze
const COMMON_INCOME_RANGES = [
  "Less than $10,000",
  "$10,000 to $14,999",
  "$15,000 to $19,999", 
  "$20,000 to $24,999",
  "$25,000 to $29,999",
  "$30,000 to $34,999",
  "$35,000 to $39,999",
  "$40,000 to $44,999",
  "$45,000 to $49,999",
  "$50,000 to $59,999",
  "$60,000 to $74,999",
  "$75,000 to $99,999",
  "$100,000 to $124,999",
  "$125,000 to $149,999",
  "$150,000 to $199,999",
  "$200,000 or more"
];

// Colors for different distribution types
const DISTRIBUTION_COLORS = {
  age: '#319dff',
  gender: '#f97316',
  profession: '#06b6d4'
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

const getOverlapIndicator = (score) => {
  if (score >= 0.95) return { text: "Perfect Match", color: "#10b981" };
  if (score >= 0.8) return { text: "Very Good Match", color: "#059669" };
  if (score >= 0.5) return { text: "Good Match", color: "#fbbf24" };
  if (score >= 0.3) return { text: "Partial Match", color: "#f59e0b" };
  return { text: "Limited Match", color: "#ef4444" };
};

function UnifiedIncomeAnalysis({ selectedLocation, locationName }) {
  const [selectedIncome, setSelectedIncome] = useState("$50,000 to $59,999");
  const [analysisData, setAnalysisData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [customIncome, setCustomIncome] = useState('');
  const [showCustomInput, setShowCustomInput] = useState(false);

  // Fetch analysis when location or income changes
  useEffect(() => {
    if (selectedLocation && selectedIncome) {
      fetchUnifiedAnalysis();
    }
  }, [selectedLocation, selectedIncome]);

  const fetchUnifiedAnalysis = async () => {
    if (!selectedLocation || !selectedIncome) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('http://localhost:5001/unified_income_analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lat: selectedLocation.lat,
          lng: selectedLocation.lng,
          income_range: selectedIncome
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
      setError('Failed to fetch unified income analysis data');
      setAnalysisData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleCustomIncomeSubmit = () => {
    if (customIncome.trim()) {
      setSelectedIncome(customIncome.trim());
      setShowCustomInput(false);
      setCustomIncome('');
    }
  };

  const renderDistributionChart = (distributionKey, distributionData) => {
    if (distributionData.status !== 'success') return null;

    const chartData = distributionData.conditional_distribution.data.map(item => ({
      ...item,
      name: item.category
    }));

    const overlap = getOverlapIndicator(distributionData.overlap_score);

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
                color: overlap.color,
                fontWeight: '500',
                padding: '2px 6px',
                backgroundColor: `${overlap.color}20`,
                borderRadius: '4px'
              }}>
                {overlap.text}
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
          
          {/* Income range mapping info */}
          <div style={{ 
            backgroundColor: '#1f2937', 
            padding: '8px 12px', 
            borderRadius: '6px', 
            marginBottom: '16px',
            fontSize: '12px'
          }}>
            <div style={{ color: '#9ca3af', marginBottom: '4px' }}>
              <strong>Income Range Mapping:</strong>
            </div>
            <div style={{ color: '#f9fafb' }}>
              Requested: <span style={{ color: '#319dff' }}>{analysisData.target_income}</span>
            </div>
            <div style={{ color: '#f9fafb' }}>
              Matched: <span style={{ color: '#10b981' }}>{distributionData.matched_income}</span>
            </div>
            <div style={{ color: '#f59e0b', fontSize: '11px', marginTop: '4px' }}>
              {distributionData.income_explanation}
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
            <span>Population in Income Group: <strong>{distributionData.total_population.toLocaleString()}</strong></span>
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
          Unified Income Distribution Analysis
        </h1>
        <p style={{ 
          fontSize: '14px', 
          color: '#9ca3af',
          marginBottom: '8px'
        }}>
          Comprehensive income-based demographic analysis combining multiple bivariate distributions
        </p>
        {locationName && (
          <div style={{ color: '#f97316', fontSize: '14px' }}>
            📍 {locationName}
          </div>
        )}
      </div>

      {/* Income Range Selection */}
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
          Select Income Range to Analyze
        </h2>
        
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', 
          gap: '8px',
          marginBottom: '16px'
        }}>
          {COMMON_INCOME_RANGES.map((income) => (
            <button
              key={income}
              onClick={() => setSelectedIncome(income)}
              style={{
                backgroundColor: selectedIncome === income ? '#319dff' : '#4b5563',
                color: selectedIncome === income ? '#ffffff' : '#f9fafb',
                border: `1px solid ${selectedIncome === income ? '#319dff' : '#6b7280'}`,
                padding: '10px 12px',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: '500',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                textAlign: 'left'
              }}
            >
              {income}
            </button>
          ))}
        </div>

        {/* Custom income input */}
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
                value={customIncome}
                onChange={(e) => setCustomIncome(e.target.value)}
                placeholder="e.g., $80,000 to $90,000"
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
                onClick={handleCustomIncomeSubmit}
                disabled={!customIncome.trim()}
                style={{
                  backgroundColor: customIncome.trim() ? '#319dff' : '#4b5563',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '8px 16px',
                  fontSize: '12px',
                  cursor: customIncome.trim() ? 'pointer' : 'not-allowed'
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
              Loading unified income analysis...
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
                    <div style={{ color: '#9ca3af', fontSize: '12px' }}>Target Income Range</div>
                    <div style={{ color: '#319dff', fontSize: '14px', fontWeight: '500' }}>
                      {analysisData.target_income}
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
            Click on the map to select a location and analyze income-based demographic distributions
          </p>
        </div>
      )}
    </div>
  );
}

export default UnifiedIncomeAnalysis;