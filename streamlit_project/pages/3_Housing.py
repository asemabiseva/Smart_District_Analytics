import streamlit as st
import pandas as pd
import re
import pydeck as pdk
import plotly.express as px

st.set_page_config(page_title="Housing Prices — Almaty", layout="wide", page_icon="🏠")

# ─── District keyword mapping ─────────────────────────────────────────────────
DISTRICT_MAP = {
    "Алмалинский":   {"keywords": ["алмалин", "алматы-центр", "центр", "арбат"],
                      "lat": 43.2565, "lon": 76.9286, "name_en": "Almalinsky"},
    "Бостандыкский": {"keywords": ["бостандык", "самал", "орбита", "коктем", "горный гигант", "юбилейный"],
                      "lat": 43.2200, "lon": 76.8900, "name_en": "Bostandyk"},
    "Медеуский":     {"keywords": ["медеу", "достык", "керемет", "карасай", "нурлытау"],
                      "lat": 43.2300, "lon": 76.9700, "name_en": "Medeu"},
    "Турксибский":   {"keywords": ["турксиб", "шанырак", "жулдыз"],
                      "lat": 43.3100, "lon": 77.0200, "name_en": "Turksib"},
    "Жетысуский":    {"keywords": ["жетысу", "степной", "горный"],
                      "lat": 43.2900, "lon": 76.9900, "name_en": "Zhetysu"},
    "Наурызбайский": {"keywords": ["наурызбай", "думан", "атырау"],
                      "lat": 43.1700, "lon": 76.8100, "name_en": "Nauryzbay"},
    "Ауэзовский":    {"keywords": ["ауэзов", "саяхат", "тастак", "дорожник", "момышулы", "абая"],
                      "lat": 43.2100, "lon": 76.8300, "name_en": "Auezov"},
    "Алатауский":    {"keywords": ["алатау", "кайрат", "акбулак", "шарипова"],
                      "lat": 43.3400, "lon": 76.8800, "name_en": "Alatau"},
}

def detect_district(address: str) -> str:
    if not isinstance(address, str):
        return "Other"
    addr_lower = address.lower()
    for dist, info in DISTRICT_MAP.items():
        for kw in info["keywords"]:
            if kw in addr_lower:
                return dist
    if "р-н" in addr_lower:
        for dist in DISTRICT_MAP:
            if dist[:4].lower() in addr_lower:
                return dist
    return "Other"

def parse_price(price_str) -> float | None:
    if not isinstance(price_str, str):
        return None
    digits = re.sub(r"[^\d]", "", price_str)
    if not digits:
        return None
    return float(digits)

def parse_area(title: str) -> float | None:
    m = re.search(r"(\d+\.?\d*)\s*м²", title)
    return float(m.group(1)) if m else None

def parse_rooms(title: str) -> str:
    m = re.search(r"(\d+)-комнатная", title)
    return m.group(1) + "-к" if m else "Другое"

# ─── Load data ────────────────────────────────────────────────────────────────
@st.cache_data
def load_housing():
    df = pd.read_csv("datasets/krisha_final.csv")
    df["price_num"]  = df["Price"].apply(parse_price)
    df["area_m2"]    = df["Title"].apply(parse_area)
    df["rooms"]      = df["Title"].apply(parse_rooms)
    df["district"]   = df["Address"].apply(detect_district)
    df = df[df["price_num"].notna() & (df["price_num"] > 1_000_000)]
    df["price_M"]    = df["price_num"] / 1_000_000  # millions KZT
    df["price_m2"]   = df["price_num"] / df["area_m2"].replace(0, None)
    return df

try:
    df = load_housing()
except FileNotFoundError:
    st.error("⚠️ Could not find `datasets/krisha_final.csv`. Place the dataset next to the app.")
    st.stop()

