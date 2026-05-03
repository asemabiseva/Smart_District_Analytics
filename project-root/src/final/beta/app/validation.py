"""Input validation, geocoding, and error message helpers."""

import os
import re
import requests
from typing import Dict, Any, Tuple, Optional
import pandas as pd
from .constants import ALMATY_BOUNDS, DISTRICT_COORDS


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


def validate_price(price: Any) -> float:
    """Validate and convert price to float.
    
    Raises ValidationError with specific reason if invalid.
    """
    if price is None or price == "":
        raise ValidationError("Price is required. Please enter a number.")
    
    try:
        p = float(price)
    except (ValueError, TypeError):
        raise ValidationError(f"Price must be a number, got '{price}'.")
    
    if p <= 0:
        raise ValidationError(f"Price must be positive (got {p} ₸).")
    
    if p > 500_000_000:
        raise ValidationError(f"Price seems unrealistic ({p} ₸). Max expected ~500M ₸.")
    
    return p


def validate_address(address: str) -> str:
    """Validate address string.
    
    Raises ValidationError if invalid.
    """
    if not address or not isinstance(address, str) or not address.strip():
        raise ValidationError("Address is required. Please enter a street address or district name.")
    
    if len(address) < 3:
        raise ValidationError(f"Address too short ('{address}'). Please provide more detail.")
    
    if len(address) > 500:
        raise ValidationError(f"Address too long ({len(address)} chars). Please shorten.")
    
    return address.strip()


def validate_coordinates(lat: Any, lon: Any) -> Tuple[float, float]:
    """Validate latitude and longitude.
    
    Raises ValidationError if invalid.
    Returns (lat, lon) tuple if valid.
    """
    if lat is None or lon is None:
        raise ValidationError("Both latitude and longitude are required.")
    
    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except (ValueError, TypeError):
        raise ValidationError(f"Coordinates must be numbers (got lat={lat}, lon={lon}).")
    
    lat_min, lat_max = ALMATY_BOUNDS["lat_min"], ALMATY_BOUNDS["lat_max"]
    lon_min, lon_max = ALMATY_BOUNDS["lon_min"], ALMATY_BOUNDS["lon_max"]
    
    if not (lat_min <= lat_f <= lat_max):
        raise ValidationError(f"Latitude {lat_f} is outside Almaty range ({lat_min}-{lat_max}).")
    
    if not (lon_min <= lon_f <= lon_max):
        raise ValidationError(f"Longitude {lon_f} is outside Almaty range ({lon_min}-{lon_max}).")
    
    return (lat_f, lon_f)


def validate_district(district: str) -> str:
    """Validate that district is a known district in Almaty.
    
    Raises ValidationError if invalid.
    """
    if not district or not isinstance(district, str):
        raise ValidationError("District is required. Please select a district.")
    
    if district not in DISTRICT_COORDS:
        valid_dists = ", ".join(sorted(DISTRICT_COORDS.keys()))
        raise ValidationError(
            f"'{district}' is not a recognized district. "
            f"Valid options: {valid_dists}."
        )
    
    return district


def validate_url(url: str) -> str:
    """Validate that URL is a valid Krisha.kz listing URL.
    
    Raises ValidationError if invalid format.
    """
    if not url or not isinstance(url, str) or not url.strip():
        raise ValidationError("URL is required or leave blank for manual entry.")
    
    url = url.strip()
    
    # Accept URLs that look like Krisha.kz listings
    if "krisha.kz" not in url.lower():
        raise ValidationError(
            f"URL must be from krisha.kz (got: {url[:50]}...)."
        )
    
    if not url.lower().startswith(("http://", "https://")):
        raise ValidationError(
            f"URL must start with http:// or https://"
        )
    
    return url


# def geocode_address(address: str, timeout: int = 5) -> Optional[Tuple[float, float]]:
#     """Convert address to coordinates using Nominatim (free, no API key needed).
    
