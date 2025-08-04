import React, { useState, useEffect, useMemo, useRef } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

// Configuration for all available distributions - Using Propheus color palette
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
  age_income: { 
    title: 'Age-Income Joint Distribution', 
    color: '#319dff', // Propheus blue
    type: 'joint',
    conditionalTypes: ['age', 'income'],
    marginals: ['age_marginal', 'income_marginal']
  },
  profession: { 
    title: 'Profession Distribution', 
    color: '#008a89', // Propheus teal
    type: 'joint',
    conditionalTypes: ['profession', 'gender'],
    marginals: ['profession_marginal', 'gender_marginal']
  }
};

// Conditional value options for each type
const CONDITIONAL_OPTIONS = {
  age: ["Under 25 years", "25 to 44 years", "45 to 64 years", "65 years and over"],
  income: [
    "Less than $10,000", "$10,000 to $14,999", "$15,000 to $19,999",
    "$20,000 to $24,999", "$25,000 to $29,999", "$30,000 to $34,999",
    "$35,000 to $39,999", "$40,000 to $44,999", "$45,000 to $49,999",
    "$50,000 to $59,999", "$60,000 to $74,999", "$75,000 to $99,999",
    "$100,000 to $124,999", "$125,000 to $149,999",
    "$150,000 to $199,999", "$200,000 or more"
  ],
  profession: [
    "Management, business, science, and arts occupations",
    "Service occupations",
    "Sales and office occupations", 
    "Natural resources, construction, and maintenance occupations",
    "Production, transportation, and material moving occupations"
  ],
  gender: ["Male", "Female"]
};