# ─── Page header ──────────────────────────────────────────────────────────────
st.title("🏠 Housing Prices — Almaty (Krisha.kz)")
st.markdown("Explore apartment listings across Almaty districts.")

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔍 Filters")
    price_range = st.slider("Price range (million KZT)",
                            float(df["price_M"].min()), float(df["price_M"].quantile(0.99)),
                            (float(df["price_M"].min()), float(df["price_M"].quantile(0.95))))
    room_opts = sorted(df["rooms"].unique())
    sel_rooms = st.multiselect("Room types", room_opts, default=room_opts)
    sel_dists = st.multiselect("Districts", [d for d in DISTRICT_MAP if d in df["district"].unique()],
                                default=[d for d in DISTRICT_MAP if d in df["district"].unique()])

fdf = df[
    (df["price_M"] >= price_range[0]) &
    (df["price_M"] <= price_range[1]) &
    (df["rooms"].isin(sel_rooms)) &
    (df["district"].isin(sel_dists))
]

# ─── KPIs ─────────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Listings", f"{len(fdf):,}")
c2.metric("Median Price", f"{fdf['price_M'].median():.1f}M ₸")
c3.metric("Avg Area", f"{fdf['area_m2'].mean():.0f} m²" if fdf['area_m2'].notna().any() else "—")
c4.metric("Avg Price/m²", f"{fdf['price_m2'].median()/1000:.0f}K ₸" if fdf['price_m2'].notna().any() else "—")

st.markdown("---")

# ─── Map ──────────────────────────────────────────────────────────────────────
st.subheader("🗺️ Average Price by District")

dist_avg = fdf.groupby("district")["price_M"].median().reset_index()
dist_avg.columns = ["district", "median_price"]
price_max = dist_avg["median_price"].max()

map_rows = []
for _, row in dist_avg.iterrows():
    d = row["district"]
    if d in DISTRICT_MAP:
        info = DISTRICT_MAP[d]
        norm = row["median_price"] / price_max if price_max > 0 else 0
        color = [int(255 * norm), int(150 * (1 - norm)), 200, 180]
        map_rows.append({
            "lat": info["lat"], "lon": info["lon"],
            "name_en": info["name_en"],
            "district": d,
            "median_price": f"{row['median_price']:.1f}M ₸",
            "color": color,
            "radius": max(1000, int(row["median_price"] * 30000)),
        })

if map_rows:
    map_df = pd.DataFrame(map_rows)
    layer = pdk.Layer("ScatterplotLayer", data=map_df,
                       get_position=["lon", "lat"], get_color="color",
                       get_radius="radius", opacity=0.75, pickable=True)
    text_layer = pdk.Layer("TextLayer", data=map_df,
                            get_position=["lon", "lat"], get_text="name_en",
                            get_size=14, get_color=[255, 255, 255])
    view = pdk.ViewState(latitude=43.25, longitude=76.93, zoom=10, pitch=30)
    tooltip = {
        "html": "<b>{district}</b><br/>Median Price: <b>{median_price}</b>",
        "style": {"background": "#1e1e2e", "color": "white", "borderRadius": "8px", "padding": "8px"}
    }
    st.pydeck_chart(pdk.Deck(layers=[layer, text_layer], initial_view_state=view,
                              tooltip=tooltip, map_style="mapbox://styles/mapbox/dark-v10"))

st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    st.subheader("💰 Price Distribution by District")
    fig = px.box(fdf[fdf["district"] != "Other"], x="district", y="price_M",
                 color="district", labels={"price_M": "Price (million ₸)", "district": ""},
                 title="Price Spread per District")
    fig.update_layout(template="plotly_dark", showlegend=False,
                      xaxis={"tickangle": -30})
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("🏗️ Price by Room Count")
    fig2 = px.violin(fdf[fdf["rooms"].str.contains(r"\d")], x="rooms", y="price_M",
                     box=True, color="rooms",
                     labels={"price_M": "Price (million ₸)", "rooms": "Room type"})
    fig2.update_layout(template="plotly_dark", showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("📋 Sample Listings")
show_cols = ["Title", "Address", "Price", "district", "rooms", "area_m2"]
show_cols = [c for c in show_cols if c in fdf.columns]
st.dataframe(fdf[show_cols].head(50).reset_index(drop=True), use_container_width=True)
