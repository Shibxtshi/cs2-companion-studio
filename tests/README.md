# Test suites

Automated checks are organized by execution model:

- `tests/test_*.py` — regular pytest tests (security, documentation, release metadata, source quality).
- `tests/standalone/test_*.py` — independent backend regression scripts run in **separate Python processes** so their synthetic environment variables and global state do not interfere with other suites.
- `tests/test_live_browser.py` — real HTTP/WebSocket integration tests on Chromium, Firefox and WebKit in CI.
- `tests/legacy_browser/` — historical offline Chromium UX checks, kept for reference and manual execution, not part of the main quality gates.

## Run locally

```bash
python scripts/run_checks.py
python -m pytest -q
```

A single standalone test can run with `python -m tests.standalone.test_security`. The legacy Chromium check is `python -m tests.legacy_browser.test_e1_browser` and requires a local `/usr/bin/chromium` plus the Playwright Python package.

Do not run standalone backend suites as ordinary pytest modules: they configure process-wide synthetic credentials and in-memory global GSI state.
