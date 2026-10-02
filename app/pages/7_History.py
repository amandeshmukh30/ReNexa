"""
ReNexa — History & Personal Recovery Log
=========================================
Tracks personalized past recovery attempts, scans, recommendations, and execution outcomes.
Phase 9C: Personalized Multi-View History, Filters, and User Metrics.
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
from database.database import (
    get_database_status,
    get_user_scans,
    get_user_recommendations,
    get_user_feedback,
    get_all_feedback,
    get_user_dashboard_metrics,
)
from database.auth import get_auth_service, AUTH_USER_KEY, AUTH_TOKEN_KEY

# ── Page config ───────────────────────────────────────────────────────────
configure_page(title="History — ReNexa", icon="📜")

# ── Sidebar ───────────────────────────────────────────────────────────────
render_sidebar("pages/7_History.py")

# ── Header ────────────────────────────────────────────────────────────────
page_header("📜 Your Recovery History", "Personalized log of waste scans, recommendations, and execution outcomes.")

# ── Auth & Storage Context ────────────────────────────────────────────────
db_status = get_database_status()
current_user = st.session_state.get(AUTH_USER_KEY)
token = st.session_state.get(AUTH_TOKEN_KEY)
user_id = current_user.get("id") if current_user else None
auth_service = get_auth_service()

# ── Top Account & Sync Banner ─────────────────────────────────────────────
st.markdown(
    f"""
    <div class="renexa-card" style="margin-bottom: 20px; padding: 14px 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 1.3rem;">{'☁️' if db_status['configured'] else '📁'}</span>
                <div>
                    <div style="color: #F5FFF8; font-weight: 600; font-size: 0.95rem;">
                        {'Cloud Synchronized' if (db_status['configured'] and current_user) else ('Cloud Ready' if db_status['configured'] else 'Local Guest Storage')}
                    </div>
                    <div style="color: #A9C3B8; font-size: 0.8rem;">
                        {db_status['storage_target']} {f"({db_status['url_masked']})" if db_status.get('url_masked') else ''}
                    </div>
                </div>
            </div>
            <div>
                {status_badge(f"👤 {current_user.get('display_name', 'User')}" if current_user else "🔒 Guest Mode", "allow" if current_user else "neutral")}
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Sign In / Register Expander ───────────────────────────────────────────
if not current_user and db_status["configured"]:
    with st.expander("🔑 Sign In / Register to access Cloud History", expanded=False):
        tab_login, tab_signup = st.tabs(["🔐 Sign In", "📝 Create Account"])

        with tab_login:
            with st.form("form_login_hist"):
                login_email = st.text_input("Email:", key="login_email_hist")
                login_password = st.text_input("Password:", type="password", key="login_password_hist")
                submit_login = st.form_submit_button("Sign In", use_container_width=True)

                if submit_login:
                    res = auth_service.login(login_email, login_password)
                    if res["success"]:
                        st.session_state[AUTH_USER_KEY] = res["user"]
                        st.session_state[AUTH_TOKEN_KEY] = res["token"]
                        st.success(f"Welcome back, {res['user']['display_name']}!")
                        st.rerun()
                    else:
                        st.error(f"❌ {res['error']}")

        with tab_signup:
            with st.form("form_signup_hist"):
                signup_email = st.text_input("Email:", key="signup_email_hist")
                signup_password = st.text_input("Password (min 6 chars):", type="password", key="signup_password_hist")
                signup_name = st.text_input("Display Name (optional):", key="signup_name_hist")
                submit_signup = st.form_submit_button("Create Account", use_container_width=True)

                if submit_signup:
                    res = auth_service.signup(signup_email, signup_password, display_name=signup_name)
                    if res["success"]:
                        st.session_state[AUTH_USER_KEY] = res["user"]
                        st.session_state[AUTH_TOKEN_KEY] = res["token"]
                        st.success(f"Account created! Welcome, {res['user']['display_name']}!")
                        st.rerun()
                    else:
                        st.error(f"❌ {res['error']}")
elif current_user:
    if st.button("🚪 Sign Out of Account", key="btn_signout_hist"):
        st.session_state.pop(AUTH_USER_KEY, None)
        st.session_state.pop(AUTH_TOKEN_KEY, None)
        st.rerun()

# ── 1. Overview Metric Cards ──────────────────────────────────────────────
metrics = get_user_dashboard_metrics(user_id=user_id, token=token)

st.markdown("### 📊 Activity Overview")
c1, c2, c3, c4 = st.columns(4)
with c1:
    metric_card("Total Scans", str(metrics["total_scans"]), icon="📷")
with c2:
    metric_card("Evaluations", str(metrics["total_recommendations"]), icon="🎯")
with c3:
    metric_card("Executions", str(metrics["total_attempts"]), icon="🛠️")