function UnifiedDistributionChart({ data, title, color, type }) {
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

        const sortedData = marginalKey.includes('income') 
          ? [...marginalData].sort((a, b) => CONDITIONAL_OPTIONS.income.indexOf(a.category) - CONDITIONAL_OPTIONS.income.indexOf(b.category))
          : marginalKey.includes('age')
          ? [...marginalData].sort((a, b) => CONDITIONAL_OPTIONS.age.indexOf(a.category) - CONDITIONAL_OPTIONS.age.indexOf(b.category))
          : marginalData;

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
                  tickFormatter={(value) => 
                    marginalKey.includes('income') 
                      ? value.replace('$', '').replace(',000', 'K').replace(' or more', '+')
                      : marginalKey.includes('age')
                      ? value.replace(' years', '').replace(' and over', '+')
                      : value.length > 15 ? value.substring(0, 15) + '...' : value
                  }
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
  const [showConditional, setShowConditional] = useState(false);
  const [conditionType, setConditionType] = useState('');
  const [conditionValue, setConditionValue] = useState('');
  const [conditionalData, setConditionalData] = useState(null);
  const [loading, setLoading] = useState(false);
  const conditionalChartRef = useRef(null);

  // Reset conditional when base distribution changes
  useEffect(() => {
    setShowConditional(false);
    setConditionType('');
    setConditionValue('');
    setConditionalData(null);
  }, [baseDistribution, selectedLocation]);

  // Set default condition type when enabling conditional
  useEffect(() => {
    if (showConditional && !conditionType) {
      const config = DISTRIBUTION_CONFIGS[baseDistribution];
      if (config.conditionalTypes && config.conditionalTypes.length > 0) {
        setConditionType(config.conditionalTypes[0]);
      }
    }
  }, [showConditional, baseDistribution, conditionType]);

  const currentConfig = DISTRIBUTION_CONFIGS[baseDistribution];
  const currentData = distributionData?.distributions?.[baseDistribution];

  const handleGetConditional = async () => {
    if (!conditionValue || !selectedLocation || !currentConfig.conditionalTypes?.includes(conditionType)) {
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('http://localhost:5001/unified_conditional', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lat: selectedLocation.lat,
          lng: selectedLocation.lng,
          base_distribution: baseDistribution,
          condition_type: conditionType,
          condition_value: conditionValue
        }),
      });

      if (response.ok) {
        const result = await response.json();
        setConditionalData(result.conditional_distribution);
        setTimeout(() => {
          conditionalChartRef.current?.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
          });
        }, 100);
      } else {
        console.error('Failed to fetch conditional distribution');
        setConditionalData(null);
      }
    } catch (error) {
      console.error('Error fetching conditional distribution:', error);
      setConditionalData(null);
    } finally {
      setLoading(false);
    }
  };

  if (!distributionData) return null;

  const availableOptions = conditionType ? CONDITIONAL_OPTIONS[conditionType] || [] : [];

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
          {Object.entries(DISTRIBUTION_CONFIGS).map(([key, config]) => (
            <button
              key={key}
              onClick={() => setBaseDistribution(key)}
              disabled={!distributionData.distributions[key]}
              style={{
                backgroundColor: baseDistribution === key ? '#008a89' : '#1f2937',
                color: baseDistribution === key ? '#ffffff' : distributionData.distributions[key] ? '#f9fafb' : '#6b7280',
                border: `1px solid ${baseDistribution === key ? '#008a89' : '#374151'}`,
                padding: '12px 16px',
                borderRadius: '8px',
                fontSize: '13px',
                fontWeight: '600',
                cursor: distributionData.distributions[key] ? 'pointer' : 'not-allowed',
                transition: 'all 0.2s ease',
                opacity: distributionData.distributions[key] ? 1 : 0.5,
                boxShadow: baseDistribution === key ? '0 0 0 2px rgba(0, 138, 137, 0.2)' : 'none'
              }}
            >
              {config.title}
            </button>
          ))}
        </div>
      </div>

      {/* Conditional Analysis Toggle */}
      {currentConfig.type === 'joint' && (
        <div style={{ 
          marginBottom: '24px',
          padding: '20px',
          backgroundColor: '#111827',
          borderRadius: '12px',
          border: '1px solid #374151'
        }}>
          <label style={{ 
            display: 'flex', 
            alignItems: 'center', 
            cursor: 'pointer',
            marginBottom: showConditional ? '16px' : '0'
          }}>
            <input
              type="checkbox"
              checked={showConditional}
              onChange={(e) => setShowConditional(e.target.checked)}
              style={{ marginRight: '8px' }}
            />
            <span style={{ fontSize: '14px', fontWeight: '500', color: '#ffffff' }}>
              Show Conditional Analysis
            </span>
          </label>

          {showConditional && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: '12px', alignItems: 'end' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px', color: '#9ca3af' }}>
                  Condition On
                </label>
                <select
                  value={conditionType}
                  onChange={(e) => {
                    setConditionType(e.target.value);
                    setConditionValue('');
                  }}
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    backgroundColor: '#1f2937',
                    border: '1px solid #4b5563',
                    borderRadius: '8px',
                    color: '#f9fafb',
                    fontSize: '13px',
                    fontFamily: 'Inter, system-ui, sans-serif'
                  }}
                >
                  {currentConfig.conditionalTypes?.map(type => (
                    <option key={type} value={type}>
                      {type.charAt(0).toUpperCase() + type.slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px', color: '#9ca3af' }}>
                  Value
                </label>
                <select
                  value={conditionValue}
                  onChange={(e) => setConditionValue(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    backgroundColor: '#1f2937',
                    border: '1px solid #4b5563',
                    borderRadius: '8px',
                    color: '#f9fafb',
                    fontSize: '13px',
                    fontFamily: 'Inter, system-ui, sans-serif'
                  }}
                >
                  <option value="">Select {conditionType}...</option>
                  {availableOptions.map(option => (
                    <option key={option} value={option}>
                      {option.length > 30 ? option.substring(0, 30) + '...' : option}
                    </option>
                  ))}
                </select>
              </div>

              <button
                onClick={handleGetConditional}
                disabled={loading || !conditionValue}
                style={{
                  padding: '10px 20px',
                  backgroundColor: loading || !conditionValue ? '#4b5563' : '#008a89',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '13px',
                  fontWeight: '600',
                  cursor: loading || !conditionValue ? 'not-allowed' : 'pointer',
                  transition: 'all 0.2s ease',
                  fontFamily: 'Inter, system-ui, sans-serif',
                  boxShadow: loading || !conditionValue ? 'none' : '0 0 0 2px rgba(0, 138, 137, 0.2)'
                }}
              >
                {loading ? 'Loading...' : 'Analyze'}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Distribution Display */}
      {currentData && (
        <div>
          {/* Marginal Distributions for Joint Types */}
          {currentConfig.type === 'joint' && (
            <MarginalDistributions 
              distributionData={currentData} 
              baseDistribution={baseDistribution} 
            />
          )}

          {/* Main Distribution Chart */}
          {currentConfig.type === 'individual' ? (
            <UnifiedDistributionChart
              data={currentData.data}
              title={currentConfig.title}
              color={currentConfig.color}
              type={baseDistribution}
            />
          ) : (
            <UnifiedDistributionChart
              data={currentData.data}
              title={`${currentConfig.title} - Overview`}
              color={currentConfig.color}
              type={baseDistribution}
            />
          )}

          {/* Conditional Results */}
          {conditionalData && (
            <div ref={conditionalChartRef}>
              <UnifiedDistributionChart
                data={conditionalData.data}
                title={conditionalData.condition}
                color="#f97316"
                type={conditionType}
              />
              <div style={{
                marginTop: '12px',
                padding: '12px',
                backgroundColor: '#0a0d10',
                borderRadius: '6px',
                border: '1px solid #2a2e36',
                fontSize: '12px',
                color: '#9ca3af'
              }}>
                <strong>Total: {conditionalData.total_population?.toLocaleString()}</strong>
                <span style={{ marginLeft: '16px' }}>
                  Type: {conditionalData.type?.replace('_', ' given ')}
                </span>
              </div>
            </div>
          )}

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
                Categories: {currentConfig.type === 'individual' 
                  ? currentData.data?.length 
                  : currentData.data?.length}
              </span>
              <span>
                Total: {currentConfig.type === 'individual'
                  ? currentData.data?.reduce((sum, item) => sum + item.value, 0).toLocaleString()
                  : currentData.total_population?.toLocaleString()}
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