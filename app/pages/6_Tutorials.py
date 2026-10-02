"""
ReNexa — Tutorials & Knowledge Base
===================================
Reference-inspired DIY recovery guides and verified tutorials catalog.
Phase 7/8: Searchable Knowledge Base and Recipe Guides.
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
from services.recovery_service import get_all_pathways

# ── Page config ───────────────────────────────────────────────────────────
configure_page(title="Tutorials — ReNexa", icon="📚")

# ── Sidebar ───────────────────────────────────────────────────────────────
render_sidebar("pages/6_Tutorials.py")

# ── Header ────────────────────────────────────────────────────────────────
page_header(
    "📚 Learn How to Recover",
    "Explore verified step-by-step DIY recovery guides, upcycling tutorials, and repair techniques.",
)

# ── Load actual pathways ──────────────────────────────────────────────────
all_pathways = get_all_pathways()

# ── Search & Filter Controls ──────────────────────────────────────────────
col_search, col_cat = st.columns([3, 2])
with col_search:
    search_query = st.text_input("🔍 Search Tutorials & Guides", placeholder="e.g. Planter, insulation, compost, patchwork...", key="tut_search")

with col_cat:
    CATEGORY_OPTIONS = ["All", "Repair", "Reuse", "Upcycling", "Recycling"]
    selected_cat = st.selectbox("Category Filter", CATEGORY_OPTIONS, index=0)

# Filter pathways
filtered = []
for p in all_pathways:
    ptype = p.get("pathway_type", "").lower()
    title = p.get("title", "").lower()
    desc = p.get("description", "").lower()
    mat = p.get("input_material", "").lower()

    if selected_cat != "All" and ptype != selected_cat.lower().replace("upcycling", "upcycle"):
        continue

    if search_query:
        q = search_query.lower().strip()
        if q not in title and q not in desc and q not in mat:
            continue

    filtered.append(p)

# ── Summary metrics ───────────────────────────────────────────────────────
col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    metric_card("Total Recipes", len(all_pathways), icon="📖")
with col_m2:
    metric_card("Matching Guides", len(filtered), icon="🔍")
with col_m3:
    metric_card("Material Types", len(set(p.get("input_material", "") for p in all_pathways)), icon="♻️")

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

# ── Display Tutorial Cards ────────────────────────────────────────────────
if filtered:
    st.markdown(f"### 📋 Verified Recovery Tutorials ({len(filtered)})")
    
    # 2-column responsive layout
    col1, col2 = st.columns(2)
    for idx, p in enumerate(filtered):
        target_col = col1 if (idx % 2 == 0) else col2
        ptype = p.get("pathway_type", "reuse").lower()
        badge_type = "allow" if ptype == "repair" else ("warn" if ptype == "recycle" else "neutral")
        
        tools = p.get("tools_required", [])
        tools_str = ", ".join(tools) if isinstance(tools, list) and tools else "None required"
        
        with target_col:
            st.markdown(
                f"""
                <div class="renexa-card" style="margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
                        <span class="renexa-badge renexa-badge-{badge_type}">{ptype.upper()}</span>
                        <span style="color: #A9C3B8; font-size: 0.85rem;">⏱️ {p.get('time_required', '15 mins')}</span>
                    </div>
                    <h3 style="margin: 0 0 8px 0; color: #F5FFF8; font-size: 1.15rem;">{p.get('title')}</h3>
                    <p style="color: #A9C3B8; font-size: 0.9rem; margin-bottom: 12px; line-height: 1.4;">
                        {p.get('description', '')}
                    </p>
                    <div style="background: #011B18; border-radius: 10px; padding: 10px 14px; font-size: 0.85rem; color: #A9C3B8; margin-bottom: 14px;">
                        <div>Material: <strong style="color:#F5FFF8;">{p.get('input_material', '').capitalize()}</strong></div>
                        <div>Skill: <strong style="color:#F5FFF8;">{p.get('skill_level', 'Beginner')}</strong> | Budget: <strong style="color:#9FEA45;">₹{p.get('budget', 0)}</strong></div>
                        <div>Tools: <span style="color:#F5FFF8;">{tools_str}</span></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(f"📖 Start Guide: {p.get('title')[:25]}...", key=f"btn_tut_{p.get('pathway_id')}", use_container_width=True):
                st.session_state["selected_pathway_id"] = p.get("pathway_id")
                st.switch_page("pages/6_Execution.py")
else:
    empty_state(
        f"No recovery tutorials match '{search_query}'. Try a broader keyword or select 'All' categories.",
        icon="🔍",
    )

st.divider()
st.caption("📌 **Curated Knowledge:** All tutorials are mapped to grounded Phase 4 recovery pathways with verified safety constraints.")
