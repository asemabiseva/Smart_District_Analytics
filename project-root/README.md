# 🏙️ Almaty Living Guide — Streamlit App

A multi-page interactive dashboard about Almaty districts covering air quality, road accidents, housing prices and forecasting.

## 📁 Setup

### 1. Folder structure
```
almaty_app/
├── Home.py
├── requirements.txt
├── pages/
│   ├── 1_Air_Quality.py
│   ├── 2_Accidents.py
│   ├── 3_Housing.py
│   └── 4_Forecast.py
└── datasets/
    ├── processed_air_ala_data.csv   ← from your capstone/datasets/
    ├── processed_table.csv          ← from your capstone/datasets/
    └── krisha_final.csv             ← from your capstone/datasets/
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the app
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
