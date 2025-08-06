import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

// Color schemes for different data types
const DATA_TYPE_COLORS = {
  'Age': '#008a89',
  'Gender': '#f97316', 
  'Education': '#319dff',
  'Income': '#06b6d4',
  'Profession': '#8b5cf6',
  'Race/Ethnicity': '#10b981'
};

// Get colors for pie chart
const getPieColors = (dataType) => {
  const baseColor = DATA_TYPE_COLORS[dataType] || '#6b7280';
  return [
    baseColor,
    `${baseColor}CC`, // 80% opacity
    `${baseColor}99`, // 60% opacity
    `${baseColor}66`, // 40% opacity
    `${baseColor}33`, // 20% opacity
    '#e5e7eb', '#d1d5db', '#9ca3af', '#6b7280', '#4b5563', '#374151'
  ];
};

// Custom tooltip for charts
const CustomTooltip = ({ active, payload, label, dataType }) => {
  if (active && payload && payload.length) {
    const data = payload[0];
    const value = data.value;
    const total = data.payload.total || 0;
    const percentage = total > 0 ? ((value / total) * 100) : 0;
    
    return (
      <div style={{
        backgroundColor: '#1f2937',
        border: '1px solid #4b5563',
        borderRadius: '6px',
        padding: '12px',
        color: '#f9fafb',
        fontSize: '12px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
      }}>
        <div style={{ fontWeight: '600', marginBottom: '4px', color: DATA_TYPE_COLORS[dataType] }}>
          {label}
        </div>
        <div>Population: <strong>{value.toLocaleString()}</strong></div>
        <div>Percentage: <strong>{percentage.toFixed(1)}%</strong></div>
      </div>
    );
  }
  return null;
};

