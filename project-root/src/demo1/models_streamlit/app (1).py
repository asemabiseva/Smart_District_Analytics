import streamlit as st
import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import RandomizedSearchCV

st.set_page_config(
    page_title="Accident Severity Predictor",
    layout="centered"
)

# =========================
# LOAD DATA + TRAIN MODEL
# =========================
@st.cache_resource
def train_best_random_forest():
    df = pd.read_csv("AlmatyDTP.csv")
    df["Accident_Date"] = pd.to_datetime(df["Accident_Date"], errors="coerce")

    # Target (EXACTLY as in your notebook)
    df["Severe_Accident"] = (df["Number_of_Injured"] > 1).astype(int)

    categorical_features = ["Accident_Location", "District"]

    X = df.drop(columns=[
        "Accident_Type",
        "Accident_Date",
        "Number_of_Injured",
        "Severe_Accident"
    ])

    X = pd.get_dummies(X, columns=categorical_features)
    y = df["Severe_Accident"]

    # Base RF
    rf = RandomForestClassifier(
        random_state=42,
        n_jobs=-1,
        class_weight="balanced"
    )

    # Hyperparameter space (YOUR VERSION)
    param_dist = {
        'n_estimators': [150, 200, 300, 400],
        'max_depth': [8, 10, 12, None],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4],
        'max_features': ['sqrt', 'log2']
    }

    tuner = RandomizedSearchCV(
        estimator=rf,
        param_distributions=param_dist,
        n_iter=25,
        cv=5,
        scoring='f1',
        random_state=42,
        n_jobs=-1,
        verbose=0
    )

    tuner.fit(X, y)

    best_rf = tuner.best_estimator_

    return best_rf, X.columns, df, tuner.best_params_

best_model, model_columns, df, best_params = train_best_random_forest()

# =========================
# STREAMLIT UI
# =========================
st.title(" Accident Severity Predictor")
st.write("Prediction using a **hyperparameter-tuned Random Forest model**.")

st.subheader(" Best Model Parameters")
st.json(best_params)

st.divider()

# =========================
# USER INPUTS
# =========================
st.subheader("Enter Accident Details")

accident_location = st.selectbox(
    "Accident Location",
    sorted(df["Accident_Location"].dropna().unique())
)

district = st.selectbox(
    "District",
    sorted(df["District"].dropna().unique())
)

weather = st.selectbox(
    "Weather Conditions",
    sorted(df["Weather_Conditions"].dropna().unique())
)

lighting = st.selectbox(
    "Lighting Conditions",
    sorted(df["Lighting_Conditions"].dropna().unique())
)

street_lighting = st.selectbox(
    "Street Lighting at Night",
    sorted(df["Street_Lighting_Night"].dropna().unique())
)

road_surface = st.selectbox(
    "Road Surface Condition",
    sorted(df["Road_Surface_Condition"].dropna().unique())
)

speed_limit = st.slider(
    "Speed Limit (km/h)",
    min_value=20,
    max_value=140,
    step=10
)

gender = st.selectbox(
    "Fault Person Gender",
    sorted(df["Fault_Person_Gender"].dropna().unique())
)

# =========================
# PREDICTION
# =========================
if st.button("Predict Accident Severity"):
    input_data = {
        "Lighting_Conditions": lighting,
        "Street_Lighting_Night": street_lighting,
        "Weather_Conditions": weather,
        "Speed_Limit": speed_limit,
        "Fault_Person_Gender": gender,
        "Road_Surface_Condition": road_surface,
        "Accident_Location": accident_location,
        "District": district
    }

    input_df = pd.DataFrame([input_data])

    # One-hot encoding
    input_df = pd.get_dummies(input_df)

    # Align with training columns
    input_df = input_df.reindex(columns=model_columns, fill_value=0)

    # Prediction
    prediction = best_model.predict(input_df)[0]
    probability = best_model.predict_proba(input_df)[0][1]

    st.divider()

    if prediction == 1:
        st.error(f" **Severe Accident Likely**\n\nProbability: **{probability:.2%}**")
    else:
        st.success(f"**Accident Likely NOT Severe**\n\nProbability: **{probability:.2%}**")
