# import streamlit as st
# import pandas as pd
# import re
# import requests
# from bs4 import BeautifulSoup
# from pathlib import Path

# # Ensure all paths are relative to this script, not the working directory
# SCRIPT_DIR = Path(__file__).parent.absolute()

# from app import (
#     apply_base_style,
#     render_data_freshness,
#     render_feedback_widget,
#     render_glossary,
#     render_insight,
#     render_page_intro,
#     render_theme_toggle,
#     safe_read_csv as _safe_read_csv_orig,
#     DISTRICT_COORDS,
#     DISTRICT_KEYWORDS,
#     ValidationError,
#     validate_price,
#     validate_address,
#     validate_coordinates,
#     validate_district,
#     validate_url,
#     geocode_address,
#     format_error_message,
#     format_success_message,
# )

# # Monkey-patch safe_read_csv to use absolute paths
# def safe_read_csv(path: str, **kwargs) -> pd.DataFrame:
#     """Load CSV with absolute path resolution relative to script location."""
#     abs_path = SCRIPT_DIR / path
#     return _safe_read_csv_orig(str(abs_path), **kwargs)

# from app.listing_analyzer import analyze_listing, infer_district
# from app.theme import get_theme

# st.set_page_config(
#     page_title="Almaty Living Guide",
#     page_icon="🏙️",
#     layout="wide",
#     initial_sidebar_state="expanded",
# )

# apply_base_style()
# render_theme_toggle()

# # --- Session history initialization
# if "analysis_history" not in st.session_state:
#     st.session_state["analysis_history"] = []


# def _auto_geocode_and_infer():
#     """Callback to geocode address and infer district when the address input changes.

#     This sets `home_listing_lat`, `home_listing_lon`, and `home_listing_district` in session_state.
#     """
#     addr = st.session_state.get("home_listing_address", "")
#     if not addr:
#         return
#     # Try geocoding
#     coords = None
#     try:
#         coords = geocode_address(addr, timeout=3)
#     except Exception:
#         coords = None
#     if coords:
#         st.session_state["home_listing_lat"] = f"{coords[0]:.6f}"
#         st.session_state["home_listing_lon"] = f"{coords[1]:.6f}"
#     # Infer district from address keywords
#     try:
#         inferred = infer_district(addr)
#         if inferred and inferred in DISTRICT_COORDS:
#             st.session_state["home_listing_district"] = inferred
#     except Exception:
#         pass

# # ─── HERO SECTION ─────────────────────────────────────────────────────────────
# theme = get_theme(st.session_state.get("theme_mode", "light"))
# st.markdown(f"""
# <div class='hero-box'>
#     <h1>🏙️ Almaty Living Guide</h1>
#     <p>Find the best district for you: Compare safety, air quality, housing prices & services</p>
# </div>
# """, unsafe_allow_html=True)

# # ─── STEP 1: SELECT DISTRICT ──────────────────────────────────────────────────
# st.markdown("## 1️⃣ Choose a District")

# col1, col2 = st.columns([2, 1])

# with col1:
#     selected_district = st.selectbox(
#         "Select a district to explore:",
#         options=sorted(DISTRICT_COORDS.keys()),
#         index=0,
#         help="Click to see all 8 districts in Almaty"
#     )

# with col2:
#     st.info(f"📍 **{selected_district}** selected")

# # ─── STEP 2: KEY METRICS FOR SELECTED DISTRICT ────────────────────────────────
# st.markdown("## 2️⃣ District Overview")
# st.markdown(f"**{selected_district}** — Key statistics at a glance")

# metric_cols = st.columns(4)

# # Air Quality
# try:
#     air = safe_read_csv("datasets/processed_air_ala_data.csv")
#     air["date"] = pd.to_datetime(air["date"], errors="coerce") if "date" in air.columns else None
#     if air is not None and not air.empty and "date" in air.columns:
#         latest_date = air["date"].max()
#         latest_air = air.loc[air["date"] == latest_date].groupby("district")["pm25_avg"].mean()
#     else:
#         latest_air = pd.Series(dtype=float)

#     air_pm25 = latest_air.get(selected_district, None)

#     with metric_cols[0]:
#         if air_pm25 is not None and not pd.isna(air_pm25):
#             if air_pm25 < 35:
#                 status = "🟢 Good"
#             elif air_pm25 < 75:
#                 status = "🟡 Moderate"
#             else:
#                 status = "🔴 Poor"
#             st.metric("Air Quality (PM2.5)", f"{air_pm25:.1f} µg/m³", status)
#         else:
#             # Fallback to city average if available
#             if not latest_air.empty:
#                 city_avg = float(latest_air.mean())
#                 st.metric("Air Quality (PM2.5)", f"{city_avg:.1f} µg/m³", "No district data — city average")
#             else:
#                 st.metric("Air Quality (PM2.5)", "—", "No recent air data")
# except Exception as e:
#     with metric_cols[0]:
#         st.metric("Air Quality", "—", "Data unavailable")

# # Safety
# try:
#     acc = safe_read_csv("datasets/processed_table.csv")
#     acc = acc.copy()
#     # Map numeric district codes if present
#     if acc.empty:
#         acc_rates = pd.Series(dtype=float)
#     else:
#         if acc["District"].dtype == "int64" or acc["District"].dtype == "float64":
#             code_to_name = {191910: "Алмалинский", 191960: "Бостандыкский", 191956: "Медеуский", 191966: "Турксибский", 191932: "Жетысуский", 191934: "Наурызбайский", 191916: "Ауэзовский", 191926: "Алатауский"}
#             acc["district_name"] = acc["District"].map(code_to_name).fillna(acc.get("district_name"))
#         else:
#             acc["district_name"] = acc.get("district_name") if "district_name" in acc.columns else acc.get("District")
#         acc["severe"] = (acc.get("Number_of_Injured", 0) > 1).astype(int)
#         acc_rates = acc.groupby("district_name")["severe"].mean()

#     with metric_cols[1]:
#         if selected_district in acc_rates.index:
#             safety_rate = float(acc_rates.loc[selected_district])
#             if safety_rate < 0.25:
#                 status = "🟢 Safe"
#             elif safety_rate < 0.50:
#                 status = "🟡 Moderate"
#             else:
#                 status = "🔴 High risk"
#             st.metric("Accident Severity", f"{safety_rate:.1%}", status)
#         else:
#             if not acc_rates.empty:
#                 city_rate = float(acc_rates.mean())
#                 st.metric("Accident Severity", f"{city_rate:.1%}", "No district data — city average")
#             else:
#                 st.metric("Accident Severity", "—", "No accident data")
# except Exception as e:
#     with metric_cols[1]:
#         st.metric("Safety", "—", "Data unavailable")

