import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

# Resolve paths relative to script location
SCRIPT_DIR = Path(__file__).parent.parent.absolute()
ACCIDENTS_DATASET = SCRIPT_DIR / "datasets/jestka_preprocessed_dataset.csv"

from app import (
    apply_base_style,
    render_theme_toggle,
    max_dataset_mtime,
    render_data_freshness,
    render_feedback_widget,
    render_glossary,
    render_insight,
    render_page_intro,
    severity_bucket,
)

st.set_page_config(page_title="Accident Forecast - Almaty", layout="wide", page_icon="📈")
apply_base_style()
render_theme_toggle()

@st.cache_data
def load_data():
    df = pd.read_csv(str(ACCIDENTS_DATASET), parse_dates=["Accident_Date"])
    df = df.dropna(subset=["Accident_Date"]).set_index("Accident_Date")
    monthly = df.resample("ME").size().rename("accidents")
    return monthly

@st.cache_resource
def train_sarima(ts_tuple):
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    ts = pd.Series(ts_tuple[1], index=pd.DatetimeIndex(ts_tuple[0]))
    model = SARIMAX(ts, order=(1,1,1), seasonal_order=(1,1,1,12),
                    enforce_stationarity=False, enforce_invertibility=False)
    return model.fit(disp=False)

try:
    monthly = load_data()
except FileNotFoundError:
    st.error("⚠️ Could not find `datasets/jestka_preprocessed_dataset.csv`. Place the dataset next to the app.")
    st.stop()

st.title("Accident Forecast")
render_page_intro(
    problem="Estimate near-term accident pressure to plan staffing and prevention proactively.",
    how_to_use=[
        "Set forecast horizon.",
        "Read forecast average and confidence interval.",
        "Use insights for monthly enforcement/resource planning.",
    ],
)
st.markdown("SARIMA time-series model predicting future monthly accident counts.")

with st.sidebar:
    st.header("⚙️ Model Settings")
    horizon = st.slider("Forecast horizon (months)", 3, 24, 12)
    show_ci = st.checkbox("Show confidence interval", value=True)

with st.spinner("Fitting SARIMA model..."):
    ts_tuple = (monthly.index.tolist(), monthly.values.tolist())
    result = train_sarima(ts_tuple)

# ─── KPIs ─────────────────────────────────────────────────────────────────────
forecast = result.get_forecast(steps=horizon)
fc_mean  = forecast.predicted_mean
fc_ci    = forecast.conf_int()

c1, c2, c3 = st.columns(3)
c1.metric("Historical Average (monthly)", f"{monthly.mean():.0f}")
c2.metric("Forecasted Average (next period)", f"{fc_mean.mean():.0f}")
delta = fc_mean.mean() - monthly.mean()
c3.metric("Change vs Historical", f"{delta:+.0f}", delta_color="inverse")

risk = severity_bucket(float(delta), 0.0, 30.0)
direction = "increase" if delta >= 0 else "decrease"
render_insight(
    title="Forecast signal",
    finding=f"Model projects an average {direction} of {abs(delta):.0f} accidents/month versus history.",
    action="Align traffic police scheduling and campaign intensity with projected high months.",
    risk=risk,
)

st.markdown("---")

# ─── Forecast plot ────────────────────────────────────────────────────────────
st.subheader("Monthly Accident Forecast")

fig = go.Figure()
fig.add_trace(go.Scatter(x=monthly.index, y=monthly.values,
                          name="Historical", line=dict(color="#4fc3f7", width=2)))
fig.add_trace(go.Scatter(x=fc_mean.index, y=fc_mean.values,
                          name="Forecast", line=dict(color="#e94560", width=2, dash="dash")))
if show_ci:
    fig.add_trace(go.Scatter(
        x=list(fc_ci.index) + list(fc_ci.index[::-1]),
        y=list(fc_ci.iloc[:, 1]) + list(fc_ci.iloc[::-1, 0]),
        fill="toself", fillcolor="rgba(233,69,96,0.15)",
        line=dict(color="rgba(255,255,255,0)"),
        name="95% CI"
    ))
fig.update_layout(template="plotly_dark", height=450,
                  xaxis_title="Date", yaxis_title="Monthly Accidents",
                  legend=dict(bgcolor="rgba(0,0,0,0)"))
st.plotly_chart(fig, use_container_width=True)

# ─── Forecast table ───────────────────────────────────────────────────────────
st.subheader("Forecast Table")
fc_df = pd.DataFrame({
    "Month": fc_mean.index.strftime("%Y-%m"),
    "Predicted Accidents": fc_mean.values.astype(int),
    "Lower 95% CI": fc_ci.iloc[:, 0].values.astype(int),
    "Upper 95% CI": fc_ci.iloc[:, 1].values.astype(int),
})
st.dataframe(fc_df.reset_index(drop=True), use_container_width=True)

st.markdown("---")
# ─── Seasonal decomposition chart ────────────────────────────────────────────
st.subheader("Historical Seasonality")
monthly_by_month = monthly.groupby(monthly.index.month).mean()
fig2 = px.bar(x=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],
              y=monthly_by_month.values,
              labels={"x": "Month", "y": "Avg Accidents"},
              color=monthly_by_month.values,
              color_continuous_scale="RdYlGn_r",
              title="Average Monthly Accidents by Calendar Month")
fig2.update_layout(template="plotly_dark", showlegend=False)
st.plotly_chart(fig2, use_container_width=True)

render_glossary(
    {
        "SARIMA": "Seasonal time series model that captures trend and yearly periodicity.",
        "95% CI": "Expected range where future values are likely to fall.",
    }
)

render_data_freshness(
    updated_at=max_dataset_mtime(["datasets/processed_table.csv"]),
    source_list=["processed_table.csv"],
    limitations=[
        "Forecast uses historical aggregate counts without exogenous events.",
        "Confidence intervals widen for longer horizons.",
    ],
)

render_feedback_widget("Forecast")
