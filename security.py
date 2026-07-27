"""Toegangsbeveiliging voor lokaal en online gebruik van GeertOS."""

from __future__ import annotations

import hashlib
import hmac
import os

import streamlit as st


def _configured_access_code() -> str:
    """Lees de toegangscode uit Streamlit secrets of de omgeving."""
    try:
        value = st.secrets.get("GEERTOS_ACCESS_CODE", "")
    except (FileNotFoundError, KeyError):
        value = ""
    return str(value or os.getenv("GEERTOS_ACCESS_CODE", "")).strip()


def access_control_enabled() -> bool:
    """Geef aan of voor deze installatie een toegangscode is ingesteld."""
    return bool(_configured_access_code())


def require_access() -> None:
    """Stop de app totdat de juiste toegangscode is ingevoerd."""
    configured_code = _configured_access_code()
    if not configured_code:
        return

    if st.session_state.get("geertos_authenticated", False):
        with st.sidebar:
            if st.button("GeertOS vergrendelen", use_container_width=True):
                st.session_state["geertos_authenticated"] = False
                st.rerun()
        return

    st.title("🔒 GeertOS")
    st.caption("Deze persoonlijke cockpit is beveiligd.")
    with st.form("geertos_login", clear_on_submit=True):
        entered_code = st.text_input(
            "Toegangscode",
            type="password",
            autocomplete="current-password",
        )
        submitted = st.form_submit_button(
            "Open GeertOS",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        entered_hash = hashlib.sha256(entered_code.encode("utf-8")).digest()
        configured_hash = hashlib.sha256(configured_code.encode("utf-8")).digest()
        if hmac.compare_digest(entered_hash, configured_hash):
            st.session_state["geertos_authenticated"] = True
            st.rerun()
        st.error("De toegangscode is niet juist.")

    st.stop()
