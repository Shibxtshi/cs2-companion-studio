#!/usr/bin/env python3
"""Local 1.0.0 quality gate (stdlib orchestration; no CS2/FACEIT connection)."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TEST_MODULES = [
    "tests.standalone.test_economy",
    "tests.standalone.test_timer",
    "tests.standalone.test_studio",
    "tests.standalone.test_security",
    "tests.standalone.test_lifecycle",
    "tests.standalone.test_profiles_and_diagnostics",
]


def run():
    for testModule in TEST_MODULES:
        print('Running:', testModule, flush=True)
        subprocess.run([sys.executable, '-m', testModule], cwd=ROOT, check=True)
    print('Running: public security and persistence regressions', flush=True)
    subprocess.run([sys.executable, '-m', 'pytest', '-q', 'tests/test_public_security.py', 'tests/test_secret_hygiene.py', 'tests/test_public_docs.py', 'tests/test_release_version.py', 'tests/test_code_quality.py'], cwd=ROOT, check=True)
    subprocess.run([sys.executable, 'scripts/check_secrets.py'], cwd=ROOT, check=True)
    print('OK: local backend/security quality gate. Browser, Docker and dependency scans run in CI.', flush=True)


if __name__ == '__main__':
    run()
