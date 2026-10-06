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


import time


def get_splash_html() -> str:
    """Return the complete reference-matched splash screen HTML and CSS."""
    return f"""
    <div id="renexa-splash-screen" class="renexa-splash-overlay">
        <!-- Center Content: Logo, Brand, Tagline, Subtitle -->
        <div class="renexa-splash-center">
            <div class="renexa-splash-logo-wrap">
                <!-- Clean Modern Organic Eco Leaf Logo -->
                <svg class="renexa-splash-leaf-svg" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                        <linearGradient id="leafGrad" x1="15" y1="85" x2="85" y2="15" gradientUnits="userSpaceOnUse">
                            <stop offset="0%" stop-color="#76C936"/>
                            <stop offset="100%" stop-color="#9FEA45"/>
                        </linearGradient>
                        <linearGradient id="leafGradDark" x1="15" y1="85" x2="85" y2="15" gradientUnits="userSpaceOnUse">
                            <stop offset="0%" stop-color="#0A4235"/>
                            <stop offset="100%" stop-color="#185F32"/>
                        </linearGradient>
                    </defs>
                    <!-- Left Leaf Half -->
                    <path d="M50 12C50 12 18 32 18 62C18 78 32 88 50 88C50 88 50 12 50 12Z" fill="url(#leafGradDark)" opacity="0.9"/>
                    <!-- Right Leaf Half -->
                    <path d="M50 12C50 12 82 32 82 62C82 78 68 88 50 88C50 88 50 12 50 12Z" fill="url(#leafGrad)"/>
                    <!-- Central Stem and Vein Glow -->
                    <path d="M50 88V20" stroke="#011B18" stroke-width="3" stroke-linecap="round"/>
                    <path d="M50 42L66 32" stroke="#011B18" stroke-width="2.5" stroke-linecap="round"/>
                    <path d="M50 56L70 46" stroke="#011B18" stroke-width="2.5" stroke-linecap="round"/>
                    <path d="M50 70L65 62" stroke="#011B18" stroke-width="2.5" stroke-linecap="round"/>
                </svg>
            </div>
            <div class="renexa-splash-brand">ReNexa</div>
            <div class="renexa-splash-tagline">Give Waste Its Next Life.</div>
            <div class="renexa-splash-subtitle">
                <span>AI-Powered Waste Recovery</span>
                <span class="sub-break"> Intelligence.</span>
            </div>
        </div>

        <!-- Lower Section: Stylized Eco Landscape & Rolling Hills -->
        <div class="renexa-splash-landscape">
            <svg class="renexa-landscape-svg" viewBox="0 0 1200 320" preserveAspectRatio="none" fill="none" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <linearGradient id="hillGrad1" x1="600" y1="0" x2="600" y2="320" gradientUnits="userSpaceOnUse">
                        <stop offset="0%" stop-color="#07352A" stop-opacity="0.8"/>
                        <stop offset="100%" stop-color="#011B18"/>
                    </linearGradient>
                    <linearGradient id="hillGrad2" x1="600" y1="0" x2="600" y2="320" gradientUnits="userSpaceOnUse">
                        <stop offset="0%" stop-color="#0E483A"/>
                        <stop offset="100%" stop-color="#03211B"/>
                    </linearGradient>
                    <linearGradient id="hillGrad3" x1="600" y1="0" x2="600" y2="320" gradientUnits="userSpaceOnUse">
                        <stop offset="0%" stop-color="#185F32"/>
                        <stop offset="100%" stop-color="#062823"/>
                    </linearGradient>
                    <linearGradient id="foliageGrad" x1="0" y1="120" x2="180" y2="320" gradientUnits="userSpaceOnUse">
                        <stop offset="0%" stop-color="#9FEA45"/>
                        <stop offset="50%" stop-color="#76C936"/>
                        <stop offset="100%" stop-color="#0E483A"/>
                    </linearGradient>
                </defs>

                <!-- Layer 1: Distant Eco City / Building Silhouettes (Center-Right Background) -->
                <g fill="#06261F" opacity="0.65">
                    <rect x="740" y="110" width="28" height="90" rx="3"/>
                    <rect x="775" y="85" width="34" height="115" rx="4"/>
                    <polygon points="792,55 778,85 806,85"/>
                    <rect x="816" y="120" width="24" height="80" rx="3"/>
                    <rect x="846" y="98" width="30" height="102" rx="3"/>
                    <rect x="882" y="130" width="22" height="70" rx="2"/>
                    <rect x="910" y="115" width="28" height="85" rx="3"/>
                </g>

                <!-- Layer 2: Distant Layered Rolling Hills -->
                <path d="M0 160 Q 300 90, 620 140 T 1200 120 L 1200 320 L 0 320 Z" fill="url(#hillGrad1)"/>

                <!-- Layer 3: Middle Layer with Stylized Tree Crowns -->
                <g fill="#0C4436">
                    <circle cx="280" cy="155" r="26"/>
                    <circle cx="315" cy="148" r="32"/>
                    <circle cx="355" cy="158" r="24"/>
                    <circle cx="560" cy="165" r="28"/>
                    <circle cx="595" cy="155" r="34"/>
                    <circle cx="635" cy="168" r="22"/>
                    <circle cx="980" cy="160" r="30"/>
                    <circle cx="1020" cy="150" r="38"/>
                    <circle cx="1065" cy="164" r="26"/>
                </g>
                <path d="M0 190 Q 340 140, 720 185 T 1200 170 L 1200 320 L 0 320 Z" fill="url(#hillGrad2)"/>

                <!-- Layer 4: Foreground Rolling Contour -->
                <path d="M0 230 Q 400 180, 850 225 T 1200 210 L 1200 320 L 0 320 Z" fill="url(#hillGrad3)"/>

                <!-- Layer 5: Prominent Stylized Botanical Foliage / Large Leaf on Left -->
                <g>
                    <!-- Small Background Leaves -->
                    <path d="M80 320 C 60 250, 110 200, 160 180 C 150 230, 120 280, 110 320 Z" fill="#185F32" opacity="0.8"/>
                    <path d="M140 320 C 130 260, 180 220, 230 205 C 220 255, 190 295, 175 320 Z" fill="#2E7D32" opacity="0.7"/>

                    <!-- Main Large Hero Leaf Rising from Left -->
                    <path d="M0 320 C 0 220, 50 140, 125 110 C 135 170, 95 250, 45 320 Z" fill="url(#foliageGrad)"/>
                    <!-- Leaf Veins -->
                    <path d="M25 320 Q 70 210, 125 110" stroke="#07352A" stroke-width="3" stroke-linecap="round" fill="none"/>
                    <path d="M55 240 Q 85 220, 105 190" stroke="#07352A" stroke-width="2" stroke-linecap="round" fill="none"/>
                    <path d="M40 275 Q 70 260, 90 235" stroke="#07352A" stroke-width="2" stroke-linecap="round" fill="none"/>

                    <!-- Small Sprout/Grass Accents on Right -->
                    <path d="M1100 320 C 1105 270, 1125 240, 1150 220 C 1145 260, 1130 290, 1125 320 Z" fill="#76C936" opacity="0.9"/>
                    <path d="M1135 320 C 1145 280, 1170 255, 1195 245 C 1185 280, 1165 305, 1155 320 Z" fill="#9FEA45" opacity="0.85"/>
                </g>
            </svg>
        </div>
    </div>

    <style>
    /* Full-screen Dark Forest Viewport Overlay (Absolute Visual Priority) */
    .renexa-splash-overlay {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background-color: #011B18;
        z-index: 99999999;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        animation: splashViewportFade 2.50s cubic-bezier(0.4, 0, 0.2, 1) forwards;
        pointer-events: auto;
    }}

    /* Centered Branding Group */
    .renexa-splash-center {{
        position: relative;
        z-index: 10;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 0 24px;
        margin-top: -6vh; /* Center-balanced optical elevation above landscape */
        max-width: 680px;
    }}

    /* 1. Leaf Logo: Small at 0.00-0.35s, scales smoothly 0.35-1.10s */
    .renexa-splash-logo-wrap {{
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 14px;
        animation: splashLogoGrow 2.50s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }}
    .renexa-splash-leaf-svg {{
        width: 96px;
        height: 96px;
        filter: drop-shadow(0 4px 16px rgba(159, 234, 69, 0.25));
    }}

    /* 2. ReNexa Brand Title: Appears 0.75-1.25s */
    .renexa-splash-brand {{
        color: #F5FFF8;
        font-size: clamp(2.6rem, 7vw, 3.8rem);
        font-weight: 800;
        letter-spacing: -0.035em;
        line-height: 1.05;
        margin-bottom: 12px;
        text-shadow: 0 2px 12px rgba(0, 0, 0, 0.5);
        animation: splashBrandAppear 2.50s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }}

    /* 3. Tagline: Appears 1.00-1.40s */
    .renexa-splash-tagline {{
        color: #F5FFF8;
        font-size: clamp(1.15rem, 3.2vw, 1.45rem);
        font-weight: 600;
        letter-spacing: -0.01em;
        line-height: 1.3;
        margin-bottom: 10px;
        animation: splashTaglineAppear 2.50s ease-out forwards;
    }}

    /* 4. Subtitle: Appears 1.15-1.55s */
    .renexa-splash-subtitle {{
        color: #A9C3B8;
        font-size: clamp(0.92rem, 2.4vw, 1.12rem);
        font-weight: 400;
        letter-spacing: 0.01em;
        line-height: 1.45;
        animation: splashSubtitleAppear 2.50s ease-out forwards;
    }}
    .sub-break {{
        display: inline;
    }}

    /* Lower Section: Landscape Container: Rises 0.20-1.00s */
    .renexa-splash-landscape {{
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100vw;
        height: 32vh;
        min-height: 180px;
        max-height: 340px;
        z-index: 5;
        pointer-events: none;
        animation: splashLandscapeReveal 2.50s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }}
    .renexa-landscape-svg {{
        width: 100%;
        height: 100%;
        display: block;
    }}

    /* Keyframe Choreography (Exact Timeline over 2.50s) */

    /* Viewport: 100% visible 0.00s - 2.20s (88%), then smooth fade out 2.20s - 2.50s */
    @keyframes splashViewportFade {{
        0%   {{ opacity: 1; visibility: visible; }}
        88%  {{ opacity: 1; visibility: visible; }}
        100% {{ opacity: 0; visibility: hidden; pointer-events: none; }}
    }}

    /* 1. Logo: small at 0.00-0.35s (0-14%), scales 0.35-1.10s (14-44%), holds 1.10-2.50s */
    @keyframes splashLogoGrow {{
        0%   {{ transform: scale(0.25); opacity: 0.95; }}
        14%  {{ transform: scale(0.25); opacity: 1; }}
        44%  {{ transform: scale(1.0); opacity: 1; }}
        100% {{ transform: scale(1.0); opacity: 1; }}
    }}

    /* 2. Brand: reveals 0.75-1.25s (30-50%), holds 1.25-2.50s */
    @keyframes splashBrandAppear {{
        0%   {{ transform: scale(0.75) translateY(16px); opacity: 0; }}
        30%  {{ transform: scale(0.75) translateY(16px); opacity: 0; }}
        50%  {{ transform: scale(1.0) translateY(0); opacity: 1; }}
        100% {{ transform: scale(1.0) translateY(0); opacity: 1; }}
    }}

    /* 3. Tagline: reveals 1.00-1.40s (40-56%), holds 1.40-2.50s */
    @keyframes splashTaglineAppear {{
        0%   {{ transform: translateY(12px); opacity: 0; }}
        40%  {{ transform: translateY(12px); opacity: 0; }}
        56%  {{ transform: translateY(0); opacity: 1; }}
        100% {{ transform: translateY(0); opacity: 1; }}
    }}

    /* 4. Subtitle: reveals 1.15-1.55s (46-62%), holds 1.55-2.50s */
    @keyframes splashSubtitleAppear {{
        0%   {{ transform: translateY(10px); opacity: 0; }}
        46%  {{ transform: translateY(10px); opacity: 0; }}
        62%  {{ transform: translateY(0); opacity: 1; }}
        100% {{ transform: translateY(0); opacity: 1; }}
    }}

    /* 5. Landscape: reveals 0.20-1.00s (8-40%), holds 1.00-2.50s */
    @keyframes splashLandscapeReveal {{
        0%   {{ transform: translateY(28px); opacity: 0; }}
        8%   {{ transform: translateY(28px); opacity: 0; }}
        40%  {{ transform: translateY(0); opacity: 1; }}
        100% {{ transform: translateY(0); opacity: 1; }}
    }}

    /* Responsive Mobile Refinements */
    @media (max-width: 480px) {{
        .renexa-splash-leaf-svg {{
            width: 82px;
            height: 82px;
        }}
        .renexa-splash-center {{
            margin-top: -8vh;
            padding: 0 16px;
        }}
        .sub-break {{
            display: block;
        }}
        .renexa-splash-landscape {{
            height: 28vh;
        }}
    }}

    /* Accessibility / Reduced Motion Mode */
    @media (prefers-reduced-motion: reduce) {{
        .renexa-splash-overlay {{
            animation: splashReducedFade 0.3s ease-out forwards !important;
        }}
        .renexa-splash-logo-wrap,
        .renexa-splash-brand,
        .renexa-splash-tagline,
        .renexa-splash-subtitle,
        .renexa-splash-landscape {{
            animation: none !important;
            opacity: 1 !important;
            transform: none !important;
        }}
        @keyframes splashReducedFade {{
            0%   {{ opacity: 1; }}
            100% {{ opacity: 0; visibility: hidden; pointer-events: none; }}
        }}
    }}
    </style>
    """


def show_splash(force: bool = False):
    """
    Render reference-matched opening launch screen once per session.
    Guarantees full-screen display before the Home Dashboard renders.
    """
    if not force and st.session_state.get("renexa_splash_shown", False):
        return

    st.session_state["renexa_splash_shown"] = True

    splash_holder = st.empty()
    splash_holder.markdown(get_splash_html(), unsafe_allow_html=True)
    
    # Hold execution cleanly to allow the browser to complete the 2.50s choreography
    time.sleep(2.45)
    splash_holder.empty()



