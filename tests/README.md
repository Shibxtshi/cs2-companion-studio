# Test suites

Checks are grouped by responsibility and execution model.

| Directory | Scope | Execution |
| --- | --- | --- |
| unit/ | Recovery, disk failures and dashboard delivery | pytest |
| integration/ | HTTP/WebSocket security and private-path isolation | pytest |
| contracts/ | Catalog parity, source hygiene, documentation and release metadata | pytest |
| docker/ | Disposable Compose instance, persistence and settings reload | Standalone Python runners in Docker CI |
| windows/ | PowerShell parsing and synthetic installer helpers | PowerShell 5.1; no UAC/Steam/CS2 |
| browser/ | Real server, desktop/mobile, profiles and reconnect journeys | Standalone Playwright runner |
| js/ | Profile synchronization controller behavior | Node.js |
| standalone/ | Backend suites with process-global synthetic fixtures | Separate Python process per module |
| browser/legacy/ | Historical offline Chromium checks | Manual/reference only |

## Local quality gate

```bash
python -m pip install -r requirements-dev.txt pytest
python scripts/run_checks.py
node tests/js/test_profile_sync.js
node tests/js/test_reconnect.js
node tests/js/test_i18n.js
node tests/js/test_display_format.js
node tests/js/test_dashboard_client.js
```

Ordinary pytest checks can also run with `python -m pytest -q`. Standalone and historical suites are excluded from pytest collection. Run a single backend suite with `python -m tests.standalone.test_security`; never collect these as ordinary pytest modules because they configure process-wide credentials and game state.

## Windows checks

```powershell
powershell -NoProfile -File tests/windows/check_syntax.ps1
powershell -NoProfile -File tests/windows/test_helpers.ps1
```

These test the operational scripts in installer/ and the test runners themselves. Helper tests use temporary synthetic files and mock Docker; they do not install into Steam/CS2 or request elevation.

## Docker checks

Docker CI creates disposable credentials and volumes, builds the image, then runs:

```bash
python tests/docker/smoke.py
python tests/docker/settings.py
```

Run these only against the disposable synthetic instance from the CI workflow. They modify game state and settings. The settings runner toggles the timer and checks authenticated WebSocket state, unchanged image IDs and profile content. They are excluded from ordinary pytest collection.

## Browser checks

```bash
python -m pip install playwright==1.57.0
python tests/browser/test_live_browser.py --browser chromium
```

Install the matching Playwright browser binaries first, or set CS2_CHROMIUM_BIN to an installed compatible browser for a local Chromium check. CI runs Chromium, Firefox and WebKit against a real synthetic server using the version-matched prebuilt image.

The consolidated historical runner is `python -m tests.browser.legacy.test_e1_browser`; it requires local /usr/bin/chromium and Playwright. The former i18n, experience and widget-editor wrappers all ran this same check and have been removed. It is not a substitute for the current integration journey.

All automated checks use synthetic data. They do not certify real CS2/UAC/LAN installation, anti-cheat approval or release readiness. See [architecture](../docs/development/architecture.md) and [release gates](../docs/releases/checklist.md).

Edge cases include repeated health failures, authentication concurrency, malformed/Unicode inputs, JSON complexity, private archive variants and untranslated personal labels. Windows helper tests also inject a failed atomic write without touching Steam/CS2.

Publication-preparation regressions cover binary WebSocket frames before/after authentication and deeply nested/non-finite profile storage. Linux CI also builds a ZIP from tracked source with git archive and checks its paths; this is not a full-history secret scan or a published release artifact.

## Widget characterization and local comparison evidence

```bash
python tests/browser/test_widget_characterization.py --browser chromium
python tests/browser/test_widget_characterization.py --browser chromium --output ../comparison-evidence --benchmark --repeats 9
```

The default path checks the frozen synthetic fixtures in tests/browser/fixtures/ without changing them. CI runs it in Chromium, Firefox and WebKit after the real HTTP/WebSocket journey. --record is a deliberate baseline-authoring operation; do not regenerate expected data from a failing refactor.

--output optionally saves desktop/mobile EN/FR screenshots of the synthetic dashboard, plus a performance JSON when --benchmark is requested. It never captures the login PIN or reads personal runtime files. Date and timer anchors are frozen for characterization; benchmark pages use real clocks.

Benchmarks use fresh contexts, a fixed 1280x900 viewport and the same fixtures. Metrics include navigation DCL, initial dashboard opening, 29/60-widget rebuilds, entry into the existing editor, and 29-widget refresh. UI click metrics force layout; initial/transport updates also include Playwright round-trip overhead. Raw samples accompany median/min/max. Run baseline and candidate sequentially on the same machine, repeat, and report noise rather than inventing a pass threshold. No benchmark timing is a CI performance gate.
