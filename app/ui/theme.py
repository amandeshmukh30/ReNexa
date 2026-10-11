import streamlit as st


# --------------------------------------------------
# RENEXA THEME COLORS
# --------------------------------------------------

PALETTES = {
    "Light": {
        "bg": "#F5F8F6",
        "surface": "#FFFFFF",
        "surface2": "#EEF7F1",
        "text": "#10352D",
        "muted": "#607A72",
        "border": "#DCEAE3",
        "primary": "#087F50",
        "sidebar": "#063B30",
        "hero_end": "#DDF3D9",
        "btn_bg": "#087F50",
        "btn_text": "#FFFFFF",
        "btn_hover_bg": "#066841",
        "btn_hover_text": "#FFFFFF",
        "btn_disabled_bg": "#E2ECE6",
        "btn_disabled_text": "#7A9B90",
        "btn_disabled_border": "#CAD9D1",
        "pagelink_bg": "#087F50",
        "pagelink_text": "#FFFFFF",
        "pagelink_hover_bg": "#066841",
        "pagelink_hover_text": "#FFFFFF",
    },
    "Dark": {
        "bg": "#071B17",
        "surface": "#0D2922",
        "surface2": "#12372D",
        "text": "#EAF5EF",
        "muted": "#A1BEB1",
        "border": "#234A3E",
        "primary": "#4DD68B",
        "sidebar": "#041E19",
        "hero_end": "#12372D",
        "btn_bg": "#062823",
        "btn_text": "#EAF5EF",
        "btn_hover_bg": "#0D3830",
        "btn_hover_text": "#4DD68B",
        "btn_disabled_bg": "#0A1F1B",
        "btn_disabled_text": "#4E7368",
        "btn_disabled_border": "#1A3D33",
        "pagelink_bg": "#062823",
        "pagelink_text": "#EAF5EF",
        "pagelink_hover_bg": "#0D3830",
        "pagelink_hover_text": "#4DD68B",
    },
    "System": {
        "bg": "#F5F8F6",
        "surface": "#FFFFFF",
        "surface2": "#EEF7F1",
        "text": "#10352D",
        "muted": "#607A72",
        "border": "#DCEAE3",
        "primary": "#087F50",
        "sidebar": "#063B30",
        "hero_end": "#DDF3D9",
        "btn_bg": "#087F50",
        "btn_text": "#FFFFFF",
        "btn_hover_bg": "#066841",
        "btn_hover_text": "#FFFFFF",
        "btn_disabled_bg": "#E2ECE6",
        "btn_disabled_text": "#7A9B90",
        "btn_disabled_border": "#CAD9D1",
        "pagelink_bg": "#087F50",
        "pagelink_text": "#FFFFFF",
        "pagelink_hover_bg": "#066841",
        "pagelink_hover_text": "#FFFFFF",
    },
}


# --------------------------------------------------
# INITIALIZE THEME
# --------------------------------------------------

def init_theme():
    """Set the default ReNexa appearance."""

    if "renexa_theme" not in st.session_state:
        st.session_state["renexa_theme"] = "Light"


def get_theme():
    """Return the currently selected theme."""

    init_theme()
    return st.session_state["renexa_theme"]


# --------------------------------------------------
# APPLY GLOBAL CSS
# --------------------------------------------------

