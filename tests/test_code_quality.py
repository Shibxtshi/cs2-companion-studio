"""Prevent regressions in the first code-quality refactor."""
import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_example_configuration_comments_are_english():
    comments = [
        line.strip() for line in read(".env.example").splitlines()
        if line.lstrip().startswith("#")
    ]
    assert len(comments) >= 3
    assert all(line.isascii() for line in comments)
    generator = read("scripts/generate_config.py")
    assert "# Local private configuration: never publish to GitHub." in generator
    assert "# Localhost by default." in generator


def test_refactored_python_locals_use_camel_case():
    previous_locals = {
        "app.py": {
            "old_map", "old_round", "incoming_map", "incoming_player",
            "fresh_match", "changed_round", "prev_health", "prev_kills",
            "new_bomb_state", "session_id", "raw_msg",
        },
        "gsi_lifecycle.py": {"half_start", "half_end", "team_data"},
        "profile_store.py": {"widgets_raw", "next_rev"},
        "scripts/check_secrets.py": {"repo_root"},
        "scripts/docker_smoke.py": {"last_error"},
    }
    for path, retired_names in previous_locals.items():
        parsed = ast.parse(read(path), filename=path)
        identifiers = {node.id for node in ast.walk(parsed) if isinstance(node, ast.Name)}
        assert identifiers.isdisjoint(retired_names), path


def test_snapshot_and_countdown_skip_idle_rendering():
    backend = read("app.py")
    frontend = read("static/studio.js")
    assert "async def send_state() -> None:\n    # Do not serialize" in backend
    assert "if not connected:\n        return" in backend
    assert "if(!document.hidden&&last?.bomb_timer?.status==='active')paintBomb();" in frontend


def test_historical_docs_are_grouped_without_dropping_content():
    history = ROOT / "docs" / "history"
    for name in (
        "BASELINE.md",
        "CHANGELOG_FONCTIONNEL.md",
        "FIX_V1P_F1.md",
        "GITHUB_SETUP.md",
        "QA_V1P_F.md",
    ):
        assert (history / name).is_file()
        assert not (ROOT / "docs" / name).exists()
    assert "docs/history/CHANGELOG_FONCTIONNEL.md" in read("CHANGELOG.md")


def test_widget_catalog_module_and_script_load_order():
    page = read("static/index.html")
    assert page.index("i18n.js?v=1.0.0") < page.index("widgets.js?v=1.0.0")
    assert page.index("widgets.js?v=1.0.0") < page.index("studio.js?v=1.0.0")
    catalog = read("static/widgets.js")
    script = read("static/studio.js")
    assert catalog.count("size:") == 29
    assert "window.CS2WidgetCatalog=Object.freeze(" in catalog
    assert "const W=window.CS2WidgetCatalog" in script
    assert "const W={" not in script


def test_standalone_suites_are_isolated_and_grouped():
    runner = read("scripts/run_checks.py")
    workflow = read(".github/workflows/checks.yml")
    config = read("pytest.ini")
    suites = (
        "test_economy", "test_timer", "test_studio", "test_security",
        "test_lifecycle", "test_profiles_and_diagnostics",
    )
    for suite in suites:
        module = f"tests.standalone.{suite}"
        assert (ROOT / "tests" / "standalone" / f"{suite}.py").exists()
        assert not (ROOT / f"{suite}.py").exists()
        assert module in runner
        assert suite in workflow
    assert "python -m" in workflow
    assert "tests/standalone tests/legacy_browser" in config
    assert (ROOT / "tests" / "legacy_browser" / "test_e1_browser.py").exists()
