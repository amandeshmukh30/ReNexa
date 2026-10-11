
import sys
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    st.set_page_config(
        page_title="ReNexa | Waste Profile Results",
        page_icon="♻",
        layout="wide",
        initial_sidebar_state="expanded",
    )
except Exception:
    pass

from app.ui import login_gate, render_shell
from app.ui.feature_hub import render_feature_page

login_gate()
render_shell("Results")
render_feature_page("Results")
