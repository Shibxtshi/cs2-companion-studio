#!/usr/bin/env python3
"""Local V1P-F quality gate (stdlib orchestration; no CS2/FACEIT connection)."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TESTS = ['test_economy.py','test_timer.py','test_studio.py','test_security.py',
         'test_lifecycle.py','test_profiles_and_diagnostics.py']


def run():
    for test in TESTS:
        print('Running:', test, flush=True)
        subprocess.run([sys.executable, str(ROOT/test)], cwd=ROOT, check=True)
    print('Running: public security and persistence regressions', flush=True)
    subprocess.run([sys.executable, '-m', 'pytest', '-q', 'tests/test_public_security.py', 'tests/test_secret_hygiene.py', 'tests/test_public_docs.py'], cwd=ROOT, check=True)
    subprocess.run([sys.executable, 'scripts/check_secrets.py'], cwd=ROOT, check=True)
    print('OK: local backend/security quality gate. Browser, Docker and dependency scans run in CI.', flush=True)


if __name__ == '__main__':
    run()
