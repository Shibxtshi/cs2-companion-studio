#!/usr/bin/env python3
"""Check source/commit hygiene without reading or rejecting local user secrets.

Running from an installed app is NOT the same as publishing a release. A local
.env (and local profile data) is expected; the release-zip check is separate.
"""
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


class HygieneError(Exception):
    pass


def assert_ignored_patterns(root):
    required = {
        '.gitignore': ('.env', '.env.*', 'PIN.txt', 'cs2_cfg/*.cfg',
                       '.installer-state/', 'data/*', 'logs/*'),
        '.dockerignore': ('.env', 'PIN.txt', 'cs2_cfg/', '.installer-state/',
                          'data/', 'logs/'),
    }
    for filename, patterns in required.items():
        path = root / filename
        if not path.is_file():
            raise HygieneError(f'Missing distribution safeguard: {filename}')
        lines = {line.strip() for line in path.read_text(encoding='utf-8').splitlines()
                 if line.strip() and not line.lstrip().startswith('#')}
        for pattern in patterns:
            if pattern not in lines:
                raise HygieneError(f'Missing exclusion {pattern!r} in {filename}')


def is_private_git_path(path):
    path = path.replace('\\', '/')
    pieces = path.split('/')
    name = pieces[-1]
    if name == '.env' or (name.startswith('.env.') and name != '.env.example'):
        return True
    if name == 'PIN.txt':
        return True
    if path.startswith('cs2_cfg/') and name.endswith('.cfg'):
        return True
    if '.installer-state' in pieces:
        return True
    if path.startswith('data/') and path != 'data/.gitkeep':
        return True
    if path.startswith('logs/') and path != 'logs/.gitkeep':
        return True
    return False


def check_git_index(root):
    """Inspect only indexed filenames, never the contents of .env or profiles."""
    if not shutil.which('git'):
        print('NOTE: git not installed; repository index check skipped')
        return
    parent = subprocess.run(['git', '-C', str(root), 'rev-parse', '--show-toplevel'],
                            capture_output=True, text=True, check=False)
    if parent.returncode != 0:
        print('NOTE: not a git checkout; repository index check skipped')
        return
    repoRoot = Path(parent.stdout.strip()).resolve()
    prefix = root.resolve().relative_to(repoRoot).as_posix()
    prefix = '' if prefix == '.' else prefix + '/'
    tracked = subprocess.run(['git', '-C', str(root), 'ls-files', '--cached', '-z', '--full-name'],
                             capture_output=True, check=True).stdout.decode('utf-8', errors='replace')
    for name in tracked.split('\0'):
        if not name or not name.startswith(prefix):
            continue
        relative = name[len(prefix):]
        if is_private_git_path(relative):
            raise HygieneError('Private runtime file is TRACKED by git: ' + relative)


def check_embedded_credentials(root):
    # Only shipped SOURCE files are inspected, never personal config files.
    for name in ('Dockerfile', 'compose.yaml', 'static/index.html',
                 'static/studio.js', 'static/styles.css'):
        content = (root / name).read_text(encoding='utf-8')
        if re.search(r'(?im)^\s*(?:GSI_TOKEN|DASHBOARD_PIN)\s*=\s*\S+', content):
            raise HygieneError('Embedded credentials found in source: ' + name)


def check(root):
    assert_ignored_patterns(root)
    check_git_index(root)
    check_embedded_credentials(root)


if __name__ == '__main__':
    try:
        check(ROOT)
    except (HygieneError, subprocess.CalledProcessError, ValueError) as exc:
        raise SystemExit('FAIL: ' + str(exc))
    print('OK: source ignores local secrets; no secrets tracked or embedded')
