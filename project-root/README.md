# Smart District Analytics: A Data-Driven Housing Selection Platform for Almaty

**An interactive analytics platform helping users make informed housing decisions in Almaty through data science and machine learning.**

## 🏙️ Problem Statement
Choosing a place to live in Almaty is a complex decision influenced by safety, housing prices, environmental conditions, and infrastructure. Currently, this information is scattered across different sources and is not integrated into a single analytical platform. This fragmentation leads to housing decisions made without comprehensive data comparison, potentially resulting in financial or lifestyle dissatisfaction.

## 🚀 Key Features
* **Interactive District Comparison:** Compare districts and neighborhoods based on real-time metrics.
* **Safety Index:** A data-driven score calculated from historical traffic accident statistics.
* **Environmental Score:** Analysis of air quality and ecological indicators across different city sectors.
* **Price Prediction:** A regression-based model to analyze housing affordability and predict market prices.
* **Customizable Ranking:** A multi-criteria scoring system that allows users to weight priorities like price, safety, or ecology.
* **Data Visualization:** Interactive maps, heatmaps, and charts powered by ArcGIS and Plotly.

## 🛠️ Technology Stack
* **Frontend:** Streamlit
* **Backend:** Python
* **Data Analytics:** Pandas, NumPy, Matplotlib, Plotly
* **Machine Learning:** Scikit-learn (Regression & Clustering)
* **Database:** ArcGIS
* **Deployment:** Streamlit Cloud

## 📁 Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the app
```bash
streamlit run Home.py
```

## 🗺️ Pages

| Page | Data used | Features |
|------|-----------|---------|
| 🌬️ Air Quality | `processed_air_ala_data.csv` | Interactive map, PM2.5/PM10 trends by district |
| 🚗 Accidents | `processed_table.csv` | Heatmap, ML severity predictor (Random Forest) |
| 🏠 Housing | `krisha_final.csv` | Price map, box plots, listing table |
| 📈 Forecast | `processed_table.csv` | SARIMA forecast, confidence intervals |

## 🗺️ Maps
Maps use **pydeck** (PyDeck) which is a Python wrapper around deck.gl.  
For full Mapbox basemap tiles, set a Mapbox token:
```bash
export MAPBOX_API_KEY=pk.eyJ1IjoiYWlnYTIiLCJhIjoiY21ucnl4bzlyMDd0aTJzcXk1Nno4bjg4aCJ9.a-IzFh4dtA7zz8InRtwGSA
```
Or in `.streamlit/secrets.toml`:
```toml
MAPBOX_API_KEY = "your_token_here"
```
Without a token the map will still work but show a plain base layer.

## RESEARCH PAPER
## Data-Driven Road Accident Probability Modeling and Fatality-Based Clustering in Almaty: A Machine Learning Approach to Public Safety Improvement
### Abstract
In the urban world, road traffic accidents have become a big social safety issue that causes massive losses to people, economies, and infrastructures annually. It is necessary to know the circumstances in which accidents happen and escalate in order to minimize their effects. This paper focuses on road traffic accidents in Almaty, Kazakhstan based on the past record of accidents experienced during the period between 2015 and 2025 to examine the risk factors, the level of accidents and the future trends of accidents. The research approximates the likelihood of the occurrence of accidents in different conditions and categorizes accidents according to their fatal and non-fatal results. The models of supervised machine learning are used to forecast the severity of accidents and determine the factors that have an impact on them, whereas clustering of accidents is done using the unsupervised methods. Moreover, time-series analysis is also used to model time-behavior and predict the future quantities of accidents using past data. The findings have practical implications on the high risk conditions, hazardous sites and severity profiles that can be used in decision making on road safety enhancement, emergency management plans, and urban infrastructure development in Almaty.