# # Housing Price
# try:
#     house = safe_read_csv("datasets/krisha_final.csv")
    
#     if "district" not in house.columns:
#         def find_district_from_address(a: str) -> str:
#             if not isinstance(a, str):
#                 return None
#             al = a.lower()
#             for d in DISTRICT_COORDS.keys():
#                 if d.lower() in al:
#                     return d
#             return None
#         house["district"] = house.get("Address", "").apply(find_district_from_address)
    
#     house["price_num"] = pd.to_numeric(
#         house.get("Price", "").astype(str).str.replace(r"[^0-9]", "", regex=True).replace("", pd.NA),
#         errors="coerce"
#     )
    
#     dist_house = house[house["district"] == selected_district]
#     with metric_cols[2]:
#         if not dist_house.empty and dist_house["price_num"].notna().any():
#             median_price = dist_house["price_num"].median()
#             if pd.notna(median_price):
#                 price_m = f"{(median_price/1_000_000):.1f}M ₸"
#                 st.metric("Median Price", price_m, f"{len(dist_house)} listings")
#         else:
#             # Fallback to city median if available
#             all_prices = house[house["price_num"].notna()]["price_num"]
#             if not all_prices.empty:
#                 city_med = float(all_prices.median())
#                 st.metric("Median Price", f"{(city_med/1_000_000):.1f}M ₸", "No district listings — city median")
#             else:
#                 st.metric("Median Price", "—", "No housing data")
# except Exception as e:
#     with metric_cols[2]:
#         st.metric("Housing Price", "—", "Data unavailable")

# # Education & Services
# try:
#     edu = safe_read_csv("datasets/Almaty_Education_Master.csv")
#     if "Type" in edu.columns and "District" in edu.columns:
#         type_dist_counts = edu[edu["District"] == selected_district].groupby("Type").size()
#         kinder_count = int(type_dist_counts.get("садик", 0))
#         school_count = int(type_dist_counts.get("школа", 0))
#         services_total = kinder_count + school_count

#         with metric_cols[3]:
#             if services_total > 0:
#                 st.metric("Schools & Kindergartens", services_total, f"{kinder_count}K + {school_count}S")
#             else:
#                 # fallback: show total city counts
#                 city_counts = edu.groupby("Type").size()
#                 city_k = int(city_counts.get("садик", 0))
#                 city_s = int(city_counts.get("школа", 0))
#                 if city_k + city_s > 0:
#                     st.metric("Schools & Kindergartens", city_k + city_s, "No district data — city total")
#                 else:
#                     st.metric("Schools & Kindergartens", "—", "No education data")
# except Exception as e:
#     with metric_cols[3]:
#         st.metric("Services", "—", "Data unavailable")

# # ─── STEP 2B: ANALYZE A LISTING ──────────────────────────────────────────────
# st.markdown("---")
# st.markdown("## 3️⃣ Analyze a Listing")
# st.markdown("""
# **Option A**: Paste a Krisha.kz URL for automatic data extraction  
# **Option B**: Enter details manually below  
# **Select a district** so the analysis compares against local data.
# """)

# analyze_cols = st.columns([2, 1])
# with analyze_cols[0]:
#     listing_url = st.text_input(
#         "Krisha.kz URL (optional)",
#         key="home_listing_url",
#         placeholder="e.g., https://krisha.kz/a/..."
#     )
# with analyze_cols[1]:
#     listing_district = st.selectbox(
#         "District *",
#         options=sorted(DISTRICT_COORDS.keys()),
#         index=sorted(DISTRICT_COORDS.keys()).index(selected_district),
#         key="home_listing_district",
#         help="Required for accurate analysis"
#     )

# with st.expander("📝 Manual Entry", expanded=True):
#     col1, col2 = st.columns(2)
    
#     with col1:
#         title = st.text_input(
#             "Listing title",
#             key="home_listing_title",
#             placeholder="e.g., 2-к квартира, 58 м²"
#         )
#         address = st.text_input(
#                 "Address *",
#                 key="home_listing_address",
#                 placeholder="e.g., Жамбыла ул., 100, Алмалинский р-н",
#                 help="Street name and number help with location",
#                 on_change=_auto_geocode_and_infer,
#             )
#         price_input = st.text_input(
#             "Price (₸) *",
#             key="home_listing_price",
#             placeholder="e.g., 42000000"
#         )
    
#     with col2:
#         area_input = st.text_input(
#             "Area (m²)",
#             key="home_listing_area",
#             placeholder="e.g., 58"
#         )
#         rooms_input = st.text_input(
#             "Rooms",
#             key="home_listing_rooms",
#             placeholder="e.g., 2-к"
#         )
    
#     # Coordinates section
#     st.markdown("**Coordinates** (optional — auto-filled from address if blank)")
#     coord_cols = st.columns(3)
    
#     with coord_cols[0]:
#         lat_input = st.text_input(
#             "Latitude",
#             key="home_listing_lat",
#             placeholder="e.g., 43.256"
#         )
#     with coord_cols[1]:
#         lon_input = st.text_input(
#             "Longitude",
#             key="home_listing_lon",
#             placeholder="e.g., 76.929"
#         )
#     with coord_cols[2]:
#         if address and not lat_input:
#             if st.button("📍 Auto-fill", key="home_geocode_button"):
#                 with st.spinner("Geocoding address..."):
#                     coords = geocode_address(address, timeout=5)
#                     if coords:
#                         st.success(f"✅ Found: {coords[0]:.4f}, {coords[1]:.4f}")
#                         # set into session state so inputs reflect the change
#                         st.session_state["home_listing_lat"] = f"{coords[0]:.6f}"
#                         st.session_state["home_listing_lon"] = f"{coords[1]:.6f}"
#                     else:
#                         st.warning("Could not geocode address. Please enter coordinates manually.")

#     analyze_clicked = st.button("🔍 Analyze Listing", key="home_analyze_button", type="primary")

#     if analyze_clicked:
#         # ─── Validation block
#         errors = []
        
