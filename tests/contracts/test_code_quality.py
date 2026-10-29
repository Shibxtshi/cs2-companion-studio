"""Prevent regressions in the first code-quality refactor."""
import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


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
        "companion/server.py": {
            "old_map", "old_round", "incoming_map", "incoming_player",
            "fresh_match", "changed_round", "prev_health", "prev_kills",
            "new_bomb_state", "session_id", "raw_msg",
        },
        "companion/gsi_lifecycle.py": {"half_start", "half_end", "team_data"},
        "companion/profile_store.py": {"widgets_raw", "next_rev"},
        "scripts/check_secrets.py": {"repo_root"},
        "tests/docker/smoke.py": {"last_error"},
    }
    for path, retired_names in previous_locals.items():
        parsed = ast.parse(read(path), filename=path)
        identifiers = {node.id for node in ast.walk(parsed) if isinstance(node, ast.Name)}
        assert identifiers.isdisjoint(retired_names), path


def test_snapshot_and_countdown_skip_idle_rendering():
    backend = read("companion/server.py")
    frontend = read("static/js/studio.js")
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
    from html.parser import HTMLParser

    class Scripts(HTMLParser):
        def __init__(self):
            super().__init__()
            self.sources = []

        def handle_starttag(self, tag, attrs):
            if tag == 'script':
                source = dict(attrs).get('src', '').split('?')[0]
                self.sources.append(source)

    parser = Scripts()
    parser.feed(read('static/index.html'))
    required = ['/static/js/i18n.js', '/static/js/widgets.js', '/static/js/profile-sync.js', '/static/js/reconnect.js', '/static/js/display-format.js', '/static/js/widget-renderer.js', '/static/js/dashboard-client.js', '/static/js/studio.js']
    assert [source for source in parser.sources if source in required] == required


def test_frontend_widget_kinds_match_server_validation():
    import json
    import shutil
    import subprocess
    import pytest
    from companion.profile_store import PROFILE_KINDS

    node = shutil.which('node')
    if not node:
        pytest.skip('Node.js is required to execute the widget catalog; CI checks it')
    script = 'global.window={};require("./static/js/widgets.js");console.log(JSON.stringify(Object.keys(window.CS2WidgetCatalog)))'
    result = subprocess.run([node, '-e', script], cwd=ROOT, capture_output=True, text=True, check=True)
    assert set(json.loads(result.stdout)) == PROFILE_KINDS


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
    assert "tests/standalone tests/browser tests/docker tests/windows" in config
    assert (ROOT / "tests" / "browser" / "legacy" / "test_e1_browser.py").exists()


def test_connection_states_do_not_depend_on_localized_messages():
    studio = read("static/js/studio.js")
    experience = read("static/js/experience.js")
    assert "detail:{message:msg,kind,code}" in studio
    assert "setStatus('Connexion…','','connecting')" in studio
    assert "['connecting','error','lost'].includes(event.detail?.code)" in experience
    assert "socketState = event.detail.code" in experience
    assert "if(/Connexion…/.test(msg))" not in experience