def apply_theme():
    """Apply ReNexa styling to the current Streamlit page."""

    init_theme()

    theme_name = get_theme()
    colors = PALETTES.get(theme_name, PALETTES["Light"])

    css = """
    <style>

    /* =========================================
       GLOBAL COLORS
    ========================================= */

    :root {
        --rx-bg: %(bg)s;
        --rx-surface: %(surface)s;
        --rx-surface2: %(surface2)s;
        --rx-text: %(text)s;
        --rx-muted: %(muted)s;
        --rx-border: %(border)s;
        --rx-primary: %(primary)s;
        --rx-sidebar: %(sidebar)s;
        --rx-hero-end: %(hero_end)s;
        --rx-btn-bg: %(btn_bg)s;
        --rx-btn-text: %(btn_text)s;
        --rx-btn-hover-bg: %(btn_hover_bg)s;
        --rx-btn-hover-text: %(btn_hover_text)s;
        --rx-btn-disabled-bg: %(btn_disabled_bg)s;
        --rx-btn-disabled-text: %(btn_disabled_text)s;
        --rx-btn-disabled-border: %(btn_disabled_border)s;
        --rx-pagelink-bg: %(pagelink_bg)s;
        --rx-pagelink-text: %(pagelink_text)s;
        --rx-pagelink-hover-bg: %(pagelink_hover_bg)s;
        --rx-pagelink-hover-text: %(pagelink_hover_text)s;
    }

    html,
    body,
    [data-testid="stAppViewContainer"] {
        background: var(--rx-bg);
        color: var(--rx-text);
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stToolbar"] {
        right: 1rem;
    }

    .block-container {
        max-width: 1500px;
        padding-top: 1.2rem;
        padding-bottom: 2.2rem;
    }

    h1,
    h2,
    h3,
    h4,
    h5,
    p,
    label,
    [data-testid="stMarkdownContainer"] {
        color: var(--rx-text);
    }

    [data-testid="stCaptionContainer"],
    .rx-muted,
    .rx-copy {
        color: var(--rx-muted) !important;
    }

    a {
        color: var(--rx-primary);
    }


    /* =========================================
       SIDEBAR
    ========================================= */

    [data-testid="stSidebar"] {
        background: var(--rx-sidebar);
        border-right: 1px solid var(--rx-border);
    }

    [data-testid="stSidebar"] * {
        color: #E7F4ED;
    }

    [data-testid="stSidebar"] hr {
        border-color: #2B5B4B;
    }


    /* =========================================
       BUTTONS AND INTERACTIVE CONTROLS
    ========================================= */

    /* Standard and Action Buttons */
    .stButton > button,
    .stDownloadButton > button,
    [data-testid="stFormSubmitButton"] > button,
    [data-testid="stBaseButton-secondary"],
    [data-testid="stBaseButton-primary"],
    [data-testid="stFileUploader"] button,
    [data-testid="stCameraInput"] button {
        border-radius: 10px;
        font-weight: 650;
        border: 1px solid var(--rx-primary);
        background-color: var(--rx-btn-bg) !important;
        color: var(--rx-btn-text) !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
        transition: all 0.18s ease;
    }

    /* Force all text/elements inside buttons to contrast properly */
    .stButton > button *,
    .stDownloadButton > button *,
    [data-testid="stFormSubmitButton"] > button *,
    [data-testid="stBaseButton-secondary"] *,
    [data-testid="stBaseButton-primary"] *,
    [data-testid="stFileUploader"] button *,
    [data-testid="stCameraInput"] button * {
        color: var(--rx-btn-text) !important;
    }

    /* Hover State */
    .stButton > button:hover,
    .stDownloadButton > button:hover,
    [data-testid="stFormSubmitButton"] > button:hover,
    [data-testid="stBaseButton-secondary"]:hover,
    [data-testid="stBaseButton-primary"]:hover,
    [data-testid="stFileUploader"] button:hover,
    [data-testid="stCameraInput"] button:hover {
        transform: translateY(-1px);
        background-color: var(--rx-btn-hover-bg) !important;
        border-color: var(--rx-primary) !important;
        color: var(--rx-btn-hover-text) !important;
        box-shadow: 0 4px 12px rgba(8, 127, 80, 0.25);
    }

    .stButton > button:hover *,
    .stDownloadButton > button:hover *,
    [data-testid="stFormSubmitButton"] > button:hover *,
    [data-testid="stBaseButton-secondary"]:hover *,
    [data-testid="stBaseButton-primary"]:hover *,
    [data-testid="stFileUploader"] button:hover *,
    [data-testid="stCameraInput"] button:hover * {
        color: var(--rx-btn-hover-text) !important;
    }

    /* Active / Focus State */
    .stButton > button:active,
    .stDownloadButton > button:active,
    [data-testid="stFormSubmitButton"] > button:active,
    .stButton > button:focus-visible,
    [data-testid="stFormSubmitButton"] > button:focus-visible {
        transform: translateY(0);
        outline: 2px solid var(--rx-primary) !important;
        outline-offset: 1px;
    }

    /* Disabled Button State */
    .stButton > button:disabled,
    .stButton > button[disabled],
    .stDownloadButton > button:disabled,
    .stDownloadButton > button[disabled],
    [data-testid="stFormSubmitButton"] > button:disabled,
    [data-testid="stFormSubmitButton"] > button[disabled] {
        background-color: var(--rx-btn-disabled-bg) !important;
        border-color: var(--rx-btn-disabled-border) !important;
        color: var(--rx-btn-disabled-text) !important;
        box-shadow: none !important;
        transform: none !important;
        cursor: not-allowed !important;
        opacity: 0.9 !important;
    }

    .stButton > button:disabled *,
    .stButton > button[disabled] *,
    .stDownloadButton > button:disabled *,
    .stDownloadButton > button[disabled] *,
    [data-testid="stFormSubmitButton"] > button:disabled *,
    [data-testid="stFormSubmitButton"] > button[disabled] * {
        color: var(--rx-btn-disabled-text) !important;
    }

    /* Sidebar Sign Out button */
    [data-testid="stSidebar"] .stButton > button {
        background-color: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] .stButton > button * {
        color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: rgba(255, 255, 255, 0.16) !important;
        border-color: #9BE36B !important;
        color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] .stButton > button:hover * {
        color: #FFFFFF !important;
    }

    /* Main Page Action Links styled as buttons (st.page_link in main area) */
    [data-testid="stMain"] [data-testid="stPageLink-NavLink"],
    .main .block-container [data-testid="stPageLink-NavLink"] {
        border-radius: 10px;
        border: 1px solid var(--rx-primary);
        background-color: var(--rx-pagelink-bg) !important;
        transition: all 0.18s ease;
        padding: 0.35rem 0.8rem;
    }

    [data-testid="stMain"] [data-testid="stPageLink-NavLink"] *,
    .main .block-container [data-testid="stPageLink-NavLink"] * {
        color: var(--rx-pagelink-text) !important;
        font-weight: 650;
    }

    [data-testid="stMain"] [data-testid="stPageLink-NavLink"]:hover,
    .main .block-container [data-testid="stPageLink-NavLink"]:hover {
        transform: translateY(-1px);
        background-color: var(--rx-pagelink-hover-bg) !important;
        border-color: var(--rx-primary) !important;
        box-shadow: 0 4px 12px rgba(8, 127, 80, 0.25);
    }

    [data-testid="stMain"] [data-testid="stPageLink-NavLink"]:hover *,
    .main .block-container [data-testid="stPageLink-NavLink"]:hover * {
        color: var(--rx-pagelink-hover-text) !important;
    }

    /* Tabs styling */
    [data-testid="stTabs"] [data-baseweb="tab"] {
        color: var(--rx-muted);
        font-weight: 600;
    }

    [data-testid="stTabs"] [aria-selected="true"] {
        color: var(--rx-primary) !important;
        border-bottom-color: var(--rx-primary) !important;
        font-weight: 750;
    }


    /* =========================================
       INPUTS AND FORMS
    ========================================= */

    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stNumberInput"] input {
        border-radius: 10px;
        background: var(--rx-surface) !important;
        color: var(--rx-text) !important;
        border: 1px solid var(--rx-border) !important;
    }

    [data-testid="stTextInput"] input:focus,
    [data-testid="stTextArea"] textarea:focus,
    [data-testid="stNumberInput"] input:focus {
        border-color: var(--rx-primary) !important;
        box-shadow: 0 0 0 1px var(--rx-primary) !important;
    }

    /* Selectbox & Multiselect */
    div[data-baseweb="select"] {
        border-radius: 10px !important;
        background-color: var(--rx-surface) !important;
        border: 1px solid var(--rx-border) !important;
    }

    div[data-baseweb="select"] * {
        color: var(--rx-text) !important;
    }

    /* Multiselect Selected Tags */
    [data-baseweb="tag"] {
        background-color: var(--rx-surface2) !important;
        border: 1px solid var(--rx-border) !important;
        border-radius: 8px !important;
    }

    [data-baseweb="tag"] * {
        color: var(--rx-primary) !important;
        font-weight: 650;
    }

    /* Radio Buttons & Checkboxes */
    [data-testid="stRadio"] label,
    [data-testid="stCheckbox"] label {
        color: var(--rx-text) !important;
        font-weight: 550;
    }

    [data-testid="stForm"],
    [data-testid="stFileUploader"] {
        border-radius: 16px;
        background: var(--rx-surface);
        border: 1px solid var(--rx-border);
    }


    /* =========================================
       METRIC COMPONENTS
    ========================================= */

    [data-testid="stMetric"] {
        background: var(--rx-surface);
        border: 1px solid var(--rx-border);
        padding: 1rem;
        border-radius: 16px;
        box-shadow: 0 7px 22px rgba(10, 54, 40, 0.045);
    }

    [data-testid="stMetricLabel"] {
        color: var(--rx-muted);
    }

    [data-testid="stMetricValue"] {
        color: var(--rx-primary);
    }

    /* Image display and aspect ratio consistency */
    [data-testid="stImage"] {
        display: flex;
        justify-content: center;
        align-items: center;
    }

    [data-testid="stImage"] img {
        border-radius: 12px;
        object-fit: contain;
        max-height: 440px;
        width: auto !important;
        max-width: 100% !important;
        border: 1px solid var(--rx-border);
    }


    /* =========================================
       BRANDING
    ========================================= */

    .rx-brand {
        display: flex;
        gap: 11px;
        align-items: center;
        padding: 8px 0 18px;
    }

    .rx-leaf {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 43px;
        height: 43px;
        border-radius: 14px;
        background: linear-gradient(
            145deg,
            #9BE36B,
            #24A86A
        );
        color: #063B30 !important;
        font-size: 25px;
        font-weight: 800;
    }

    .rx-brand-title {
        font-size: 24px;
        font-weight: 800;
        color: #F5FFF9 !important;
        line-height: 1.1;
    }

    .rx-brand-sub {
        font-size: 11px;
        margin-top: 4px;
        color: #B9D9C9 !important;
    }


    /* =========================================
       TOP NAVIGATION BAR
    ========================================= */

    .rx-topbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
        padding: 0.75rem 1rem;
        margin-bottom: 1rem;
        background: var(--rx-surface);
        border: 1px solid var(--rx-border);
        border-radius: 14px;
        color: var(--rx-muted);
    }


    /* =========================================
       PAGE HEADINGS
    ========================================= */

    .rx-eyebrow {
        color: var(--rx-primary) !important;
        font-size: 0.76rem;
        font-weight: 800;
        letter-spacing: 0.09em;
        text-transform: uppercase;
    }

    .rx-section {
        display: flex;
        gap: 0.6rem;
        align-items: center;
        margin: 1.45rem 0 0.8rem;
    }

    .rx-section h2 {
        font-size: 1.23rem;
        margin: 0;
        letter-spacing: -0.02em;
    }


    /* =========================================
       HERO SECTION
    ========================================= */

    .rx-hero {
        position: relative;
        overflow: hidden;
        padding: 2rem 2.2rem;
        border-radius: 22px;
        border: 1px solid var(--rx-border);
        background: linear-gradient(
            110deg,
            var(--rx-surface2),
            var(--rx-surface) 58%,
            var(--rx-hero-end)
        );
        margin-bottom: 1.2rem;
        animation: rxFade 0.55s ease both;
    }

    .rx-hero h1 {
        font-size: clamp(2rem, 3vw, 3.2rem);
        line-height: 1.04;
        margin: 0.5rem 0 0.8rem;
        letter-spacing: -0.04em;
    }

    .rx-hero p {
        max-width: 610px;
        color: var(--rx-muted);
        line-height: 1.65;
    }

    .rx-art {
        position: absolute;
        right: 5%;
        top: 8%;
        font-size: 7rem;
        opacity: 0.17;
        pointer-events: none;
    }


    /* =========================================
       CARDS
    ========================================= */

    .rx-card {
        background: var(--rx-surface);
        border: 1px solid var(--rx-border);
        border-radius: 16px;
        padding: 1.05rem;
        min-height: 125px;
        box-shadow: 0 7px 22px rgba(10, 54, 40, 0.045);
        transition: transform 0.18s ease,
                    border-color 0.18s ease;
    }

    .rx-card:hover {
        transform: translateY(-2px);
        border-color: var(--rx-primary);
    }

    .rx-card-title {
        font-size: 1rem;
        font-weight: 750;
        margin-bottom: 0.35rem;
    }

    .rx-copy {
        font-size: 0.86rem;
        line-height: 1.5;
        color: var(--rx-muted);
    }

    .rx-icon {
        width: 42px;
        height: 42px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 13px;
        background: var(--rx-surface2);
        color: var(--rx-primary);
        font-size: 1.25rem;
        margin-bottom: 0.7rem;
    }


    /* =========================================
       PROCESS STEPS
    ========================================= */

    .rx-step {
        background: var(--rx-surface);
        border: 1px solid var(--rx-border);
        border-radius: 14px;
        padding: 1rem 0.6rem;
        text-align: center;
        height: 100%;
    }

    .rx-num {
        display: inline-flex;
        width: 27px;
        height: 27px;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        background: var(--rx-primary);
        color: white;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }


    /* =========================================
       LOGIN PAGE
    ========================================= */

    .rx-login-art {
        min-height: 410px;
        border-radius: 20px;
        padding: 2rem;
        background: linear-gradient(
            145deg,
            #063B30,
            #087F50 70%,
            #7BCB65
        );
        color: white;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .rx-login-art h1,
    .rx-login-art p {
        color: white !important;
    }

    .rx-login-art h1 {
        font-size: 2.4rem;
        letter-spacing: -0.04em;
    }

    .rx-login-panel {
        background: var(--rx-surface);
        border: 1px solid var(--rx-border);
        border-radius: 20px;
        padding: 1.5rem;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.06);
    }


    /* =========================================
       FOOTER
    ========================================= */

    .rx-footer {
        border-top: 1px solid var(--rx-border);
        margin-top: 2rem;
        padding-top: 1rem;
        text-align: center;
        color: var(--rx-muted);
        font-size: 0.82rem;
    }


    /* =========================================
       OPENING / PAGE ANIMATION
    ========================================= */

    @keyframes rxFade {
        from {
            opacity: 0;
            transform: translateY(12px);
        }

        to {
            opacity: 1;
            transform: translateY(0);
        }
    }


    /* =========================================
       RESPONSIVE LAYOUT
    ========================================= */

    @media (max-width: 800px) {
        .rx-art {
            display: none;
        }

        .rx-hero {
            padding: 1.3rem;
        }

        .rx-login-art {
            min-height: 220px;
            margin-bottom: 1rem;
        }
    }

    </style>
    """

    # Replace color variables only.
    # CSS percentages (100%, 3vw, 5%, etc.) remain unchanged.
    for key, value in colors.items():
        css = css.replace(f"%({key})s", value)

    st.markdown(css, unsafe_allow_html=True)


# --------------------------------------------------
# LIGHT / DARK / SYSTEM THEME SELECTOR
# --------------------------------------------------

def theme_control():
    init_theme()

    st.selectbox(
        "Appearance",
        options=["Light", "Dark", "System"],
        key="renexa_theme",
        help="Choose the ReNexa interface appearance.",
    )

    apply_theme()