"""
ReNexa — Recovery Pathways Page
================================
Displays candidate recovery pathways from the Recovery Knowledge Base.
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
    render_sidebar,
    pill_badge,
    empty_state,
    PRIMARY,
    SURFACE,
    BORDER,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from services.recovery_service import (
    get_recovery_pathways,
    get_available_materials,
)

# ── Page config ───────────────────────────────────────────────────────────
configure_page(title="Recovery Pathways — ReNexa", icon="🔄")

# ── Sidebar ───────────────────────────────────────────────────────────────
render_sidebar("pages/3_Recovery.py")

# ── Header ────────────────────────────────────────────────────────────────
page_header(
    "🔄 Recovery Knowledge Base",
    "Candidate recovery options mapped across Repair, Reuse, Upcycle, Recycle, and Safe Disposal.",
)

# ── Retrieve active profile ───────────────────────────────────────────────
profile = st.session_state.get("waste_profile")

TYPE_ICONS = {
    "repair": "🔧",
    "reuse": "🔄",
    "upcycle": "✨",
    "recycle": "♻️",
    "dispose": "🗑️",
}

if profile and profile.get("material") and profile.get("material") != "Unknown":
    with st.container(border=True):
        st.markdown(f"### 📋 Active Profile: **{profile.get('material', '').capitalize()}** {pill_badge('Context Active', 'primary')}", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"**Item:** `{profile.get('item', 'Unknown')}`")
        with c2:
            st.markdown(f"**Condition:** `{profile.get('condition', 'Unknown')}`")
        with c3:
            st.markdown(f"**Contamination:** `{profile.get('contamination', 'Unknown')}`")
        with c4:
            st.markdown(f"**Quantity:** `{profile.get('confirmed_quantity', 1)}`")

    st.divider()

    active_material = profile.get("material")
    pathways = get_recovery_pathways(material=active_material)

    st.markdown(f"### 📚 Pathways for `{active_material.capitalize()}` ({len(pathways)} catalogued)")

    if pathways:
        for p in pathways:
            ptype = p.get("pathway_type", "reuse").lower()
            icon = TYPE_ICONS.get(ptype, "📋")
            with st.container(border=True):
                col_t, col_b = st.columns([3, 1])
                with col_t:
                    st.markdown(f"#### {icon} {p.get('title')}")
                with col_b:
                    st.markdown(pill_badge(ptype.upper(), "primary"), unsafe_allow_html=True)

                st.write(p.get("description", ""))

                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.markdown(f"**Tools:** {p.get('tools')}")
                    st.markdown(f"**Condition:** {p.get('condition_requirement')}")
                with m2:
                    st.markdown(f"**Materials:** {p.get('extra_materials')}")
                    st.markdown(f"**Skill:** {p.get('skill_level')}")
                with m3:
                    st.markdown(f"**Cost:** ₹{p.get('budget', '0')}")
                    st.markdown(f"**Workspace:** {p.get('workspace')}")
                with m4:
                    st.markdown(f"**Duration:** {p.get('time_required')}")
                    st.markdown(f"**Safety:** {p.get('safety_level')}")

                with st.expander("📖 Step-by-Step Procedure & Output"):
                    st.markdown(f"**Expected Output:** {p.get('expected_output')}")
                    st.markdown(f"**Execution Steps:**  \n{p.get('steps')}")
                    st.markdown(f"**Fallback:** {p.get('fallback')}")
    else:
        empty_state(f"No catalog pathways found for material '{active_material}'.", icon="🔄")

else:
    st.info("ℹ️ **Browse Mode:** Select any material category below to explore recovery options.")

    available_mats = get_available_materials()
    if available_mats:
        selected_mat = st.selectbox("Select Material to Explore:", options=available_mats, index=0)
        browse_pathways = get_recovery_pathways(material=selected_mat)

        st.markdown(f"### 📚 Available Pathways for `{selected_mat.capitalize()}` ({len(browse_pathways)})")
        for p in browse_pathways:
            ptype = p.get("pathway_type", "reuse").lower()
            icon = TYPE_ICONS.get(ptype, "📋")
            with st.container(border=True):
                c_title, c_badge = st.columns([3, 1])
                with c_title:
                    st.markdown(f"#### {icon} {p.get('title')}")
                with c_badge:
                    st.markdown(pill_badge(ptype.upper(), "primary"), unsafe_allow_html=True)

                st.write(p.get("description", ""))
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.caption(f"**Tools:** {p.get('tools')}")
                with c2:
                    st.caption(f"**Materials:** {p.get('extra_materials')}")
                with c3:
                    st.caption(f"**Cost:** ₹{p.get('budget')} | **Time:** {p.get('time_required')}")
                with c4:
                    st.caption(f"**Skill:** {p.get('skill_level')} | **Safety:** {p.get('safety_level')}")

st.divider()
st.caption("📌 **Next Steps:** Proceed to Constraints to input what tools and budget you have at home.")
