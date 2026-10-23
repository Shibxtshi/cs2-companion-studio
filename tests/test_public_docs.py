"""The project must not quietly drop its AI transparency or public safety docs."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def test_prominent_personal_ai_disclosure():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Personal" in readme[:550]
    assert "ChatGPT" in readme[:800] and "OpenAI" in readme[:800]
    assert "not" in readme.lower() and "faceit" in readme.lower()
    assert "substantial" in (ROOT / "AI_DISCLOSURE.md").read_text(encoding="utf-8").lower()

def test_required_public_community_files():
    for name in ("README.md", "AI_DISCLOSURE.md", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md",
                 "SECURITY.md", "SUPPORT.md", "LICENSE", "CHANGELOG.md",
                 ".github/ISSUE_TEMPLATE/bug_report.yml",
                 ".github/ISSUE_TEMPLATE/feature_request.yml",
                 ".github/pull_request_template.md",
                 "docs/PUBLIC_RELEASE_CHECKLIST.md", "docs/README.fr.md"):
        assert (ROOT/name).is_file(), name

def test_transparent_in_app_help():
    assert "ChatGPT (OpenAI)" in (ROOT/"static/index.html").read_text(encoding="utf-8")
    assert "Personal project developed with substantial help" in (ROOT/"static/i18n.js").read_text(encoding="utf-8")
