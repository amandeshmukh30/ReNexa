
import html
import streamlit as st

from .theme import apply_theme, theme_control
from .auth import logout


NAV = [
    ("Home", "⌂", "main.py"),
    ("Scan Waste", "▣", "pages/1_Scan_Waste.py"),
    ("Results", "▤", "pages/2_Results.py"),
    ("Pathways", "⌘", "pages/3_Recovery.py"),
    ("Constraints", "◇", "pages/4_Constraints.py"),
    ("Recommendations", "↗", "pages/5_Recommendations.py"),
    ("Execution", "✓", "pages/6_Execution.py"),
    ("Tutorials", "▷", "pages/6_Tutorials.py"),
    ("History", "◷", "pages/7_History.py"),
    ("Outcome", "▥", "pages/7_Outcome.py"),
    ("Impact", "◒", "pages/8_Impact.py"),
    ("Benchmark", "▤", "pages/9_Research_Benchmark.py"),
]


def render_shell(active="Home"):
    apply_theme()

    st.sidebar.markdown(
        """
        <div style="padding:12px 4px 20px 4px;">
            <div style="font-size:28px;font-weight:800;">↗ ReNexa</div>
            <div style="font-size:12px;opacity:0.7;">
                Give Waste Its Next Life.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for label, icon, target in NAV:
        if label == active:
            st.sidebar.markdown(
                f"""
                <div style="
                    padding:10px 12px;
                    margin:4px 0;
                    border-radius:10px;
                    font-weight:700;
                    background:rgba(80,160,120,0.18);
                ">
                    {icon} &nbsp; {html.escape(label)}
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.sidebar.page_link(
                target,
                label=f"{icon}  {label}",
                use_container_width=True,
            )

    theme_control()

    if st.sidebar.button("Sign out", use_container_width=True):
        logout()

    st.sidebar.caption("AI-Powered Waste Recovery Intelligence")


def render_header(title, subtitle=""):
    st.title(title)

    if subtitle:
        st.caption(subtitle)


def render_footer():
    st.divider()
    st.caption("ReNexa — Give Waste Its Next Life.")
