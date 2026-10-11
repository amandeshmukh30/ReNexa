
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from app.ui import login_gate, render_shell, render_footer
from app.ui.components import section, metric, card


st.set_page_config(
    page_title="ReNexa | Waste Recovery Intelligence",
    page_icon="♻",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Authentication and page layout
login_gate()
render_shell("Home")


# Hero section
st.markdown(
    """
    <div class="rx-hero">
        <div class="rx-eyebrow">WELCOME TO RENEXA</div>
        <h1>Turn Waste into<br>Opportunity</h1>
        <p>
            Scan, discover, and give your waste a second life with
            AI-assisted insights, safer recovery options, and practical
            step-by-step guidance.
        </p>
        <div style="color:var(--rx-primary);font-weight:750">
            Start with a waste scan →
        </div>
        <div class="rx-art">♻</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# System overview
section(
    "System Overview",
    "A snapshot of your recovery workspace",
    "▥",
)

cols = st.columns(4, gap="medium")

try:
    from services.recovery_service import load_recovery_pathways, get_tutorials
    from services.outcome_service import load_outcome_feedback

    pathways_total = len(load_recovery_pathways())
    tutorials_total = len(get_tutorials(verified_only=True))
    feedback_records = load_outcome_feedback()
    confirmed_recoveries = sum(
        1 for x in feedback_records if str(x.get("attempt_status", "")).lower() == "successful"
    )
except Exception:
    pathways_total = "55"
    tutorials_total = "—"
    confirmed_recoveries = 0

stats = [
    (
        "Scans Processed",
        st.session_state.get("scan_count", len(st.session_state.get("scan_history", []))),
        "Current session count",
        "⌗",
    ),
    (
        "Pathways Available",
        pathways_total,
        "Recovery knowledge catalog",
        "▤",
    ),
    (
        "Tutorials Linked",
        tutorials_total,
        "Verified video references",
        "▷",
    ),
    (
        "Successful Recoveries",
        st.session_state.get("successful_recoveries", confirmed_recoveries),
        "User-confirmed outcomes",
        "✓",
    ),
]

for col, args in zip(cols, stats):
    with col:
        metric(*args)


# Quick access
section(
    "Quick Access",
    "Open a ReNexa feature",
    "↗",
)

quick = [
    (
        "Scan Waste",
        "Upload a photo or use the camera to inspect a waste item.",
        "▣",
        "pages/1_Scan_Waste.py",
    ),
    (
        "Recovery Options",
        "Explore reuse, repair, upcycling and recycling pathways.",
        "⌘",
        "pages/3_Recovery.py",
    ),
    (
        "Safety Guidelines",
        "Review precautions and constraint checks before action.",
        "◇",
        "pages/4_Constraints.py",
    ),
    (
        "Tutorials",
        "Browse step-by-step guidance and linked videos.",
        "▷",
        "pages/6_Tutorials.py",
    ),
    (
        "Personal History",
        "Review past scans and saved recommendations.",
        "◷",
        "pages/7_History.py",
    ),
    (
        "Impact Analysis",
        "Track confirmed recovery outcomes and estimates.",
        "▥",
        "pages/8_Impact.py",
    ),
]

for start in (0, 3):
    cols = st.columns(3, gap="medium")

    for col, item in zip(cols, quick[start:start + 3]):
        title, description, icon, target = item

        with col:
            card(
                title,
                description,
                icon,
                target=target,
            )


# Workflow overview
section(
    "How ReNexa Works",
    "A constraint-aware path from identification to recovery.",
    "↗",
)

steps = [
    ("Identify", "Upload or capture a waste item."),
    ("Classify", "Detect its material category."),
    (
        "Check Constraints",
        "Consider condition, safety and feasibility.",
    ),
    ("Rank Options", "Compare eligible recovery pathways."),
    ("Get Guidance", "Review tools, steps and precautions."),
    ("Measure Impact", "Record outcomes when confirmed."),
]

cols = st.columns(6, gap="small")

for i, (title, description) in enumerate(steps):
    with cols[i]:
        st.markdown(
            f"""
            <div class="rx-step">
                <div class="rx-num">{i + 1}</div>
                <div><b>{title}</b></div>
                <div class="rx-copy">{description}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# Footer
render_footer()