#         # Validate required fields
#         try:
#             if not listing_district:
#                 raise ValidationError("District is required. Please select one.")
#             validate_district(listing_district)
#         except ValidationError as e:
#             errors.append(format_error_message(e))
        
#         # Validate address
#         try:
#             if not address:
#                 raise ValidationError("Address is required.")
#             validate_address(address)
#         except ValidationError as e:
#             errors.append(format_error_message(e))
        
#         # Validate price
#         try:
#             if not price_input:
#                 raise ValidationError("Price is required.")
#             price_num = validate_price(price_input)
#         except ValidationError as e:
#             errors.append(format_error_message(e))
#             price_num = None
        
#         # Parse area and rooms (non-critical)
#         try:
#             area_m2 = float(re.sub(r"[^0-9.]", "", area_input)) if area_input else None
#         except Exception:
#             area_m2 = None
        
#         rooms = rooms_input if rooms_input else "Unknown"
        
#         # Handle coordinates
#         coords_to_use = None
#         if lat_input and lon_input:
#             try:
#                 coords_to_use = validate_coordinates(lat_input, lon_input)
#             except ValidationError as e:
#                 errors.append(format_error_message(e))
        
#         # Try URL fetch if provided
#         fetched_title = title
#         fetched_address = address
#         if listing_url:
#             try:
#                 validate_url(listing_url)
#                 with st.spinner("Fetching listing details from URL..."):
#                     r = requests.get(listing_url, timeout=8)
#                     soup = BeautifulSoup(r.text, "html.parser")
#                     h1 = soup.find("h1")
#                     if h1:
#                         fetched_title = h1.get_text(strip=True)
#                     page_text = soup.get_text(separator=" ")
#                     price_match = re.search(r"([\d\s]+)\s*₸", page_text.replace("\xa0", " "))
#                     if price_match and not price_input:
#                         price_input = re.sub(r"\D", "", price_match.group(1))
#                     addr_match = re.search(r"Адрес[:\s]*([\w\s,\-\.]+)", page_text)
#                     if addr_match:
#                         fetched_address = addr_match.group(1).strip()
#                 st.success("✅ URL data extracted successfully")
#             except ValidationError as e:
#                 errors.append(format_error_message(e))
#             except requests.Timeout:
#                 errors.append("⏱️ URL fetch timed out (8s). Continuing with manual fields.")
#             except Exception as e:
#                 errors.append(f"⚠️ Could not fetch URL: {str(e)[:80]}. Using manual fields instead.")
        
#         # Display validation errors
#         if errors:
#             st.error("**Validation failed:**")
#             for error in errors:
#                 st.markdown(error)
#             st.stop()
        
#         # ─── Run analysis with spinner
#         with st.spinner("Analyzing listing against district data..."):
#             listing = {
#                 "title": fetched_title or "Untitled",
#                 "address": fetched_address,
#                 "price_num": price_num,
#                 "area_m2": area_m2,
#                 "rooms": rooms,
#                 "district": listing_district,
#             }
#             if coords_to_use:
#                 listing["lat"], listing["lon"] = coords_to_use
#             # Run analysis
#             res = analyze_listing(listing)

#         # Save to history (append lightweight summary)
#         try:
#             hist_item = {
#                 "time": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
#                 "title": listing.get("title"),
#                 "address": listing.get("address"),
#                 "district": listing.get("district"),
#                 "price": listing.get("price_num"),
#                 "rating": res.get("star_rating"),
#                 "verdict": res.get("verdict"),
#             }
#             st.session_state["analysis_history"].insert(0, hist_item)
#             # cap history to 50 items
#             st.session_state["analysis_history"] = st.session_state["analysis_history"][:50]
#         except Exception:
#             pass
        
#         st.subheader("✅ Analysis Complete")
#         st.caption(f"📍 District: **{listing_district}**")
        
#         # Show verdict
#         verdict = res.get("verdict", "")
#         if verdict:
#             emoji_map = {"good": "✅", "acceptable": "🟡", "risky": "⚠️"}
#             emoji = emoji_map.get(verdict.lower().split()[0], "📊")
#             st.success(f"{emoji} {verdict}")
        
#         # Star rating
#         rating = res.get("star_rating")
#         if rating is not None:
#             star_str = "⭐" * int(rating) + "☆" * (5 - int(rating))
#             st.metric("Rating", f"{rating:.1f}/5", star_str)
        
#         # Four-column breakdown
#         b1, b2, b3, b4 = st.columns(4)
        
#         with b1:
#             if res.get("price_score") is not None:
#                 st.metric(
#                     "💰 Price vs District",
#                     f"{res['price_score']:.0%}",
#                     f"District median: {res.get('district_median_price') or '—'}"
#                 )
#             else:
#                 st.metric("💰 Price vs District", "—", "Data unavailable")
        
#         with b2:
#             if res.get("safety_score") is not None:
#                 safety_pct = f"{res['safety_score']:.0%}"
#                 st.metric("🚗 Road Safety", safety_pct, "Lower accidents = higher score")
#             else:
#                 st.metric("🚗 Road Safety", "—", "Data unavailable")
        
#         with b3:
#             if res.get("air_score") is not None:
#                 air_pct = f"{res['air_score']:.0%}"
#                 st.metric("🌬️ Air Quality", air_pct, "Lower PM2.5 = higher score")
#             else:
#                 st.metric("🌬️ Air Quality", "—", "Data unavailable")
        
#         with b4:
#             if res.get("services_score") is not None:
#                 svc_pct = f"{res['services_score']:.0%}"
#                 counts = res.get("counts")
#                 if isinstance(counts, dict):
#                     counts_str = f"Edu:{counts.get('edu', 0)} Hosp:{counts.get('hosp', 0)} Uni:{counts.get('uni', 0)}"
#                 else:
#                     counts_str = counts or "Edu/Hosp/Uni"
#                 st.metric("🏫 Services", svc_pct, counts_str)
#             else:
#                 st.metric("🏫 Services", "—", "District data needed")
        
#         # Summary
#         summary_lines = res.get("summary") or []
#         if summary_lines:
#             st.write("**Key Points**")
#             for line in summary_lines:
#                 st.write(f"✓ {line}")
        
