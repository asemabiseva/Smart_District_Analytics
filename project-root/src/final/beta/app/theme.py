"""
Theme system for Almaty Living Guide with day/night mode support.
"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class ColorPalette:
    """Color palette for a theme."""
    # Primary colors
    primary: str
    primary_light: str
    primary_dark: str

    # Backgrounds
    bg_main: str
    bg_secondary: str
    bg_tertiary: str

    # Text colors
    text_primary: str
    text_secondary: str
    text_muted: str

    # Semantic colors
    success: str
    warning: str
    danger: str
    info: str

    # Component colors
    border: str
    shadow: str
    card_bg: str

    # Accent colors for charts
    accent_1: str
    accent_2: str
    accent_3: str
    accent_4: str

    # Streamlit-specific overrides
    st_bg: str
    st_sidebar_bg: str
    st_text: str
    st_widget_bg: str
    st_widget_border: str


# Light theme palette
LIGHT_THEME = ColorPalette(
    primary="#1a6ef5",
    primary_light="#4d8ef7",
    primary_dark="#1254cc",

    bg_main="#f7f9fc",
    bg_secondary="#eef1f6",
    bg_tertiary="#e3eaf5",

    text_primary="#0f1923",
    text_secondary="#374151",
    text_muted="#6b7280",

    success="#059669",
    warning="#d97706",
    danger="#dc2626",
    info="#0284c7",

    border="#dde3ec",
    shadow="rgba(15,25,35,0.08)",
    card_bg="#ffffff",

    accent_1="#0ea5e9",
    accent_2="#06b6d4",
    accent_3="#f59e0b",
    accent_4="#ef4444",

    # Streamlit internal
    st_bg="#f7f9fc",
    st_sidebar_bg="#eef1f6",
    st_text="#0f1923",
    st_widget_bg="#ffffff",
    st_widget_border="#dde3ec",
)

# Dark theme palette
DARK_THEME = ColorPalette(
    primary="#4d8ef7",
    primary_light="#7aaeff",
    primary_dark="#2563eb",

    bg_main="#0d1117",
    bg_secondary="#161b22",
    bg_tertiary="#21262d",

    text_primary="#e6edf3",
    text_secondary="#c9d1d9",
    text_muted="#8b949e",

    success="#3fb950",
    warning="#d29922",
    danger="#f85149",
    info="#58a6ff",

    border="#30363d",
    shadow="rgba(0,0,0,0.5)",
    card_bg="#161b22",

    accent_1="#58a6ff",
    accent_2="#3fb950",
    accent_3="#d29922",
    accent_4="#f85149",

    # Streamlit internal
    st_bg="#0d1117",
    st_sidebar_bg="#161b22",
    st_text="#e6edf3",
    st_widget_bg="#21262d",
    st_widget_border="#30363d",
)


def get_theme(mode: Literal["light", "dark"]) -> ColorPalette:
    """Get the color palette for the specified theme mode."""
    return LIGHT_THEME if mode == "light" else DARK_THEME


def get_css_variables(colors: ColorPalette) -> str:
    """Generate CSS variable definitions for the given color palette."""
    return f"""
    --primary: {colors.primary};
    --primary-light: {colors.primary_light};
    --primary-dark: {colors.primary_dark};
    --bg-main: {colors.bg_main};
    --bg-secondary: {colors.bg_secondary};
    --bg-tertiary: {colors.bg_tertiary};
    --text-primary: {colors.text_primary};
    --text-secondary: {colors.text_secondary};
    --text-muted: {colors.text_muted};
    --success: {colors.success};
    --warning: {colors.warning};
    --danger: {colors.danger};
    --info: {colors.info};
    --border: {colors.border};
    --shadow: {colors.shadow};
    --card-bg: {colors.card_bg};
    --accent-1: {colors.accent_1};
    --accent-2: {colors.accent_2};
    --accent-3: {colors.accent_3};
    --accent-4: {colors.accent_4};
    """
