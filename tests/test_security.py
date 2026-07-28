"""Tests voor de toegangsconfiguratie van GeertOS."""

from __future__ import annotations

import security


def test_access_control_disabled_without_configuration(monkeypatch) -> None:
    monkeypatch.delenv("GEERTOS_ACCESS_CODE", raising=False)
    monkeypatch.delenv("GEERTOS_ACCESS_CODE_HASH", raising=False)
    monkeypatch.setattr(security.st, "secrets", {})

    assert security.access_control_enabled() is False


def test_access_control_enabled_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("GEERTOS_ACCESS_CODE", "een-geheime-code")
    monkeypatch.setattr(security.st, "secrets", {})

    assert security.access_control_enabled() is True


def test_hashed_access_code_can_be_verified(monkeypatch) -> None:
    value = security.make_access_code_hash("een-sterke-code")
    monkeypatch.delenv("GEERTOS_ACCESS_CODE", raising=False)
    monkeypatch.setenv("GEERTOS_ACCESS_CODE_HASH", value)
    monkeypatch.setattr(security.st, "secrets", {})

    assert security.access_control_enabled() is True
    assert security._verify_code("een-sterke-code") is True
    assert security._verify_code("verkeerd") is False


def test_short_access_code_cannot_be_hashed() -> None:
    import pytest

    with pytest.raises(ValueError, match="minimaal 10"):
        security.make_access_code_hash("kort")
