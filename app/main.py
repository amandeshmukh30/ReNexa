"""
ReNexa — Main Dashboard
========================
Entry point for the Streamlit multi-page app.
ReNexa: Give Waste Its Next Life.
AI-Powered Waste Recovery Intelligence.
"""

import warnings
import logging

warnings.filterwarnings("ignore")
logging.disable(logging.WARNING)

import streamlit as st
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from utils.ui import (
    configure_page,
    render_sidebar,
    render_renexa_header,
    render_dashboard_card,
    metric_card,
    show_splash,
    PRIMARY,
    SURFACE,
    BORDER,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from database.auth import AUTH_USER_KEY, AUTH_TOKEN_KEY
from database.database import get_user_dashboard_metrics, get_all_feedback, get_user_scans
from services.recovery_service import load_recovery_pathways

# ── Page config ────────────────────────────────────────────────────────────
configure_page(title="ReNexa — Give Waste Its Next Life", icon="♻️", layout="wide")

# ── Opening Splash Screen Animation (Once per session) ────────────────────
show_splash()

# ── Sidebar navigation ───────────────────────────────────────────────────
render_sidebar(current_page="main.py")

# ── Hero Header ───────────────────────────────────────────────────────────
render_renexa_header()


# ── Primary CTAs ──────────────────────────────────────────────────────────
cta_col1, cta_col2 = st.columns(2)
with cta_col1:
    st.page_link("pages/1_Scan_Waste.py", label="📷  Scan Household Waste Item", use_container_width=True)
with cta_col2:
    st.page_link("pages/3_Recovery.py", label="🔄  Explore Recovery Pathways", use_container_width=True)

st.divider()

# ── Authentic Overview Stats ──────────────────────────────────────────────
current_user = st.session_state.get(AUTH_USER_KEY)
token = st.session_state.get(AUTH_TOKEN_KEY)
user_id = current_user.get("id") if current_user else None

pathways_catalog = load_recovery_pathways()
catalog_count = len(pathways_catalog)

if current_user:
    metrics = get_user_dashboard_metrics(user_id=user_id, token=token)
    st.markdown(f"### 👋 Personal Recovery Dashboard — **{current_user.get('display_name', 'Eco User')}**")
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        metric_card("My Scans", metrics["total_scans"], icon="📷")
    with s2:
        metric_card("Pathways Catalog", catalog_count, icon="🔄")
    with s3:
        metric_card("DIY Attempts", metrics["total_attempts"], icon="🛠️")
    with s4:
        metric_card("Success Rate", f"{metrics['resr']}%", icon="🏆")
else:
    # Guest / neutral overview with authentic system figures
    guest_scans = len(get_user_scans(limit=100))
    guest_fb = get_all_feedback()
    guest_attempts = len([f for f in guest_fb if str(f.get("attempt_status", "")).lower() in ("successful", "partial", "failed")])
    guest_success = len([f for f in guest_fb if str(f.get("attempt_status", "")).lower() == "successful"])

    st.markdown("### 📊 System Overview")
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        metric_card("Scans Recorded", guest_scans, icon="📷")
    with s2:
        metric_card("Pathways Catalog", catalog_count, icon="🔄")
    with s3:
        metric_card("Executions Logged", guest_attempts, icon="🛠️")
    with s4:
        metric_card("Successful Recoveries", guest_success, icon="✅")

st.divider()

# ── Quick Access Grid ─────────────────────────────────────────────────────
st.markdown("### 🧭 Quick Access")

row1 = st.columns(3)
with row1[0]:
    render_dashboard_card(
        title="Scan Waste",
        description="Upload or take a photo to detect material and assess physical condition.",
        icon="📷",
        target_page="pages/1_Scan_Waste.py",
    )
with row1[1]:
    render_dashboard_card(
        title="Recovery Options",
        description="Browse repair, reuse, upcycle, recycle, and disposal pathways.",
        icon="🔄",
        target_page="pages/3_Recovery.py",
    )
with row1[2]:
    render_dashboard_card(
        title="My Constraints",
        description="Set your household budget, tools, skill, time, and workspace.",
        icon="⚙️",
        target_page="pages/4_Constraints.py",
    )

row2 = st.columns(3)
with row2[0]:
    render_dashboard_card(
        title="Tutorial Guides",
        description="Step-by-step execution procedures and safety guidance.",
        icon="📚",
        target_page="pages/6_Tutorials.py",
    )
with row2[1]:
    render_dashboard_card(
        title="Personal History",
        description="View your past scans, recommendations, and execution feedback.",
        icon="📜",
        target_page="pages/7_History.py",
    )
with row2[2]:
    render_dashboard_card(
        title="Outcome Analytics",
        description="Real-world recipe reliability (OVRR) and execution metrics.",
        icon="📈",
        target_page="pages/7_Outcome.py",
    )

st.divider()

# ── How ReNexa Works ──────────────────────────────────────────────────────
st.markdown("### 🔬 How ReNexa Works")
st.caption("Constraint-aware intelligent recovery workflow.")

steps = [
    ("1️⃣", "Identify", "Detect waste material category via trained computer vision."),
    ("2️⃣", "Profile", "Assess condition, contamination, and item quantity."),
    ("3️⃣", "Check Constraints", "Filter by user budget, available tools, time, and skill."),
    ("4️⃣", "Validate Safety", "Enforce safety rules and block hazardous operations."),
    ("5️⃣", "Rank Options", "Score feasible pathways via transparent MCDA multi-criteria analysis."),
    ("6️⃣", "Execute", "Provide clear, safe, step-by-step DIY instructions."),
    ("7️⃣", "Validate Outcome", "Record real-world execution success to validate recipe feasibility."),
]

cols = st.columns(len(steps))
for col, (num, title, desc) in zip(cols, steps):
    with col:
        with st.container(border=True):
            st.markdown(
                f"""
                <div style="text-align: center; padding: 0.3rem 0; min-height: 140px;">
                    <div style="font-size: 1.4rem; margin-bottom: 0.3rem;">{num}</div>
                    <div style="font-weight: 800; color: {PRIMARY}; font-size: 0.95rem; margin-bottom: 0.25rem;">{title}</div>
                    <div style="font-size: 0.78rem; color: {TEXT_SECONDARY}; line-height: 1.35;">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

st.divider()

# ── Research Focus ────────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown("### 💡 Why ReNexa?")
    st.markdown(
        "Traditional waste applications focus on classification and generic disposal advice. "
        "**ReNexa** is built from the ground up for **Constraint-Aware Household Waste Recovery**, "
        "verifying whether recommendations are safe and physically executable in real-world households."
    )

# ── Terminal Output: Sklearn Benchmark Accuracy & Classification Report ─────
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from services.benchmark_evaluation import evaluate_benchmarks


def print_benchmark_metrics_to_terminal():
    """Evaluate benchmark scenarios using scikit-learn and print results to terminal."""
    try:
        metrics = evaluate_benchmarks()
        print("\n" + "=" * 70)
        print(" [RESEARCH BENCHMARK] Evaluation Results (scikit-learn)")
        print("=" * 70)
        print(f" Overall Accuracy: {metrics['overall_accuracy']:.4f} ({metrics['overall_accuracy']*100:.2f}%)")
        print("-" * 70)
        print(" Classification Report (by Pathway ID):")
        print(metrics["classification_report_str"])
        print(" Performance by Material:")
        for mat, info in metrics["by_category"].items():
            print(f"   * {mat.capitalize():<12}: Samples={info['samples']:<2} | Accuracy={info['accuracy']*100:.1f}%")
        print("=" * 70 + "\n")
    except Exception as e:
        print(f"[!] Error computing benchmark metrics: {e}")


# Print to terminal once per session
try:
    if "benchmark_metrics_printed" not in st.session_state:
        print_benchmark_metrics_to_terminal()
        st.session_state["benchmark_metrics_printed"] = True
except Exception:
    print_benchmark_metrics_to_terminal()


