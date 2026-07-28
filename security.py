"""Toegangsbeveiliging voor lokaal en online gebruik van GeertOS."""

from __future__ import annotations

import hashlib
import hmac
import os
import time

import streamlit as st


MAX_ATTEMPTS = 5
LOCK_SECONDS = 300
SESSION_TIMEOUT_SECONDS = 30 * 60


def _secret(name: str) -> str:
    try:
        value = st.secrets.get(name, "")
    except (FileNotFoundError, KeyError):
        value = ""
    return str(value or os.getenv(name, "")).strip()


def _configured_access_code() -> str:
    """Lees de oude toegangscode voor achterwaartse compatibiliteit."""
    return _secret("GEERTOS_ACCESS_CODE")


def _configured_access_hash() -> str:
    """Lees bij voorkeur een niet-terugleesbare toegangscodehash."""
    return _secret("GEERTOS_ACCESS_CODE_HASH")


def make_access_code_hash(code: str, *, iterations: int = 310_000) -> str:
    """Maak een PBKDF2-hash die veilig als Streamlit secret kan worden bewaard."""
    if len(code) < 10:
        raise ValueError("Gebruik een toegangscode van minimaal 10 tekens.")
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", code.encode("utf-8"), salt, iterations
    )
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


def _verify_code(entered_code: str) -> bool:
    configured_hash = _configured_access_hash()
    if configured_hash:
        try:
            algorithm, iterations, salt, expected = configured_hash.split("$", 3)
            if algorithm != "pbkdf2_sha256":
                return False
            actual = hashlib.pbkdf2_hmac(
                "sha256",
                entered_code.encode("utf-8"),
                bytes.fromhex(salt),
                int(iterations),
            )
            return hmac.compare_digest(actual, bytes.fromhex(expected))
        except (ValueError, TypeError):
            return False

    entered_hash = hashlib.sha256(entered_code.encode("utf-8")).digest()
    configured_hash = hashlib.sha256(
        _configured_access_code().encode("utf-8")
    ).digest()
    return hmac.compare_digest(entered_hash, configured_hash)


def access_control_enabled() -> bool:
    """Geef aan of voor deze installatie een toegangscode is ingesteld."""
    return bool(_configured_access_hash() or _configured_access_code())


def require_access() -> None:
    """Beveilig toegang, begrens pogingen en vergrendel inactieve sessies."""
    if not access_control_enabled():
        return

    now = time.time()
    if st.session_state.get("geertos_authenticated", False):
        last_activity = float(st.session_state.get("geertos_last_activity", now))
        if now - last_activity > SESSION_TIMEOUT_SECONDS:
            st.session_state["geertos_authenticated"] = False
            st.session_state["geertos_login_notice"] = (
                "GeertOS is na 30 minuten zonder gebruik automatisch vergrendeld."
            )
            st.rerun()
        st.session_state["geertos_last_activity"] = now
        with st.sidebar:
            if st.button("GeertOS vergrendelen", use_container_width=True):
                st.session_state["geertos_authenticated"] = False
                st.rerun()
        return

    locked_until = float(st.session_state.get("geertos_locked_until", 0.0))
    st.title("🔒 GeertOS")
    st.caption("Deze persoonlijke cockpit is beveiligd.")
    if notice := st.session_state.pop("geertos_login_notice", None):
        st.warning(notice)
    if locked_until > now:
        remaining = max(1, int((locked_until - now + 59) // 60))
        unit = "minuut" if remaining == 1 else "minuten"
        st.error(
            f"Te veel mislukte pogingen. Probeer het over {remaining} {unit} opnieuw."
        )
        st.stop()

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
        if _verify_code(entered_code):
            st.session_state["geertos_authenticated"] = True
            st.session_state["geertos_last_activity"] = now
            st.session_state["geertos_failed_attempts"] = 0
            st.rerun()
        attempts = int(st.session_state.get("geertos_failed_attempts", 0)) + 1
        st.session_state["geertos_failed_attempts"] = attempts
        if attempts >= MAX_ATTEMPTS:
            st.session_state["geertos_locked_until"] = now + LOCK_SECONDS
            st.session_state["geertos_failed_attempts"] = 0
            st.error("GeertOS is na vijf mislukte pogingen vijf minuten vergrendeld.")
        else:
            st.error(
                f"De toegangscode is niet juist. Nog {MAX_ATTEMPTS - attempts} "
                "pogingen voordat GeertOS tijdelijk wordt vergrendeld."
            )

    st.stop()