#         # Proximity table
#         prox = res.get("proximity") or {}
#         if prox:
#             st.write("**Nearby Facilities**")
#             prox_df = pd.DataFrame([
#                 {
#                     "Type": "Education",
#                     "Within 500m": prox.get("edu", {}).get("500", 0),
#                     "Within 1km": prox.get("edu", {}).get("1000", 0),
#                     "Within 2km": prox.get("edu", {}).get("2000", 0),
#                 },
#                 {
#                     "Type": "Hospitals",
#                     "Within 500m": prox.get("hosp", {}).get("500", 0),
#                     "Within 1km": prox.get("hosp", {}).get("1000", 0),
#                     "Within 2km": prox.get("hosp", {}).get("2000", 0),
#                 },
#                 {
#                     "Type": "Universities",
#                     "Within 500m": prox.get("uni", {}).get("500", 0),
#                     "Within 1km": prox.get("uni", {}).get("1000", 0),
#                     "Within 2km": prox.get("uni", {}).get("2000", 0),
#                 },
#             ])
#             st.dataframe(prox_df, use_container_width=True, hide_index=True)
        
#         # Candidate districts if inference failed
#         cand = res.get("candidates") or []
#         if cand and listing_district not in cand:
#             st.warning(
#                 f"⚠️ District was inferred from keywords. "
#                 f"Top matches: {', '.join(cand[:3])}. "
#                 f"Selected: **{listing_district}**"
#             )
        
#         # Smart suggestions
#         suggestions = []
#         if res.get("price_score") is not None:
#             if res["price_score"] < 0.4:
#                 suggestions.append("🔴 **Price is significantly above median** — negotiate or search alternatives")
#             elif res["price_score"] < 0.7:
#                 suggestions.append("🟡 **Price is above median** — verify features justify the premium")
#             else:
#                 suggestions.append("🟢 **Price is competitive** for this district")
        
#         if res.get("safety_score") is not None and res["safety_score"] < 0.35:
#             suggestions.append("⚠️ **Road safety is lower here** — review accident trends on the Accidents page")
        
#         if res.get("air_score") is not None and res["air_score"] < 0.35:
#             suggestions.append("⚠️ **Air quality is weaker here** — check Air Quality page for seasonal trends")
        
#         if suggestions:
#             st.write("**Recommendations**")
#             for sug in suggestions:
#                 st.write(sug)

#     # --- Analysis history UI
#     with st.expander("🕘 Analysis history", expanded=False):
#         hist = st.session_state.get("analysis_history", [])
#         if hist:
#             hist_df = pd.DataFrame(hist)
#             st.dataframe(hist_df, use_container_width=True)
#             csv = hist_df.to_csv(index=False)
#             st.download_button("Download history CSV", data=csv, file_name="analysis_history.csv")
#         else:
#             st.info("No analyses performed in this session yet.")


# # ─── STEP 3: HOUSING LISTINGS ────────────────────────────────────────────────
# st.markdown("## 4️⃣ Housing Listings in this District")

# try:
#     house = safe_read_csv("datasets/krisha_final.csv")
    
#     if "district" not in house.columns:
#         def find_district_from_address(a: str) -> str:
#             if not isinstance(a, str):
#                 return None
#             al = a.lower()
#             for d in DISTRICT_COORDS.keys():
#                 if d.lower() in al:
#                     return d
#             return None
#         house["district"] = house.get("Address", "").apply(find_district_from_address)
    
#     house["price_num"] = pd.to_numeric(
#         house.get("Price", "").astype(str).str.replace(r"[^0-9]", "", regex=True).replace("", pd.NA),
#         errors="coerce"
#     )
    
#     dist_house = house[house["district"] == selected_district].dropna(subset=["price_num"])
    
#     if not dist_house.empty:
#         # Price filter
#         min_p = int(dist_house["price_num"].min())
#         max_p = int(dist_house["price_num"].max())
        
#         col_filter1, col_filter2 = st.columns(2)
#         with col_filter1:
#             price_min_filter = st.number_input("Min price (₸)", value=min_p, step=1_000_000)
#         with col_filter2:
#             price_max_filter = st.number_input("Max price (₸)", value=max_p, step=1_000_000)
        
#         # Apply filter
#         filtered = dist_house[
#             (dist_house["price_num"] >= price_min_filter) &
#             (dist_house["price_num"] <= price_max_filter)
#         ]
        
#         st.markdown(f"**Found {len(filtered)} listings** in your price range")
        
#         # Display listings
#         if len(filtered) > 0:
#             for idx, (_, row) in enumerate(filtered.head(10).iterrows()):
#                 with st.container():
#                     col_left, col_right = st.columns([3, 1])
                    
#                     with col_left:
#                         title = row.get("Title", "Listing")
#                         address = row.get("Address", "Address not available")
#                         price = int(row.get("price_num", 0))
                        
#                         st.markdown(f"**{title}**")
#                         st.caption(f"📍 {address}")
                    
#                     with col_right:
#                         price_m = f"{(price/1_000_000):.1f}M"
#                         st.metric("Price", price_m, label_visibility="collapsed")
                    
#                     st.divider()
#     else:
#         st.info("No housing listings found for this district.")

# except Exception as e:
#     st.error(f"Could not load housing data: {type(e).__name__}")

# # ─── STEP 5: EXPLORE OTHER ANALYSIS ────────────────────────────────────────
# st.markdown("---")
# st.markdown("## 5️⃣ Deep Dive into Other Aspects")

# explore_cols = st.columns(4)

# with explore_cols[0]:
#     st.page_link(
#         "pages/1_Air_Quality.py",
#         label="🌬️ Air Quality",
#         icon="📊",
#         help="Detailed air pollution data by district and time"
#     )

# with explore_cols[1]:
#     st.page_link(
#         "pages/2_Accidents.py",
#         label="🚗 Road Safety",
#         icon="📊",
#         help="Accident hotspots and severity analysis"
#     )

# with explore_cols[2]:
#     st.page_link(
#         "pages/4_Forecast.py",
#         label="📈 Forecast",
#         icon="📊",
#         help="Predict future accident trends"
#     )

# with explore_cols[3]:
#     st.page_link(
#         "pages/6_District_Score.py",
#         label="⭐ Compare All",
#         icon="📊",
#         help="Weighted scoring of all districts"
#     )

# # ─── FOOTER ───────────────────────────────────────────────────────────────────
# st.markdown("---")

# st.markdown("""
# ### How to use this app

