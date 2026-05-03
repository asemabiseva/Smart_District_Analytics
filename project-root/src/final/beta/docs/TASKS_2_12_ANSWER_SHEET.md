# Beta System Tasks 2-12 Answer Sheet

Project: Almaty Living Guide
Date: 2026-04-30

## Task 2: Break Your Own System

Tested against the current listing analyzer and housing flow.

| Test | Result | Failure | Severity | Fix Idea |
|---|---|---|---|---|
| Rapid requests | Analyzer can be triggered repeatedly, but each run reloads CSV data and can feel slow under back-to-back clicks. | No crash, but repeated use wastes time and resources. | Medium | Cache loaded datasets more aggressively and debounce the Analyze button. |
| Long input | Very long title/address text is accepted. Analysis still runs, but the text can make the form hard to read. | UI clutter and lower usability. | Low | Add max length hints and truncate preview text. |
| Empty input | If title/address are empty, the analyzer cannot infer district well and returns weak results. | Missing district, missing price context, weak score. | High | Block submit until required fields are filled or show clear validation messages. |
| Invalid formats | Non-numeric price or invalid lat/lon can break parsing or be ignored. | Inconsistent output and warnings. | High | Validate price and coordinates before analysis. |

## Task 3: Logging Implementation

Add logging for request start, success, and failure.

### Code snippet
```python
import logging

logger = logging.getLogger("almaty_living_guide")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def analyze_request(listing: dict):
    logger.info("request_start", extra={"district": listing.get("district")})
    try:
        result = analyze_listing(listing)
        logger.info("request_success", extra={"verdict": result.get("verdict"), "rating": result.get("star_rating")})
        return result
    except Exception as exc:
        logger.exception("request_failure")
        raise
```

### Example log output
```text
2026-04-30 17:13:19 INFO request_start district=Алмалинский
2026-04-30 17:13:19 INFO request_success verdict=Risky option rating=0.05
```

## Task 4: Performance Measurement

Measured in the project virtual environment using the current analyzer.

| Case | Time | Observation |
|---|---|---|
| Normal input | 0.113 s | Fast enough for interactive use. Most time is spent loading datasets. |
| Heavy input | 0.100 s | Long text does not change time much because file loading dominates cost. |

## Task 5: Bottleneck Identification

- Slowest part: loading CSV datasets on every analysis run. This is the main cost because the analyzer reads housing, accidents, air, education, hospitals, and universities data each time.
- Fragile part: district inference from text and URL parsing. If the address is short or the page layout changes, the analyzer loses context and results become weaker.
- Complex part: proximity analysis. Matching one listing to many education, hospital, and university records with distance calculations is the most logic-heavy part.

## Task 6: Tech Debt Fix

Three issues found:
- Hardcoding: district names, coordinates, and code mappings were repeated in several places.
- Repetition: similar loading and parsing logic appeared in multiple files.
- Poor structure: the listing analyzer was originally mixed into the housing page instead of living in one module.

Fix applied:
- Moved the scoring logic into `app/listing_analyzer.py` and kept shared district constants in `app/constants.py`.
- This reduced duplication and made the code easier to change.

## Task 7: Input Validation

Checks added or needed:
- Empty input: require at least address or district before analysis.
- Invalid format: block invalid price, latitude, and longitude values.

Improved behavior:
- Before: empty or weak input returned generic scores like `0.50` and `0%`.
- After: the app warns the user and shows that district or coordinates are needed for a meaningful result.

## Task 8: Failure Recovery Design

| Scenario | Current Behavior | Improved Behavior |
|---|---|---|
| API fails | If URL fetch fails, the analysis may continue with manual fields only or return a warning. | Keep manual entry available and show a clear message: the user can still analyze the listing without URL fetch. |
| Database fails | The app uses CSV files; if one is missing, the current page can stop or show an error. | Use `safe_read_csv`, cached fallback summaries, and a friendly error that names the missing dataset. |
| Server crash | Session data can be lost and the user must start over. | Save the latest analysis inputs in `st.session_state` and let the user restore the last form values. |

## Task 9: Feature Expansion

Added feature: listing analysis search.

What it does:
- The user can paste a Krisha.kz URL or enter listing details manually.
- The system analyzes that one property option and gives a short recommendation.

Why this helps:
- It moves the app from district comparison only to a practical property decision tool.
- It is easier for users to test one listing than to interpret many charts.

## Task 10: UI/UX Improvement

Improvements made:
- Layout: the Home page now has a clear flow: choose district, view metrics, analyze a listing, then explore other pages.
- Error messages: the app now explains when district, price, or coordinates are missing instead of failing silently.
- Feedback: result cards show a verdict, rating, summary, and nearby facility table in a more readable format.

## Task 11: Data Handling

### Null values
Before:
- Missing district or coordinates produced weak fallback values.
- Some outputs showed `None` or unreadable raw dictionaries.

After:
- Missing values are treated as unavailable and explained to the user.
- The app asks for a district or coordinates when they are needed.

### Formatting
Before:
- Output could look like `Edu/Hosp/Uni: {'edu': 0, 'hosp': 0, 'uni': 0}`.
- Ratings and metrics were harder to read.

After:
- Results are shown as short labels, metrics, and a simple verdict.
- Nearby facilities are shown in a table with clean counts.

## Task 12: System Explanation

### What it does, about 200 words
Almaty Living Guide helps a person decide where to live in Almaty. It compares districts using real data about air quality, accidents, housing prices, schools, hospitals, and universities. A user can open the Home page, pick a district, and quickly see how that area looks in terms of safety, cost, and services. The system also lets the user check one housing listing from Krisha.kz and judge whether it is a good option. For that, the app compares the listing price with the district median, looks at local safety and air quality, and checks whether useful services are nearby. The goal is not to replace human judgment. The goal is to make the decision easier by combining several kinds of city data into one place. That way, a user does not need to jump between many websites or guess based on price alone. The app gives a practical view of the district and the listing so the user can choose with more confidence.

### How it works, about 200 words
The system is a Streamlit app built with Python. It loads several CSV files with city data. One file contains air quality data, another contains road accident data, and other files contain housing, schools, hospitals, and universities. The app uses shared helper functions to keep the interface and data loading consistent across pages. When the user selects a district, the app calculates summary metrics for that district and shows them on the screen. When the user analyzes a listing, the app reads the listing fields, tries to infer the district from the address, and uses optional latitude and longitude values if they are given. It then compares the listing price with the district median and checks nearby services by calculating distance from the listing to each school, hospital, and university in the data. The app also gives a short verdict, such as good, acceptable, or risky. If data is missing, the app now warns the user instead of pretending the result is certain. This keeps the system simple, explainable, and easier to use.