with c4:
    metric_card("Recovered", str(metrics["successful_executions"]), icon="✅")

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

# ── 2. Filters ────────────────────────────────────────────────────────────
st.markdown("### 🔍 Filter History")
f_col1, f_col2 = st.columns(2)

MATERIAL_OPTIONS = [
    "All", "Plastic", "Glass", "Metal", "Paper", "Cardboard", "Clothes", "Shoes", "Biological", "Trash"
]
STATUS_OPTIONS = [
    "All", "Successful", "Partial", "Failed", "Not_Attempted"
]

with f_col1:
    selected_material = st.selectbox("Filter by Material:", options=MATERIAL_OPTIONS, index=0)
with f_col2:
    selected_status = st.selectbox("Filter by Outcome Status:", options=STATUS_OPTIONS, index=0)

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

# ── 3. Execution Outcomes Log ─────────────────────────────────────────────
st.markdown("### 🛠️ Execution Outcomes & Validation Feedback")
st.caption("Detailed results from household recovery procedures.")

feedback_records = get_user_feedback(
    user_id=user_id,
    token=token,
    status_filter=selected_status if selected_status != "All" else None,
    material_filter=selected_material if selected_material != "All" else None,
    limit=50,
)

if feedback_records:
    log_rows = []
    for f in feedback_records:
        created_date = str(f.get("created_at") or f.get("timestamp") or "—")[:10]
        status = str(f.get("attempt_status", "Unknown")).capitalize()
        pathway = f"{f.get('pathway_id', '')} - {f.get('pathway_title', '')}"
        act_t = f.get("actual_time_minutes")
        time_str = f"{act_t} mins" if act_t is not None else "—"
        rating = f"{f.get('user_rating')} ⭐" if f.get("user_rating") else "—"
        safety = "⚠️ Flagged" if f.get("safety_issue") else "✅ Safe"

        log_rows.append({
            "Date": created_date,
            "Pathway": pathway,
            "Status": status,
            "Actual Time": time_str,
            "Safety": safety,
            "Rating": rating,
            "Notes": f.get("notes") or "—",
        })
    df_feedback = pd.DataFrame(log_rows)
    st.dataframe(df_feedback, use_container_width=True, hide_index=True)
else:
    empty_state("No execution outcomes match the selected filter.", icon="📋")

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

# ── 4. Recent Waste Scans ─────────────────────────────────────────────────
st.markdown("### 📷 Recent Waste Scans")
st.caption("Metadata log of uploaded and recognized household waste items.")

scans = get_user_scans(
    user_id=user_id,
    token=token,
    material=selected_material if selected_material != "All" else None,
    limit=25,
)

if scans:
    scan_rows = []
    for s in scans:
        created_date = str(s.get("created_at", "—"))[:19].replace("T", " ")
        mat = str(s.get("detected_material", "Unknown")).capitalize()
        conf = f"{float(s['confidence']) * 100:.1f}%" if s.get("confidence") is not None else "—"
        qty = s.get("confirmed_quantity", s.get("detected_object_count", 1))

        scan_rows.append({
            "Timestamp": created_date,
            "Material": mat,
            "Quantity": qty,
            "AI Confidence": conf,
            "Model Label": s.get("model_label") or "—",
            "Image File": s.get("image_filename") or "Direct Capture",
        })
    df_scans = pd.DataFrame(scan_rows)
    st.dataframe(df_scans, use_container_width=True, hide_index=True)
else:
    empty_state("No waste scans match the selected filter.", icon="📷")

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

# ── 5. Recent Evaluated Recommendations ───────────────────────────────────
st.markdown("### 🎯 Evaluated Recovery Recommendations")
st.caption("Top-K recommendations generated by Phase 6 MCDA ranking for your scans.")

recs = get_user_recommendations(user_id=user_id, token=token, limit=25)
if recs:
    rec_rows = []
    for r in recs:
        created_date = str(r.get("created_at", "—"))[:10]
        rank_str = f"#{r.get('rank', 1)}"
        score_str = f"{float(r.get('mcda_score', 0)):.1f} / 100"
        rec_rows.append({
            "Date": created_date,
            "Rank": rank_str,
            "Pathway ID": r.get("pathway_id", "—"),
            "Title": r.get("pathway_title", "—"),
            "Type": str(r.get("pathway_type", "—")).upper(),
            "MCDA Score": score_str,
        })
    df_recs = pd.DataFrame(rec_rows)
    st.dataframe(df_recs, use_container_width=True, hide_index=True)
else:
    empty_state("No recommendation records found.", icon="🎯")

st.divider()
st.caption("📌 **Personalized Data Isolation:** All displayed history is filtered exclusively for your user profile in accordance with Row Level Security (RLS).")
