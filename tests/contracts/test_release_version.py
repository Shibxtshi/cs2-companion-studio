"""Ensure user-facing version, API and CI tests stay on the same release."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
VERSION = "1.0.0"

def text(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")

def test_version_identifiers_are_consistent():
    assert "VERSION = '1.0.0'" in text("companion/server.py")
    assert "const VERSION='1.0.0'" in text("static/js/studio.js")
    assert "Match Center · Player Edition · v1.0.0" in text("static/index.html")
    assert "styles.css?v=1.0.0" in text("static/index.html")
    assert "version='1.0.0'" in text("installer/install.ps1")
    assert "json.loads(data).get('version') == '1.0.0'" in text("tests/docker/smoke.py")

def test_licensing_draft_does_not_misrepresent_mit_or_open_source():
    license_text = text("LICENSE")
    readme = text("README.md")
    assert "DRAFT v0.2" in license_text
    assert "NOT YET APPROVED OR EFFECTIVE" in license_text
    assert "Prohibition on selling the Software" in license_text
    assert "professional/business purposes" in license_text
    assert "Private and purely internal modifications need not be published" in license_text
    assert "paid coaching" in license_text
    assert "corresponding source code" in license_text
    assert "MIT License" not in license_text
    assert "source-available" in readme
    assert "not OSI-approved open source" in readme

def test_disclosure_survives_release():
    readme = text("README.md")
    assert "ChatGPT" in readme and "personal project" in readme.lower()
    assert "FACEIT" in readme and "not affiliated" in readme.lower()
    assert (ROOT / "docs" / "releases" / "release-notes-1.0.0.md").exists()
