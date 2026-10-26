"""Ensure user-facing version, API and CI tests stay on the same release."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.0.0"

def text(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")

def test_version_identifiers_are_consistent():
    assert "VERSION = '1.0.0'" in text("app.py")
    assert "const VERSION='1.0.0'" in text("static/studio.js")
    assert "Dashboard Studio · v1.0.0" in text("static/index.html")
    assert "styles.css?v=1.0.0" in text("static/index.html")
    assert "version='1.0.0'" in text("installer/install.ps1")
    assert "json.loads(data).get('version') == '1.0.0'" in text("scripts/docker_smoke.py")

def test_disclosure_survives_release():
    readme = text("README.md")
    assert "ChatGPT" in readme and "personal project" in readme.lower()
    assert "FACEIT" in readme and "not affiliated" in readme.lower()
    assert (ROOT / "docs" / "RELEASE_NOTES_1.0.0.md").exists()
