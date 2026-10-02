"""
ReNexa — Results & Structured Waste Profile Page
=================================================
Displays structured recognition results, condition assessment,
and catalogued recovery pathways for the active waste item.
"""

import streamlit as st
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.ui import (
    configure_page,
    page_header,
    status_badge,
    render_sidebar,
    pill_badge,
    PRIMARY,
    SURFACE,
    BORDER,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from services.recovery_service import get_pathways_for_profile

# ── Page config ───────────────────────────────────────────────────────────
configure_page(title="Results — ReNexa", icon="📊")

# ── Sidebar ───────────────────────────────────────────────────────────────
render_sidebar("pages/2_Results.py")

# ── Header ────────────────────────────────────────────────────────────────
page_header("📊 Structured Waste Profile", "AI identification and physical condition assessment results.")

# ── Check for uploaded image ──────────────────────────────────────────────
if "uploaded_image" not in st.session_state:
    st.warning("⚠️ No waste image analyzed yet. Please scan an item first.")
    st.page_link("pages/1_Scan_Waste.py", label="📷  Go to Scan Waste")
    st.stop()

# ── Retrieve session data ─────────────────────────────────────────────────
profile = st.session_state.get("waste_profile")
detection = st.session_state.get("detection_result")
has_profile = profile is not None and profile.get("user_confirmed", False)

# ── Image + Profile Card ──────────────────────────────────────────────────
col_img, col_info = st.columns([1, 1.4])

with col_img:
    with st.container(border=True):
        st.image(
            st.session_state["uploaded_image"],
            caption=st.session_state.get("uploaded_filename", "Analyzed waste image"),
            use_container_width=True,
        )

with col_info:
    if has_profile:
        with st.container(border=True):
            st.markdown(f"### ♻️ Verified Waste Profile {pill_badge('Active', 'primary')}", unsafe_allow_html=True)
            st.markdown(f"**Material:** `{profile.get('material', 'Unknown').capitalize()}`")
            st.markdown(f"**Item Assessment:** `{profile.get('item', 'Unknown')}`")
            st.markdown(f"**Quantity:** `{profile.get('confirmed_quantity', 1)}` object(s)")
            st.markdown(f"**Condition:** `{profile.get('condition', 'Unknown')}`")
            st.markdown(f"**Contamination:** `{profile.get('contamination', 'Unknown')}`")
            st.markdown(f"**AI Confidence:** `{(profile.get('confidence') or 0.0) * 100:.1f}%`")

            mat_counts = profile.get("material_counts", {})
            if mat_counts and len(mat_counts) > 1:
                st.caption("Detailed breakdown:")
                for m, c in mat_counts.items():
                    st.markdown(f"- `{m.capitalize()}`: {c}")

    elif detection and detection.get("detected"):
        with st.container(border=True):
            st.markdown(f"### Recognition Status {pill_badge('Pending Confirmation', 'warning')}", unsafe_allow_html=True)
            st.markdown(f"**Detected Material:** `{detection['label'].capitalize()}`")
            st.markdown(f"**Confidence:** `{detection['confidence'] * 100:.1f}%`")
            st.warning("⚠️ Return to Scan page to confirm physical condition.")
            st.page_link("pages/1_Scan_Waste.py", label="📷  Back to Scan")
    else:
        st.warning("🔍 No waste detected. Please scan another image.")
        st.page_link("pages/1_Scan_Waste.py", label="📷  Back to Scan")

st.divider()

# ── Matched Recovery Possibilities ────────────────────────────────────────
if has_profile:
    st.markdown("### 🔄 Recovery Possibilities for this Material")
    st.caption("Standard catalog pathways matching this material category.")

    matched_pathways = get_pathways_for_profile(profile)
    if matched_pathways:
        p_cols = st.columns(min(3, len(matched_pathways)))
        for idx, p in enumerate(matched_pathways[:6]):
            col = p_cols[idx % len(p_cols)]
            with col:
                with st.container(border=True):
                    ptype = str(p.get("pathway_type", "reuse")).upper()
                    st.markdown(f"**{p.get('title')}**")
                    st.markdown(f"{pill_badge(ptype, 'primary')} &nbsp; ⏱️ `{p.get('time_required')}`", unsafe_allow_html=True)
                    st.caption(f"Estimated Cost: ₹{p.get('budget', '0')} | Skill: {p.get('skill_level', 'Beginner')}")
    else:
        st.info("No specific catalog pathways found for this material.")

st.divider()

# ── Navigation Actions ────────────────────────────────────────────────────
n_col1, n_col2 = st.columns(2)
with n_col1:
    st.page_link("pages/4_Constraints.py", label="⚙️  Set Recovery Constraints & Tools →", use_container_width=True)
with n_col2:
    st.page_link("pages/5_Recommendations.py", label="🎯  View Feasible Recommendations →", use_container_width=True)
