"""Statische regressietests voor Sprint 10E."""

import ast
from pathlib import Path


APP_SOURCE = Path(__file__).parents[1].joinpath("app.py").read_text(
    encoding="utf-8"
)


def test_today_remains_the_first_page() -> None:
    tree = ast.parse(APP_SOURCE)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "PAGES":
                    pages = ast.literal_eval(node.value)
                    assert pages[0] == "Vandaag"
                    return
    raise AssertionError("PAGES niet gevonden")


def test_today_reuses_the_existing_advisor() -> None:
    assert "def render_today_advisor()" in APP_SOURCE
    assert "answer_question(question, make_engine(), settings)" in APP_SOURCE
    assert "Open volledige AI-assistent" in APP_SOURCE


def test_quick_actions_only_open_existing_modules() -> None:
    for label in ("＋ Bitcoin", "＋ ETF", "＋ Uitgave", "↗ Scenario"):
        assert label in APP_SOURCE
    assert "Gewicht invoeren" not in APP_SOURCE
    assert "Notitie maken" not in APP_SOURCE
