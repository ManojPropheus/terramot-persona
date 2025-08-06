# Census Distribution Analytics - Propheus

A comprehensive demographic analysis platform built with React and Flask, featuring AI-powered insights and interactive visualizations.

## 🚀 Features

- **Interactive Census Data Visualization** - Maps with real-time demographic analysis
- **Unified Distribution System** - Seamless interface for all distribution types
- **AI-Powered Analytics** - Gemini 2.5 Pro chatbot with memory and tool calling
- **Conditional Analysis** - Advanced demographic correlations and insights
- **Professional UI** - Propheus-branded design with modern aesthetics

## 📊 Supported Distributions

- **Age Distribution** - Population by age groups
- **Gender Distribution** - Population by gender
- **Education Distribution** - Educational attainment levels  
- **Income Distribution** - Household income brackets
- **Profession Distribution** - Occupation categories with gender breakdown
- **Joint Distributions** - Age-Income and Profession-Gender correlations

## 🛠️ Tech Stack

### Backend
- **Flask** - Python web framework
- **Google Gemini 2.5 Pro** - AI chatbot with function calling
- **US Census API** - Real demographic data
- **Pandas** - Data processing and analysis

### Frontend  
- **React** - Modern UI framework
- **Leaflet** - Interactive maps
- **Recharts** - Data visualization
- **Inter Font** - Propheus design system

## 🏗️ Project Structure

```
Data_collection_pipeline/
├── backend/
│   ├── app.py                 # Flask API server
│   ├── chatbot_service.py     # AI chatbot with memory
│   ├── requirements.txt       # Python dependencies
│   └── .env.example          # Environment variables template
├── distribution/
│   ├── age_distribution.py    # Age demographics
│   ├── gender_distribution.py # Gender demographics  
│   ├── education_distribution.py # Education levels
│   ├── income_distribution.py # Income brackets
│   ├── profession_distribution.py # Job categories
│   └── age_income_distribution.py # Joint analysis
├── frontend/
│   ├── src/
│   │   ├── App.js            # Main application
│   │   ├── UnifiedDistributionSystem.js # Distribution interface
│   │   └── ...
│   ├── package.json          # Node dependencies
│   └── public/
└── setup.py                  # Python package setup
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Gemini API Key

### Backend Setup

1. **Clone and navigate**
   ```bash
   git clone https://github.com/ManojPropheus/terramot-persona.git
   cd terramot-persona
   ```

2. **Install Python dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

4. **Start Flask server**
   ```bash
   python app.py
   ```
   Server runs on `http://localhost:5001`

### Frontend Setup

1. **Install Node dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Start React development server**
   ```bash
   npm start
   ```
   Application runs on `http://localhost:3000`

## 🎯 Usage

1. **Select Location** - Click anywhere on the map to load demographic data
2. **Choose Distribution** - Select from age, gender, education, income, or profession
3. **Conditional Analysis** - For joint distributions, analyze correlations
4. **AI Chat** - Ask questions about the data using natural language
5. **Interactive Insights** - Explore charts with tooltips and detailed breakdowns

## 🤖 AI Chatbot Features

- **Memory Management** - Remembers conversation history and user preferences
- **Location History** - Tracks previously analyzed locations
- **Tool Calling** - Intelligently selects appropriate analysis tools
- **Personalization** - Adapts responses based on user patterns
- **Natural Language** - Ask complex demographic questions in plain English

## 📈 API Endpoints

### Distribution Data
- `POST /distribution` - Get all distributions for coordinates
- `POST /unified_conditional` - Flexible conditional analysis
- `POST /conditional_distribution` - Legacy age-income conditionals

### AI Chatbot
- `POST /chat` - Send message to AI assistant
- `GET /chat/history` - Get conversation history
- `POST /chat/clear` - Clear conversation history

### Utilities
- `POST /geography` - Get location info from coordinates
- `GET /health` - Health check endpoint

## 🎨 Design System

Following **Propheus** design principles:
- **Colors**: Teal (#008a89), Blue (#319dff), Dark theme
- **Typography**: Inter font family with multiple weights
- **Components**: Modern cards, buttons, and form elements
- **Layout**: Clean, professional, technical aesthetic

## 🔧 Configuration

### Environment Variables
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

### Census API
Uses the US Census Bureau's American Community Survey (ACS) 5-Year data:
- **Age**: Subject Table S0101
- **Gender**: Subject Table S0101  
- **Education**: Subject Table S1501
- **Income**: Subject Table S1901
- **Profession**: Subject Table S2401
- **Age-Income**: Detailed Table B19037

## 🚀 Deployment

### Backend (Flask)
```bash
# Production WSGI server
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 app:app
```

### Frontend (React)
```bash
# Build for production
npm run build
# Serve static files with nginx/apache
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request