# 1. **Choose a District** — Select from 8 Almaty districts
# 2. **See Overview** — Air quality, safety, price, schools at a glance
# 3. **Browse Housing** — Filter listings by your budget
# 4. **Explore Details** — Click the buttons above to dive into specific topics
# 5. **Compare All** — Use the "Compare All" page to rank districts by your priorities

# ### Questions?
# - 💭 **What do the scores mean?** See the District Score page for methodology
# - 🏠 **Where's housing data from?** Krisha.kz listings (most recent)
# - 📊 **When is data updated?** Check the Data Freshness note on each page
# """)

# render_glossary({})
# render_feedback_widget("Home")


import streamlit as st
import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
from pathlib import Path

# Ensure all paths are relative to this script, not the working directory
SCRIPT_DIR = Path(__file__).parent.absolute()

from app import (
    apply_base_style,
    render_data_freshness,
    render_feedback_widget,
    render_glossary,
    render_insight,
    render_page_intro,
    render_theme_toggle,
    safe_read_csv as _safe_read_csv_orig,
    DISTRICT_COORDS,
    DISTRICT_KEYWORDS,
    ValidationError,
    validate_price,
    validate_address,
    validate_coordinates,
    validate_district,
    validate_url,
    geocode_address,
    format_error_message,
    format_success_message,
)

# Monkey-patch safe_read_csv to use absolute paths
def safe_read_csv(path: str, **kwargs) -> pd.DataFrame:
    """Load CSV with absolute path resolution relative to script location."""
    abs_path = SCRIPT_DIR / path
    return _safe_read_csv_orig(str(abs_path), **kwargs)

from app.listing_analyzer import analyze_listing, infer_district
from app.theme import get_theme

