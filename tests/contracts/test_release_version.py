"""Ensure user-facing version, API and CI tests stay on the same release."""
from hashlib import sha256
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
VERSION = "1.1.0"

def text(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")

def test_version_identifiers_are_consistent():
    assert "VERSION = '1.1.0'" in text("companion/server.py")
    assert "version: '1.1.0'" in text("static/js/application.js")
    assert "Match Center · Player Edition · v1.1.0" in text("static/index.html")
    assert "styles.css?v=1.1.0" in text("static/index.html")
    assert "version='1.1.0'" in text("installer/install.ps1")
    assert "json.loads(data).get('version') == '1.1.0'" in text("tests/docker/smoke.py")
    assert "v1.1.0" in text("static/preview.html")
    assert "version.textContent = 'v1.1.0'" in text("static/js/experience.js")
    registry = json.loads(text("static/locales/languages.json"))
    for language in registry['languages']:
        catalog = json.loads(text('static/locales/' + language['file']))
        assert VERSION in catalog['installer.intro'], language['code']
        assert '1.0.0' not in catalog['installer.intro'], language['code']

def test_license_and_translation_match_the_supplied_v1_candidates():
    # Normalize checkout line endings without rewriting the approved candidate.
    licenseText = text("LICENSE")
    translationText = text("docs/legal/LICENSE.fr.md")
    assert sha256(licenseText.encode("utf-8")).hexdigest() == (
        "c1eb5a47a70589cebbf7fb75fa6d65de4e39aecb003a3f56df613142e27bf283"
    )
    assert sha256(translationText.encode("utf-8")).hexdigest() == (
        "135455ac02c999808efb39c5a2f152fad588e4d01f83519204ef63e78abc3d6b"
    )


def test_license_documentation_preserves_scope_and_adoption_boundaries():
    readme = text("README.md")
    licensing = text("docs/legal/licensing.md")
    contributions = text("CONTRIBUTING.md")
    assert "source-available" in readme
    assert "not OSI-approved open source" in readme
    assert "expressly authorized merge" in readme
    assert "open PR is not adoption" in licensing
    assert "No prebuilt Docker image is published" in licensing
    assert "explicit permission" in contributions
    assert "Contributors retain ownership" in contributions
    assert "no general permission for future relicensing" in contributions
    assert "MIT License" not in text("LICENSE")


def test_disclosure_survives_release():
    readme = text("README.md")
    assert "ChatGPT" in readme and "personal project" in readme.lower()
    assert "FACEIT" in readme and "not affiliated" in readme.lower()
    assert (ROOT / "docs" / "releases" / "release-notes-1.1.0.md").exists()
