"""Repository moves must preserve launch contracts, assets and document navigation."""
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_canonical_server_keeps_project_root(tmp_path):
    env = dict(os.environ, PYTHONPATH=str(ROOT), PROFILE_DATA_DIR=str(tmp_path / 'data'),
               DIAGNOSTICS_DIR=str(tmp_path / 'logs'), GSI_TOKEN='synthetic-layout-token',
               DASHBOARD_PIN='synthetic-layout-pin')
    script = (
        "import sys, companion; assert 'companion.server' not in sys.modules; "
        "from companion import server; "
        "from pathlib import Path; "
        "assert server.ROOT == Path(sys.argv[1])"
    )
    subprocess.run([sys.executable, '-c', script, str(ROOT)], cwd=tmp_path, env=env, check=True)
    assert (tmp_path / 'data' / 'profiles.json').is_file()
    assert not (ROOT / 'companion' / 'data').exists()


def test_document_links_resolve_after_moves():
    files = list(ROOT.glob('*.md')) + list((ROOT / 'docs').rglob('*.md'))
    files += [ROOT / 'scripts' / 'README.md', ROOT / 'tests' / 'README.md']
    for source in files:
        for target in re.findall(r'!?\[[^\]]*\]\(([^\s)]+)\)', source.read_text('utf-8-sig')):
            if re.match(r'^(?:[a-z]+:|#|/)', target, re.I):
                continue
            relative = re.split(r'[?#]', target, maxsplit=1)[0]
            assert (source.parent / relative).exists(), (source.relative_to(ROOT), target)
