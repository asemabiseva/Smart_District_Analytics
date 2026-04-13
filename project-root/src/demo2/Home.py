import streamlit as st

st.set_page_config(
    page_title="Almaty Living Guide",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .hero {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 3rem 2rem;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 2rem;
    }
    .hero h1 { color: #e94560; font-size: 3rem; margin-bottom: 0.5rem; }
    .hero p  { color: #a8b2d8; font-size: 1.2rem; }
    .card {
        background: #1e1e2e;
        border: 1px solid #2d2d42;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        transition: border-color 0.2s;
    }
    .card:hover { border-color: #e94560; }
    .card-icon { font-size: 2.5rem; margin-bottom: 0.5rem; }
    .card-title { color: #cdd6f4; font-weight: 700; font-size: 1.1rem; }
    .card-desc { color: #a6adc8; font-size: 0.9rem; margin-top: 0.3rem; }
    [data-testid="stSidebar"] { background: #1e1e2e; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <h1>🏙️ Almaty Living Guide</h1>
    <p>Explore Almaty districts by air quality, accidents, housing prices & more</p>
</div>
""", unsafe_allow_html=True)

cols = st.columns(4)
cards = [
    ("🌬️", "Air Quality", "PM2.5 & PM10 by district, real-time monitoring", "pages/1_Air_Quality.py"),
    ("🚗", "Road Accidents", "Severity prediction & accident hotspot maps", "pages/2_Accidents.py"),
    ("🏠", "Housing Prices", "Krisha.kz listings by district & price range", "pages/3_Housing.py"),
    ("📈", "Forecasting", "SARIMA time-series accident forecasting", "pages/4_Forecast.py"),
]
for col, (icon, title, desc, _) in zip(cols, cards):
    with col:
        st.markdown(f"""
        <div class="card">
            <div class="card-icon">{icon}</div>
            <div class="card-title">{title}</div>
            <div class="card-desc">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")
st.markdown("### 🗺️ About this project")
st.markdown("""
This dashboard helps residents and newcomers understand Almaty's districts across multiple dimensions:

- **Air Quality** — Hourly PM2.5 and PM10 data across 8 districts with color-coded map
- **Road Safety** — Accident hotspots, severity prediction using Random Forest ML model  
- **Housing** — Krisha.kz rental/sale listings parsed by district and price
- **Forecasting** — SARIMA model predicting future monthly accident counts

Use the sidebar to navigate between pages.
""")

st.info("👈 Use the sidebar to navigate between sections of the dashboard.")
