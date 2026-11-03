"""Check licensed local assets and the lightweight theme boundary."""
import hashlib
import json
from pathlib import Path
import re

from companion.profile_contracts import THEMES

ROOT = Path(__file__).resolve().parents[2]


def test_local_font_provenance_and_license_notices():
    folder = ROOT / 'static' / 'fonts'
    manifest = json.loads((folder / 'sources.json').read_text(encoding='utf-8'))
    assert len(manifest) == 3
    for entry in manifest:
        content = (folder / entry['file']).read_bytes()
        assert content.startswith(b'wOF2')
        assert hashlib.sha256(content).hexdigest() == entry['sha256']
        assert len(content) == entry['bytes']
        assert entry['source'].startswith('https://fonts.gstatic.com/')
    for name in ('inter', 'barlow-condensed'):
        text = (folder / (name + '-OFL.txt')).read_text(encoding='utf-8')
        assert 'SIL OPEN FONT LICENSE Version 1.1' in text
        assert 'Copyright' in text


def test_theme_assets_are_same_origin_and_palettes_are_complete():
    html = (ROOT / 'static' / 'index.html').read_text(encoding='utf-8')
    assert 'data-theme="tactical-blue"' in html
    links = re.findall(r'<link[^>]+href="([^"]+)"', html)
    assert all(link.startswith('/static/') for link in links)
    css = (ROOT / 'static' / 'css' / 'themes.css').read_text(encoding='utf-8')
    palettes = re.findall(r'\[data-theme="([a-z-]+)"\] \{([^}]+)', css)
    assert {name for name, _ in palettes} == set(THEMES)
    properties = [set(re.findall(r'--ccs-([a-z-]+):', block)) for _, block in palettes]
    assert all(keys == properties[0] for keys in properties)
    assert len(properties[0]) == 16
    styles = (ROOT / 'static' / 'css' / 'styles.css').read_text(encoding='utf-8')
    assert not re.search(r'#[0-9a-fA-F]{3,8}\b', styles)
    assert 'var(--profile-accent,var(--ccs-accent))' in (
        ROOT / 'static' / 'css' / 'tokens.css').read_text(encoding='utf-8')


def test_identity_svg_contains_no_active_or_external_content():
    from xml.etree import ElementTree
    for name in ('repere.svg', 'ccs-logo.svg'):
        root = ElementTree.parse(ROOT / 'static' / 'branding' / name).getroot()
        assert root.attrib.get('viewBox')
        for element in root.iter():
            assert element.tag.rsplit('}', 1)[-1] in {'svg', 'title', 'path'}
            assert not any(key.lower().startswith('on') or key.endswith('href')
                           for key in element.attrib)


def test_original_palette_values_are_unchanged():
    css = (ROOT / 'static/css/themes.css').read_text('utf8')
    palettes = dict(re.findall(r'\[data-theme="([a-z-]+)"\] \{([^}]+)', css))
    approved = {
        "tactical-blue": "d13bf828a6c314574cd215a1b8fe27c9b4206190bce41eedc747f8fb6187e3e0",
        "competitive-red": "27c957f14feb47b451134153902c8530e962c351836828d5197b07d6f955f12c",
        "performance-green": "c41a25e5cf02495cf5e34b7686553f6b741286b95c9f5dcf40a8f7aa4d358b90",
        "creator-purple": "f734b2f789a4c3de10bc286aba145ae65c4fd14b2cf8ff2cb984a256148db260"
}
    for name, expected in approved.items():
        assert hashlib.sha256(palettes[name].encode()).hexdigest() == expected
