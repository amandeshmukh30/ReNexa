"""
ReNexa — Recommendations Page
==============================
Displays feasible recovery recommendations (Top-K) and multi-criteria trade-off comparison.
Phase 6: Deterministic Multi-Criteria Decision Analysis (MCDA) Ranking.
"""

import streamlit as st
import sys
import os
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.ui import (
    configure_page,
    page_header,
    render_sidebar,
    pill_badge,
    PRIMARY,
    SURFACE,
    BORDER,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from utils.validation import get_default_constraints
from services.ranking_service import (
    get_ranked_recommendations_for_profile,
    get_ranked_pathways,
)
from services.eligibility_service import get_eligible_pathways_for_profile

# ── Page config ───────────────────────────────────────────────────────────
configure_page(title="Recommendations — ReNexa", icon="🎯")

# ── Sidebar ───────────────────────────────────────────────────────────────
render_sidebar("pages/5_Recommendations.py")

# ── Header ────────────────────────────────────────────────────────────────
page_header(
    "🎯 Feasible Recovery Recommendations",
    "Top-K recovery options ranked by transparent Multi-Criteria Decision Analysis (MCDA).",
)

# ── Retrieve active profile and constraints ───────────────────────────────
profile = st.session_state.get("waste_profile")
defaults = get_default_constraints()

current_constraints = {
    "budget": st.session_state.get("budget", defaults["budget"]),
    "tools": st.session_state.get("tools", defaults["tools"]),
    "skill": st.session_state.get("skill", defaults["skill"]),
    "time": st.session_state.get("time", defaults["time"]),
    "workspace": st.session_state.get("workspace", defaults["workspace"]),
    "extra_materials": st.session_state.get(
        "extra_materials",
        [m.strip() for m in st.session_state.get("extra_materials_text", "").split(",") if m.strip()]
        if st.session_state.get("extra_materials_text")
        else ["Tape", "Thread", "Twine", "Potting soil"],
    ),
    "safety_preference": st.session_state.get("safety_preference", defaults["safety_preference"]),
}

TYPE_ICONS = {
    "repair": "🔧",
    "reuse": "🔄",
    "upcycle": "✨",
    "recycle": "♻️",
    "dispose": "🗑️",
}

RANK_MEDALS = {1: "🥇 TOP 1", 2: "🥈 TOP 2", 3: "🥉 TOP 3"}

if profile and profile.get("material") and profile.get("material") != "Unknown":
    with st.container(border=True):
        st.markdown(f"### 📋 Active Evaluation Context {pill_badge(profile['material'].capitalize(), 'primary')}", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"**Item:** `{profile.get('item', 'Unknown')}`")
            st.caption(f"Count: {profile.get('confirmed_quantity', 1)}")
        with c2:
            st.markdown(f"**Condition:** `{profile.get('condition', 'Unknown')}`")
            st.caption(f"Contamination: {profile.get('contamination', 'Unknown')}")
        with c3:
            st.markdown(f"**Budget:** `{current_constraints['budget']}`")
            st.caption(f"Time: {current_constraints['time']}")
        with c4:
            st.markdown(f"**Skill:** `{current_constraints['skill']}`")
            st.caption(f"Workspace: {current_constraints['workspace']}")

    st.divider()

    # ── Run Phase 5 Eligibility & Phase 6 Ranking ─────────────────────────
    all_evaluated = get_eligible_pathways_for_profile(profile, current_constraints)
    ranked_top3 = get_ranked_pathways(
        eligibility_records=all_evaluated,
        user_constraints=current_constraints,
        waste_profile=profile,
        top_k=3,
    )
    all_ranked = get_ranked_pathways(
        eligibility_records=all_evaluated,
        user_constraints=current_constraints,
        waste_profile=profile,
        top_k=None,
    )

    if ranked_top3:
        try:
            from database.database import save_recommendations
            save_recommendations(ranked_top3, scan_id=st.session_state.get("active_scan_id"))
        except Exception:
            pass

        st.markdown(f"### 🏆 Top Recommendations ({len(ranked_top3)} Feasible Options)")
        st.caption(
            "Ranked deterministically across Budget (20%), Time (20%), Tools (15%), "
            "Recovery Value (15%), Extra Materials (10%), Skill (10%), and Condition (10%)."
        )

        for rec in ranked_top3:
            rank = rec["rank"]
            badge_label = RANK_MEDALS.get(rank, f"RANK {rank}")
            score = rec["score"]
            crit = rec["criterion_scores"]
            p = rec["pathway"]
            ptype = rec.get("pathway_type", "reuse").lower()
            icon = TYPE_ICONS.get(ptype, "📋")

            with st.container(border=True):
                col_title, col_score = st.columns([3, 1])
                with col_title:
                    st.markdown(f"#### {icon} {rec['title']} &nbsp; {pill_badge(badge_label, 'primary')}", unsafe_allow_html=True)
                    st.caption(f"Pathway ID: `{rec['pathway_id']}` | Category: `{ptype.upper()}`")
                with col_score:
                    st.metric("MCDA Score", f"{score:.1f} / 100")

                st.markdown("##### 💡 Why this recommendation?")
                for reason in rec.get("why_this", []):
                    st.markdown(f"- ✅ {reason}")

                if rank > 1 and rec.get("why_not_this"):
                    st.markdown("##### ⚖️ Trade-off vs Top-1")
                    for note in rec["why_not_this"]:
                        st.markdown(f"- ℹ️ {note}")

                if rec.get("warnings"):
                    for w in rec["warnings"]:
                        st.warning(f"⚠️ {w}")

                st.markdown("##### 📦 Requirements & Implementation")
                r1, r2, r3, r4 = st.columns(4)
                with r1:
                    st.markdown(f"**Cost:** ₹{rec.get('budget', '0')}")
                    st.markdown(f"**Tools:** {rec.get('required_tools', 'None')}")
                with r2:
                    st.markdown(f"**Time:** {rec.get('time_required', '15 mins')}")
                    st.markdown(f"**Materials:** {rec.get('extra_materials', 'None')}")
                with r3:
                    st.markdown(f"**Skill:** {rec.get('skill_level', 'Beginner')}")
                    st.markdown(f"**Workspace:** {rec.get('workspace', 'Any')}")
                with r4:
                    st.markdown(f"**Condition:** {p.get('condition_requirement', 'Any')}")
                    st.markdown(f"**Min Qty:** {p.get('min_quantity', 1)} item(s)")

                with st.expander("📊 View Criterion Breakdown Scores (0–100)"):
                    c_col1, c_col2, c_col3, c_col4 = st.columns(4)
                    with c_col1:
                        st.progress(int(crit["practical_fit"]), text=f"Practical Fit: {crit['practical_fit']:.1f}")
                        st.progress(int(crit["budget_fit"]), text=f"Budget Fit: {crit['budget_fit']:.1f}")
                    with c_col2:
                        st.progress(int(crit["time_fit"]), text=f"Time Fit: {crit['time_fit']:.1f}")
                        st.progress(int(crit["tool_fit"]), text=f"Tool Fit: {crit['tool_fit']:.1f}")
                    with c_col3:
                        st.progress(int(crit["extra_material_fit"]), text=f"Materials Fit: {crit['extra_material_fit']:.1f}")
                        st.progress(int(crit["skill_fit"]), text=f"Skill Fit: {crit['skill_fit']:.1f}")
                    with c_col4:
                        st.progress(int(crit["condition_fit"]), text=f"Condition Fit: {crit['condition_fit']:.1f}")
                        st.progress(int(crit["recovery_value"]), text=f"Recovery Value: {crit['recovery_value']:.1f}")

                if st.button(f"📖 Open Execution Guide (Option #{rank})", key=f"btn_exec_{rec['pathway_id']}", use_container_width=True):
                    st.session_state["selected_pathway_id"] = rec["pathway_id"]
                    st.switch_page("pages/6_Execution.py")

        st.divider()

        # Multi-option comparison
        st.markdown("### 📊 Side-by-Side Comparison")
        comp_rows = []
        for r in all_ranked:
            comp_rows.append({
                "Rank": f"#{r['rank']}",
                "Option Title": r["title"],
                "Score": f"{r['score']:.1f}",
                "Type": r["pathway_type"].upper(),
                "Budget": f"₹{r['budget']}",
                "Time": r["time_required"],
                "Skill": r["skill_level"],
                "Tools": r["required_tools"],
                "Practical Fit": f"{r['criterion_scores']['practical_fit']:.1f}",
                "Recovery Value": f"{r['criterion_scores']['recovery_value']:.1f}",
            })

        df_comp = pd.DataFrame(comp_rows)
        st.dataframe(df_comp, use_container_width=True, hide_index=True)

    else:
        st.warning("⚠️ **No Recovery Pathways are Currently Feasible.**")
        st.markdown("None of the catalogued recovery options satisfied all safety rules and household constraints.")
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            st.page_link("pages/4_Constraints.py", label="⚙️ Adjust Constraints & Tools", use_container_width=True)
        with col_b2:
            st.page_link("pages/1_Scan_Waste.py", label="📷 Scan Another Item", use_container_width=True)

else:
    st.info("ℹ️ **No active waste profile detected.**")
    st.markdown("Please scan a waste item first to generate structured recognition data.")
    st.page_link("pages/1_Scan_Waste.py", label="📷 Go to Scan Waste", use_container_width=True)

st.divider()
st.caption("📌 Transparent Multi-Criteria Decision Analysis (MCDA). Filtered strictly by Safety and Physical Feasibility before ranking.")
