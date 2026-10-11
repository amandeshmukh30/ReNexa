
import os
import streamlit as st
from .theme import apply_theme


def login_gate():
    if st.session_state.get("renexa_authenticated", False):
        return

    apply_theme()

    left, right = st.columns([1.05, 1], gap="large")

    with left:
        st.markdown(
            '<div class="rx-login-art">'
            '<div>'
            '<div style="font-size:4rem">◈</div>'
            '<h1>Give Waste<br>Its Next Life.</h1>'
            '<p>Smarter recovery starts with a better decision.</p>'
            '</div>'
            '<div>ReNexa · AI-Powered Waste Recovery Intelligence</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with right:
        st.markdown("### Welcome to ReNexa")
        st.caption("Sign in to continue to your workspace.")

        with st.form("renexa_login"):
            user = st.text_input(
                "Username or email",
                placeholder="Enter username",
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter password",
            )
            st.checkbox("Keep me signed in", key="rx_remember")
            submit = st.form_submit_button(
                "Sign in",
                use_container_width=True,
            )

        if submit:
            demo = os.getenv("RENEXA_DEMO_LOGIN", "1") != "0"
            expected_user = os.getenv("RENEXA_LOGIN_USER", "")
            expected_password = os.getenv("RENEXA_LOGIN_PASSWORD", "")

            if (
                (demo and user.strip() and password)
                or (
                    expected_user
                    and expected_password
                    and user == expected_user
                    and password == expected_password
                )
            ):
                st.session_state["renexa_authenticated"] = True
                st.session_state["renexa_username"] = user.strip()
                st.rerun()
            else:
                st.error(
                    "Sign-in failed. Check credentials or configure "
                    "login environment variables."
                )

        st.markdown(
            '<div class="rx-footer">'
            'ReNexa · Give Waste Its Next Life.'
            '</div>',
            unsafe_allow_html=True,
        )

    st.stop()


def logout():
    st.session_state.pop("renexa_authenticated", None)
    st.session_state.pop("renexa_username", None)
    st.rerun()
