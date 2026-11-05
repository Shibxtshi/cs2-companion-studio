# Test suites

Run from the source root, using disposable fixtures and credentials only. Never point destructive tests at an installed personal service. This page lists commands, **not results**. Record OS, Python/browser versions, exact commit, executed/passed/failed/skipped/not-run checks and limitations. Historical evidence is not a fresh run. Hosted CI can be unavailable; never infer a green status from local tests.

## Prerequisites and backend

Use Python 3.12 in a virtual environment and Node.js for JavaScript tests. The development requirements include the pinned runtime/test dependencies; browser engines and Docker are separate prerequisites.

```bash
python -m pip install -r requirements-dev.txt pytest
python scripts/run_checks.py
```

The gate launches six standalone modules in **separate processes**, validates catalogs, runs unit/integration/contracts and secret hygiene. Standalone modules set process-global fixtures and must not be collected into the same pytest process. For example:

```bash
python -m tests.standalone.test_security
python -m pytest -q tests/unit tests/integration tests/contracts
python scripts/check_locales.py
python scripts/generate_profile_schema.py --check
python scripts/check_docs.py
```

| Directory | Responsibility |
|---|---|
| `tests/unit/` | Target runtime, strict profiles, recovery, atomic failures, publication and delivery |
| `tests/integration/` | HTTP/WebSocket, PIN/Origin/security, malformed messages and publication |
| `tests/contracts/` | Schema parity, catalogs, public documents, assets, archive/privacy and version invariants |
| `tests/standalone/` | Economy, timer, studio/backend, security, lifecycle and profile/diagnostics suites |
| `tests/js/` | Pure/controller behavior, history, local draft contract and UI adapters |
| `tests/browser/` | Real browser journeys, guarded synthetic hosts and production composition |
| `tests/windows/` | PowerShell syntax, installer helpers and shared locales without actual Steam/UAC |
| `tests/docker/` | Disposable image, startup, isolation, settings, recovery and publication |

Select checks for the changed behavior; expand across affected security/GSI/storage/platform boundaries. Public release gates remain separate. A skipped Windows symlink check is not proof that Linux symlink behavior passed.

## JavaScript

Node needs no frontend framework installation for these suites. Run each relevant file directly:

```bash
node tests/js/test_studio_data.js
node tests/js/test_reconnect.js
node tests/js/test_i18n.js
node tests/js/test_display_format.js
node tests/js/test_dashboard_client.js
node tests/js/test_theme_preview.js
node tests/js/test_drafts.js
node tests/js/test_profile_publication.js
node tests/js/test_dashboard_layout.js
node tests/js/test_widget_presentation.js
node tests/js/test_studio_model.js
node tests/js/test_experience.js
```

Use `node --check <actual-file.js>` for syntax. The browser harnesses are `tests/browser/studio-target.js` and `tests/browser/dashboard-target.js`, not production static assets.

## Browser checks

Install the matching package and engines in the disposable development environment:

```bash
python -m pip install playwright==1.57.0
python -m playwright install chromium firefox webkit
python tests/browser/test_live_browser.py --browser chromium
```

Linux engines also need their OS libraries (or the version-matched pinned Playwright image in CI). Repeat a selected journey with `--browser firefox` / `--browser webkit` when installed. Production runners can use `CCS_CHROMIUM_EXECUTABLE` for installed Chrome; older isolated module runners use `CS2_CHROMIUM_BIN`. Inspect the selected runner/helper before setting an override. Missing binaries mean not executed, not passed. Mobile/touch emulation is not a physical-device test.

| Runner under `tests/browser/` | Scope |
|---|---|
| `test_live_browser.py` | Fresh real production startup, normal PIN, Studio/publication, synthetic GSI, absent historical assets |
| `test_production_studio.py` | Production auth/catalog, profiles/tabs, draft/history, import/export, publication and responsive widgets |
| `test_production_acceptance.py` | Profile operations, local/published separation, geometry, exits, preview and recovery controls |
| `test_production_resilience.py` | Browser close/reopen, logout, IndexedDB unavailable/quota/abort |
| `test_production_faults.py` | Throttling, stale/metadata-only GSI, invalid imports, lost reply and server restart |
| `test_rendering_regressions.py` | Computed custom surfaces/opacity, same-ID type replacement, focus and demo bomb controls |
| `test_themes.py` | Ten published palettes, light/native controls, draft/history/preview, profiles, FR/EN and contrast samples |
| `test_localization.py` | Seven locales, real auth/publication, hot language changes, reload, preview, mobile overflow, personal-text isolation and temporary test language |
| `test_experience.py`, `test_experience_edges.py`, `test_logo_navigation.py` | Help/onboarding/settings/diagnostics, offline/errors/zoom, guarded logo exits, mouse/keyboard/touch |
| `test_widget_preview.py` | 29 × 3 presentations across ten themes (870 combinations), missing/zero/stale/demo/long content and overrides |
| `test_drafts.py`, `test_profile_publication.py` | Native IndexedDB, CAS/context revocation, journals/receipts/conflicts and failure injection |
| `test_dashboard_target.py` | Isolated layout/collision/tab-sync host; not a production substitute |
| `test_customization_studio.py`, `test_studio_workflows.py`, `test_studio_matrix.py` | Isolated component Studio model/workflows, 87 presentations and responsive/touch |

