import React, { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

// Configuration for individual distributions
const DISTRIBUTION_CONFIGS = {
  age: { 
    title: 'Age Distribution', 
    color: '#319dff',
    dataPath: 'data'
  },
  gender: { 
    title: 'Gender Distribution', 
    color: '#f97316',
    dataPath: 'data'
  },
  education: { 
    title: 'Education Distribution', 
    color: '#008a89',
    dataPath: 'data'
  },
  income: { 
    title: 'Income Distribution', 
    color: '#8b5cf6',
    dataPath: 'data'
  },
  profession: { 
    title: 'Profession Distribution', 
    color: '#10b981',
    dataPath: 'data'
  },
  race_ethnicity: { 
    title: 'Race & Ethnicity Distribution', 
    color: '#06b6d4',
    dataPath: 'data'
  }
};

function DistributionChart({ data, title, color, type }) {
  if (!data || data.length === 0) return null;

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
        <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
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

export default function IndividualDistributions({ distributionData, selectedLocation }) {
  const [selectedDistribution, setSelectedDistribution] = useState('age');

  if (!distributionData) return null;

  const currentConfig = DISTRIBUTION_CONFIGS[selectedDistribution];
  const currentData = distributionData?.distributions?.[selectedDistribution];

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
            const isAvailable = distributionData?.distributions?.[key];
            return (
              <button
                key={key}
                onClick={() => setSelectedDistribution(key)}
                disabled={!isAvailable}
                style={{
                  backgroundColor: selectedDistribution === key ? '#008a89' : '#1f2937',
                  color: selectedDistribution === key ? '#ffffff' : isAvailable ? '#f9fafb' : '#6b7280',
                  border: `1px solid ${selectedDistribution === key ? '#008a89' : '#374151'}`,
                  padding: '12px 16px',
                  borderRadius: '8px',
                  fontSize: '13px',
                  fontWeight: '600',
                  cursor: isAvailable ? 'pointer' : 'not-allowed',
                  transition: 'all 0.2s ease',
                  opacity: isAvailable ? 1 : 0.5,
                  boxShadow: selectedDistribution === key ? '0 0 0 2px rgba(0, 138, 137, 0.2)' : 'none'
                }}
              >
                {config.title}
              </button>
            );
          })}
        </div>
      </div>

      {/* Distribution Display */}
      {currentData && (
        <div>
          {/* Main Distribution Chart */}
          <DistributionChart
            data={currentData.data}
            title={currentConfig.title}
            color={currentConfig.color}
            type={selectedDistribution}
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