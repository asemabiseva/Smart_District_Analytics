import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from statsmodels.tsa.statespace.sarimax import SARIMAX

st.set_page_config(
    page_title="Accident Time Series Forecast",
    layout="wide"
)

# =========================
# LOAD & PREPARE DATA
# =========================
@st.cache_data
def load_time_series():
    df = pd.read_csv("AlmatyDTP.csv")
    df["Accident_Date"] = pd.to_datetime(df["Accident_Date"], errors="coerce")

    df = df.dropna(subset=["Accident_Date"])
    df = df.set_index("Accident_Date")

    # Monthly accident counts
    monthly_accidents = df.resample("M").size()

    return monthly_accidents

monthly_accidents = load_time_series()

# =========================
# TRAIN SARIMA MODEL
# =========================
@st.cache_resource
def train_sarima(ts):
    model = SARIMAX(
        ts,
        order=(1, 1, 1),
        seasonal_order=(1, 1, 1, 12),
        enforce_stationarity=False,
        enforce_invertibility=False
    )
    return model.fit()

sarima_result = train_sarima(monthly_accidents)

# =========================
# STREAMLIT UI
# =========================
st.title("Accident Time Series Forecasting (SARIMA)")
st.write(
    "Forecasting future **monthly accident counts** using a Seasonal ARIMA model."
)

st.divider()

# =========================
# USER CONTROL
# =========================
forecast_horizon = st.slider(
    "Select Forecast Horizon (months)",
    min_value=3,
    max_value=24,
    value=12,
    step=1
)

# =========================
# FORECAST
# =========================
future_forecast = sarima_result.predict(
    start=monthly_accidents.index[-1],
    end=monthly_accidents.index[-1] + pd.DateOffset(months=forecast_horizon)
)

# =========================
# PLOT
# =========================
st.subheader(" Accident Forecast")

fig, ax = plt.subplots(figsize=(14,5))
ax.plot(monthly_accidents, label="Historical")
ax.plot(future_forecast, label="Forecast", color="red")
ax.set_title("Monthly Accident Forecast")
ax.set_xlabel("Date")
ax.set_ylabel("Number of Accidents")
ax.legend()

st.pyplot(fig)

# =========================
# FORECAST TABLE
# =========================
st.subheader("Forecast Table")

forecast_df = pd.DataFrame({
    "Month": future_forecast.index,
    "Predicted_Accidents": future_forecast.values.astype(int)
})

st.dataframe(forecast_df)
