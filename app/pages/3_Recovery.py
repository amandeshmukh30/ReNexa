
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)) if str(ROOT) not in sys.path else None

from app.ui import login_gate, render_shell
from app.ui.feature_hub import render_feature_page

login_gate()
render_shell("Pathways")
render_feature_page("Pathways")
