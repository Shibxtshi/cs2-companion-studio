"""Check licensed local assets and the lightweight theme boundary."""
import hashlib
import json
from pathlib import Path
import re

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
    assert {name for name, _ in palettes} == {
        'tactical-blue', 'competitive-red', 'performance-green', 'creator-purple'}
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
