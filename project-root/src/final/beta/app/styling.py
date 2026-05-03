"""
Advanced styling utilities for the Almaty Living Guide app.
"""

import streamlit as st
from .theme import get_theme


def apply_advanced_styles() -> None:
    """Apply additional CSS animations (base styles are in ui.py apply_base_style)."""
    # The comprehensive styling is already applied by apply_base_style() in ui.py.
    # This function applies any additional or page-specific styles.
    theme = get_theme(st.session_state.get("theme_mode", "light"))

    st.markdown(
        f"""
        <style>
        /* Staggered fade-in for columns */
        [data-testid="column"]:nth-child(1) {{ animation: fadeIn 0.3s ease-out; }}
        [data-testid="column"]:nth-child(2) {{ animation: fadeIn 0.4s ease-out; }}
        [data-testid="column"]:nth-child(3) {{ animation: fadeIn 0.5s ease-out; }}
        [data-testid="column"]:nth-child(4) {{ animation: fadeIn 0.6s ease-out; }}

        /* Metric container fade */
        [data-testid="metric-container"] {{
            animation: fadeIn 0.4s ease-out;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_badge(text: str, badge_type: str = "primary") -> None:
    """Render a styled badge."""
    st.markdown(f'<span class="badge badge-{badge_type}">{text}</span>', unsafe_allow_html=True)


def render_metric_card(label: str, value: str | int, change: str = "", icon: str = "") -> None:
    """Render a styled metric card."""
    st.markdown(f"""
    <div class="metric-card">
        {f'<div style="font-size: 1.8rem; margin-bottom: 6px;">{icon}</div>' if icon else ''}
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
        {f'<div class="metric-subtitle">{change}</div>' if change else ''}
    </div>
    """, unsafe_allow_html=True)
