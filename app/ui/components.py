
import html
import streamlit as st


def section(title, subtitle="", icon=""):
    sub = (
        f'<div class="rx-copy">{html.escape(subtitle)}</div>'
        if subtitle
        else ""
    )

    st.markdown(
        f"""
        <div class="rx-section">
            <span style="
                color:var(--rx-primary);
                font-size:1.3rem">
                {html.escape(icon)}
            </span>
            <div>
                <h2>{html.escape(title)}</h2>
                {sub}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric(label, value, caption="", icon=""):
    st.markdown(
        f"""
        <div class="rx-card">
            <div class="rx-icon">{html.escape(icon)}</div>
            <div class="rx-copy">{html.escape(label)}</div>
            <div style="
                font-size:1.8rem;
                font-weight:800;
                color:var(--rx-primary);
                margin:.15rem 0">
                {html.escape(str(value))}
            </div>
            <div class="rx-copy">{html.escape(caption)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def card(
    title,
    description,
    icon="",
    target=None,
    link_label="Open",
):
    st.markdown(
        f"""
        <div class="rx-card">
            <div class="rx-icon">{html.escape(icon)}</div>
            <div class="rx-card-title">{html.escape(title)}</div>
            <div class="rx-copy">{html.escape(description)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if target:
        st.page_link(
            target,
            label=f"{link_label} →",
            use_container_width=True,
        )


def note(title, description, kind="info"):
    colors = {
        "info": "#DDEEFF",
        "warning": "#FFF1D6",
        "success": "#DDF7E7",
        "danger": "#FFE4E4",
    }

    background = colors.get(kind, colors["info"])

    st.markdown(
        f"""
        <div style="
            padding:1rem;
            border-radius:12px;
            background:{background};
            margin:.5rem 0">
            <b>{html.escape(title)}</b>
            <div>{html.escape(description)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
