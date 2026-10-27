"""Repository moves must preserve launch contracts, assets and document navigation."""
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_app_entry_point_keeps_one_server_and_project_root(tmp_path):
    env = dict(os.environ, PYTHONPATH=str(ROOT), PROFILE_DATA_DIR=str(tmp_path / 'data'),
               DIAGNOSTICS_DIR=str(tmp_path / 'logs'), GSI_TOKEN='synthetic-layout-token',
               DASHBOARD_PIN='synthetic-layout-pin')
    script = (
        "import sys, companion; assert 'companion.server' not in sys.modules; "
        "import app; from companion import server; "
        "from pathlib import Path; assert app is server; "
        "assert server.ROOT == Path(sys.argv[1])"
    )
    subprocess.run([sys.executable, '-c', script, str(ROOT)], cwd=tmp_path, env=env, check=True)
    assert (tmp_path / 'data' / 'profiles.json').is_file()
    assert not (ROOT / 'companion' / 'data').exists()


@pytest.mark.parametrize('name,canonical', [
    ('styles.css', 'css/styles.css'),
    ('i18n.js', 'js/i18n.js'),
    ('widgets.js', 'js/widgets.js'),
    ('profile-sync.js', 'js/profile-sync.js'),
    ('studio.js', 'js/studio.js'),
    ('experience.js', 'js/experience.js'),
])
def test_legacy_asset_urls_keep_identical_content_and_headers(name, canonical):
    from fastapi.testclient import TestClient
    import app

    with TestClient(app.app) as client:
        legacy = client.get('/static/' + name)
        current = client.get('/static/' + canonical)
        head = client.head('/static/' + name)
        partial = client.get('/static/' + name, headers={'Range': 'bytes=0-15'})
        unchanged = client.get('/static/' + name, headers={'If-None-Match': legacy.headers['etag']})
    assert legacy.status_code == current.status_code == head.status_code == 200
    assert not head.content
    assert partial.status_code == 206 and partial.content == legacy.content[:16]
    assert unchanged.status_code == 304
    assert legacy.content == current.content == (ROOT / 'static' / canonical).read_bytes()
    assert legacy.headers['content-type'] == current.headers['content-type']
    assert "script-src 'self'" in legacy.headers['content-security-policy']
    assert legacy.headers['cache-control'] == 'no-store'


def test_document_links_resolve_after_moves():
    files = list(ROOT.glob('*.md')) + list((ROOT / 'docs').rglob('*.md'))
    files += [ROOT / 'scripts' / 'README.md', ROOT / 'tests' / 'README.md']
    for source in files:
        for target in re.findall(r'!?\[[^\]]*\]\(([^\s)]+)\)', source.read_text('utf-8-sig')):
            if re.match(r'^(?:[a-z]+:|#|/)', target, re.I):
                continue
            relative = re.split(r'[?#]', target, maxsplit=1)[0]
            assert (source.parent / relative).exists(), (source.relative_to(ROOT), target)