// Individual distribution chart component
function DistributionChart({ title, data, dataType, chartType = 'bar' }) {
  if (!data || data.length === 0) return null;

  // Calculate total for percentages
  const total = data.reduce((sum, item) => sum + item.population, 0);
  const chartData = data.map(item => ({
    ...item,
    total: total,
    name: item.category.length > 20 ? item.category.substring(0, 20) + '...' : item.category
  }));

  if (chartType === 'pie') {
    return (
      <div style={{
        backgroundColor: '#374151',
        padding: '20px',
        borderRadius: '12px',
        marginBottom: '20px'
      }}>
        <h3 style={{
          fontSize: '16px',
          fontWeight: '600',
          marginBottom: '16px',
          color: DATA_TYPE_COLORS[dataType],
          textAlign: 'center'
        }}>
          {title}
        </h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div style={{ flex: 1 }}>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  fill={DATA_TYPE_COLORS[dataType]}
                  dataKey="population"
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  labelLine={false}
                  fontSize={10}
                >
                  {chartData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={getPieColors(dataType)[index % getPieColors(dataType).length]} 
                    />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip dataType={dataType} />} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: '14px', color: '#d1d5db' }}>
              <div style={{ marginBottom: '12px' }}>
                <strong>Total Population: {total.toLocaleString()}</strong>
              </div>
              {chartData.slice(0, 6).map((item, index) => (
                <div key={index} style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  marginBottom: '6px',
                  padding: '4px 0'
                }}>
                  <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '6px'
                  }}>
                    <div style={{
                      width: '12px',
                      height: '12px',
                      backgroundColor: getPieColors(dataType)[index],
                      borderRadius: '2px'
                    }}></div>
                    <span style={{ fontSize: '12px' }}>
                      {item.category.length > 25 ? item.category.substring(0, 25) + '...' : item.category}
                    </span>
                  </div>
                  <span style={{ fontSize: '12px', fontWeight: '500' }}>
                    {item.population.toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      backgroundColor: '#374151',
      padding: '20px',
      borderRadius: '12px',
      marginBottom: '20px'
    }}>
      <h3 style={{
        fontSize: '16px',
        fontWeight: '600',
        marginBottom: '16px',
        color: DATA_TYPE_COLORS[dataType],
        textAlign: 'center'
      }}>
        {title}
      </h3>
      
      <div style={{ 
        fontSize: '14px', 
        color: '#9ca3af', 
        textAlign: 'center', 
        marginBottom: '16px' 
      }}>
        Total Population: <strong style={{ color: '#f9fafb' }}>{total.toLocaleString()}</strong>
      </div>

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
          />
          <YAxis stroke="#9ca3af" fontSize={11} />
          <Tooltip content={<CustomTooltip dataType={dataType} />} />
          <Bar
            dataKey="population"
            fill={DATA_TYPE_COLORS[dataType]}
            radius={[4, 4, 0, 0]}
            opacity={0.9}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function StorewiseDemographics({ selectedLocation, locationName, storewiseData, loading }) {
  const [error, setError] = useState(null);
  const [chartType, setChartType] = useState('bar'); // 'bar' or 'pie'

  // Handle error detection when storewise data fails to load
  useEffect(() => {
    if (selectedLocation && !loading && !storewiseData) {
      setError('Failed to fetch trade area demographics. Please ensure the backend is running and try again.');
    } else if (storewiseData) {
      setError(null);
    }
  }, [selectedLocation, storewiseData, loading]);


  // Process the data for visualization
  const processStorewiseData = (rawData) => {
    if (!rawData || !rawData.properties) return {};
    
    const distributions = {};
    
    // Group data by data type
    Object.entries(rawData.properties).forEach(([key, population]) => {
      const [dataType, ...categoryParts] = key.split('_');
      const category = categoryParts.join('_').replace(/_/g, ' ');
      
      if (!distributions[dataType]) {
        distributions[dataType] = [];
      }
      
      distributions[dataType].push({
        category: category,
        population: population
      });
    });

    // Sort each distribution by population (descending)
    Object.keys(distributions).forEach(dataType => {
      distributions[dataType].sort((a, b) => b.population - a.population);
    });

    return distributions;
  };

  const processedData = storewiseData ? processStorewiseData(storewiseData) : {};
  const totalPopulation = storewiseData ? 
    Object.values(storewiseData.properties || {}).reduce((sum, pop) => sum + pop, 0) : 0;

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
          Store Trade Area Demographics
        </h1>
        <p style={{ 
          fontSize: '14px', 
          color: '#9ca3af',
          marginBottom: '8px'
        }}>
          10-minute walking radius demographic analysis using isochrone mapping
        </p>
        {locationName && (
          <div style={{ color: '#008a89', fontSize: '14px' }}>
            📍 {locationName}
          </div>
        )}
      </div>

      {/* Chart Type Toggle */}
      <div style={{ 
        marginBottom: '24px',
        display: 'flex',
        gap: '12px',
        alignItems: 'center'
      }}>
        <span style={{ fontSize: '14px', color: '#d1d5db' }}>Chart Type:</span>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={() => setChartType('bar')}
            style={{
              padding: '6px 12px',
              backgroundColor: chartType === 'bar' ? '#008a89' : '#4b5563',
              color: '#ffffff',
              border: 'none',
              borderRadius: '6px',
              fontSize: '12px',
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
          >
            Bar Charts
          </button>
          <button
            onClick={() => setChartType('pie')}
            style={{
              padding: '6px 12px',
              backgroundColor: chartType === 'pie' ? '#008a89' : '#4b5563',
              color: '#ffffff',
              border: 'none',
              borderRadius: '6px',
              fontSize: '12px',
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
          >
            Pie Charts
          </button>
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
              <div style={{
                width: '40px',
                height: '40px',
                border: '4px solid #374151',
                borderTop: '4px solid #008a89',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite',
                margin: '0 auto 16px'
              }}></div>
              <div style={{ fontSize: '16px', marginBottom: '8px' }}>
                Generating Trade Area Analysis...
              </div>
              <div style={{ fontSize: '14px' }}>
                Creating 10-minute walking isochrone and analyzing demographics
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

          {storewiseData && !loading && (
            <>
              {/* Summary Card */}
              <div style={{ 
                backgroundColor: '#374151', 
                padding: '20px', 
                borderRadius: '12px',
                marginBottom: '24px',
                border: '1px solid #4b5563'
              }}>
                <h2 style={{ 
                  fontSize: '18px', 
                  fontWeight: '600', 
                  marginBottom: '16px',
                  color: '#f9fafb'
                }}>
                  Trade Area Summary
                </h2>
                <div style={{ 
                  display: 'grid', 
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
                  gap: '16px'
                }}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ color: '#9ca3af', fontSize: '12px', marginBottom: '4px' }}>
                      Catchment Area
                    </div>
                    <div style={{ color: '#008a89', fontSize: '16px', fontWeight: '600' }}>
                      10-min Walk
                    </div>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ color: '#9ca3af', fontSize: '12px', marginBottom: '4px' }}>
                      Total Population
                    </div>
                    <div style={{ color: '#10b981', fontSize: '16px', fontWeight: '600' }}>
                      {totalPopulation.toLocaleString()}
                    </div>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ color: '#9ca3af', fontSize: '12px', marginBottom: '4px' }}>
                      Data Categories
                    </div>
                    <div style={{ color: '#319dff', fontSize: '16px', fontWeight: '600' }}>
                      {Object.keys(processedData).length}
                    </div>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ color: '#9ca3af', fontSize: '12px', marginBottom: '4px' }}>
                      Analysis Method
                    </div>
                    <div style={{ color: '#f97316', fontSize: '16px', fontWeight: '600' }}>
                      Isochrone
                    </div>
                  </div>
                </div>
              </div>

              {/* Distribution Charts */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: chartType === 'pie' ? '1fr' : 'repeat(auto-fit, minmax(400px, 1fr))',
                gap: '20px'
              }}>
                {Object.entries(processedData).map(([dataType, data]) => (
                  <DistributionChart
                    key={dataType}
                    title={`${dataType} Distribution in Trade Area`}
                    data={data}
                    dataType={dataType}
                    chartType={chartType}
                  />
                ))}
              </div>

              {/* Methodology */}
              <div style={{ 
                backgroundColor: '#374151', 
                padding: '16px', 
                borderRadius: '8px',
                marginTop: '24px'
              }}>
                <h3 style={{ 
                  fontSize: '16px', 
                  fontWeight: '500', 
                  marginBottom: '12px',
                  color: '#f9fafb'
                }}>
                  Methodology
                </h3>
                <div style={{ fontSize: '14px', color: '#d1d5db', lineHeight: '1.6' }}>
                  <p style={{ margin: '0 0 8px 0' }}>
                    <strong>Trade Area Definition:</strong> 10-minute pedestrian walking radius calculated using Valhalla routing engine
                  </p>
                  <p style={{ margin: '0 0 8px 0' }}>
                    <strong>Data Processing:</strong> Census block groups intersected with isochrone geometry, population weighted by intersection area
                  </p>
                  <p style={{ margin: '0 0 8px 0' }}>
                    <strong>Geographic Precision:</strong> Block group level demographic data from US Census ACS 5-Year estimates
                  </p>
                  <p style={{ margin: '0' }}>
                    <strong>Update Frequency:</strong> Real-time analysis using current Census API data
                  </p>
                </div>
              </div>

              {/* Data Source */}
              <div style={{ 
                marginTop: '16px', 
                fontSize: '12px', 
                color: '#6b7280',
                textAlign: 'center'
              }}>
                Data Sources: US Census Bureau ACS 5-Year • Valhalla Routing Engine • OpenStreetMap
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
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>🏪</div>
          <h2 style={{ fontSize: '18px', marginBottom: '8px' }}>
            Select a Location for Trade Area Analysis
          </h2>
          <p style={{ fontSize: '14px', marginBottom: '16px' }}>
            Click on the map to analyze the demographic composition of a 10-minute walking radius around your selected location
          </p>
          <div style={{ 
            backgroundColor: '#374151',
            padding: '16px',
            borderRadius: '8px',
            fontSize: '13px',
            color: '#d1d5db',
            maxWidth: '500px',
            margin: '0 auto'
          }}>
            <strong>Perfect for:</strong> Retail site selection, market analysis, customer demographic profiling, 
            walkable catchment area studies, and urban planning insights.
          </div>
        </div>
      )}

      <style>
        {`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}
      </style>
    </div>
  );
}

export default StorewiseDemographics;