#     Returns (lat, lon) if successful, None if failed.
#     Gracefully handles network errors.
#     """
#     if not address or not isinstance(address, str):
#         return None
    
#     try:
#         # Nominatim free API - specify Almaty to focus search
#         query = f"{address}, Almaty, Kazakhstan"
#         headers = {"User-Agent": "AlmatyLivingGuide/1.0"}
        
#         response = requests.get(
#             "https://nominatim.openstreetmap.org/search",
#             params={"q": query, "format": "json"},
#             headers=headers,
#             timeout=timeout,
#         )
        
#         if response.status_code == 200 and response.json():
#             result = response.json()[0]
#             lat = float(result.get("lat"))
#             lon = float(result.get("lon"))
            
#             # Validate coordinates are in Almaty bounds
#             if ALMATY_BOUNDS["lat_min"] <= lat <= ALMATY_BOUNDS["lat_max"] and \
#                ALMATY_BOUNDS["lon_min"] <= lon <= ALMATY_BOUNDS["lon_max"]:
#                 return (lat, lon)
#     except (requests.RequestException, TimeoutError, ValueError, IndexError):
#         # Network error, timeout, or parsing error - return None gracefully
#         pass
    
#     return None
def geocode_address(address: str, timeout: int = 5) -> Optional[Tuple[float, float]]:
    if not address or not isinstance(address, str):
        return None

    try:
        query = address
        if "almaty" not in address.lower():
            query = f"{address}, Almaty, Kazakhstan"

        headers = {"User-Agent": "AlmatyLivingGuide/1.0"}

        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": query, "format": "json"},
            headers=headers,
            timeout=timeout,
        )

        response.raise_for_status()
        data = response.json()

        if not data:
            return None

        result = data[0]
        lat = result.get("lat")
        lon = result.get("lon")

        if lat is None or lon is None:
            return None

        lat, lon = float(lat), float(lon)

        if (
            ALMATY_BOUNDS["lat_min"] <= lat <= ALMATY_BOUNDS["lat_max"]
            and ALMATY_BOUNDS["lon_min"] <= lon <= ALMATY_BOUNDS["lon_max"]
        ):
            return (lat, lon)

    except Exception as e:
        print(f"Geocoding error: {e}")

    return None

def format_error_message(error: Exception) -> str:
    """Format an exception into a user-friendly error message.
    
    Args:
        error: ValidationError or other exception
    
    Returns:
        Formatted error string with emoji
    """
    if isinstance(error, ValidationError):
        return f"⚠️ {str(error)}"
    
    return f"❌ Unexpected error: {str(error)}"


def format_success_message(listing_title: str, verdict: str) -> str:
    """Format a success message after listing analysis.
    
    Args:
        listing_title: Title of the analyzed listing
        verdict: Analysis verdict (e.g., "Good option", "Risky option")
    
    Returns:
        Formatted success string with emoji
    """
    emoji_map = {
        "good": "✅",
        "acceptable": "🟡",
        "risky": "⚠️",
    }
    emoji = emoji_map.get(verdict.lower().split()[0], "📊")
    return f"{emoji} **{listing_title}**: {verdict}"


def safe_read_csv(path: str, parse_dates=None, required_columns: Optional[list] = None, **kwargs) -> Optional[pd.DataFrame]:
    """Safely read a CSV file returning a DataFrame or None.

    - Returns None if the file is missing or cannot be parsed.
    - If `required_columns` is provided, returns None when missing.
    - Keeps callers simple: they can check `if df is not None and not df.empty`.
    """
    if not path:
        return None

    # Support both relative and absolute paths
    try:
        if not os.path.isabs(path):
            base = os.getcwd()
            path = os.path.join(base, path)
    except Exception:
        # Fall back to given path
        pass

    if not os.path.exists(path):
        return None

    try:
        df = pd.read_csv(path, parse_dates=parse_dates, **kwargs)
    except Exception:
        return None

    if required_columns:
        missing = [c for c in required_columns if c not in df.columns]
        if missing:
            return None

    return df
