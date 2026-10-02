"""
ReNexa — Impact Page
=====================
Displays user recovery impact metrics and environmental contribution.
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
    metric_card,
    render_sidebar,
    status_badge,
)
from database.database import get_user_dashboard_metrics
from database.auth import AUTH_USER_KEY, AUTH_TOKEN_KEY

# ── Page config ───────────────────────────────────────────────────────────
configure_page(title="Impact — ReNexa", icon="🌍")

# ── Sidebar ───────────────────────────────────────────────────────────────
render_sidebar("pages/8_Impact.py")

# ── Header ────────────────────────────────────────────────────────────────
page_header("🌍 Recovery Impact & Sustainability", "Track your cumulative household environmental contribution and waste diverted.")

# ── Metrics Context ───────────────────────────────────────────────────────
current_user = st.session_state.get(AUTH_USER_KEY)
token = st.session_state.get(AUTH_TOKEN_KEY)
user_id = current_user.get("id") if current_user else None

user_metrics = get_user_dashboard_metrics(user_id=user_id, token=token)
recovered_count = user_metrics.get("successful_executions", 0)
attempts_count = user_metrics.get("total_attempts", 0)
scans_count = user_metrics.get("total_scans", 0)

# ── Impact metrics ────────────────────────────────────────────────────────
st.markdown("### 📊 Household Impact Scorecard")

metric_cols = st.columns(4)

with metric_cols[0]:
    metric_card("Items Recovered", str(recovered_count), icon="♻️")
with metric_cols[1]:
    # 0.25kg average estimated per recovered household item
    diverted_kg = recovered_count * 0.25
    metric_card("Waste Diverted", f"{diverted_kg:.1f} kg", icon="🗑️")
with metric_cols[2]:
    metric_card("Recovery Attempts", str(attempts_count), icon="🔄")
with metric_cols[3]:
    # Estimated ~0.5 kg CO2 avoided per kg waste recovered
    co2_saved = diverted_kg * 0.5
    metric_card("CO₂ Avoided", f"{co2_saved:.1f} kg", icon="🌱")

st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

# ── Explanation Card ──────────────────────────────────────────────────────
st.markdown(
    """
    <div class="renexa-card">
        <div style="font-weight: 700; color: #9FEA45; margin-bottom: 8px;">📌 Grounded Sustainability Accounting</div>
        <p style="color: #F5FFF8; font-size: 0.95rem; line-height: 1.5; margin: 0 0 10px 0;">
            ReNexa avoids fabricated badges or ungrounded claims. All metrics displayed above reflect 
            <strong>actual verified physical recovery outcomes</strong> logged through the execution guidance system.
        </p>
        <div style="font-size: 0.85rem; color: #A9C3B8;">
            New users start at 0 and build real verifiable impact as items are scanned, repaired, upcycled, or diverted.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()
st.caption(
    "📌 **Research Impact Framework:** Empirically connects machine-assisted waste classification with tangible "
    "household circular economy outcomes."
)
