"""
ReNexa — Recovery Outcome Analytics & Validation Page
======================================================
Measures real-world feasibility and execution outcomes for household waste recovery recommendations.
Phase 8: Outcome Validation Analytics (RESR, OVRR, Time MAE, Resource Completeness, Safety Rates).
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
    metric_card,
    status_badge,
    empty_state,
)
from services.outcome_service import (
    load_outcome_feedback,
    calculate_outcome_metrics,
    summarize_failure_reasons,
    analyze_pathway_outcomes,
)

# ── Page config ───────────────────────────────────────────────────────────
configure_page(title="Outcome Analytics — ReNexa", icon="📈")

# ── Sidebar ───────────────────────────────────────────────────────────────
render_sidebar("pages/7_Outcome.py")

# ── Header ────────────────────────────────────────────────────────────────
page_header(
    "📈 Recovery Outcome Analytics",
    "Empirical validation of recommendation feasibility, real-world execution success, and time accuracy.",
)

# ── Load feedback records ─────────────────────────────────────────────────
records = load_outcome_feedback()

if not records:
    empty_state(
        "No execution outcomes have been recorded yet. Real-world execution metrics are calculated dynamically when users execute recommended pathways and submit outcome feedback.",
        icon="📈",
        action_label="📖 Open Execution Guide",
        action_page="pages/6_Execution.py",
    )
else:
    metrics = calculate_outcome_metrics(records)
    total_recorded = metrics["total_recorded"]
    total_attempted = metrics["total_attempted"]

    # ── Overview Metrics Grid ─────────────────────────────────────────────
    st.markdown("### 📊 Real-World Execution Overview")
    st.caption(f"Based on **{total_recorded}** recorded feedback submissions (**{total_attempted}** physically attempted).")

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        metric_card("Total Recorded", str(total_recorded), icon="📝")
    with m2:
        metric_card("Total Attempted", str(total_attempted), icon="🛠️")
    with m3:
        metric_card("Successful", str(metrics["successful_count"]), icon="✅")
    with m4:
        metric_card("Partially Completed", str(metrics["partial_count"]), icon="⏳")
    with m5:
        metric_card("Failed / Incomplete", str(metrics["failed_count"]), icon="❌")

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # ── Core Research Analytics Metrics ───────────────────────────────────
    st.markdown("### 🔬 Feasibility & Reliability Metrics")

    col_r1, col_r2, col_r3 = st.columns(3)
    with col_r1:
        st.markdown(
            f"""
            <div class="renexa-card" style="margin-bottom: 16px;">
                <div style="font-size: 0.85rem; color: #A9C3B8; margin-bottom: 4px;">RESR (Execution Success Rate)</div>
                <div style="font-size: 1.8rem; font-weight: 800; color: #9FEA45;">{metrics['resr']:.1f}%</div>
                <div style="font-size: 0.8rem; color: #A9C3B8; margin-top: 6px;">
                    {metrics['successful_count']} of {total_attempted} attempts completed successfully.
                </div>
            </div>
            <div class="renexa-card">
                <div style="font-size: 0.85rem; color: #A9C3B8; margin-bottom: 4px;">Execution Failure Rate</div>
                <div style="font-size: 1.8rem; font-weight: 800; color: {'#E97878' if metrics['failure_rate'] > 0 else '#9FEA45'};">{metrics['failure_rate']:.1f}%</div>
                <div style="font-size: 0.8rem; color: #A9C3B8; margin-top: 6px;">
                    {metrics['failed_count']} of {total_attempted} attempts encountered blockers.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_r2:
        st.markdown(
            f"""
            <div class="renexa-card" style="margin-bottom: 16px;">
                <div style="font-size: 0.85rem; color: #A9C3B8; margin-bottom: 4px;">OVRR (Recipe Reliability)</div>
                <div style="font-size: 1.8rem; font-weight: 800; color: #9FEA45;">{metrics['ovrr']:.1f}%</div>
                <div style="font-size: 0.8rem; color: #A9C3B8; margin-top: 6px;">
                    Clean execution with complete resources and no safety incidents.
                </div>
            </div>
            <div class="renexa-card">
                <div style="font-size: 0.85rem; color: #A9C3B8; margin-bottom: 4px;">Resource Completeness</div>
                <div style="font-size: 1.8rem; font-weight: 800; color: #9FEA45;">{metrics['resource_completeness_rate']:.1f}%</div>
                <div style="font-size: 0.8rem; color: #A9C3B8; margin-top: 6px;">
                    Validates Phase 5 constraint engine prediction accuracy.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_r3:
        time_mae_str = f"{metrics['time_mae']:.1f} mins" if metrics["time_mae"] is not None else "N/A"
        safety_color = "#9FEA45" if metrics["safety_issue_rate"] == 0 else "#E97878"
        st.markdown(
            f"""
            <div class="renexa-card" style="margin-bottom: 16px;">
                <div style="font-size: 0.85rem; color: #A9C3B8; margin-bottom: 4px;">Time Estimation MAE</div>
                <div style="font-size: 1.8rem; font-weight: 800; color: #F5FFF8;">{time_mae_str}</div>
                <div style="font-size: 0.8rem; color: #A9C3B8; margin-top: 6px;">
                    Across {metrics['time_evaluated_count']} duration-reported attempts.
                </div>
            </div>
            <div class="renexa-card">
                <div style="font-size: 0.85rem; color: #A9C3B8; margin-bottom: 4px;">Safety Incident Rate</div>
                <div style="font-size: 1.8rem; font-weight: 800; color: {safety_color};">{metrics['safety_issue_rate']:.1f}%</div>
                <div style="font-size: 0.8rem; color: #A9C3B8; margin-top: 6px;">
                    Monitors effectiveness of Phase 5 Safety rules.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # ── Failure Reason Analysis ───────────────────────────────────────────
    st.markdown("### 🔍 Execution Challenges & Diagnostics")
    failure_reasons = summarize_failure_reasons(records)
    total_issues = sum(failure_reasons.values())

    if total_issues > 0:
        col_chart, col_details = st.columns([2, 1])
        with col_chart:
            df_reasons = pd.DataFrame([
                {"Challenge Category": k.replace("_", " ").title(), "Occurrences": v}
                for k, v in failure_reasons.items()
                if v > 0
            ])
            st.dataframe(df_reasons, use_container_width=True, hide_index=True)
        with col_details:
            st.markdown(
                """
                <div class="renexa-card">
                    <div style="font-weight: 700; color: #9FEA45; margin-bottom: 8px;">📌 Diagnostic Insights</div>
                """,
                unsafe_allow_html=True,
            )
            for cat, count in failure_reasons.items():
                if count > 0:
                    st.markdown(f"- **{cat.replace('_', ' ').title()}:** {count} report(s)")
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown(
            """
            <div class="renexa-card" style="border-left: 4px solid #9FEA45;">
                <span style="color: #9FEA45; font-weight: 700;">✅ Clean Execution Track Record:</span>
                <span style="color: #F5FFF8; margin-left: 6px;">Zero execution challenges or resource shortages reported in recorded feedback.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # ── Per-Pathway Breakdown Table ───────────────────────────────────────
    st.markdown("### 📋 Recipe-Level Feasibility Performance")
    pathway_table = analyze_pathway_outcomes(records)

    if pathway_table:
        df_pathway = pd.DataFrame(pathway_table)
        st.dataframe(df_pathway, use_container_width=True, hide_index=True)
    else:
        empty_state("No recipe-specific attempts recorded yet.", icon="📋")

st.divider()
st.caption(
    "📌 **Research Framework:** ReNexa Phase 8 evaluates actual physical outcomes to ground "
    "predicted feasibility against real-world household execution data."
)
