import React, { useState, useRef, useEffect, useMemo } from 'react';
import { MapContainer, TileLayer, useMapEvents, Marker, Popup } from 'react-leaflet';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import 'leaflet/dist/leaflet.css';
import './App.css';
import L from 'leaflet';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';
import UnifiedDistributionSystem from './UnifiedDistributionSystem';

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;

// --- Helper Components ---

function MapClickHandler({ onMapClick }) {
  useMapEvents({
    click: (e) => {
      onMapClick(e.latlng);
    },
  });
  return null;
}

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
    return category;
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const dataPoint = payload[0].payload;
      return (
        <div className="custom-tooltip">
          <p className="label">{dataPoint.category}</p>
          <p className="value">
            {type === 'income' ? 'Households' : 'Population'}: {payload[0].value.toLocaleString()}
          </p>
          <p className="percentage">Percentage: {dataPoint.percentage.toFixed(1)}%</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="chart-container">
      <h3 className="chart-title">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis
            dataKey="category"
            tick={{ fontSize: 10 }}
            angle={-45}
            textAnchor="end"
            height={60}
            tickFormatter={formatCategory}
          />
          <YAxis tick={{ fontSize: 10 }} />
          <Tooltip content={<CustomTooltip />} />
          <Bar
            dataKey="value"
            fill={color}
            radius={[4, 4, 0, 0]}
            animationDuration={1500}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function AgeIncomeJointChart({ data, selectedLocation }) {
  const [conditionType, setConditionType] = useState('age');
  const [conditionValue, setConditionValue] = useState('');
  const [conditionalData, setConditionalData] = useState(null);
  const [loading, setLoading] = useState(false);
  const conditionalChartRef = useRef(null);

  useEffect(() => {
    setConditionalData(null);
    setConditionValue('');
  }, [selectedLocation]);

  const sortedAgeData = useMemo(() => {
    if (!data?.age_marginal) return [];
    const ageOrder = ["Under 25 years", "25 to 44 years", "45 to 64 years", "65 years and over"];
    return [...data.age_marginal].sort((a, b) => ageOrder.indexOf(a.category) - ageOrder.indexOf(b.category));
  }, [data?.age_marginal]);

  const sortedIncomeData = useMemo(() => {
    if (!data?.income_marginal) return [];
    const incomeOrder = [
        "Less than $10,000", "$10,000 to $14,999", "$15,000 to $19,999",
        "$20,000 to $24,999", "$25,000 to $29,999", "$30,000 to $34,999",
        "$35,000 to $39,999", "$40,000 to $44,999", "$45,000 to $49,999",
        "$50,000 to $59,999", "$60,000 to $74,999", "$75,000 to $99,999",
        "$100,000 to $124,999", "$125,000 to $149,999",
        "$150,000 to $199,999", "$200,000 or more"
    ];
    return [...data.income_marginal].sort((a, b) => incomeOrder.indexOf(a.category) - incomeOrder.indexOf(b.category));
  }, [data?.income_marginal]);

  if (!data) return null;

  const ageOptions = data.age_marginal?.map(item => item.category) || [];
  const incomeOptions = data.income_marginal?.map(item => item.category) || [];

  const handleGetConditional = async () => {
    if (!conditionValue || !selectedLocation) return;

    setLoading(true);
    try {
      const response = await fetch('http://localhost:5001/conditional_distribution', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lat: selectedLocation.lat,
          lng: selectedLocation.lng,
          condition_type: conditionType,
          condition_value: conditionValue
        }),
      });

      if (response.ok) {
        const result = await response.json();
        setConditionalData(result.conditional_distribution);
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

  return (
    <div className="joint-chart-container" style={{
      maxHeight: '80vh',
      overflowY: 'auto',
      paddingRight: '10px',
      paddingTop: '10px'
    }}>
      <h3 className="chart-title" style={{ marginTop: '0', marginBottom: '20px' }}>Age-Income Joint Distribution</h3>

      <div className="marginal-distributions" style={{ display: 'flex', gap: '20px', marginBottom: '20px' }}>
        <div style={{ flex: 1 }}>
          <h4>Age Distribution (Marginal)</h4>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={sortedAgeData} margin={{ top: 10, right: 10, left: 10, bottom: 40 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis
                dataKey="category"
                tick={{ fontSize: 8 }}
                angle={-45}
                textAnchor="end"
                height={40}
              />
              <YAxis tick={{ fontSize: 8 }} />
              <Tooltip />
              <Bar dataKey="value" fill="#3b82f6" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div style={{ flex: 1 }}>
          <h4>Income Distribution (Marginal)</h4>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={sortedIncomeData} margin={{ top: 10, right: 10, left: 10, bottom: 40 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis
                dataKey="category"
                tick={{ fontSize: 8 }}
                angle={-45}
                textAnchor="end"
                height={40}
                tickFormatter={(value) => value.replace('$', '').replace(',000', 'K').replace(' or more', '+')}
              />
              <YAxis tick={{ fontSize: 8 }} />
              <Tooltip />
              <Bar dataKey="value" fill="#f59e0b" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="conditional-controls" style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#5936d6', borderRadius: '8px' }}>
        <h4>View Conditional Distribution</h4>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
          <label>
            Condition on:
            <select
              value={conditionType}
              onChange={(e) => {
                setConditionType(e.target.value);
                setConditionValue('');
                setConditionalData(null);
              }}
              style={{ marginLeft: '5px', padding: '5px' }}
            >
              <option value="age">Age</option>
              <option value="income">Income</option>
            </select>
          </label>

          <label>
            Value:
            <select
              value={conditionValue}
              onChange={(e) => setConditionValue(e.target.value)}
              style={{ marginLeft: '5px', padding: '5px', minWidth: '200px' }}
            >
              <option value="">Select {conditionType} range...</option>
              {(conditionType === 'age' ? ageOptions : incomeOptions).map(option => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
          </label>

          <button
            onClick={handleGetConditional}
            disabled={!conditionValue || loading}
            style={{
              padding: '8px 16px',
              backgroundColor: loading ? '#ccc' : '#8b5cf6',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Loading...' : 'Show Distribution'}
          </button>
        </div>
      </div>

      {conditionalData && (
        <div className="conditional-chart" ref={conditionalChartRef} style={{
          marginTop: '30px',
          marginBottom: '20px',
          padding: '20px',
          backgroundColor: 'rgba(255,255,255,0)',
          borderRadius: '8px',
          border: '1px solid #e2e8f0'
        }}>
          <h4 style={{ marginTop: '0' }}>Conditional Distribution: {conditionalData.condition}</h4>
          <p>Total Households: {conditionalData.total_households?.toLocaleString()}</p>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={conditionalData.data} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis
                dataKey="category"
                tick={{ fontSize: 10 }}
                angle={-45}
                textAnchor="end"
                height={60}
                tickFormatter={(value) => {
                  if (conditionType === 'age') {
                    return value.replace('$', '').replace(',000', 'K').replace(' or more', '+');
                  } else {
                    return value.replace(' years', '').replace(' and over', '+');
                  }
                }}
              />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip
                formatter={(value, name, props) => [
                  `${value.toLocaleString()} households (${props.payload.percentage.toFixed(1)}%)`,
                  'Count'
                ]}
              />
              <Bar
                dataKey="value"
                fill="#8b5cf6"
                radius={[4, 4, 0, 0]}
                animationDuration={1500}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

function ChatBot({ selectedLocation, distributionData }) {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const messagesEndRef = useRef(null);

  // State and refs for dragging
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const dragRef = useRef(null);
  const offsetRef = useRef({ x: 0, y: 0 });

  // Set initial position when chatbot opens
  useEffect(() => {
    if (isOpen && dragRef.current) {
        const { offsetWidth, offsetHeight } = dragRef.current;
        setPosition({
          x: window.innerWidth - offsetWidth - 20,
          y: window.innerHeight - offsetHeight - 20,
        });
    }
  }, [isOpen]);

  // Drag event handlers
  const handleMouseDown = (e) => {
    e.preventDefault();
    setIsDragging(true);
    const rect = dragRef.current.getBoundingClientRect();
    offsetRef.current = {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    };
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    const newX = e.clientX - offsetRef.current.x;
    const newY = e.clientY - offsetRef.current.y;
    setPosition({ x: newX, y: newY });
  };

  // Effect to add/remove global drag listeners
  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');

    const newMessages = [...messages, { type: 'user', content: userMessage, timestamp: new Date() }];
    setMessages(newMessages);
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:5001/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          lat: selectedLocation?.lat,
          lng: selectedLocation?.lng
        }),
      });

      const data = await response.json();

      if (response.ok && !data.error) {
        setMessages(prev => [...prev, {
          type: 'assistant',
          content: data.response,
          timestamp: new Date(),
          hasData: data.has_data,
          location: data.location
        }]);
      } else {
        setMessages(prev => [...prev, {
          type: 'error',
          content: data.error || 'Failed to get response from chatbot',
          timestamp: new Date()
        }]);
      }
    } catch (error) {
      setMessages(prev => [...prev, {
        type: 'error',
        content: 'Network error: Could not connect to chatbot service',
        timestamp: new Date()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearChat = async () => {
    try {
      await fetch('http://localhost:5001/chat/clear', { method: 'POST' });
      setMessages([]);
    } catch (error) {
      console.error('Failed to clear chat history:', error);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const suggestedQuestions = [
    "What's the demographic profile of this location?",
    "Compare the age and income distributions",
    "What's the income distribution for young adults (25-44)?",
    "Show me education levels in this area",
    "What are the key demographic insights?"
  ];

  if (!isOpen) {
    return (
      <div className="chatbot-toggle" style={{
        position: 'fixed',
        bottom: '20px',
        right: '20px',
        zIndex: 1000
      }}>
        <button
          onClick={() => setIsOpen(true)}
          style={{
            width: '56px',
            height: '56px',
            borderRadius: '12px',
            backgroundColor: '#008a89',
            color: 'white',
            border: '1px solid #2a2e36',
            fontSize: '20px',
            cursor: 'pointer',
            boxShadow: '0 4px 12px rgba(0, 138, 137, 0.3)',
            transition: 'all 0.2s ease',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontFamily: 'Inter, system-ui, sans-serif'
          }}
          onMouseEnter={(e) => {
            e.target.style.transform = 'scale(1.05)';
            e.target.style.boxShadow = '0 6px 16px rgba(0, 138, 137, 0.4)';
          }}
          onMouseLeave={(e) => {
            e.target.style.transform = 'scale(1)';
            e.target.style.boxShadow = '0 4px 12px rgba(0, 138, 137, 0.3)';
          }}
        >
          💬
        </button>
      </div>
    );
  }

  return (
    <div
      ref={dragRef}
      className="chatbot-container"
      style={{
        position: 'fixed',
        left: `${position.x}px`,
        top: `${position.y}px`,
        width: '400px',
        height: '600px',
        backgroundColor: '#1a1e26',
        borderRadius: '12px',
        boxShadow: '0 10px 25px rgba(0, 0, 0, 0.4)',
        display: 'flex',
        flexDirection: 'column',
        zIndex: 1000,
        border: '1px solid #2a2e36',
        userSelect: 'none',
        fontFamily: 'Inter, system-ui, sans-serif'
      }}
    >
      {/* Header */}
      <div
        onMouseDown={handleMouseDown}
        style={{
          padding: '16px',
          borderBottom: '1px solid #2a2e36',
          borderRadius: '12px 12px 0 0',
          backgroundColor: '#008a89',
          color: '#eef0f4',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          cursor: 'move',
        }}
      >
        <div>
          <h3 style={{ margin: '0', fontSize: '15px', fontWeight: '600' }}>
            Census Analytics AI
          </h3>
          <p style={{ margin: '0', fontSize: '12px', opacity: '0.8', fontWeight: '400' }}>
            Demographic insights assistant
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={clearChat}
            style={{
              background: 'rgba(255,255,255,0.2)',
              border: 'none',
              borderRadius: '6px',
              color: 'white',
              padding: '4px 8px',
              fontSize: '12px',
              cursor: 'pointer'
            }}
          >
            Clear
          </button>
          <button
            onClick={() => setIsOpen(false)}
            style={{
              background: 'rgba(255,255,255,0.2)',
              border: 'none',
              borderRadius: '6px',
              color: 'white',
              padding: '4px 8px',
              fontSize: '14px',
              cursor: 'pointer'
            }}
          >
            ✕
          </button>
        </div>
      </div>

      {/* Messages */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '16px',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px'
      }}>
        {messages.length === 0 && (
          <div>
            <div style={{
              textAlign: 'center',
              color: '#64748b',
              fontSize: '14px',
              marginBottom: '16px'
            }}>
              👋 Hi! I'm your Census Data AI assistant. I can analyze demographic data for any location you select on the map.
            </div>

            {selectedLocation && (
              <div style={{
                backgroundColor: '#f1f5f9',
                padding: '12px',
                borderRadius: '8px',
                fontSize: '12px',
                color: '#475569',
                marginBottom: '16px'
              }}>
                📍 Current location: {selectedLocation.lat.toFixed(4)}, {selectedLocation.lng.toFixed(4)}
                {distributionData && <div>✅ Distribution data loaded</div>}
              </div>
            )}

            <div style={{ fontSize: '14px', color: '#64748b', marginBottom: '8px' }}>
              Try asking:
            </div>
            {suggestedQuestions.map((question, index) => (
              <button
                key={index}
                onClick={() => setInputMessage(question)}
                style={{
                  display: 'block',
                  width: '100%',
                  textAlign: 'left',
                  padding: '8px 12px',
                  margin: '4px 0',
                  backgroundColor: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                  fontSize: '12px',
                  color: '#475569',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
                onMouseEnter={(e) => {
                  e.target.style.backgroundColor = '#e2e8f0';
                }}
                onMouseLeave={(e) => {
                  e.target.style.backgroundColor = '#f8fafc';
                }}
              >
                {question}
              </button>
            ))}
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            style={{
              display: 'flex',
              justifyContent: message.type === 'user' ? 'flex-end' : 'flex-start',
              marginBottom: '8px'
            }}
          >
            <div
              style={{
                maxWidth: '85%',
                padding: '14px',
                borderRadius: '12px',
                backgroundColor: message.type === 'user'
                  ? '#8b5cf6'
                  : message.type === 'error'
                  ? '#fef2f2'
                  : '#f8fafc',
                color: message.type === 'user'
                  ? 'white'
                  : message.type === 'error'
                  ? '#dc2626'
                  : '#374151',
                fontSize: '14px',
                lineHeight: '1.6',
                border: message.type === 'error' ? '1px solid #fecaca' : '1px solid #e2e8f0',
                boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
              }}
            >
              <div style={{
                whiteSpace: 'pre-line',
                fontFamily: message.type === 'assistant' ? 'system-ui, -apple-system, sans-serif' : 'inherit'
              }}>
                {message.content}
              </div>
              {message.hasData && (
                <div style={{
                  fontSize: '11px',
                  opacity: '0.7',
                  marginTop: '8px',
                  fontStyle: 'italic',
                  borderTop: '1px solid rgba(255,255,255,0.2)',
                  paddingTop: '6px'
                }}>
                  📊 Using current location data
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div style={{
              backgroundColor: '#f8fafc',
              padding: '12px',
              borderRadius: '12px',
              fontSize: '14px',
              color: '#64748b'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div style={{
                  width: '20px',
                  height: '20px',
                  border: '2px solid #e2e8f0',
                  borderTop: '2px solid #8b5cf6',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite'
                }}></div>
                Analyzing data...
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div style={{
        padding: '16px',
        borderTop: '1px solid #e2e8f0',
        borderRadius: '0 0 16px 16px'
      }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={selectedLocation ? "Ask about the demographic data..." : "Select a location on the map first..."}
            disabled={isLoading}
            style={{
              flex: 1,
              padding: '12px',
              border: '1px solid #e2e8f0',
              borderRadius: '8px',
              fontSize: '14px',
              resize: 'none',
              minHeight: '40px',
              maxHeight: '80px',
              outline: 'none',
              fontFamily: 'inherit'
            }}
            rows={1}
          />
          <button
            onClick={sendMessage}
            disabled={!inputMessage.trim() || isLoading}
            style={{
              padding: '12px 16px',
              backgroundColor: inputMessage.trim() && !isLoading ? '#8b5cf6' : '#e2e8f0',
              color: inputMessage.trim() && !isLoading ? 'white' : '#9ca3af',
              border: 'none',
              borderRadius: '8px',
              cursor: inputMessage.trim() && !isLoading ? 'pointer' : 'not-allowed',
              fontSize: '14px',
              fontWeight: '500',
              transition: 'all 0.2s ease'
            }}
          >
            Send
          </button>
        </div>
      </div>

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

// --- Main App Component ---

function App() {
  const [distributionData, setDistributionData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [geography, setGeography] = useState(null);

  const handleMapClick = async (latlng) => {
    const { lat, lng } = latlng;
    setLoading(true);
    setSelectedLocation({ lat, lng });
    setGeography(null);

    try {
      const response = await fetch('http://localhost:5001/distribution', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ lat, lng }),
      });

      const geographyResponse = await fetch('http://localhost:5001/geography', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lat, lng }),
      });

      if (response.ok) {
        const data = await response.json();
        setDistributionData(data);
      } else {
        console.error('Failed to fetch distribution data');
        setDistributionData(null);
      }

      if (geographyResponse.ok) {
        const data = await geographyResponse.json();
        setGeography(data.location);
      } else {
        console.error('Failed to fetch geography data');
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      setDistributionData(null);
      setGeography(null);
    } finally {
      setLoading(false);
    }
  };

  const locationName = geography
    ? (geography.subdivision_name || geography.county_name)
    : '';

  return (
    <div className="app" style={{
      fontFamily: 'Inter, system-ui, -apple-system, BlinkMacSystemFont, sans-serif',
      backgroundColor: '#0a0d10',
      color: '#eef0f4',
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
    }}>
      {/* Header */}
      <header style={{
        width: '100%',
        maxWidth: '1800px',
        padding: '16px 20px',
        borderBottom: '1px solid #1f2937',
        backgroundColor: '#111827',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '32px',
            height: '32px',
            backgroundColor: '#008a89',
            borderRadius: '6px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '16px',
            fontWeight: '700',
            color: '#ffffff'
          }}>
            P
          </div>
          <div>
            <h1 style={{ 
              margin: '0', 
              fontSize: '20px', 
              fontWeight: '700',
              color: '#f9fafb',
              letterSpacing: '-0.025em'
            }}>
              Propheus
            </h1>
            <p style={{ 
              margin: '0', 
              fontSize: '13px', 
              color: '#9ca3af',
              fontWeight: '400'
            }}>
              Census Distribution Analytics
            </p>
          </div>
        </div>
        <div style={{
          fontSize: '12px',
          color: '#6b7280',
          fontFamily: 'JetBrains Mono, monospace'
        }}>
          {selectedLocation && locationName && (
            <span style={{ color: '#319dff' }}>
              📍 {locationName}
            </span>
          )}
        </div>
      </header>

      <div className="main-content" style={{
        display: 'flex',
        gap: '20px',
        padding: '20px',
        width: '100%',
        maxWidth: '1800px',
        flex: 1
      }}>
        <div className="map-section" style={{
          flex: 2,
          borderRadius: '12px',
          overflow: 'hidden',
          border: '1px solid #2a2e36',
          position: 'relative',
          minHeight: 'calc(100vh - 40px)'
        }}>
          <MapContainer
            center={[39.8283, -98.5795]}
            zoom={4}
            style={{ height: '100%', width: '100%' }}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            <MapClickHandler onMapClick={handleMapClick} />
            {selectedLocation && (
                <Marker position={[selectedLocation.lat,selectedLocation.lng]}>
                  <Popup>
                  You clicked here! <br />
                  Lat: {selectedLocation.lat.toFixed(4)}, Lng: {selectedLocation.lng.toFixed(4)}
                </Popup>
                </Marker>
            )}
          </MapContainer>

          {loading && (
            <div style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(10, 13, 16, 0.8)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 1000,
              borderRadius: '12px'
            }}>
              <div style={{
                backgroundColor: '#1a1e26',
                padding: '20px',
                borderRadius: '8px',
                border: '1px solid #2a2e36',
                display: 'flex',
                alignItems: 'center',
                gap: '12px'
              }}>
                <div style={{
                  width: '20px',
                  height: '20px',
                  border: '2px solid #2a2e36',
                  borderTop: '2px solid #008a89',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite'
                }}></div>
                <p style={{ margin: 0, color: '#eef0f4', fontSize: '14px' }}>Loading distribution data...</p>
              </div>
            </div>
          )}

          {selectedLocation && (
            <div style={{
              position: 'absolute',
              top: '16px',
              left: '16px',
              backgroundColor: '#1a1e26',
              padding: '12px 16px',
              borderRadius: '8px',
              border: '1px solid #2a2e36',
              zIndex: 1000,
              fontSize: '12px',
              color: '#eef0f4'
            }}>
              <div style={{ fontWeight: '500', marginBottom: '4px' }}>Selected Location</div>
              <div style={{ color: '#9ca3af' }}>
                {selectedLocation.lat.toFixed(4)}, {selectedLocation.lng.toFixed(4)}
              </div>
              {locationName && <div style={{ marginTop: '4px', color: '#008a89' }}>{locationName}</div>}
            </div>
          )}
        </div>

        <div className="charts-section" style={{
          flex: 1,
          maxWidth: '500px',
          minWidth: '400px',
          height: 'calc(100vh - 40px)',
          backgroundColor: '#1a1e26',
          borderRadius: '12px',
          border: '1px solid #2a2e36',
          display: 'flex',
          flexDirection: 'column'
        }}>
          {distributionData ? (
            <div style={{
              flex: 1,
              overflowY: 'auto'
            }}>
              <UnifiedDistributionSystem 
                distributionData={distributionData}
                selectedLocation={selectedLocation}
              />
            </div>
          ) : (
            <div style={{
              padding: '24px',
              textAlign: 'center',
              color: '#9ca3af',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              height: '100%'
            }}>
              <div style={{
                fontSize: '16px',
                fontWeight: '500',
                marginBottom: '12px',
                color: '#eef0f4'
              }}>
                Distribution Analytics
              </div>
              <p style={{
                fontSize: '14px',
                marginBottom: '20px',
                lineHeight: '1.5'
              }}>
                Select a location on the map to view demographic data
              </p>
            </div>
          )}
        </div>
      </div>

      <ChatBot 
        selectedLocation={selectedLocation} 
        distributionData={distributionData} 
      />
    </div>
  );
}

export default App;