# Census Distribution Explorer

A modern web application for exploring U.S. Census demographic data through interactive maps and animated charts. Click anywhere on the US map to get real-time age, gender, education, and income distributions for that location.

## ✨ Features

- **Interactive US Map**: Full-screen Folium map with click-to-explore functionality
- **Real-time Census Data**: Live data from U.S. Census Bureau APIs
- **4 Distribution Types**: Age, Gender, Education, and Income demographics
- **Animated Charts**: Beautiful bar chart visualizations using Plotly
- **Modern Design**: Clean, minimal Streamlit interface with custom styling
- **Responsive Layout**: Works on desktop and mobile devices

## 🚀 Quick Start

### Backend Setup

1. **Install Python dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Start the Flask API**:
   ```bash
   python app.py
   ```
   Server runs on `http://localhost:5001`

### Frontend Setup

1. **Install Python dependencies**:
   ```bash
   cd frontend
   pip install -r requirements.txt
   ```

2. **Start the Streamlit app**:
   ```bash
   streamlit run app.py
   ```
   App runs on `http://localhost:8501`

## 📱 Usage

1. Open `http://localhost:8501` in your browser
2. Click anywhere on the US map
3. View animated charts showing demographic distributions for that location
4. Navigate through tabs: Age → Gender → Education → Income
5. Explore summary statistics and metrics for each distribution

## 🏗️ Architecture

```
Data_collection_pipeline/
├── backend/                 # Flask API server
│   ├── app.py              # Main API with /distribution endpoint
│   └── requirements.txt    # Python dependencies
├── distribution/           # Census data modules
│   ├── age_distribution.py
│   ├── gender_distribution.py
│   ├── education_distribution.py
│   └── income_distribution.py
├── frontend/               # Streamlit application
│   ├── app.py             # Main Streamlit app with Folium map
│   └── requirements.txt   # Python dependencies
└── README.md              # This file
```

## 🛠️ Dependencies

### Backend (Python)
- **Flask**: Web framework for the API
- **Flask-CORS**: Cross-origin resource sharing
- **requests**: HTTP client for Census API calls
- **pandas**: Data manipulation and analysis

### Frontend (Python)
- **Streamlit**: Web app framework
- **Folium**: Interactive map visualization
- **Plotly**: Animated chart library
- **Streamlit-Folium**: Streamlit + Folium integration

## 📊 Data Sources

All demographic data comes directly from the U.S. Census Bureau:
- **Age Distribution**: ACS Subject Table S0101
- **Gender Distribution**: ACS Subject Table S0101
- **Education Distribution**: ACS Subject Table S1501
- **Income Distribution**: ACS Subject Table S1901

## 🎨 Design

- **Modern UI**: Clean, minimal Streamlit interface with custom CSS styling
- **Interactive Charts**: Plotly charts with hover effects and smooth animations
- **Tabbed Interface**: Easy navigation between different distribution types
- **Responsive**: Adapts to different screen sizes automatically
- **Color Coded**: Each distribution type has its own color theme