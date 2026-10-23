"""Regression tests for local install vs public source vs release zip."""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'check_secrets.py'
spec = importlib.util.spec_from_file_location('secret_checker', SCRIPT)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def test_local_env_is_not_an_error(tmp_path):
    for name in ('.gitignore', '.dockerignore', 'Dockerfile', 'compose.yaml'):
        shutil.copyfile(ROOT / name, tmp_path / name)
    (tmp_path / 'static').mkdir()
    for name in ('index.html', 'studio.js', 'styles.css'):
        shutil.copyfile(ROOT / 'static' / name, tmp_path / 'static' / name)
    (tmp_path / '.env').write_text('DASHBOARD_PIN=private-test-value\nGSI_TOKEN=private-test-value\n')
    (tmp_path / 'data').mkdir()
    (tmp_path / 'data' / 'profiles.json').write_text('{"profiles": []}')
    checker.check(tmp_path)
    assert (tmp_path / '.env').exists(), 'Checker must never remove local configuration'


def test_tracked_secret_is_rejected(tmp_path):
    if not shutil.which('git'):
        pytest.skip('git unavailable')
    (tmp_path / '.gitignore').write_text('.env\n')
    (tmp_path / '.env').write_text('DASHBOARD_PIN=test\n')
    subprocess.run(['git', 'init', '-q'], cwd=tmp_path, check=True)
    subprocess.run(['git', 'add', '-f', '.env'], cwd=tmp_path, check=True)
    with pytest.raises(checker.HygieneError, match='TRACKED'):
        checker.check_git_index(tmp_path)


def test_private_env_rejected_in_public_archive(tmp_path):
    from importlib.machinery import SourceFileLoader
    archive_spec = importlib.util.spec_from_file_location(
        'public_zip_checker', ROOT / 'scripts' / 'check_public_archive.py')
    archive = importlib.util.module_from_spec(archive_spec)
    archive_spec.loader.exec_module(archive)
    path = tmp_path / 'bad-release.zip'
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('CS2_Companion_Studio/.env', 'GSI_TOKEN=not-a-real-token')
    with pytest.raises(ValueError, match='Private'):
        archive.check_zip(path)
