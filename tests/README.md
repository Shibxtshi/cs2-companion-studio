# Test suites

Checks are grouped by responsibility and execution model.

| Directory | Scope | Execution |
| --- | --- | --- |
| unit/ | Recovery, disk failures and dashboard delivery | pytest |
| integration/ | HTTP/WebSocket security and private-path isolation | pytest |
| contracts/ | Catalog parity, source hygiene, documentation and release metadata | pytest |
| browser/ | Real server, desktop/mobile, profiles and reconnect journeys | Standalone Playwright runner |
| js/ | Profile synchronization controller behavior | Node.js |
| standalone/ | Backend suites with process-global synthetic fixtures | Separate Python process per module |
| legacy_browser/ | Historical offline Chromium checks | Manual/reference only |

## Local quality gate

```bash
python -m pip install -r requirements-dev.txt pytest
python scripts/run_checks.py
node tests/js/test_profile_sync.js
```

Ordinary pytest checks can also run with `python -m pytest -q`. Standalone and historical suites are excluded from pytest collection. Run a single backend suite with `python -m tests.standalone.test_security`; never collect these as ordinary pytest modules because they configure process-wide credentials and game state.

## Browser checks

```bash
python -m pip install playwright==1.57.0
python tests/browser/test_live_browser.py --browser chromium
```

Install the matching Playwright browser binaries first, or set CS2_CHROMIUM_BIN to an installed compatible browser for a local Chromium check. CI runs Chromium, Firefox and WebKit against a real synthetic server using the version-matched prebuilt image.

The historical runner is `python -m tests.legacy_browser.test_e1_browser`; it requires local /usr/bin/chromium and Playwright. It is not a substitute for the current integration journey.

All automated checks use synthetic data. They do not certify real CS2/UAC/LAN installation, anti-cheat approval or release readiness. See [architecture](../docs/development/architecture.md) and [release gates](../docs/releases/checklist.md).
