import re
from typing import Dict, Any
import math
import pandas as pd

from app.constants import DISTRICT_COORDS, DISTRICT_KEYWORDS, DISTRICT_CODE_TO_NAME


def _safe_read_csv(path: str):
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def infer_district(address: str) -> str | None:
    """Return best matching district or None."""
    if not isinstance(address, str):
        return None
    a = address.lower()
    for d, kws in DISTRICT_KEYWORDS.items():
        for kw in kws:
            if kw in a:
                return d
    return None


def candidate_districts(address: str) -> list:
    """Return ranked list of candidate districts by keyword matches."""
    if not isinstance(address, str):
        return []
    a = address.lower()
    scores = []
    for d, kws in DISTRICT_KEYWORDS.items():
        s = sum(1 for kw in kws if kw in a)
        if s > 0:
            scores.append((d, s))
    scores.sort(key=lambda x: x[1], reverse=True)
    return [d for d, _ in scores]


def _median_by_district(df: pd.DataFrame):
    if df.empty or "price_num" not in df.columns:
        return {}
    med = df.groupby("district")["price_num"].median().to_dict()
    return med


def _parse_coords(coord_str: str) -> tuple[float, float] | None:
    """Parse a 'lon,lat' or 'lat,lon' string into (lat, lon)."""
    if not isinstance(coord_str, str):
        return None
    parts = [p.strip() for p in coord_str.split(",") if p.strip()]
    if len(parts) < 2:
        return None
    try:
        a = float(parts[0])
        b = float(parts[1])
    except Exception:
        return None
    if 40.0 <= a <= 50.0 and 60.0 <= b <= 80.0:
        return (a, b)
    if 40.0 <= b <= 50.0 and 60.0 <= a <= 80.0:
        return (b, a)
    return (b, a)


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def get_listing_coords(listing: Dict[str, Any]) -> tuple[float, float] | None:
    lat = listing.get("lat")
    lon = listing.get("lon")
    if lat is not None and lon is not None:
        try:
            return (float(lat), float(lon))
        except Exception:
            pass
    coord_str = listing.get("coordinates") or listing.get("Coordinates")
    if coord_str:
        parsed = _parse_coords(coord_str)
        if parsed:
            return parsed
    district = listing.get("district")
    if district and district in DISTRICT_COORDS:
        info = DISTRICT_COORDS[district]
        return (info.get("lat"), info.get("lon"))
    return None


def _build_coords_series(df: pd.DataFrame) -> pd.DataFrame:
    """Parse the Coordinates column into a DataFrame with lat/lon columns."""
    lats, lons = [], []
    for v in df["Coordinates"].astype(str):
        p = _parse_coords(v)
        if p:
            lats.append(p[0]); lons.append(p[1])
        else:
            lats.append(None); lons.append(None)
    return pd.DataFrame({"lat": lats, "lon": lons}).dropna()


