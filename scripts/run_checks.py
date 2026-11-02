#!/usr/bin/env python3
"""Local 1.0.0 quality gate (stdlib orchestration; no CS2/FACEIT connection)."""
from pathlib import Path
import subprocess
import sys
import os
import tempfile

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
        with tempfile.TemporaryDirectory(prefix='ccs-standalone-') as directory:
            env = dict(os.environ, PROFILE_DATA_DIR=str(Path(directory) / 'data'),
                       DIAGNOSTICS_DIR=str(Path(directory) / 'logs'))
            subprocess.run([sys.executable, '-m', testModule], cwd=ROOT, env=env, check=True)
    print('Running: public security and persistence regressions', flush=True)
    subprocess.run([sys.executable, '-m', 'pytest', '-q', 'tests/unit', 'tests/integration', 'tests/contracts'], cwd=ROOT, check=True)
    subprocess.run([sys.executable, 'scripts/check_secrets.py'], cwd=ROOT, check=True)
    print('OK: local backend/security quality gate. Browser, Docker and dependency scans run in CI.', flush=True)


if __name__ == '__main__':
    run()
