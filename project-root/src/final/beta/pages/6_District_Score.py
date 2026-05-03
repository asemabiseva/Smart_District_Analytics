import re

import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path

# Resolve paths relative to script location
SCRIPT_DIR = Path(__file__).parent.parent.absolute()

from app import (
    DISTRICT_COORDS,
    DISTRICT_KEYWORDS,
    apply_base_style,
    render_theme_toggle,
    max_dataset_mtime,
    render_data_freshness,
    render_feedback_widget,
    render_glossary,
    render_insight,
    render_page_intro,
    sidebar_common_filters,
)

st.set_page_config(page_title="District Score - Almaty", layout="wide", page_icon="🏆")
apply_base_style()
render_theme_toggle()


def detect_district(address: str) -> str:
    """Detect district using centralized DISTRICT_KEYWORDS."""
    if not isinstance(address, str):
        return "Other"
    addr_lower = address.lower()
    for district, keywords in DISTRICT_KEYWORDS.items():
        if any(key in addr_lower for key in keywords):
            return district
    return "Other"


def parse_price(price_str: str) -> float | None:
    if not isinstance(price_str, str):
        return None
    digits = re.sub(r"[^\d]", "", price_str)
    if not digits:
        return None
    return float(digits)


def normalize_series(s: pd.Series, invert: bool = False) -> pd.Series:
    if s.empty:
        return s
    min_v, max_v = float(s.min()), float(s.max())
    if max_v - min_v <= 1e-9:
        out = pd.Series([0.5] * len(s), index=s.index)
    else:
        out = (s - min_v) / (max_v - min_v)
    return 1 - out if invert else out


@st.cache_data
def load_components() -> pd.DataFrame:
    air = pd.read_csv(str(SCRIPT_DIR / "datasets/processed_air_ala_data.csv"), parse_dates=["date"])
    acc = pd.read_csv(str(SCRIPT_DIR / "datasets/processed_table.csv"), parse_dates=["Accident_Date"])
    house = pd.read_csv(str(SCRIPT_DIR / "datasets/krisha_final.csv"))
    edu = pd.read_csv(str(SCRIPT_DIR / "datasets/Almaty_Education_Master.csv"))
    hosp = pd.read_csv(str(SCRIPT_DIR / "datasets/hospitals_almaty.csv"))

    # Air component
    latest_date = air["date"].max()
    air_df = (
        air[air["date"] == latest_date]
        .groupby("district")["pm25_avg"]
        .mean()
        .rename("air_pm25")
        .to_frame()
    )

    # Accident component
    acc["severe"] = (acc["Number_of_Injured"] > 1).astype(int)
    code_to_name = {191910: "Алмалинский", 191960: "Бостандыкский", 191956: "Медеуский", 191966: "Турксибский", 191932: "Жетысуский", 191934: "Наурызбайский", 191916: "Ауэзовский", 191926: "Алатауский"}
    acc["district_name"] = acc["District"].map(code_to_name)
    acc_df = (
        acc.dropna(subset=["district_name"])
        .groupby("district_name")["severe"]
        .mean()
        .rename("accident_severity")
        .to_frame()
    )

    # Housing component
    house["district"] = house["Address"].apply(detect_district)
    house["price"] = house["Price"].apply(parse_price)
    house_df = (
        house[house["district"] != "Other"]
        .dropna(subset=["price"])
        .groupby("district")["price"]
        .median()
        .rename("median_price")
        .to_frame()
    )

    # Infrastructure component
    edu["District"] = edu["District"].replace("Наурызбайскйи", "Наурызбайский")
    infra_edu = edu.groupby("District").size().rename("edu_count")
    infra_hosp = hosp.assign(dummy=1).groupby(lambda _: "all")["dummy"].sum()
    if len(infra_hosp):
        hospital_proxy = pd.Series({d: float(infra_hosp.iloc[0]) / len(DISTRICT_COORDS) for d in DISTRICT_COORDS})
    else:
        hospital_proxy = pd.Series({d: 0.0 for d in DISTRICT_COORDS})
    infra_df = pd.concat([infra_edu, hospital_proxy.rename("hosp_proxy")], axis=1).fillna(0)
    infra_df["infra_total"] = infra_df["edu_count"] + infra_df["hosp_proxy"]
    infra_df = infra_df[["infra_total"]]

    merged = air_df.join(acc_df, how="outer")
    merged = merged.join(house_df, how="outer")
    merged = merged.join(infra_df, how="outer")
    merged = merged.fillna(merged.median(numeric_only=True)).reset_index().rename(columns={"index": "district"})

    merged["air_risk"] = normalize_series(merged["air_pm25"], invert=False)
    merged["safety_risk"] = normalize_series(merged["accident_severity"], invert=False)
    merged["affordability_score"] = normalize_series(merged["median_price"], invert=True)
    merged["infrastructure_score"] = normalize_series(merged["infra_total"], invert=False)
    return merged


