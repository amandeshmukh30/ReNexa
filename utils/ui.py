"""
ReNexa — Master UI Design System & Component Library
=====================================================
Centralized dark eco-tech styling, responsive layouts, modern mobile/desktop
navigation, pill badges, interactive cards, and theme tokens.

Visual Identity:
- Background:        #011B18 (Deep Forest Void)
- Surface:           #062823 (Dark Pine Surface)
- Surface Light:     #0A342D (Elevated Surface)
- Surface Hover:     #0F4036 (Interactive Hover)
- Primary Accent:    #9FEA45 (Electric Eco Lime)
- Primary Hover:     #84D637 (Vibrant Green)
- Primary Dark:      #75C92F (Deep Lime)
- Text Primary:      #F5FFF8 (Crisp Mint White)
- Text Secondary:    #A9C3B8 (Muted Mint Gray)
- Border:            #1B4A40 (Subtle Pine Border)
- Success:           #9FEA45
- Warning:           #F2C94C
- Error:             #E97878
"""

import streamlit as st

# ── Color & Theme Tokens ───────────────────────────────────────────────────
BACKGROUND = "#011B18"
SURFACE = "#062823"
SURFACE_LIGHT = "#0A342D"
SURFACE_HOVER = "#0F4036"
PRIMARY = "#9FEA45"
PRIMARY_HOVER = "#84D637"
PRIMARY_DARK = "#75C92F"
TEXT_PRIMARY = "#F5FFF8"
TEXT_SECONDARY = "#A9C3B8"
BORDER = "#1B4A40"
SUCCESS = "#9FEA45"
WARNING = "#F2C94C"
ERROR = "#E97878"

# ── Navigation Manifest ────────────────────────────────────────────────────
NAV_ITEMS = [
    ("main.py", "🏠", "Home"),
    ("pages/1_Scan_Waste.py", "📷", "Scan"),
    ("pages/2_Results.py", "📊", "Results"),
    ("pages/3_Recovery.py", "🔄", "Pathways"),
    ("pages/4_Constraints.py", "⚙️", "Constraints"),
    ("pages/5_Recommendations.py", "🎯", "Recommendations"),
    ("pages/6_Execution.py", "📖", "Execution"),
    ("pages/6_Tutorials.py", "📚", "Tutorials"),
    ("pages/7_History.py", "📜", "History"),
    ("pages/7_Outcome.py", "📈", "Outcome"),
    ("pages/8_Impact.py", "🌍", "Impact"),
    ("pages/9_Research_Benchmark.py", "🔬", "Benchmark"),
]

MOBILE_NAV_ITEMS = [
    ("main.py", "🏠", "Home"),
    ("pages/1_Scan_Waste.py", "📷", "Scan"),
    ("pages/3_Recovery.py", "🔄", "Pathways"),
    ("pages/6_Tutorials.py", "📚", "Tutorials"),
    ("pages/7_History.py", "📜", "History"),
]


