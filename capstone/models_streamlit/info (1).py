import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Accident Dataset Exploration",
    layout="wide"
)

# ======================
# LOAD DATA
# ======================
@st.cache_data
def load_data():
    df = pd.read_csv("AlmatyDTP.csv")
    df["Accident_Date"] = pd.to_datetime(df["Accident_Date"], errors="coerce")

    # Same definition as your project
    df["Severe_Accident"] = (df["Number_of_Injured"] > 1).astype(int)

    return df

df = load_data()

# ======================
# TITLE
# ======================
st.title(" Accident Dataset Exploration Dashboard")
st.write(
    "Interactive analysis of road accident data. "
    "Use filters to explore patterns by location, district, weather, and severity."
)

st.divider()

# ======================
# FILTERS
# ======================
st.subheader(" Filters")

col1, col2, col3 = st.columns(3)

with col1:
    locations = st.multiselect(
        "Accident Location",
        options=sorted(df["Accident_Location"].dropna().unique())
    )

with col2:
    districts = st.multiselect(
        "District",
        options=sorted(df["District"].dropna().unique())
    )

with col3:
    weather = st.multiselect(
        "Weather Conditions",
        options=sorted(df["Weather_Conditions"].dropna().unique())
    )

filtered_df = df.copy()

if locations:
    filtered_df = filtered_df[filtered_df["Accident_Location"].isin(locations)]

if districts:
    filtered_df = filtered_df[filtered_df["District"].isin(districts)]

if weather:
    filtered_df = filtered_df[filtered_df["Weather_Conditions"].isin(weather)]

st.divider()

# ======================
# KPI METRICS
# ======================
st.subheader("📌 Overview")

c1, c2, c3 = st.columns(3)

c1.metric("Total Accidents", len(filtered_df))
c2.metric("Severe Accidents", int(filtered_df["Severe_Accident"].sum()))
c3.metric(
    "Severe Accident Rate",
    f"{filtered_df['Severe_Accident'].mean() * 100:.1f}%"
    if len(filtered_df) > 0 else "0%"
)

st.divider()

# ======================
# ACCIDENTS BY LOCATION
# ======================
st.subheader("Accidents by Location")

location_counts = filtered_df["Accident_Location"].value_counts()

st.bar_chart(location_counts)

# ======================
# ACCIDENTS BY DISTRICT
# ======================
st.subheader(" Accidents by District")

district_counts = filtered_df["District"].value_counts()

st.bar_chart(district_counts)

# ======================
# SEVERITY DISTRIBUTION
# ======================
st.subheader(" Severity Distribution")

severity_counts = filtered_df["Severe_Accident"].value_counts()
severity_counts.index = ["Not Severe", "Severe"]

st.bar_chart(severity_counts)

# ======================
# WEATHER vs ACCIDENTS
# ======================
st.subheader(" Weather Conditions vs Accidents")

weather_counts = filtered_df["Weather_Conditions"].value_counts()

st.bar_chart(weather_counts)

# ======================
# ROAD SURFACE vs SEVERITY
# ======================
st.subheader(" Road Surface vs Severity")

surface_severity = (
    filtered_df
    .groupby("Road_Surface_Condition")["Severe_Accident"]
    .mean()
    .sort_values(ascending=False)
)

st.bar_chart(surface_severity)

# ======================
# RAW DATA (OPTIONAL)
# ======================
with st.expander("📄 Show filtered data table"):
    st.dataframe(filtered_df)
