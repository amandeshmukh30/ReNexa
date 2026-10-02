"""
ReNexa — Execution Guidance Page
=================================
Interactive, step-by-step physical execution guide for selected recovery pathways.
Phase 7: Step-by-Step Instructions, Resource Checklist, Safety Warnings, and Completion Feedback.
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
    metric_card,
    status_badge,
    empty_state,
)
from utils.validation import get_default_constraints
from services.execution_service import get_execution_guide
from services.ranking_service import get_ranked_recommendations_for_profile

# ── Page config ───────────────────────────────────────────────────────────
configure_page(title="Execution Guidance — ReNexa", icon="📖")

# ── Sidebar ───────────────────────────────────────────────────────────────
render_sidebar("pages/6_Execution.py")

# ── Header ────────────────────────────────────────────────────────────────
page_header(
    "📖 Step-by-Step Execution Guidance",
    "Detailed physical instructions, safety precautions, and resource verification for waste recovery.",
)

# ── Session State Context ─────────────────────────────────────────────────
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

# Determine active selected pathway ID
selected_id = st.session_state.get("selected_pathway_id")

# If no pathway currently selected but a profile exists, retrieve ranked options to let user pick
if not selected_id and profile and profile.get("material") and profile.get("material") != "Unknown":
    ranked_candidates = get_ranked_recommendations_for_profile(profile, current_constraints, top_k=5)
    if ranked_candidates:
        st.info("ℹ️ Select one of your feasible recommendations below to view its execution guide:")
        options_map = {
            f"Rank #{r['rank']}: {r['title']} ({r['pathway_type'].upper()} — Score: {r['score']:.1f})": r["pathway_id"]
            for r in ranked_candidates
        }
        chosen_label = st.selectbox("Choose a recommended pathway:", list(options_map.keys()))
        if chosen_label:
            selected_id = options_map[chosen_label]
            st.session_state["selected_pathway_id"] = selected_id

if selected_id:
    # ── Retrieve Execution Guide ──────────────────────────────────────────
    guide = get_execution_guide(
        pathway_or_id=selected_id,
        user_constraints=current_constraints,
        waste_profile=profile,
    )

    ptype = guide.get("pathway_type", "reuse").lower()
    icon = TYPE_ICONS.get(ptype, "📋")
    can_execute = guide.get("can_execute", False)
    exec_status = guide.get("execution_status", "UNKNOWN")

    # ── 1. Hero Header & Pathway Identification ───────────────────────────
    st.markdown(
        f"""
        <div class="renexa-card" style="margin-bottom: 24px;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px;">
                <div>
                    <div style="font-size: 0.85rem; color: #9FEA45; text-transform: uppercase; letter-spacing: 1px; font-weight: 700; margin-bottom: 6px;">
                        RECOVERY EXECUTION RECIPE
                    </div>
                    <h2 style="margin: 0 0 8px 0; color: #F5FFF8; font-size: 1.6rem;">{icon} {guide.get('title')}</h2>
                    <p style="margin: 0; color: #A9C3B8; font-size: 0.95rem;">{guide.get('description', '')}</p>
                </div>
                <div>
                    {status_badge("READY TO EXECUTE" if can_execute else exec_status, "allow" if can_execute else ("block" if exec_status == "BLOCKED" else "warn"))}
                </div>
            </div>
            <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-top: 16px;">
                {status_badge(f"ID: {guide.get('pathway_id')}", "neutral")}
                {status_badge(f"Material: {guide.get('input_material', '').capitalize()}", "neutral")}
                {status_badge(f"Type: {ptype.upper()}", "allow")}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── 2. Handle Ineligible or Blocked States ─────────────────────────────
    if not can_execute:
        if exec_status == "BLOCKED":
            st.error("🚫 **Safety Alert: Execution Prohibited**\n"
                     "This pathway involves operations flagged as hazardous by the ReNexa Safety Engine.")
            for r in guide.get("reasons", []):
                st.markdown(f"- 🛑 {r}")
        elif exec_status == "INFEASIBLE":
            st.warning("⚠️ **Constraint Mismatch: Execution Not Supported**\n"
                       "Your current household constraints do not support this recovery pathway.")
            for r in guide.get("reasons", []):
                st.markdown(f"- ❌ {r}")
            st.page_link("pages/4_Constraints.py", label="⚙️ Adjust Constraints & Tools", use_container_width=True)
        else:
            st.warning(f"⚠️ **Data Quality Notice:** {', '.join(guide.get('reasons', ['Instructions unavailable.']))}")

        col_back, _ = st.columns([1, 2])
        with col_back:
            st.page_link("pages/5_Recommendations.py", label="⬅️ Return to Recommendations", use_container_width=True)

    else:
        # ── 3. Quick Metadata Grid ────────────────────────────────────────
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            metric_card("Estimated Time", guide.get("time_required", "15 mins"), icon="⏱️")
        with col_m2:
            metric_card("Skill Level", guide.get("skill_level", "Beginner"), icon="🎯")
        with col_m3:
            metric_card("Cost Estimate", f"₹{guide.get('budget', '0')}", icon="💰")
        with col_m4:
            metric_card("Workspace", guide.get("workspace", "Indoor"), icon="🏠")

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        # ── 4. Prerequisites & Resource Checklist ─────────────────────────
        st.markdown("### 🛠️ What You'll Need")
        
        c_req1, c_req2 = st.columns(2)
        with c_req1:
            tools = guide.get("tools", [])
            tools_str = ", ".join(tools) if tools else "None required"
            st.markdown(
                f"""
                <div class="renexa-card" style="height: 100%;">
                    <div style="font-weight: 700; color: #9FEA45; margin-bottom: 8px;">🔧 Required Tools</div>
                    <div style="color: #F5FFF8; font-size: 1.05rem; margin-bottom: 12px;">{tools_str}</div>
                    <div style="font-size: 0.85rem; color: #A9C3B8;">
                        Target Condition: <strong style="color:#F5FFF8;">{guide.get('condition_requirement', 'Any')}</strong>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c_req2:
            mats = guide.get("extra_materials", [])
            mats_str = ", ".join(mats) if mats else "None required"
            st.markdown(
                f"""
                <div class="renexa-card" style="height: 100%;">
                    <div style="font-weight: 700; color: #9FEA45; margin-bottom: 8px;">📦 Extra Supplies</div>
                    <div style="color: #F5FFF8; font-size: 1.05rem; margin-bottom: 12px;">{mats_str}</div>
                    <div style="font-size: 0.85rem; color: #A9C3B8;">
                        Minimum Quantity: <strong style="color:#F5FFF8;">{guide.get('min_quantity', 1)} item(s)</strong>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        # ── 5. Safety Precautions ─────────────────────────────────────────
        if guide.get("warnings"):
            st.markdown("### 🛡️ Safety Precautions")
            for w in guide["warnings"]:
                st.markdown(
                    f"""
                    <div class="renexa-card" style="border-left: 4px solid #F2C94C; margin-bottom: 10px; padding: 14px 18px;">
                        <span style="font-size: 1.1rem; margin-right: 8px;">⚠️</span>
                        <span style="color: #F5FFF8; font-size: 0.95rem;">{w}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        # ── 6. Step-by-Step Procedure ─────────────────────────────────────
        st.markdown("### 📋 Step-by-Step Instructions")
        st.caption("Follow each step in exact sequence. Check off steps as you complete them:")

        steps = guide.get("steps", [])
        if steps:
            for idx, step_text in enumerate(steps, start=1):
                col_num, col_check = st.columns([1, 11])
                with col_num:
                    st.markdown(
                        f"""
                        <div style="background:#062823; border: 2px solid #9FEA45; color:#9FEA45; font-weight:800; font-size:1.1rem; border-radius:12px; height:44px; display:flex; align-items:center; justify-content:center; text-align:center;">
                            {idx:02d}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with col_check:
                    st.checkbox(f"**Step {idx}:** {step_text}", key=f"exec_step_{guide['pathway_id']}_{idx}")
                st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
        else:
            empty_state("No step-by-step instructions available for this pathway.", icon="📋")

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        # ── 7. Expected Outcome & Fallback ────────────────────────────────
        st.markdown("### 🎯 Expected Result & Fallback")
        col_out, col_fall = st.columns(2)
        with col_out:
            st.markdown(
                f"""
                <div class="renexa-card" style="height: 100%;">
                    <div style="font-weight: 700; color: #9FEA45; margin-bottom: 8px;">✨ Expected Result</div>
                    <div style="color: #F5FFF8; font-size: 0.95rem;">{guide.get('expected_output', 'Restored or repurposed item.')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_fall:
            st.markdown(
                f"""
                <div class="renexa-card" style="height: 100%;">
                    <div style="font-weight: 700; color: #A9C3B8; margin-bottom: 8px;">🔄 Fallback Plan (If execution fails)</div>
                    <div style="color: #F5FFF8; font-size: 0.95rem;">{guide.get('fallback', 'Dispose via municipal segregated waste collection.')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

        # ── 8. Verified Source / Tutorial Reference ───────────────────────
        st.markdown(
            f"""
            <div class="renexa-card" style="padding: 14px 20px;">
                <div style="font-size: 0.85rem; color: #A9C3B8;">
                    <strong>Source Authority:</strong> {guide.get('tutorial_reference')} | 
                    <strong>Verification:</strong> <span class="renexa-badge renexa-badge-neutral">{guide.get('verification_status', 'prototype')}</span> | 
                    <strong>Last Reviewed:</strong> {guide.get('last_reviewed', 'Unknown')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

        # ── 9. Completion Feedback Form ───────────────────────────────────
        st.markdown("### 📝 Execution Outcome Feedback")
        st.caption("Record your physical outcome to validate recipe feasibility and time accuracy.")

        with st.form(f"feedback_form_{guide['pathway_id']}"):
            f_tried = st.radio(
                "Execution Attempt Status:",
                options=["Not yet", "Successfully completed", "Partially completed", "Could not complete"],
                horizontal=True,
                help="Select your actual real-world attempt status.",
            )

            col_fb1, col_fb2, col_fb3 = st.columns(3)
            with col_fb1:
                f_actual_time = st.number_input(
                    "Actual Time Taken (minutes):",
                    min_value=0,
                    max_value=300,
                    value=0,
                    step=5,
                    help="Leave as 0 if not attempted.",
                )
            with col_fb2:
                f_time_acc = st.selectbox(
                    "Time Estimation Accuracy:",
                    options=["Accurate / As expected", "Took significantly longer", "Took less time", "Not applicable"],
                )
            with col_fb3:
                f_rating = st.slider("User Feasibility Rating:", min_value=1, max_value=5, value=5, help="1 = Very difficult / impractical, 5 = Highly feasible and clear")

            col_fb4, col_fb5 = st.columns(2)
            with col_fb4:
                f_missing_tools = st.radio("Were any required tools missing or inadequate?", ["No", "Yes"], horizontal=True)
                f_missing_tools_text = st.text_input("If yes, which tools?", value="", placeholder="e.g. Needle size was too small")
            with col_fb5:
                f_missing_mats = st.radio("Were any extra materials missing?", ["No", "Yes"], horizontal=True)
                f_missing_mats_text = st.text_input("If yes, which materials?", value="", placeholder="e.g. Tape did not adhere properly")

            st.divider()
            f_safety_issue = st.radio("Did you encounter any safety or hazard issues during execution?", ["No", "Yes"], horizontal=True)
            f_safety_text = st.text_area("If safety issue occurred, please describe it in detail (e.g. sharp cut, fume irritation):", height=68)

            col_fb6, col_fb7 = st.columns([1, 2])
            with col_fb6:
                f_again = st.selectbox(
                    "Would you try this pathway again?",
                    options=["Yes", "Maybe with adjustments", "No, not practical"],
                )
            with col_fb7:
                f_notes = st.text_input("Additional Observations / Qualitative Notes:", placeholder="Any tips or step clarifications")

            submitted_fb = st.form_submit_button("💾 Submit Outcome Feedback", use_container_width=True)

            if submitted_fb:
                # Derive canonical failure reason if applicable
                failure_reason = None
                if f_tried in ("Partially completed", "Could not complete"):
                    if f_safety_issue == "Yes":
                        failure_reason = "safety_issue"
                    elif f_missing_tools == "Yes":
                        failure_reason = "missing_tool"
                    elif f_missing_mats == "Yes":
                        failure_reason = "missing_material"
                    elif f_time_acc == "Took significantly longer":
                        failure_reason = "time_underestimated"
                    else:
                        failure_reason = "other"

                feedback_record = {
                    "pathway_id": guide["pathway_id"],
                    "pathway_title": guide["title"],
                    "material": guide.get("input_material", "unknown"),
                    "item": (profile or {}).get("item", "Unknown"),
                    "condition": (profile or {}).get("condition", "Unknown"),
                    "contamination": (profile or {}).get("contamination", "Unknown"),
                    "quantity": guide.get("min_quantity", 1),
                    "predicted_rank": (profile or {}).get("predicted_rank"),
                    "predicted_score": (profile or {}).get("predicted_score"),
                    "safety_status": guide.get("safety_status", "ALLOW"),
                    "constraint_status": guide.get("constraint_status", "FEASIBLE"),
                    "attempt_status": f_tried,
                    "estimated_time_minutes": guide.get("time_required"),
                    "actual_time_minutes": f_actual_time if (f_actual_time > 0 and f_tried != "Not yet") else None,
                    "time_accuracy": f_time_acc,
                    "missing_materials": (f_missing_mats == "Yes"),
                    "missing_materials_details": f_missing_mats_text if f_missing_mats == "Yes" else "",
                    "missing_tools": (f_missing_tools == "Yes"),
                    "missing_tools_details": f_missing_tools_text if f_missing_tools == "Yes" else "",
                    "safety_issue": (f_safety_issue == "Yes"),
                    "safety_issue_details": f_safety_text if f_safety_issue == "Yes" else "",
                    "failure_reason": failure_reason,
                    "user_rating": f_rating,
                    "would_try_again": f_again,
                    "notes": f_notes,
                }

                # Save record to JSON / database storage
                from services.outcome_service import save_outcome_feedback
                success = save_outcome_feedback(feedback_record)

                if success:
                    st.session_state["execution_feedback"] = feedback_record
                    st.success("✅ Thank you! Your outcome has been recorded in the ReNexa validation log.")
                    if f_safety_issue == "Yes":
                        st.warning("⚠️ **Safety Incident Recorded:** Your safety note has been flagged for safety rule review.")
                else:
                    st.error("Failed to save feedback. Please check file permissions.")

else:
    # ── Empty State: No pathway selected ──────────────────────────────────
    empty_state(
        "No recovery pathway currently selected. Please select a recommended recovery pathway to view its step-by-step physical guide.",
        icon="📖",
        action_label="🎯 View Recommendations",
        action_page="pages/5_Recommendations.py",
    )

st.divider()
st.caption(
    "📌 **Research Framework:** ReNexa Phase 7 provides grounded, constraint-verified execution guidance. "
    "All instructions and safety parameters originate strictly from catalogued knowledge base entries."
)
