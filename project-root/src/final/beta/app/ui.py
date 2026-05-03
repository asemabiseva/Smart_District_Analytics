from __future__ import annotations

import streamlit as st
from .constants import RISK_COLORS
from .theme import get_theme, get_css_variables


def apply_base_style() -> None:
    """Apply base styling with modern design and comprehensive theme support."""
    if "theme_mode" not in st.session_state:
        st.session_state.theme_mode = "light"

    theme = get_theme(st.session_state.theme_mode)
    css_vars = get_css_variables(theme)
    is_dark = st.session_state.theme_mode == "dark"

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

        :root {{
            {css_vars}
        }}

        /* ── STREAMLIT APP BACKGROUND ──────────────────────────── */
        .stApp {{
            background-color: {theme.st_bg} !important;
        }}

        /* ── MAIN CONTENT AREA ─────────────────────────────────── */
        .main .block-container {{
            background-color: {theme.st_bg} !important;
            padding-top: 2rem;
        }}

        /* ── SIDEBAR ───────────────────────────────────────────── */
        [data-testid="stSidebar"] {{
            background-color: {theme.st_sidebar_bg} !important;
            border-right: 1px solid {theme.border} !important;
        }}

        [data-testid="stSidebar"] * {{
            color: {theme.text_primary} !important;
        }}

        [data-testid="stSidebarNav"] {{
            background-color: {theme.st_sidebar_bg} !important;
        }}

        /* ── ALL TEXT ───────────────────────────────────────────── */
        body, p, span, div, label, li, td, th {{
            color: {theme.text_primary};
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }}

        h1, h2, h3, h4, h5, h6 {{
            color: {theme.text_primary} !important;
            font-family: 'Inter', sans-serif;
            font-weight: 700;
        }}

        h2 {{
            border-bottom: 2px solid {theme.border};
            padding-bottom: 0.5rem;
            margin: 2rem 0 1.25rem 0;
        }}

        /* ── STREAMLIT MARKDOWN ─────────────────────────────────── */
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] li,
        [data-testid="stMarkdownContainer"] span {{
            color: {theme.text_primary} !important;
        }}

        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3 {{
            color: {theme.text_primary} !important;
        }}

        /* ── METRICS ────────────────────────────────────────────── */
        [data-testid="stMetricValue"] {{
            color: {theme.primary} !important;
            font-weight: 800 !important;
            font-size: 1.8rem !important;
        }}

        [data-testid="stMetricLabel"] {{
            color: {theme.text_secondary} !important;
            font-weight: 500 !important;
        }}

        [data-testid="stMetricDelta"] {{
            color: {theme.text_muted} !important;
        }}

        [data-testid="metric-container"] {{
            background: {theme.card_bg} !important;
            border: 1px solid {theme.border} !important;
            border-radius: 12px !important;
            padding: 1rem 1.25rem !important;
            box-shadow: 0 2px 6px {theme.shadow} !important;
            transition: box-shadow 0.2s ease !important;
        }}

        [data-testid="metric-container"]:hover {{
            box-shadow: 0 6px 20px {theme.shadow} !important;
        }}

        /* ── INPUT WIDGETS ──────────────────────────────────────── */
        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-testid="stTextArea"] textarea {{
            background: {theme.st_widget_bg} !important;
            color: {theme.text_primary} !important;
            border: 1px solid {theme.st_widget_border} !important;
            border-radius: 8px !important;
            font-family: 'Inter', sans-serif !important;
        }}

        [data-testid="stTextInput"] input:focus,
        [data-testid="stNumberInput"] input:focus,
        [data-testid="stTextArea"] textarea:focus {{
            border-color: {theme.primary} !important;
            box-shadow: 0 0 0 3px {theme.primary}22 !important;
        }}

        [data-testid="stTextInput"] label,
        [data-testid="stNumberInput"] label,
        [data-testid="stTextArea"] label,
        [data-testid="stSelectbox"] label,
        [data-testid="stMultiSelect"] label,
        [data-testid="stSlider"] label,
        [data-testid="stRadio"] label,
        [data-testid="stDateInput"] label {{
            color: {theme.text_primary} !important;
            font-weight: 500 !important;
        }}

        /* ── SELECT & DROPDOWN ──────────────────────────────────── */
        [data-baseweb="select"] > div,
        [data-baseweb="select"] {{
            background: {theme.st_widget_bg} !important;
            border-color: {theme.st_widget_border} !important;
            border-radius: 8px !important;
        }}

        [data-baseweb="select"] span,
        [data-baseweb="select"] div {{
            color: {theme.text_primary} !important;
            background: transparent;
        }}

        [data-baseweb="popover"] {{
            background: {theme.card_bg} !important;
            border: 1px solid {theme.border} !important;
            box-shadow: 0 8px 24px {theme.shadow} !important;
        }}

        [data-baseweb="menu"] {{
            background: {theme.card_bg} !important;
        }}

        [data-baseweb="menu"] li {{
            color: {theme.text_primary} !important;
        }}

        [data-baseweb="menu"] li:hover {{
            background: {theme.bg_secondary} !important;
        }}

        [data-baseweb="tag"] {{
            background: {theme.primary}22 !important;
            border: 1px solid {theme.primary}44 !important;
        }}

        [data-baseweb="tag"] span {{
            color: {theme.primary} !important;
        }}

        /* ── SLIDERS ────────────────────────────────────────────── */
        [data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {{
            background: {theme.primary} !important;
            border-color: {theme.primary} !important;
        }}

        [data-testid="stSlider"] [data-baseweb="slider"] div[class*="track"] {{
            background: {theme.bg_tertiary} !important;
        }}

        /* ── RADIO ──────────────────────────────────────────────── */
        [data-testid="stRadio"] p {{
            color: {theme.text_primary} !important;
        }}

        /* ── BUTTONS ────────────────────────────────────────────── */
        [data-testid="baseButton-primary"],
        button[kind="primary"] {{
            background: linear-gradient(135deg, {theme.primary} 0%, {theme.primary_dark} 100%) !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            font-family: 'Inter', sans-serif !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 2px 8px {theme.primary}44 !important;
        }}

        [data-testid="baseButton-primary"]:hover {{
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 16px {theme.primary}66 !important;
        }}

        [data-testid="baseButton-secondary"],
        button[kind="secondary"] {{
            background: {theme.st_widget_bg} !important;
            color: {theme.text_primary} !important;
            border: 1px solid {theme.border} !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
            font-family: 'Inter', sans-serif !important;
            transition: all 0.2s ease !important;
        }}

        [data-testid="baseButton-secondary"]:hover {{
            border-color: {theme.primary} !important;
            color: {theme.primary} !important;
        }}

        /* ── EXPANDERS ──────────────────────────────────────────── */
        [data-testid="stExpander"] {{
            background: {theme.card_bg} !important;
            border: 1px solid {theme.border} !important;
            border-radius: 10px !important;
            overflow: hidden;
        }}

        [data-testid="stExpander"] summary {{
            color: {theme.text_primary} !important;
            font-weight: 600 !important;
        }}

        [data-testid="stExpander"] summary:hover {{
            background: {theme.bg_secondary} !important;
        }}

        [data-testid="stExpander"] > div {{
            background: {theme.card_bg} !important;
        }}

        /* ── INFO / SUCCESS / ERROR / WARNING BOXES ─────────────── */
        [data-testid="stAlert"] {{
            border-radius: 10px !important;
            border-width: 1px !important;
        }}

        div[data-testid="stInfo"] {{
            background: {theme.info}15 !important;
            border-color: {theme.info}50 !important;
            color: {theme.text_primary} !important;
        }}

        div[data-testid="stSuccess"] {{
            background: {theme.success}15 !important;
            border-color: {theme.success}50 !important;
            color: {theme.text_primary} !important;
        }}

        div[data-testid="stWarning"] {{
            background: {theme.warning}15 !important;
            border-color: {theme.warning}50 !important;
            color: {theme.text_primary} !important;
        }}

        div[data-testid="stError"] {{
            background: {theme.danger}15 !important;
            border-color: {theme.danger}50 !important;
            color: {theme.text_primary} !important;
        }}

        /* ── CAPTION / SMALL TEXT ───────────────────────────────── */
        [data-testid="stCaptionContainer"] p {{
            color: {theme.text_muted} !important;
        }}

        /* ── DATAFRAMES / TABLES ────────────────────────────────── */
        [data-testid="stDataFrame"],
        [data-testid="stTable"] {{
            background: {theme.card_bg} !important;
            border: 1px solid {theme.border} !important;
            border-radius: 10px !important;
            overflow: hidden !important;
        }}

        .stDataFrame [data-testid="column-header"] {{
            background: {theme.bg_secondary} !important;
            color: {theme.text_primary} !important;
        }}

        table {{
            background: {theme.card_bg};
            color: {theme.text_primary};
            border-collapse: collapse;
            width: 100%;
        }}

        thead {{
            background: {theme.bg_secondary};
        }}

        th {{
            background: {theme.bg_secondary};
            color: {theme.text_primary};
            padding: 12px 16px;
            font-weight: 600;
            border-bottom: 2px solid {theme.border};
        }}

        td {{
            padding: 10px 16px;
            border-bottom: 1px solid {theme.border};
            color: {theme.text_primary};
        }}

        tr:hover {{
            background: {theme.bg_secondary};
        }}

        /* ── TABS ───────────────────────────────────────────────── */
        [data-testid="stTabs"] [data-baseweb="tab-list"] {{
            background: {theme.bg_secondary} !important;
            border-radius: 10px !important;
            padding: 4px !important;
            gap: 4px;
        }}

        [data-testid="stTabs"] [data-baseweb="tab"] {{
            background: transparent !important;
            color: {theme.text_muted} !important;
            border-radius: 7px !important;
            font-weight: 500 !important;
        }}

        [data-testid="stTabs"] [aria-selected="true"] {{
            background: {theme.card_bg} !important;
            color: {theme.primary} !important;
            box-shadow: 0 1px 4px {theme.shadow} !important;
        }}

        /* ── DIVIDERS ───────────────────────────────────────────── */
        hr {{
            border: none;
            border-top: 1px solid {theme.border};
            margin: 1.5rem 0;
        }}

        /* ── DATE INPUT ─────────────────────────────────────────── */
        [data-testid="stDateInput"] input {{
            background: {theme.st_widget_bg} !important;
            color: {theme.text_primary} !important;
            border: 1px solid {theme.st_widget_border} !important;
            border-radius: 8px !important;
        }}

        /* ── MULTISELECT TAGS ───────────────────────────────────── */
        [data-baseweb="tag"] {{
            background: {theme.primary}20 !important;
        }}

        /* ── PAGE LINK BUTTONS ──────────────────────────────────── */
        [data-testid="stPageLink"] a {{
            background: {theme.card_bg} !important;
            border: 1px solid {theme.border} !important;
            color: {theme.text_primary} !important;
            border-radius: 10px !important;
            text-decoration: none !important;
            transition: all 0.2s ease !important;
        }}

        [data-testid="stPageLink"] a:hover {{
            border-color: {theme.primary} !important;
            color: {theme.primary} !important;
            box-shadow: 0 4px 12px {theme.shadow} !important;
        }}

        /* ── SCROLLBAR ──────────────────────────────────────────── */
        ::-webkit-scrollbar {{
            width: 6px;
            height: 6px;
        }}
        ::-webkit-scrollbar-track {{
            background: {theme.bg_secondary};
        }}
        ::-webkit-scrollbar-thumb {{
            background: {theme.border};
            border-radius: 3px;
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: {theme.text_muted};
        }}

        /* ══ CUSTOM COMPONENTS ═══════════════════════════════════ */

        /* Hero box */
        .hero-box {{
            background: linear-gradient(135deg, {theme.primary_dark} 0%, {theme.primary} 60%, {theme.accent_1} 100%);
            padding: 2.5rem 2.5rem;
            border-radius: 16px;
            margin: 0 0 2rem 0;
            box-shadow: 0 12px 32px {theme.primary}33;
            position: relative;
            overflow: hidden;
        }}

        .hero-box::before {{
            content: '';
            position: absolute;
            top: -40px;
            right: -40px;
            width: 240px;
            height: 240px;
            background: rgba(255,255,255,0.08);
            border-radius: 50%;
        }}

        .hero-box::after {{
            content: '';
            position: absolute;
            bottom: -60px;
            left: -20px;
            width: 180px;
            height: 180px;
            background: rgba(255,255,255,0.05);
            border-radius: 50%;
        }}

        .hero-box h1 {{
            color: #ffffff !important;
            margin: 0;
            font-size: 2.2rem;
            font-weight: 800;
            position: relative;
            z-index: 1;
            letter-spacing: -0.02em;
        }}

        .hero-box p {{
            color: rgba(255, 255, 255, 0.9) !important;
            margin: 0.6rem 0 0 0;
            font-size: 1.05rem;
            position: relative;
            z-index: 1;
            font-weight: 400;
        }}

        /* Card */
        .card {{
            background: {theme.card_bg};
            border: 1px solid {theme.border};
            border-radius: 14px;
            padding: 20px 24px;
            margin: 12px 0;
            box-shadow: 0 2px 8px {theme.shadow};
            transition: all 0.25s ease;
        }}

        .card:hover {{
            box-shadow: 0 8px 24px {theme.shadow};
            transform: translateY(-2px);
            border-color: {theme.primary}55;
        }}

        /* Intro box */
        .intro-box {{
            background: {theme.bg_secondary};
            border: 1px solid {theme.border};
            border-left: 5px solid {theme.info};
            border-radius: 12px;
            padding: 18px 22px;
            margin: 12px 0;
            color: {theme.text_primary};
        }}

        .intro-box strong {{
            color: {theme.primary};
            font-weight: 700;
        }}

        /* Insight box */
        .insight-box {{
            background: {theme.card_bg};
            border: 1px solid {theme.border};
            border-left: 4px solid {theme.primary};
            border-radius: 12px;
            padding: 18px 22px;
            margin: 12px 0;
            color: {theme.text_primary};
            transition: all 0.25s ease;
        }}

        .insight-box:hover {{
            box-shadow: 0 6px 18px {theme.shadow};
            transform: translateY(-1px);
        }}

        .insight-box strong {{
            color: {theme.primary};
            display: block;
            margin-bottom: 10px;
            font-size: 1.05rem;
        }}

        .insight-box span {{
            display: block;
            margin: 6px 0;
            line-height: 1.6;
            color: {theme.text_secondary};
        }}

        /* Metric card */
        .metric-card {{
            background: {theme.card_bg};
            border: 1px solid {theme.border};
            border-radius: 14px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 8px {theme.shadow};
            transition: all 0.25s ease;
            min-height: 130px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}

        .metric-card:hover {{
            box-shadow: 0 8px 24px {theme.shadow};
            transform: translateY(-4px);
            border-color: {theme.primary}55;
        }}

        .metric-value {{
            font-size: 2rem;
            font-weight: 800;
            color: {theme.primary};
            margin: 10px 0;
            line-height: 1.2;
        }}

        .metric-label {{
            color: {theme.text_secondary};
            font-size: 0.9rem;
            margin-top: 10px;
            font-weight: 500;
        }}

        .metric-subtitle {{
            color: {theme.text_muted};
            font-size: 0.8rem;
            margin-top: 6px;
        }}

        /* Badges */
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.82rem;
            font-weight: 600;
            margin-right: 6px;
            margin-bottom: 6px;
        }}

        .badge-primary {{
            background: {theme.primary}20;
            color: {theme.primary};
            border: 1px solid {theme.primary}40;
        }}

        .badge-success {{
            background: {theme.success}18;
            color: {theme.success};
            border: 1px solid {theme.success}40;
        }}

        .badge-warning {{
            background: {theme.warning}18;
            color: {theme.warning};
            border: 1px solid {theme.warning}40;
        }}

        .badge-danger {{
            background: {theme.danger}18;
            color: {theme.danger};
            border: 1px solid {theme.danger}40;
        }}

        .status-good {{
            background: {theme.success}15;
            color: {theme.success};
            padding: 4px 12px;
            border-radius: 8px;
            font-weight: 600;
            border: 1px solid {theme.success}30;
        }}

        .status-warning {{
            background: {theme.warning}15;
            color: {theme.warning};
            padding: 4px 12px;
            border-radius: 8px;
            font-weight: 600;
            border: 1px solid {theme.warning}30;
        }}

        .status-danger {{
            background: {theme.danger}15;
            color: {theme.danger};
            padding: 4px 12px;
            border-radius: 8px;
            font-weight: 600;
            border: 1px solid {theme.danger}30;
        }}

        /* Code */
        code {{
            background: {theme.bg_tertiary};
            color: {theme.accent_1};
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'JetBrains Mono', 'Courier New', monospace;
            font-size: 0.88em;
        }}

        /* Links */
        a {{
            color: {theme.primary};
            text-decoration: none;
            transition: color 0.2s ease;
        }}

        a:hover {{
            color: {theme.primary_light};
            text-decoration: underline;
        }}

        /* Chart container */
        .chart-container {{
            background: {theme.card_bg};
            border: 1px solid {theme.border};
            border-radius: 12px;
            padding: 16px;
            margin: 10px 0;
            box-shadow: 0 2px 8px {theme.shadow};
        }}

        /* Gradient text */
        .gradient-text {{
            background: linear-gradient(135deg, {theme.primary} 0%, {theme.accent_1} 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 800;
        }}

        /* Animations */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(8px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        @keyframes slideIn {{
            from {{ opacity: 0; transform: translateX(-16px); }}
            to {{ opacity: 1; transform: translateX(0); }}
        }}

        .fade-in {{
            animation: fadeIn 0.35s ease-out;
        }}

        .slide-in {{
            animation: slideIn 0.3s ease-out;
        }}

        /* Hover lift */
        .hover-lift {{
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: pointer;
        }}

        .hover-lift:hover {{
            transform: translateY(-6px);
            box-shadow: 0 10px 22px {theme.shadow};
        }}

        /* Section header accent */
        .section-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin: 2rem 0 1.25rem 0;
        }}

        .section-header::after {{
            content: '';
            flex: 1;
            height: 1px;
            background: linear-gradient(to right, {theme.border}, transparent);
        }}

        /* Stat pill */
        .stat-pill {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 14px;
            background: {theme.bg_secondary};
            border: 1px solid {theme.border};
            border-radius: 20px;
            font-size: 0.85rem;
            color: {theme.text_secondary};
            margin: 4px;
        }}

        /* Number input spinners */
        [data-testid="stNumberInput"] button {{
            background: {theme.st_widget_bg} !important;
            color: {theme.text_primary} !important;
            border-color: {theme.st_widget_border} !important;
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )


def render_theme_toggle() -> None:
    """Render theme toggle button in sidebar."""
    if "theme_mode" not in st.session_state:
        st.session_state.theme_mode = "light"

    is_dark = st.session_state.theme_mode == "dark"
    label = "☀️ Light mode" if is_dark else "🌙 Dark mode"

    st.sidebar.markdown("---")
    if st.sidebar.button(label, key="theme_toggle_btn", use_container_width=True):
        st.session_state.theme_mode = "dark" if not is_dark else "light"
        st.rerun()


def render_page_intro(problem: str, how_to_use: list[str]) -> None:
    st.markdown(
        f"""
        <div class="intro-box">
        <strong>What this solves:</strong> {problem}<br/>
        <strong>How to use:</strong><br/>
        1) {how_to_use[0]}<br/>
        2) {how_to_use[1]}<br/>
        3) {how_to_use[2]}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_glossary(items: dict[str, str]) -> None:
    with st.expander("Glossary"):
        for term, desc in items.items():
            st.markdown(f"- **{term}**: {desc}")


def render_data_freshness(updated_at: str, source_list: list[str], limitations: list[str]) -> None:
    st.caption(f"Last data update: {updated_at}")
    with st.expander("Sources and limitations"):
        st.markdown("**Data sources**")
        for src in source_list:
            st.markdown(f"- {src}")
        st.markdown("**Known limitations**")
        for item in limitations:
            st.markdown(f"- {item}")


def severity_bucket(value: float, low_threshold: float, high_threshold: float) -> str:
    if value < low_threshold:
        return "low"
    if value < high_threshold:
        return "medium"
    return "high"


def render_insight(title: str, finding: str, action: str, risk: str) -> None:
    color = RISK_COLORS.get(risk, "#1a6ef5")
    st.markdown(
        f"""
        <div class="insight-box" style="border-left: 4px solid {color};">
        <strong>{title}</strong>
        <span>💡 {finding}</span>
        <span>✅ {action}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(label: str, value: str | int, change: str = "", icon: str = "") -> None:
    """Render a styled metric card."""
    theme = get_theme(st.session_state.get("theme_mode", "light"))
    st.markdown(f"""
    <div class="metric-card">
        {f'<div style="font-size: 1.8rem; margin-bottom: 6px;">{icon}</div>' if icon else ''}
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
        {f'<div class="metric-subtitle">{change}</div>' if change else ''}
    </div>
    """, unsafe_allow_html=True)


def render_badge(text: str, badge_type: str = "primary") -> None:
    """Render a styled badge."""
    st.markdown(f'<span class="badge badge-{badge_type}">{text}</span>', unsafe_allow_html=True)


def sidebar_common_filters(districts: list[str], key_prefix: str = "global") -> tuple[list[str], tuple[float, float]]:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filters")
    default_selection = st.session_state.get(f"{key_prefix}_districts",
                                             st.session_state.get("selected_districts",
                                                                  sorted(districts)))
    if isinstance(default_selection, list):
        default_selection = [d for d in default_selection if d in districts]
    if not default_selection:
        default_selection = sorted(districts)

    selected = st.sidebar.multiselect(
        "Districts",
        options=sorted(districts),
        default=default_selection,
        key=f"{key_prefix}_districts",
    )
    risk_range = st.sidebar.slider(
        "Risk lens",
        min_value=0.0,
        max_value=1.0,
        value=(0.0, 1.0),
        step=0.05,
        key=f"{key_prefix}_risk",
    )
    st.session_state["selected_districts"] = selected
    return selected, risk_range


def render_feedback_widget(page_name: str) -> None:
    st.markdown("---")
    c1, c2 = st.columns([2, 3])
    with c1:
        useful = st.radio(
            f"Was this page useful? ({page_name})",
            options=["Yes", "Partly", "No"],
            horizontal=True,
            key=f"feedback_{page_name}",
        )
    with c2:
        st.write(f"Feedback captured: {useful}")
