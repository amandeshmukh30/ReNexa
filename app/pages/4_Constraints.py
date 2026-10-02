"""
ReNexa — Constraints & Feasibility Evaluation Page
===================================================
Capture household-specific constraints and evaluate recovery pathway eligibility.
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
    metric_card,
    PRIMARY,
    SURFACE,
    BORDER,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from utils.validation import get_default_constraints
from services.eligibility_service import get_eligible_pathways_for_profile

# ── Page config ───────────────────────────────────────────────────────────
configure_page(title="Constraints — ReNexa", icon="⚙️")

# ── Sidebar ───────────────────────────────────────────────────────────────
render_sidebar("pages/4_Constraints.py")

defaults = get_default_constraints()

# ── Header ────────────────────────────────────────────────────────────────
page_header(
    "⚙️ Household Recovery Constraints",
    "Tell ReNexa what budget, tools, time, and workspace you have at home to filter feasible pathways.",
)

# ── Constraint Input Form ─────────────────────────────────────────────────
with st.form("constraints_form"):
    st.markdown("### 🛠️ Household Resources & Preferences")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 💰 Maximum Budget")
        budget = st.select_slider(
            "Maximum out-of-pocket cost willing to spend:",
            options=["₹0", "₹50", "₹100", "₹250", "₹500+"],
            value=st.session_state.get("budget", defaults["budget"]),
        )
    with c2:
        st.markdown("#### ⏱️ Available Time")
        time_available = st.select_slider(
            "Dedicated time for recovery procedure:",
            options=["5 minutes", "15 minutes", "30 minutes", "1 hour", "2+ hours"],
            value=st.session_state.get("time", defaults["time"]),
        )

    st.divider()

    st.markdown("#### 🔧 Available Tools on Hand")
    st.caption("Select all tools currently available in your home:")

    tool_options = [
        "Scissors", "Utility knife", "Glue", "Tape", "Screwdriver",
        "Hammer", "Needle", "Drill", "Trowel", "Measuring tape", "Binder clip", "None",
    ]
    saved_tools = st.session_state.get("tools", defaults["tools"])

    tools = []
    tool_cols = st.columns(4)
    for i, tool in enumerate(tool_options):
        with tool_cols[i % 4]:
            checked = st.checkbox(tool, value=(tool in saved_tools), key=f"tool_{tool}")
            if checked and tool != "None":
                tools.append(tool)

    st.divider()

    c3, c4 = st.columns(2)
    with c3:
        st.markdown("#### 🎓 Skill Level")
        skill = st.radio(
            "DIY & craft experience level:",
            options=["Beginner", "Intermediate", "Advanced"],
            index=["Beginner", "Intermediate", "Advanced"].index(
                st.session_state.get("skill", defaults["skill"])
            ),
            horizontal=True,
        )
    with c4:
        st.markdown("#### 🏠 Workspace")
        workspace = st.radio(
            "Available working area:",
            options=["Indoor", "Outdoor", "Any"],
            index=["Indoor", "Outdoor", "Any"].index(
                st.session_state.get("workspace", "Any" if defaults["workspace"] not in ["Indoor", "Outdoor", "Any"] else defaults["workspace"])
            ),
            horizontal=True,
        )

    st.divider()

    st.markdown("#### 📦 Extra Materials Available")
    extra_mat_text = st.text_input(
        "List extra supplies at home (comma-separated):",
        value=st.session_state.get("extra_materials_text", "Tape, thread, twine, potting soil"),
    )

    st.markdown("#### 🛡️ Safety Preference")
    safety_preference = st.radio(
        "Safety tolerance:",
        options=["Only low-risk options", "Allow medium-risk options with warning"],
        index=0 if st.session_state.get(
            "safety_preference", defaults["safety_preference"]
        ) == "Only low-risk options" else 1,
        horizontal=True,
    )

    st.divider()
    submitted = st.form_submit_button("💾 Save Constraints & Check Feasibility", use_container_width=True)

    if submitted:
        st.session_state["budget"] = budget
        st.session_state["tools"] = tools
        st.session_state["skill"] = skill
        st.session_state["time"] = time_available
        st.session_state["workspace"] = workspace
        st.session_state["extra_materials_text"] = extra_mat_text
        st.session_state["extra_materials"] = [m.strip() for m in extra_mat_text.split(",") if m.strip()]
        st.session_state["safety_preference"] = safety_preference
        st.success("✅ Constraints saved! Evaluating feasibility below.")

# ── Evaluate Eligibility if Profile Exists ──────────────────────────────────
current_constraints = {
    "budget": st.session_state.get("budget", defaults["budget"]),
    "tools": st.session_state.get("tools", defaults["tools"]),
    "skill": st.session_state.get("skill", defaults["skill"]),
    "time": st.session_state.get("time", defaults["time"]),
    "workspace": st.session_state.get("workspace", "Any"),
    "extra_materials": st.session_state.get("extra_materials", [m.strip() for m in st.session_state.get("extra_materials_text", "").split(",") if m.strip()]),
    "safety_preference": st.session_state.get("safety_preference", defaults["safety_preference"]),
}

profile = st.session_state.get("waste_profile")

if profile and profile.get("material") and profile.get("material") != "Unknown":
    st.divider()
    st.markdown(f"### 🔬 Feasibility Evaluation for `{profile['material'].capitalize()}`")
    st.caption(
        f"Waste Context: Condition = **{profile.get('condition', 'Unknown')}** | "
        f"Contamination = **{profile.get('contamination', 'Unknown')}** | "
        f"Quantity = **{profile.get('confirmed_quantity', 1)}**"
    )

    evaluations = get_eligible_pathways_for_profile(profile, current_constraints)

    if evaluations:
        n_total = len(evaluations)
        n_eligible = sum(1 for e in evaluations if e["eligible"])
        n_infeasible = sum(1 for e in evaluations if not e["eligible"] and e["safety_status"] != "BLOCK")
        n_blocked = sum(1 for e in evaluations if e["safety_status"] == "BLOCK")

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            metric_card("Total Pathways", n_total, icon="📋")
        with col_m2:
            metric_card("Eligible", n_eligible, icon="✅")
        with col_m3:
            metric_card("Infeasible", n_infeasible, icon="⚠️")
        with col_m4:
            metric_card("Blocked (Safety)", n_blocked, icon="🚫")

        st.divider()
        st.markdown("#### 📋 Pathway-by-Pathway Feasibility Details")

        for ev in evaluations:
            p = ev["pathway"]
            is_elig = ev["eligible"]
            safety_stat = ev["safety_status"]
            const_stat = ev["constraint_status"]

            with st.container(border=True):
                col_h1, col_h2 = st.columns([3, 1])
                with col_h1:
                    st.markdown(f"##### {p.get('title', 'Pathway')}")
                    st.caption(f"Type: `{p.get('pathway_type', '').upper()}` | ID: `{p.get('pathway_id')}`")
                with col_h2:
                    if is_elig:
                        st.markdown(pill_badge("ELIGIBLE", "primary"), unsafe_allow_html=True)
                    elif safety_stat == "BLOCK":
                        st.markdown(pill_badge("BLOCKED", "error"), unsafe_allow_html=True)
                    else:
                        st.markdown(pill_badge("INFEASIBLE", "warning"), unsafe_allow_html=True)

                b1, b2, b3 = st.columns(3)
                with b1:
                    st.markdown(f"**Safety:** `{safety_stat}`")
                with b2:
                    st.markdown(f"**Constraints:** `{const_stat}`")
                with b3:
                    st.markdown(f"**Cost:** ₹{p.get('budget', '0')} | **Time:** {p.get('time_required')}")

                if ev.get("warnings"):
                    for w in ev["warnings"]:
                        st.warning(f"⚠️ {w}")

                if not is_elig and ev.get("reasons"):
                    st.error("❌ **Infeasibility Reasons:**\n" + "\n".join(f"- {r}" for r in ev["reasons"]))

                if ev.get("missing_tools"):
                    st.info(f"🔧 **Missing Tools:** {', '.join(ev['missing_tools'])}")
                if ev.get("missing_materials"):
                    st.info(f"📦 **Missing Materials:** {', '.join(ev['missing_materials'])}")

    else:
        st.info("No recovery pathways found for this material.")

else:
    st.divider()
    st.info("ℹ️ **Tip:** Scan a waste item to see live feasibility evaluation against your saved constraints.")
    st.page_link("pages/1_Scan_Waste.py", label="📷  Scan Waste Item")

st.divider()
st.page_link("pages/5_Recommendations.py", label="🎯  View Top Ranked Recommendations →", use_container_width=True)