Examples (private output directories outside source, replace with an absolute writable path on Windows):

```bash
python tests/browser/test_production_studio.py --browser chromium --output /tmp/ccs-production-review
python tests/browser/test_themes.py --browser chromium --output /tmp/ccs-theme-review
python tests/browser/test_rendering_regressions.py --browser chromium --output /tmp/ccs-rendering-review
```

Production suites start the real `companion.server:app` with temporary data and normal authentication. Guarded `publication_server.py` hosts remain useful for isolated module tests only; they and their routes are not distributed in Docker. Never substitute them for a claim of production acceptance. P1 JSON fixtures are historical observations; do not regenerate them to hide regressions. Source/game calculations remain shared by variants.

## Windows checks

On Windows with PowerShell 5.1, from the source root:

```powershell
powershell -NoProfile -File tests/windows/check_syntax.ps1
powershell -NoProfile -File tests/windows/test_helpers.ps1
powershell -NoProfile -File tests/windows/test_locales.ps1
```

Helpers use temporary files and mocked Docker/HTTP. They do not prove real UAC, Steam detection on every machine, a real game session or LAN reachability.

## Docker checks

Use only a **separate extracted checkout/Compose project** with synthetic `.env`, private writable test `data/`/`logs/` and a free host port. Review `.github/workflows/checks.yml` for the exact fixture setup, UID 10001 ownership and runner order before running. These scripts read/change their configured instance; never run them from a personal installation.

```bash
docker compose up -d --build --wait --wait-timeout 120
python tests/docker/smoke.py
python tests/docker/settings.py
python tests/docker/profile_contracts.py
python tests/docker/profile_publication.py
docker compose down --remove-orphans
```

This builds/starts and later removes the disposable project containers/network, not host bind-mounted data. The settings suite changes its synthetic timer setting; profile recovery tests stay in container temporary storage. Only `scripts/recover_profiles.py` is shipped as a maintenance command. Native Linux Docker UID/permissions and Windows Docker Desktop binds have different filesystem behavior; label the environment.

## Archive, dependencies and CI

In a clean Git checkout, create a candidate ZIP **outside source**, then inspect it:

```bash
git archive --format=zip --output=../ccs-source-check.zip HEAD
python scripts/check_public_archive.py ../ccs-source-check.zip
```

This checks archive contents, not all Git history or legal readiness. The dependency-audit job installs `pip-audit==2.10.1`, audits `requirements.txt` and generates CycloneDX; it requires network access. Preserve audit outputs privately until reviewed.

`.github/workflows/checks.yml` defines Windows/Linux regressions, PowerShell 5.1, Chromium/Firefox/WebKit, dependency audit/SBOM and Docker smoke jobs. It uses pinned action/image references. Consult actual runs on the exact commit; a workflow file or old green run is not present evidence. Do not change billing/visibility or weaken tests to obtain a green result.

## Measurements and manual limits

`benchmark_production.py`, `benchmark_studio.py`, `benchmark_experience.py` and `tests/benchmarks/profile_publication.py` accept output options documented by `--help`. Use sequential matching scenarios, raw samples and a private output path. Example:

```bash
python tests/browser/benchmark_production.py --browser chromium --repeats 5 --output /tmp/ccs-performance.json
```

The optional `--soak-only --soak-seconds 1800` production benchmark is not default CI. Automation/waits, debounce, storage and browser scheduling affect timing; these are descriptive measurements, not universal speedup claims or arbitrary thresholds. Old legacy editor timings are not equivalent to target Studio timings. Synthetic GSI, keyboard/pointer/touch emulation, process restart and temporary-directory recovery are not real CS2, physical-device or anti-cheat certification. See [release gates](../docs/releases/checklist.md) and [user first use](../docs/user/first-use.md).
