DISTRICT_COORDS = {
    "Алмалинский": {"lat": 43.2565, "lon": 76.9286, "name_en": "Almalinsky"},
    "Бостандыкский": {"lat": 43.2200, "lon": 76.8900, "name_en": "Bostandyk"},
    "Медеуский": {"lat": 43.2300, "lon": 76.9700, "name_en": "Medeu"},
    "Турксибский": {"lat": 43.3100, "lon": 77.0200, "name_en": "Turksib"},
    "Жетысуский": {"lat": 43.2900, "lon": 76.9900, "name_en": "Zhetysu"},
    "Наурызбайский": {"lat": 43.1700, "lon": 76.8100, "name_en": "Nauryzbay"},
    "Ауэзовский": {"lat": 43.2100, "lon": 76.8300, "name_en": "Auezov"},
    "Алатауский": {"lat": 43.3400, "lon": 76.8800, "name_en": "Alatau"},
}

# Centralized district keywords for consistent inference across all pages
DISTRICT_KEYWORDS = {
    "Алмалинский": ["алмалин", "алматы-центр", "центр", "арбат"],
    "Бостандыкский": ["бостандык", "самал", "орбита", "коктем", "горный гигант", "юбилейный"],
    "Медеуский": ["медеу", "достык", "керемет", "карасай", "нурлытау"],
    "Турксибский": ["турксиб", "шанырак", "жулдыз"],
    "Жетысуский": ["жетысу", "степной", "горный"],
    "Наурызбайский": ["наурызбай", "думан", "атырау"],
    "Ауэзовский": ["ауэзов", "саяхат", "тастак", "дорожник", "момышулы", "абая"],
    "Алатауский": ["алатау", "кайрат", "акбулак", "шарипова"],
}

# Almaty geobounds for coordinate validation (rough)
ALMATY_BOUNDS = {
    "lat_min": 42.8,
    "lat_max": 43.5,
    "lon_min": 76.5,
    "lon_max": 77.3,
}

RISK_COLORS = {
    "low": "#1F9D55",
    "medium": "#E6A700",
    "high": "#D64545",
}

DATA_SOURCES = {
    "air": "processed_air_ala_data.csv",
    "accidents": "processed_table.csv",
    "housing": "krisha_final.csv",
    "education": "Almaty_Education_Master.csv",
    "hospitals": "hospitals_almaty.csv",
    "universities": "universities_almaty.csv",
}

# Mapping from numeric district code (as found in some datasets) to canonical district name
# Keep this minimal and authoritative so callers can use one source for code -> name
DISTRICT_CODE_TO_NAME = {
    191910: "Алмалинский",
    191960: "Бостандыкский",
    191956: "Медеуский",
    191966: "Турксибский",
    191932: "Жетысуский",
    191934: "Наурызбайский",
    191916: "Ауэзовский",
    191926: "Алатауский",
    # Additional codes seen in accident datasets
    191940: "Жетысуский 2",
    191964: "Наурызбай 2",
}

# Optional numeric-keyed coords for mapping by code (fallback for pages that use numeric keys)
DISTRICT_CODE_COORDS = {
    191910: {"lat": 43.2565, "lon": 76.9286, "name": "Алмалинский", "name_en": "Almalinsky"},
    191960: {"lat": 43.2200, "lon": 76.8900, "name": "Бостандыкский", "name_en": "Bostandyk"},
    191956: {"lat": 43.2300, "lon": 76.9700, "name": "Медеуский", "name_en": "Medeu"},
    191966: {"lat": 43.3100, "lon": 77.0200, "name": "Турксибский", "name_en": "Turksib"},
    191932: {"lat": 43.2900, "lon": 76.9900, "name": "Жетысуский", "name_en": "Zhetysu"},
    191934: {"lat": 43.1700, "lon": 76.8100, "name": "Наурызбайский", "name_en": "Nauryzbay"},
    191916: {"lat": 43.2100, "lon": 76.8300, "name": "Ауэзовский", "name_en": "Auezov"},
    191926: {"lat": 43.3400, "lon": 76.8800, "name": "Алатауский", "name_en": "Alatau"},
}
