# Almaty Living Guide - Answer Report

Date: 2026-04-30
Project Root: /Users/mac/Desktop/jupyterLab/f2

## 1. Executive Summary

This project delivers a multi-page Streamlit decision-support app for Almaty districts.
It combines housing, air quality, traffic accidents, education, hospitals, and universities data into actionable insights.

Recent work focused on:
- Simplifying Home page usability and flow.
- Adding listing-level housing analysis.
- Enabling geolocation-based proximity checks for nearby services.

## 2. Problem Addressed

Users needed a practical way to answer:
- Is this district safer and cleaner?
- Is this housing option overpriced or fair?
- Are schools, kindergartens, hospitals, and universities nearby?

## 3. Implemented Solution

### 3.1 Core App Structure

- Multi-page Streamlit app with shared utilities in app/.
- Pages for Air Quality, Accidents, Housing, Forecast, Infrastructure, and District Score.
- Shared styling, data freshness, glossary, and feedback widgets.

### 3.2 Home Page Logic Improvement

Home page was refactored to a clearer user flow:
1. Select district.
2. View top-level district metrics.
3. Browse housing listings with budget filters.
4. Jump to detailed pages.

### 3.3 Housing Listing Analyzer (New)

A new listing analyzer was added to evaluate a single property option.

Implemented in:
- app/listing_analyzer.py
- pages/3_Housing.py

Capabilities:
- Input listing details manually (title, address, price, area, rooms).
- Optional URL fetch (best-effort parsing).
- District inference from listing text.
- Score breakdown:
  - Price vs district median
  - Safety score
  - Air quality score
  - Services score
- Combined rating output (star-style scale).

### 3.4 Geolocation + Nearby Services (New)

Geo-based analysis now supports proximity counts for nearby facilities.

What was added:
- Optional listing latitude/longitude inputs.
- Coordinate parsing from datasets.
- Haversine distance computation.
- Nearby facilities counted within:
  - 500m
  - 1000m
  - 2000m

Facility groups:
- Education (schools/kindergartens)
- Hospitals
- Universities

Behavior:
- If exact listing coordinates are missing, district center is used as fallback.
- If district inference is uncertain, candidate districts are surfaced.

## 4. Data Sources Used

From datasets/:
- processed_air_ala_data.csv
- processed_table.csv
- krisha_final.csv
- Almaty_Education_Master.csv
- hospitals_almaty.csv
- universities_almaty.csv

## 5. Validation and Checks

Completed:
- Python compile checks on modified modules:
  - pages/3_Housing.py
  - app/listing_analyzer.py
- Streamlit app launch was successful earlier in the session.

Not completed in current interpreter:
- Unit tests via pytest failed to run because pytest is not installed in the active Python executable.

## 6. Current Limitations

- URL parsing for listing extraction is best-effort and may break with site HTML changes.
- District inference is text-keyword based when exact geo data is absent.
- Safety and air mappings depend on district-level dataset consistency.
- Geolocation fallback to district center is approximate, not exact building location.

## 7. Recommended Next Steps

1. Add robust URL parser selectors for Krisha pages and graceful parser fallbacks.
2. Add address geocoding (Mapbox/Nominatim) to auto-fill lat/lon from address.
3. Add automated tests for listing_analyzer.py (district inference, scoring, proximity).
4. Add map visualization for the input listing and nearby points.
5. Install pytest in active environment and run full test suite.

## 8. Outcome

The project now goes beyond district-level dashboards and can assess a specific housing listing option with practical, explainable metrics, including nearby service accessibility based on geolocation.