def analyze_listing(listing: Dict[str, Any], datasets_path: str = "datasets") -> Dict[str, Any]:
    """Analyze a single listing dict and return a scoring breakdown."""
    result: Dict[str, Any] = {"ok": True, "errors": []}

    address = listing.get("address") or listing.get("Address") or ""
    price = listing.get("price_num")
    area = listing.get("area_m2")

    district = listing.get("district") or infer_district(address)
    result["district"] = district

    # Load datasets (best-effort)
    house = _safe_read_csv(f"{datasets_path}/krisha_final.csv")
    acc   = _safe_read_csv(f"{datasets_path}/processed_table.csv")
    air   = _safe_read_csv(f"{datasets_path}/processed_air_ala_data.csv")
    edu   = _safe_read_csv(f"{datasets_path}/Almaty_Education_Master.csv")
    hosp  = _safe_read_csv(f"{datasets_path}/hospitals_almaty.csv")
    uni   = _safe_read_csv(f"{datasets_path}/universities_almaty.csv")

    # Pre-process housing: add price_num and district columns if missing
    if not house.empty:
        if "price_num" not in house.columns:
            price_col = "Price" if "Price" in house.columns else None
            if price_col:
                house["price_num"] = pd.to_numeric(
                    house[price_col].astype(str).str.replace(r"[^0-9]", "", regex=True).replace("", pd.NA),
                    errors="coerce"
                )
            else:
                house["price_num"] = pd.NA
        if "district" not in house.columns:
            addr_col = "Address" if "Address" in house.columns else None
            if addr_col:
                house["district"] = house[addr_col].apply(infer_district)
            else:
                house["district"] = None

    # Price comparison
    med_map = _median_by_district(house)
    district_median = med_map.get(district)
    result["district_median_price"] = int(district_median) if district_median is not None else None

    price_score = None
    try:
        if price and district_median and district_median > 0:
            ratio = float(price) / float(district_median)
            price_score = max(0.0, min(1.0, 2.0 - ratio))
    except Exception:
        price_score = None
    result["price_score"] = price_score

    # Safety: severe accidents rate by district (numeric codes mapped to names)
    safety_score = None
    try:
        if not acc.empty and "District" in acc.columns:
            acc = acc.copy()
            acc["severe"] = (acc.get("Number_of_Injured", 0) > 1).astype(int)
            if pd.api.types.is_numeric_dtype(acc["District"]):
                acc["district_name"] = acc["District"].map(DISTRICT_CODE_TO_NAME)
            elif "district_name" in acc.columns:
                acc["district_name"] = acc["district_name"]
            else:
                acc["district_name"] = acc["District"]
            grp = acc.dropna(subset=["district_name"]).groupby("district_name")["severe"].mean()
            if not grp.empty:
                rates = grp.fillna(0)
                max_r = rates.max() if rates.max() > 0 else 1.0
                if district in rates.index:
                    safety_score = 1.0 - (rates.loc[district] / max_r)
    except Exception:
        safety_score = None
    result["safety_score"] = float(safety_score) if safety_score is not None else None

    # Air quality: use latest pm25 per district (lower is better)
    air_score = None
    try:
        if not air.empty and "pm25_avg" in air.columns:
            if "date" in air.columns:
                air["date"] = pd.to_datetime(air["date"], errors="coerce")
                latest = air.loc[air["date"] == air["date"].max()]
            else:
                latest = air
            pm = latest.groupby("district")["pm25_avg"].mean()
            if not pm.empty and district in pm.index:
                v = pm.loc[district]
                mn, mx = float(pm.min()), float(pm.max())
                air_score = 1.0 - ((v - mn) / (mx - mn)) if mx > mn else 0.5
    except Exception:
        air_score = None
    result["air_score"] = float(air_score) if air_score is not None else None

    # ── Proximity: compute FIRST so services_score can use it ──────────────────
    loc = get_listing_coords(listing)
    proximity = {"edu": {}, "hosp": {}, "uni": {}}
    _proximity_computed = False
    try:
        if loc is not None:
            lat0, lon0 = loc
            radii = [500, 1000, 2000]
            for name, df in [("edu", edu), ("hosp", hosp), ("uni", uni)]:
                if df.empty or "Coordinates" not in df.columns:
                    for r in radii:
                        proximity[name][str(r)] = 0
                    continue
                coords_df = _build_coords_series(df)
                dists = coords_df.apply(
                    lambda r: haversine_meters(lat0, lon0, float(r["lat"]), float(r["lon"])), axis=1
                )
                for r in radii:
                    proximity[name][str(r)] = int((dists <= r).sum())
            _proximity_computed = True
        else:
            for name in proximity:
                proximity[name] = {"500": 0, "1000": 0, "2000": 0}
    except Exception:
        for name in proximity:
            proximity[name] = {"500": 0, "1000": 0, "2000": 0}

    # ── Services score: proximity-based (2 km) when coords available ───────────
    # Falls back to district counts only when no coordinates are given.
    services_score = None
    counts = {"edu": 0, "hosp": 0, "uni": 0}
    try:
        if _proximity_computed:
            # Use facilities within 2 km as the count
            for name in ("edu", "hosp", "uni"):
                counts[name] = proximity[name].get("2000", 0)
            # Normalise against total dataset size (upper-bound proxy)
            # Max facilities within 2km across all district centers (pre-calibrated)
            MAX_2KM = {"edu": 144, "hosp": 32, "uni": 56}
            totals = {
                "edu":  MAX_2KM["edu"],
                "hosp": MAX_2KM["hosp"],
                "uni":  MAX_2KM["uni"],
            }
            norm_edu  = min(1.0, counts["edu"]  / totals["edu"])
            norm_hosp = min(1.0, counts["hosp"] / totals["hosp"])
            norm_uni  = min(1.0, counts["uni"]  / totals["uni"])
            # Weight: education 50%, hospitals 30%, universities 20%
            services_score = float(norm_edu * 0.5 + norm_hosp * 0.3 + norm_uni * 0.2)
        else:
            # Fallback: district-level counts (only edu has District column)
            for name, df in [("edu", edu), ("hosp", hosp), ("uni", uni)]:
                if df.empty:
                    counts[name] = 0; continue
                col = "District" if "District" in df.columns else ("district" if "district" in df.columns else None)
                if not col:
                    counts[name] = 0; continue
                by_dist = df.groupby(col).size()
                counts[name] = int(by_dist.get(district, 0))
            norms = []
            for name, df in [("edu", edu), ("hosp", hosp), ("uni", uni)]:
                if df.empty:
                    norms.append(0.0); continue
                col = "District" if "District" in df.columns else ("district" if "district" in df.columns else None)
                if not col:
                    norms.append(0.0); continue
                by_dist = df.groupby(col).size()
                max_c = int(by_dist.max()) if not by_dist.empty else 1
                norms.append(counts.get(name, 0) / max(1, max_c))
            services_score = float(sum(norms) / len(norms)) if norms else None
    except Exception:
        services_score = None
    result["services_score"] = float(services_score) if services_score is not None else None

    # Combine scores with weights
    weights = {"price": 0.35, "safety": 0.25, "air": 0.2, "services": 0.2}
    total_weight = 0.0
    weighted = 0.0
    for key, w in weights.items():
        val = {"price": price_score, "safety": safety_score, "air": air_score, "services": services_score}.get(key)
        if val is not None:
            weighted += float(val) * w
            total_weight += w
    combined = (weighted / total_weight) if total_weight > 0 else None
    result["combined_score"] = float(combined) if combined is not None else None
    result["star_rating"] = round((combined * 5), 2) if combined is not None else None

    # Human-friendly summary
    summary = []
    if result.get("star_rating") is not None:
        summary.append(f"Overall rating: {result['star_rating']}/5")
    if price_score is not None:
        summary.append(f"Price vs district median: {price_score:.2f}")
    if safety_score is not None:
        summary.append(f"Safety score: {safety_score:.2f}")
    if air_score is not None:
        summary.append(f"Air quality score: {air_score:.2f}")
    if services_score is not None:
        summary.append(f"Local services score (2 km): {services_score:.2f}")

    if district is None:
        result["errors"].append("District not provided or inferred.")

    result["summary"] = summary
    result["counts"] = {"edu": counts.get("edu", 0), "hosp": counts.get("hosp", 0), "uni": counts.get("uni", 0)}
    result["proximity"] = proximity
    result["candidates"] = candidate_districts(address)

    # Verdict
    if result.get("combined_score") is not None:
        score = result["combined_score"]
        if score >= 0.75:
            verdict = "Good option"
        elif score >= 0.55:
            verdict = "Acceptable option"
        else:
            verdict = "Risky option"
        result["verdict"] = verdict
    else:
        result["verdict"] = "Need district or coordinates"

    return result