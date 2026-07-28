"""Statische kwaliteitscontroles voor de Sprint 10D-interface."""

from styles import css


def test_premium_style_supports_mobile_and_accessibility() -> None:
    stylesheet = css(False)

    assert "@media (max-width: 700px)" in stylesheet
    assert "@media (prefers-reduced-motion: reduce)" in stylesheet
    assert "overflow-x: auto" in stylesheet
    assert "focus-visible" in stylesheet


def test_primary_buttons_keep_the_geertos_colour() -> None:
    stylesheet = css(False)

    assert '[data-testid="stBaseButton-primary"]' in stylesheet
    assert "background: var(--pv-green) !important" in stylesheet


def test_dark_and_light_themes_remain_distinct() -> None:
    assert css(False) != css(True)