# ── Master CSS Theme Injection ─────────────────────────────────────────────
def apply_renexa_theme():
    """Inject centralized dark eco-tech stylesheet and responsive rules."""
    css = f"""
    <style>
    /* ── 1. Hide default Streamlit chrome ──────────────────────────────── */
    #MainMenu, header, footer, [data-testid="stSidebarNav"] {{
        display: none !important;
    }}

    /* ── 2. Global Typography & Canvas ────────────────────────────────── */
    html, body, [class*="css"], [data-testid="stAppViewContainer"] {{
        background-color: {BACKGROUND} !important;
        color: {TEXT_PRIMARY} !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
        letter-spacing: -0.01em;
    }}

    /* Container constraints */
    .block-container {{
        max-width: 1280px !important;
        padding-top: 1.5rem !important;
        padding-bottom: 5.5rem !important; /* Space for mobile nav */
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
    }}

    /* ── 3. Sidebar Custom Dark Eco Styling ───────────────────────────── */
    [data-testid="stSidebar"] {{
        background-color: {SURFACE} !important;
        border-right: 1px solid {BORDER} !important;
    }}

    [data-testid="stSidebar"] .block-container {{
        padding-top: 1.5rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }}

    .renexa-sidebar-brand {{
        padding: 0.5rem;
        margin-bottom: 0.5rem;
    }}
    .renexa-sidebar-logo {{
        display: flex;
        align-items: center;
        gap: 0.6rem;
        font-size: 1.6rem;
        font-weight: 800;
        color: {PRIMARY};
        letter-spacing: -0.02em;
    }}
    .renexa-sidebar-tagline {{
        font-size: 0.85rem;
        font-weight: 500;
        color: {TEXT_SECONDARY};
        margin-top: 0.15rem;
    }}

    /* Sidebar Page Link Overrides */
    [data-testid="stSidebar"] .stPageLink a {{
        border-radius: 12px !important;
        padding: 0.6rem 0.85rem !important;
        margin-bottom: 0.3rem !important;
        font-size: 0.92rem !important;
        font-weight: 600 !important;
        color: {TEXT_SECONDARY} !important;
        background-color: transparent !important;
        border: 1px solid transparent !important;
        transition: all 0.2s ease !important;
        text-decoration: none !important;
    }}

    [data-testid="stSidebar"] .stPageLink a:hover {{
        background-color: {SURFACE_HOVER} !important;
        color: {PRIMARY} !important;
        border-color: {BORDER} !important;
        transform: translateX(3px);
    }}

    [data-testid="stSidebar"] .stPageLink a[aria-current="page"],
    [data-testid="stSidebar"] .stPageLink.active a {{
        background-color: {SURFACE_LIGHT} !important;
        color: {PRIMARY} !important;
        font-weight: 700 !important;
        border-left: 3px solid {PRIMARY} !important;
        border-color: {BORDER} !important;
    }}

    /* ── 4. Card Containers & Surfaces ────────────────────────────────── */
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: {SURFACE} !important;
        border: 1px solid {BORDER} !important;
        border-radius: 18px !important;
        padding: 0.5rem !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25) !important;
        transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease !important;
    }}

    [data-testid="stVerticalBlockBorderWrapper"]:hover {{
        border-color: rgba(159, 234, 69, 0.4) !important;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4) !important;
    }}

    .renexa-card {{
        background-color: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 18px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    }}

    /* ── 5. Buttons & CTAs ────────────────────────────────────────────── */
    .stButton > button, div.stButton > button:first-child {{
        background: {PRIMARY} !important;
        color: {BACKGROUND} !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        border-radius: 14px !important;
        border: none !important;
        padding: 0.65rem 1.4rem !important;
        min-height: 44px !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 2px 10px rgba(159, 234, 69, 0.25) !important;
        cursor: pointer !important;
    }}

    .stButton > button:hover {{
        background: {PRIMARY_HOVER} !important;
        color: {BACKGROUND} !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 18px rgba(159, 234, 69, 0.4) !important;
    }}

    /* Secondary / Form Submit buttons */
    .stFormSubmitButton > button {{
        background: {PRIMARY} !important;
        color: {BACKGROUND} !important;
        font-weight: 700 !important;
        border-radius: 14px !important;
        min-height: 44px !important;
    }}

    /* ── 6. Form Controls & Inputs ────────────────────────────────────── */
    .stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox [data-baseweb="select"] {{
        background-color: {SURFACE_LIGHT} !important;
        color: {TEXT_PRIMARY} !important;
        border: 1px solid {BORDER} !important;
        border-radius: 12px !important;
        font-size: 0.95rem !important;
    }}

    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {{
        border-color: {PRIMARY} !important;
        box-shadow: 0 0 0 1px {PRIMARY} !important;
    }}

    /* Radio, Checkbox, Multiselect Tags */
    [data-baseweb="tag"] {{
        background-color: {SURFACE_LIGHT} !important;
        border: 1px solid {BORDER} !important;
        border-radius: 8px !important;
        color: {PRIMARY} !important;
    }}

    /* File uploader */
    [data-testid="stFileUploader"] {{
        background-color: {SURFACE} !important;
        border: 1.5px dashed {BORDER} !important;
        border-radius: 18px !important;
        padding: 1.5rem !important;
    }}

    /* ── 7. Metrics & Badges ──────────────────────────────────────────── */
    [data-testid="stMetricValue"] {{
        color: {PRIMARY} !important;
        font-size: 1.9rem !important;
        font-weight: 800 !important;
    }}
    [data-testid="stMetricLabel"] {{
        color: {TEXT_SECONDARY} !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }}

    /* Pill Badges */
    .renexa-badge {{
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.3rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.02em;
    }}
    .renexa-badge-primary {{
        background-color: rgba(159, 234, 69, 0.15);
        color: {PRIMARY};
        border: 1px solid rgba(159, 234, 69, 0.4);
    }}
    .renexa-badge-warning {{
        background-color: rgba(242, 201, 76, 0.15);
        color: {WARNING};
        border: 1px solid rgba(242, 201, 76, 0.4);
    }}
    .renexa-badge-error {{
        background-color: rgba(233, 120, 120, 0.15);
        color: {ERROR};
        border: 1px solid rgba(233, 120, 120, 0.4);
    }}

    /* Progress bar */
    .stProgress > div > div > div > div {{
        background-color: {PRIMARY} !important;
        border-radius: 9999px !important;
    }}

    /* Dividers */
    hr {{
        border-color: {BORDER} !important;
        opacity: 0.7 !important;
        margin: 1.25rem 0 !important;
    }}

    /* ── 8. Mobile Bottom Navigation (<= 768px) ───────────────────────── */
    .renexa-mobile-bottom-nav {{
        display: none;
    }}

    @media (max-width: 768px) {{
        .block-container {{
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-bottom: 6rem !important;
        }}

        .renexa-mobile-bottom-nav {{
            display: flex;
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            height: 64px;
            background-color: rgba(6, 40, 35, 0.95);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-top: 1px solid {BORDER};
            z-index: 99999;
            justify-content: space-around;
            align-items: center;
            padding: 0 0.5rem;
        }}

        .renexa-mob-item {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-decoration: none;
            color: {TEXT_SECONDARY};
            font-size: 0.75rem;
            font-weight: 600;
            padding: 0.3rem 0.6rem;
            border-radius: 12px;
            transition: all 0.2s ease;
        }}

        .renexa-mob-item.active {{
            color: {PRIMARY};
            background-color: {SURFACE_LIGHT};
        }}

        .renexa-mob-icon {{
            font-size: 1.25rem;
            line-height: 1;
            margin-bottom: 0.15rem;
        }}
    }}

    @media (max-width: 480px) {{
        .renexa-card {{
            padding: 1rem;
            border-radius: 14px;
        }}
        [data-testid="stMetricValue"] {{
            font-size: 1.6rem !important;
        }}
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


# ── Page Initialization ────────────────────────────────────────────────────
def configure_page(title="ReNexa — Give Waste Its Next Life", icon="♻️", layout="wide"):
    """Set page config and apply central master theme."""
    st.set_page_config(page_title=title, page_icon=icon, layout=layout)
    apply_renexa_theme()


# ── Sidebar Navigation ─────────────────────────────────────────────────────
def render_sidebar(current_page="main.py"):
    """Render the master brand sidebar with structured navigation and version info."""
    st.sidebar.markdown(
        """
        <div class="renexa-sidebar-brand">
            <div class="renexa-sidebar-logo"><span>♻️</span> ReNexa</div>
            <div class="renexa-sidebar-tagline">Give Waste Its Next Life.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.divider()

    # Dynamic nav links
    for path, icon, label in NAV_ITEMS:
        display_label = f"{icon}  {label}"
        st.sidebar.page_link(
            path,
            label=display_label,
            use_container_width=True,
        )

    st.sidebar.divider()
    st.sidebar.markdown(
        """
        <div style="padding: 0.5rem; font-size: 0.8rem; color: #A9C3B8;">
            <div style="font-weight: 700; color: #9FEA45;">♻️ ReNexa v1.0 Production</div>
            <div>AI Recovery Intelligence</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Page Headers & Hero Blocks ─────────────────────────────────────────────
def render_renexa_header():
    """Render the official master Hero banner on the home dashboard."""
    st.markdown(
        f"""
        <div style="text-align: center; padding: 2rem 1rem 1rem 1rem;">
            <div style="display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.35rem 1rem; background: rgba(159, 234, 69, 0.12); border: 1px solid rgba(159, 234, 69, 0.3); border-radius: 9999px; color: {PRIMARY}; font-size: 0.85rem; font-weight: 700; margin-bottom: 1rem;">
                <span>♻️</span> AI-Powered Waste Recovery Intelligence
            </div>
            <h1 style="font-size: clamp(2.2rem, 5vw, 3.4rem); font-weight: 900; color: {TEXT_PRIMARY}; line-height: 1.15; margin: 0 auto 0.8rem auto; max-width: 900px; letter-spacing: -0.03em;">
                Give Waste Its <span style="color: {PRIMARY};">Next Life.</span>
            </h1>
            <p style="font-size: clamp(1rem, 2vw, 1.2rem); color: {TEXT_SECONDARY}; max-width: 720px; margin: 0 auto 1.5rem auto; line-height: 1.6;">
                Identify household waste, assess its physical condition, check what tools you have at home, and discover recovery pathways that are <strong>genuinely feasible</strong> for you.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_header(title, subtitle=None):
    """Render standard subpage title and descriptive subtitle."""
    st.markdown(
        f"""
        <div style="margin-bottom: 0.5rem;">
            <h2 style="font-size: 1.85rem; font-weight: 800; color: {TEXT_PRIMARY}; margin: 0; letter-spacing: -0.02em;">{title}</h2>
            {f'<p style="color: {TEXT_SECONDARY}; font-size: 0.95rem; margin: 0.25rem 0 0 0;">{subtitle}</p>' if subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()


# ── Badges & Cards ─────────────────────────────────────────────────────────
def pill_badge(text, variant="primary"):
    """Return HTML string for modern pill badge."""
    v_class = f"renexa-badge-{variant}"
    return f'<span class="renexa-badge {v_class}">{text}</span>'


def status_badge(label, state="pending"):
    """Render consistent status indicator."""
    icons = {
        "done": ("✅", "primary"),
        "pending": ("⏳", "warning"),
        "blocked": ("🚫", "error"),
        "warn": ("⚠️", "warning"),
        "not_connected": ("🔌", "warning"),
    }
    icon, var = icons.get(state, ("⏳", "warning"))
    st.markdown(f"{icon} **{label}**")


def metric_card(label, value, icon="📊"):
    """Render dark metric card."""
    with st.container(border=True):
        st.markdown(
            f"""
            <div style="text-align: center; padding: 0.5rem;">
                <div style="font-size: 1.4rem; margin-bottom: 0.25rem;">{icon}</div>
                <div style="font-size: 1.85rem; font-weight: 800; color: {PRIMARY};">{value}</div>
                <div style="font-size: 0.8rem; font-weight: 700; color: {TEXT_SECONDARY}; text-transform: uppercase; letter-spacing: 0.05em;">{label}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_dashboard_card(title, description, icon, target_page):
    """Render interactive card for dashboard grid."""
    with st.container(border=True):
        st.markdown(
            f"""
            <div style="min-height: 90px; padding: 0.2rem 0;">
                <div style="font-size: 1.75rem; margin-bottom: 0.35rem;">{icon}</div>
                <div style="font-size: 1.15rem; font-weight: 800; color: {TEXT_PRIMARY}; margin-bottom: 0.2rem;">{title}</div>
                <div style="font-size: 0.85rem; color: {TEXT_SECONDARY}; line-height: 1.4;">{description}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.page_link(target_page, label=f"Open {title} →", use_container_width=True)


def empty_state(message, icon="📭", cta_text=None, cta_page=None):
    """Render empty-state placeholder."""
    st.markdown(
        f"""
        <div style="text-align: center; padding: 2.5rem 1rem; background: {SURFACE}; border: 1px dashed {BORDER}; border-radius: 18px; margin: 1rem 0;">
            <div style="font-size: 2.2rem; margin-bottom: 0.5rem;">{icon}</div>
            <p style="color: {TEXT_SECONDARY}; font-size: 0.95rem; margin: 0 auto; max-width: 480px;">{message}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if cta_text and cta_page:
        st.page_link(cta_page, label=cta_text, use_container_width=False)