st.set_page_config(
    page_title="Almaty Living Guide",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_base_style()
render_theme_toggle()

# --- Session history initialization
if "analysis_history" not in st.session_state:
    st.session_state["analysis_history"] = []


def _auto_geocode_and_infer():
    """Callback fired when the address input changes.

    Always clears previous geocoded coordinates first so stale coords from a
    previous address never carry over when the new address isn't found.
    """
    addr = st.session_state.get("home_listing_address", "")

    # Clear previous geocoded coords every time address changes
    st.session_state["_geocoded_lat"] = ""
    st.session_state["_geocoded_lon"] = ""

    if not addr:
        return

    # Try geocoding
    coords = None
    try:
        coords = geocode_address(addr, timeout=3)
    except Exception:
        coords = None

    if coords:
        st.session_state["_geocoded_lat"] = f"{coords[0]:.6f}"
        st.session_state["_geocoded_lon"] = f"{coords[1]:.6f}"
    # If coords is None: fields stay empty — user sees blank, not stale values

    # Infer district from address keywords
    try:
        inferred = infer_district(addr)
        if inferred and inferred in DISTRICT_COORDS:
            st.session_state["home_listing_district"] = inferred
    except Exception:
        pass

# ─── HERO SECTION ─────────────────────────────────────────────────────────────
theme = get_theme(st.session_state.get("theme_mode", "light"))
st.markdown(f"""
<div class='hero-box'>
    <h1>🏙️ Almaty Living Guide</h1>
    <p>Find the best district for you: Compare safety, air quality, housing prices & services</p>
</div>
""", unsafe_allow_html=True)

# ─── STEP 1: SELECT DISTRICT ──────────────────────────────────────────────────
st.markdown("## 1️⃣ Choose a District")

col1, col2 = st.columns([2, 1])

with col1:
    selected_district = st.selectbox(
        "Select a district to explore:",
        options=sorted(DISTRICT_COORDS.keys()),
        index=0,
        help="Click to see all 8 districts in Almaty"
    )

with col2:
    st.info(f"📍 **{selected_district}** selected")

# ─── STEP 2: KEY METRICS FOR SELECTED DISTRICT ────────────────────────────────
st.markdown("## 2️⃣ District Overview")
st.markdown(f"**{selected_district}** — Key statistics at a glance")

metric_cols = st.columns(4)

# Air Quality
try:
    air = safe_read_csv("datasets/processed_air_ala_data.csv")
    air["date"] = pd.to_datetime(air["date"], errors="coerce") if "date" in air.columns else None
    if air is not None and not air.empty and "date" in air.columns:
        latest_date = air["date"].max()
        latest_air = air.loc[air["date"] == latest_date].groupby("district")["pm25_avg"].mean()
    else:
        latest_air = pd.Series(dtype=float)

    air_pm25 = latest_air.get(selected_district, None)

    with metric_cols[0]:
        if air_pm25 is not None and not pd.isna(air_pm25):
            if air_pm25 < 35:
                status = "🟢 Good"
            elif air_pm25 < 75:
                status = "🟡 Moderate"
            else:
                status = "🔴 Poor"
            st.metric("Air Quality (PM2.5)", f"{air_pm25:.1f} µg/m³", status)
        else:
            # Fallback to city average if available
            if not latest_air.empty:
                city_avg = float(latest_air.mean())
                st.metric("Air Quality (PM2.5)", f"{city_avg:.1f} µg/m³", "No district data — city average")
            else:
                st.metric("Air Quality (PM2.5)", "—", "No recent air data")
except Exception as e:
    with metric_cols[0]:
        st.metric("Air Quality", "—", "Data unavailable")

# Safety
try:
    from pathlib import Path
    ds_dir = SCRIPT_DIR / "datasets"
    if (ds_dir / "processed_table.csv").exists():
        acc = safe_read_csv("datasets/processed_table.csv")
    else:
        acc = safe_read_csv("datasets/processed_table.csv")
    acc = acc.copy()
    # Map numeric district codes centrally if present
    try:
        if not acc.empty and pd.api.types.is_numeric_dtype(acc["District"]):
            from app import DISTRICT_CODE_TO_NAME

            acc["district_name"] = acc["District"].map(DISTRICT_CODE_TO_NAME)
        else:
            acc["district_name"] = acc.get("district_name") if "district_name" in acc.columns else acc.get("District")
    except Exception:
        acc["district_name"] = acc.get("district_name") if "district_name" in acc.columns else acc.get("District")
    acc["severe"] = (acc.get("Number_of_Injured", 0) > 1).astype(int)
    acc_rates = acc.dropna(subset=["district_name"]).groupby("district_name")["severe"].mean()

    with metric_cols[1]:
        if selected_district in acc_rates.index:
            safety_rate = float(acc_rates.loc[selected_district])
            if safety_rate < 0.25:
                status = "🟢 Safe"
            elif safety_rate < 0.50:
                status = "🟡 Moderate"
            else:
                status = "🔴 High risk"
            st.metric("Accident Severity", f"{safety_rate:.1%}", status)
        else:
            if not acc_rates.empty:
                city_rate = float(acc_rates.mean())
                st.metric("Accident Severity", f"{city_rate:.1%}", "No district data — city average")
            else:
                st.metric("Accident Severity", "—", "No accident data")
except Exception as e:
    with metric_cols[1]:
        st.metric("Safety", "—", "Data unavailable")

# Housing Price
try:
    house = safe_read_csv("datasets/krisha_final.csv")
    
    if "district" not in house.columns:
        def find_district_from_address(a: str) -> str:
            if not isinstance(a, str):
                return "Other"
            al = a.lower()
            # keyword-based detection (fallback to direct substring match)
            for dist, kws in DISTRICT_KEYWORDS.items():
                for kw in kws:
                    if kw in al:
                        return dist
            for d in DISTRICT_COORDS.keys():
                try:
                    if d.lower() in al:
                        return d
                except Exception:
                    continue
            return "Other"

        house["district"] = house.get("Address", "").apply(find_district_from_address)
    
    house["price_num"] = pd.to_numeric(
        house.get("Price", "").astype(str).str.replace(r"[^0-9]", "", regex=True).replace("", pd.NA),
        errors="coerce"
    )
    
    dist_house = house[house["district"] == selected_district]
    with metric_cols[2]:
        if not dist_house.empty and dist_house["price_num"].notna().any():
            median_price = dist_house["price_num"].median()
            if pd.notna(median_price):
                price_m = f"{(median_price/1_000_000):.1f}M ₸"
                st.metric("Median Price", price_m, f"{len(dist_house)} listings")
        else:
            # Fallback to city median if available
            all_prices = house[house["price_num"].notna()]["price_num"]
            if not all_prices.empty:
                city_med = float(all_prices.median())
                st.metric("Median Price", f"{(city_med/1_000_000):.1f}M ₸", "No district listings — city median")
            else:
                st.metric("Median Price", "—", "No housing data")
except Exception as e:
    with metric_cols[2]:
        st.metric("Housing Price", "—", "Data unavailable")

# Education & Services
try:
    edu = safe_read_csv("datasets/Almaty_Education_Master.csv")
    if "Type" in edu.columns and "District" in edu.columns:
        type_dist_counts = edu[edu["District"] == selected_district].groupby("Type").size()
        kinder_count = int(type_dist_counts.get("садик", 0))
        school_count = int(type_dist_counts.get("школа", 0))
        services_total = kinder_count + school_count

        with metric_cols[3]:
            if services_total > 0:
                st.metric("Schools & Kindergartens", services_total, f"{kinder_count}K + {school_count}S")
            else:
                # fallback: show total city counts
                city_counts = edu.groupby("Type").size()
                city_k = int(city_counts.get("садик", 0))
                city_s = int(city_counts.get("школа", 0))
                if city_k + city_s > 0:
                    st.metric("Schools & Kindergartens", city_k + city_s, "No district data — city total")
                else:
                    st.metric("Schools & Kindergartens", "—", "No education data")
except Exception as e:
    with metric_cols[3]:
        st.metric("Services", "—", "Data unavailable")

# ─── STEP 2B: ANALYZE A LISTING ──────────────────────────────────────────────
st.markdown("---")
st.markdown("## 3️⃣ Analyze a Listing")
st.markdown("""
**Option A**: Paste a Krisha.kz URL for automatic data extraction  
**Option B**: Enter details manually below  
**Select a district** so the analysis compares against local data.
""")

analyze_cols = st.columns([2, 1])
with analyze_cols[0]:
    listing_url = st.text_input(
        "Krisha.kz URL (optional)",
        key="home_listing_url",
        placeholder="e.g., https://krisha.kz/a/..."
    )
with analyze_cols[1]:
    listing_district = st.selectbox(
        "District *",
        options=sorted(DISTRICT_COORDS.keys()),
        index=sorted(DISTRICT_COORDS.keys()).index(selected_district),
        key="home_listing_district",
        help="Required for accurate analysis"
    )

with st.expander("📝 Manual Entry", expanded=True):
    col1, col2 = st.columns(2)
    
    with col1:
        title = st.text_input(
            "Listing title",
            key="home_listing_title",
            placeholder="e.g., 2-к квартира, 58 м²"
        )
        address = st.text_input(
                "Address *",
                key="home_listing_address",
                placeholder="e.g., Жамбыла ул., 100, Алмалинский р-н",
                help="Street name and number help with location",
                on_change=_auto_geocode_and_infer,
            )
        price_input = st.text_input(
            "Price (₸) *",
            key="home_listing_price",
            placeholder="e.g., 42000000"
        )
    
    with col2:
        area_input = st.text_input(
            "Area (m²)",
            key="home_listing_area",
            placeholder="e.g., 58"
        )
        rooms_input = st.text_input(
            "Rooms",
            key="home_listing_rooms",
            placeholder="e.g., 2-к"
        )
    
    # Coordinates section
    st.markdown("**Coordinates** (optional — auto-filled from address if blank)")
    coord_cols = st.columns(3)
    
    # Read geocoded values from separate storage keys (never the widget keys)
    _geo_lat = st.session_state.get("_geocoded_lat", "")
    _geo_lon = st.session_state.get("_geocoded_lon", "")

    with coord_cols[0]:
        lat_input = st.text_input(
            "Latitude",
            value=_geo_lat,
            placeholder="e.g., 43.256"
        )
    with coord_cols[1]:
        lon_input = st.text_input(
            "Longitude",
            value=_geo_lon,
            placeholder="e.g., 76.929"
        )
    with coord_cols[2]:
        if address and not lat_input:
            if st.button("📍 Auto-fill", key="home_geocode_button"):
                with st.spinner("Geocoding address..."):
                    coords = geocode_address(address, timeout=5)
                    if coords:
                        st.success(f"✅ Found: {coords[0]:.4f}, {coords[1]:.4f}")
                        st.session_state["_geocoded_lat"] = f"{coords[0]:.6f}"
                        st.session_state["_geocoded_lon"] = f"{coords[1]:.6f}"
                        st.rerun()
                    else:
                        st.session_state["_geocoded_lat"] = ""
                        st.session_state["_geocoded_lon"] = ""
                        st.warning("Could not geocode address. Please enter coordinates manually.")

    analyze_clicked = st.button("🔍 Analyze Listing", key="home_analyze_button", type="primary")

    if analyze_clicked:
        # ─── Validation block
        errors = []
        
        # Validate required fields
        try:
            if not listing_district:
                raise ValidationError("District is required. Please select one.")
            validate_district(listing_district)
        except ValidationError as e:
            errors.append(format_error_message(e))
        
        # Validate address
        try:
            if not address:
                raise ValidationError("Address is required.")
            validate_address(address)
        except ValidationError as e:
            errors.append(format_error_message(e))
        
        # Validate price
        try:
            if not price_input:
                raise ValidationError("Price is required.")
            price_num = validate_price(price_input)
        except ValidationError as e:
            errors.append(format_error_message(e))
            price_num = None
        
        # Parse area and rooms (non-critical)
        try:
            area_m2 = float(re.sub(r"[^0-9.]", "", area_input)) if area_input else None
        except Exception:
            area_m2 = None
        
        rooms = rooms_input if rooms_input else "Unknown"
        
        # Handle coordinates
        coords_to_use = None
        if lat_input and lon_input:
            try:
                coords_to_use = validate_coordinates(lat_input, lon_input)
            except ValidationError as e:
                errors.append(format_error_message(e))
        
        # Try URL fetch if provided
        fetched_title = title
        fetched_address = address
        if listing_url:
            try:
                validate_url(listing_url)
                with st.spinner("Fetching listing details from URL..."):
                    r = requests.get(listing_url, timeout=8)
                    soup = BeautifulSoup(r.text, "html.parser")
                    h1 = soup.find("h1")
                    if h1:
                        fetched_title = h1.get_text(strip=True)
                    page_text = soup.get_text(separator=" ")
                    price_match = re.search(r"([\d\s]+)\s*₸", page_text.replace("\xa0", " "))
                    if price_match and not price_input:
                        price_input = re.sub(r"\D", "", price_match.group(1))
                    addr_match = re.search(r"Адрес[:\s]*([\w\s,\-\.]+)", page_text)
                    if addr_match:
                        fetched_address = addr_match.group(1).strip()
                st.success("✅ URL data extracted successfully")
            except ValidationError as e:
                errors.append(format_error_message(e))
            except requests.Timeout:
                errors.append("⏱️ URL fetch timed out (8s). Continuing with manual fields.")
            except Exception as e:
                errors.append(f"⚠️ Could not fetch URL: {str(e)[:80]}. Using manual fields instead.")
        
        # Display validation errors
        if errors:
            st.error("**Validation failed:**")
            for error in errors:
                st.markdown(error)
            st.stop()
        
        # ─── Run analysis with spinner
        with st.spinner("Analyzing listing against district data..."):
            listing = {
                "title": fetched_title or "Untitled",
                "address": fetched_address,
                "price_num": price_num,
                "area_m2": area_m2,
                "rooms": rooms,
                "district": listing_district,
            }
            if coords_to_use:
                listing["lat"], listing["lon"] = coords_to_use
            # Run analysis
            res = analyze_listing(listing, datasets_path=str(SCRIPT_DIR / "datasets"))

        # Save to history (append lightweight summary)
        try:
            hist_item = {
                "time": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                "title": listing.get("title"),
                "address": listing.get("address"),
                "district": listing.get("district"),
                "price": listing.get("price_num"),
                "rating": res.get("star_rating"),
                "verdict": res.get("verdict"),
            }
            st.session_state["analysis_history"].insert(0, hist_item)
            # cap history to 50 items
            st.session_state["analysis_history"] = st.session_state["analysis_history"][:50]
        except Exception:
            pass
        
        st.subheader("✅ Analysis Complete")
        st.caption(f"📍 District: **{listing_district}**")
        
        # Show verdict
        verdict = res.get("verdict", "")
        if verdict:
            emoji_map = {"good": "✅", "acceptable": "🟡", "risky": "⚠️"}
            emoji = emoji_map.get(verdict.lower().split()[0], "📊")
            st.success(f"{emoji} {verdict}")
        
        # Star rating
        rating = res.get("star_rating")
        if rating is not None:
            star_str = "⭐" * int(rating) + "☆" * (5 - int(rating))
            st.metric("Rating", f"{rating:.1f}/5", star_str)
        
        # Four-column breakdown
        b1, b2, b3, b4 = st.columns(4)
        
        with b1:
            if res.get("price_score") is not None:
                st.metric(
                    "💰 Price vs District",
                    f"{res['price_score']:.0%}",
                    f"District median: {res.get('district_median_price') or '—'}"
                )
            else:
                st.metric("💰 Price vs District", "—", "Data unavailable")
        
        with b2:
            if res.get("safety_score") is not None:
                safety_pct = f"{res['safety_score']:.0%}"
                st.metric("🚗 Road Safety", safety_pct, "Lower accidents = higher score")
            else:
                st.metric("🚗 Road Safety", "—", "Data unavailable")
        
        with b3:
            if res.get("air_score") is not None:
                air_pct = f"{res['air_score']:.0%}"
                st.metric("🌬️ Air Quality", air_pct, "Lower PM2.5 = higher score")
            else:
                st.metric("🌬️ Air Quality", "—", "Data unavailable")
        
        with b4:
            if res.get("services_score") is not None:
                svc_pct = f"{res['services_score']:.0%}"
                counts = res.get("counts")
                if isinstance(counts, dict):
                    counts_str = f"Edu:{counts.get('edu', 0)} Hosp:{counts.get('hosp', 0)} Uni:{counts.get('uni', 0)}"
                else:
                    counts_str = counts or "Edu/Hosp/Uni"
                st.metric("🏫 Services", svc_pct, counts_str)
            else:
                st.metric("🏫 Services", "—", "District data needed")
        
        # Summary
        summary_lines = res.get("summary") or []
        if summary_lines:
            st.write("**Key Points**")
            for line in summary_lines:
                st.write(f"✓ {line}")
        
        # Proximity table
        prox = res.get("proximity") or {}
        if prox:
            st.write("**Nearby Facilities**")
            prox_df = pd.DataFrame([
                {
                    "Type": "Education",
                    "Within 500m": prox.get("edu", {}).get("500", 0),
                    "Within 1km": prox.get("edu", {}).get("1000", 0),
                    "Within 2km": prox.get("edu", {}).get("2000", 0),
                },
                {
                    "Type": "Hospitals",
                    "Within 500m": prox.get("hosp", {}).get("500", 0),
                    "Within 1km": prox.get("hosp", {}).get("1000", 0),
                    "Within 2km": prox.get("hosp", {}).get("2000", 0),
                },
                {
                    "Type": "Universities",
                    "Within 500m": prox.get("uni", {}).get("500", 0),
                    "Within 1km": prox.get("uni", {}).get("1000", 0),
                    "Within 2km": prox.get("uni", {}).get("2000", 0),
                },
            ])
            st.dataframe(prox_df, use_container_width=True, hide_index=True)
        
        # Candidate districts if inference failed
        cand = res.get("candidates") or []
        if cand and listing_district not in cand:
            st.warning(
                f"⚠️ District was inferred from keywords. "
                f"Top matches: {', '.join(cand[:3])}. "
                f"Selected: **{listing_district}**"
            )
        
        # Smart suggestions
        suggestions = []
        if res.get("price_score") is not None:
            if res["price_score"] < 0.4:
                suggestions.append("🔴 **Price is significantly above median** — negotiate or search alternatives")
            elif res["price_score"] < 0.7:
                suggestions.append("🟡 **Price is above median** — verify features justify the premium")
            else:
                suggestions.append("🟢 **Price is competitive** for this district")
        
        if res.get("safety_score") is not None and res["safety_score"] < 0.35:
            suggestions.append("⚠️ **Road safety is lower here** — review accident trends on the Accidents page")
        
        if res.get("air_score") is not None and res["air_score"] < 0.35:
            suggestions.append("⚠️ **Air quality is weaker here** — check Air Quality page for seasonal trends")
        
        if suggestions:
            st.write("**Recommendations**")
            for sug in suggestions:
                st.write(sug)

    # --- Analysis history UI
    with st.expander("🕘 Analysis history", expanded=False):
        hist = st.session_state.get("analysis_history", [])
        if hist:
            hist_df = pd.DataFrame(hist)
            st.dataframe(hist_df, use_container_width=True)
            csv = hist_df.to_csv(index=False)
            st.download_button("Download history CSV", data=csv, file_name="analysis_history.csv")
        else:
            st.info("No analyses performed in this session yet.")


# ─── STEP 3: HOUSING LISTINGS ────────────────────────────────────────────────
st.markdown("## 4️⃣ Housing Listings in this District")

try:
    house = safe_read_csv("datasets/krisha_final.csv")
    
    if "district" not in house.columns:
        def find_district_from_address(a: str) -> str:
            if not isinstance(a, str):
                return None
            al = a.lower()
            for d in DISTRICT_COORDS.keys():
                if d.lower() in al:
                    return d
            return None
        house["district"] = house.get("Address", "").apply(find_district_from_address)
    
    house["price_num"] = pd.to_numeric(
        house.get("Price", "").astype(str).str.replace(r"[^0-9]", "", regex=True).replace("", pd.NA),
        errors="coerce"
    )
    
    dist_house = house[house["district"] == selected_district].dropna(subset=["price_num"])
    
    if not dist_house.empty:
        # Price filter
        min_p = int(dist_house["price_num"].min())
        max_p = int(dist_house["price_num"].max())
        
        col_filter1, col_filter2 = st.columns(2)
        with col_filter1:
            price_min_filter = st.number_input("Min price (₸)", value=min_p, step=1_000_000)
        with col_filter2:
            price_max_filter = st.number_input("Max price (₸)", value=max_p, step=1_000_000)
        
        # Apply filter
        filtered = dist_house[
            (dist_house["price_num"] >= price_min_filter) &
            (dist_house["price_num"] <= price_max_filter)
        ]
        
        st.markdown(f"**Found {len(filtered)} listings** in your price range")
        
        # Display listings
        if len(filtered) > 0:
            for idx, (_, row) in enumerate(filtered.head(10).iterrows()):
                with st.container():
                    col_left, col_right = st.columns([3, 1])
                    
                    with col_left:
                        title = row.get("Title", "Listing")
                        address = row.get("Address", "Address not available")
                        price = int(row.get("price_num", 0))
                        
                        st.markdown(f"**{title}**")
                        st.caption(f"📍 {address}")
                    
                    with col_right:
                        price_m = f"{(price/1_000_000):.1f}M"
                        st.metric("Price", price_m, label_visibility="collapsed")
                    
                    st.divider()
    else:
        st.info("No housing listings found for this district.")

except Exception as e:
    st.error(f"Could not load housing data: {type(e).__name__}")

# ─── STEP 5: EXPLORE OTHER ANALYSIS ────────────────────────────────────────
st.markdown("---")
st.markdown("## 5️⃣ Deep Dive into Other Aspects")

explore_cols = st.columns(4)

with explore_cols[0]:
    st.page_link(
        "pages/1_Air_Quality.py",
        label="🌬️ Air Quality",
        icon="📊",
        help="Detailed air pollution data by district and time"
    )

with explore_cols[1]:
    st.page_link(
        "pages/2_Accidents.py",
        label="🚗 Road Safety",
        icon="📊",
        help="Accident hotspots and severity analysis"
    )

with explore_cols[2]:
    st.page_link(
        "pages/4_Forecast.py",
        label="📈 Forecast",
        icon="📊",
        help="Predict future accident trends"
    )

with explore_cols[3]:
    st.page_link(
        "pages/6_District_Score.py",
        label="⭐ Compare All",
        icon="📊",
        help="Weighted scoring of all districts"
    )

# ─── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown("---")

st.markdown("""
### How to use this app

1. **Choose a District** — Select from 8 Almaty districts
2. **See Overview** — Air quality, safety, price, schools at a glance
3. **Browse Housing** — Filter listings by your budget
4. **Explore Details** — Click the buttons above to dive into specific topics
5. **Compare All** — Use the "Compare All" page to rank districts by your priorities

### Questions?
- 💭 **What do the scores mean?** See the District Score page for methodology
- 🏠 **Where's housing data from?** Krisha.kz listings (most recent)
- 📊 **When is data updated?** Check the Data Freshness note on each page
""")

render_glossary({})
render_feedback_widget("Home")