try:
    score_df = load_components()
except FileNotFoundError as exc:
    st.error(f"Missing input for district score: {exc}")
    st.stop()

st.title("District Score")
render_page_intro(
    problem="Rank districts by your priorities across air risk, safety risk, affordability, and infrastructure.",
    how_to_use=[
        "Set weights in sidebar.",
        "Check top and bottom districts.",
        "Open page-level details to validate final choice.",
    ],
)

available = sorted([d for d in score_df["district"].dropna().unique() if d in DISTRICT_COORDS])
selected, _ = sidebar_common_filters(available, key_prefix="district_score")
if selected:
    score_df = score_df[score_df["district"].isin(selected)]

with st.sidebar:
    st.header("Weight settings")
    w_air = st.slider("Air quality risk", 0.0, 1.0, 0.30, 0.05)
    w_safety = st.slider("Road safety risk", 0.0, 1.0, 0.30, 0.05)
    w_afford = st.slider("Affordability", 0.0, 1.0, 0.20, 0.05)
    w_infra = st.slider("Infrastructure", 0.0, 1.0, 0.20, 0.05)

weight_sum = max(0.001, w_air + w_safety + w_afford + w_infra)
w_air, w_safety, w_afford, w_infra = (
    w_air / weight_sum,
    w_safety / weight_sum,
    w_afford / weight_sum,
    w_infra / weight_sum,
)

score_df["district_score"] = 100 * (
    (1 - score_df["air_risk"]) * w_air
    + (1 - score_df["safety_risk"]) * w_safety
    + score_df["affordability_score"] * w_afford
    + score_df["infrastructure_score"] * w_infra
)
score_df = score_df.sort_values("district_score", ascending=False)

if len(score_df):
    best = score_df.iloc[0]
    worst = score_df.iloc[-1]
    c1, c2, c3 = st.columns(3)
    c1.metric("Best district", best["district"], f"{best['district_score']:.1f}")
    c2.metric("Lowest district", worst["district"], f"{worst['district_score']:.1f}")
    c3.metric("Spread", f"{best['district_score'] - worst['district_score']:.1f}")

    render_insight(
        title="Ranking explanation",
        finding=f"{best['district']} leads under the selected weights.",
        action="Validate this candidate against Air, Accidents, and Housing pages before final decision.",
        risk="low",
    )

fig = px.bar(
    score_df,
    x="district",
    y="district_score",
    color="district_score",
    color_continuous_scale=["#D64545", "#E6A700", "#1F9D55"],
    title="District Score (0-100)",
)
fig.update_layout(template="plotly_dark", showlegend=False)
st.plotly_chart(fig, use_container_width=True)

show_cols = [
    "district",
    "district_score",
    "air_pm25",
    "accident_severity",
    "median_price",
    "infra_total",
]
st.dataframe(score_df[show_cols].reset_index(drop=True), use_container_width=True)

render_glossary(
    {
        "District Score": "Weighted 0-100 composite where higher is better.",
        "Air/Safety risk": "Higher values increase district penalty.",
        "Affordability": "Higher values reflect relatively lower prices.",
    }
)

render_data_freshness(
    updated_at=max_dataset_mtime(
        [
            "datasets/processed_air_ala_data.csv",
            "datasets/processed_table.csv",
            "datasets/krisha_final.csv",
            "datasets/Almaty_Education_Master.csv",
            "datasets/hospitals_almaty.csv",
        ]
    ),
    source_list=[
        "processed_air_ala_data.csv",
        "processed_table.csv",
        "krisha_final.csv",
        "Almaty_Education_Master.csv",
        "hospitals_almaty.csv",
    ],
    limitations=[
        "Score is comparative and depends on current weight choices.",
        "Hospital component uses a proxy allocation when district labels are missing.",
    ],
)

render_feedback_widget("District_Score")
