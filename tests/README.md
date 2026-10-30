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
python tests/docker/profile_contracts.py
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

## Design-system checks

Run node tests/js/test_theme_preview.js and python tests/browser/test_themes.py --browser chromium. CI also runs the theme journey in Firefox and WebKit. Optional --output ../theme-evidence saves synthetic desktop/mobile screenshots and contrast samples. It covers four palettes, all 29 widget outputs, EN/FR, keyboard focus, four viewport widths, local fonts and profile/storage isolation. It does not certify arbitrary user-chosen widget colors or browser-owned native dialogs.

## Target profile contracts and offline recovery (P3)

Unit suites test strict server/export/draft/operation documents, all 29 kinds, geometry bounds, per-profile compare-and-swap and bounded retry receipts. Recovery tests use temporary synthetic files and inject backup/write/validation failures, interruption before/after replacement, rollback failure, process death and concurrent recovery tools. They never reset personal profiles. Windows may skip the symlink test when symlink creation is unavailable; Linux CI runs that path.

Integration tests ensure current WebSocket saves reject target version markers without changing the active revision/file. Existing autosave, import/export, authentication, GSI, reconnect and theme/browser tests continue to run. The Docker profile_contracts runner checks the packaged inactive modules and recovery entirely under container /tmp; it never resets the live mounted profile store. See [contract boundaries](../docs/development/profile-contracts.md) and [operator procedure](../docs/guides/profile-recovery.md).

## Persistent draft foundations (P4)

Run node tests/js/test_drafts.js and python tests/browser/test_drafts.py --browser chromium. The shared corpus also runs against P3 Python models during pytest; the generated schema must match scripts/generate_profile_schema.py. Browser CI adds the native IndexedDB journey in Chromium, Firefox and WebKit without replacing existing journeys.

The draft runner creates a temporary persistent browser profile and synthetic server, reopens the full browser process, injects quota/transaction/deletion failures, and checks tab conflicts, context isolation, logout revocation and HTTP origins. No personal browser profile or CCS data is read. --output ../draft-evidence saves raw 60-widget timing samples and deterministic write/history metrics. Local latency is descriptive, not a CI performance gate. The current app does not load the draft modules; see [draft foundations](../docs/development/local-drafts.md) for the P5/P8 integration boundary.

## Explicit publication foundations (P5)

Run node tests/js/test_profile_publication.js and python tests/browser/test_profile_publication.py --browser chromium (also Firefox/WebKit in CI). Python unit/integration suites cover the target store and its use through the existing authenticated WebSocket. The tests-only browser launcher substitutes one synthetic target store into companion.server:app; it requires a disposable marker directory and is never used by production Docker/Windows launchers.

The browser journey uses the real P1 transport and native IndexedDB to verify journal-before-send, acknowledgement loss, reload/server restart, retries, explicit conflicts, later local edits, cleanup failures, profile independence, local tab conflicts, deletion/orphans, confirmed logout, generation changes and preservation of P4 database-version-1 records. --output ../publication-evidence records seven 60-widget publications with three real clients.

Optional backend measurements: python tests/benchmarks/profile_publication.py --output ../publication-evidence/backend.json. These use temporary data only, with 12 profiles × 60 widgets and 64 receipts, nine samples per operation and fast in-memory fan-out peers. Run performance measurements sequentially; scheduling results are not LAN latency and no timing threshold is a CI gate. Existing demo/GSI/widget/theme/browser suites are retained. See [publication boundaries](../docs/development/profile-publication.md).

## P6 dashboard checks

Run node tests/js/test_dashboard_layout.js, python tests/browser/test_dashboard_navigation.py --browser chromium and python tests/browser/test_dashboard_target.py --browser chromium (also firefox/webkit in CI). The target test uses disposable P5 storage, real authenticated transport and synthetic GSI; it never accesses personal profiles. Add --output PATH to the target test for local screenshots and reflow timings. Keep those artifacts outside the source tree.

## P7 widget variants

Run node tests/js/test_widget_presentation.js and python tests/browser/test_widget_preview.py --browser chromium (also firefox/webkit). The synthetic review server is not packaged into Docker or started by production. --output PATH optionally writes the standalone gallery and screenshots outside the source tree. P1 JSON fixture bytes stay unchanged; reviewed display-only normalizations are explicit in the characterization comparator. P6 target tests additionally cover all 87 combinations and intrinsic-height clipping at seven resolutions.

Optional matched-board timings: python tests/browser/benchmark_widget_updates.py --browser chromium --repeats 5 --output PATH. Run baseline/candidate sequentially with matching browser/viewport/fixtures. It reports DOM counts and card/list identity as well as 29/60-widget render/update samples; no latency threshold is enforced.

## P8 Customization Studio

Run node tests/js/test_studio_model.js and all three browser journeys: test_customization_studio.py, test_studio_workflows.py and test_studio_matrix.py under tests/browser/, each with --browser chromium (also firefox/webkit). These use the guarded synthetic P5 launcher, native IndexedDB, the actual P7 renderer and existing authenticated transport. Production remains historical; no personal files are loaded or reset.

The workflow journey injects native quota/transaction/cleanup failures, real disk refusal, lost acknowledgements, reload/server restart and cross-tab conflicts. The matrix covers 29 x 3 presentations at seven resolutions, four themes, 60 instances, keyboard/touch and unchanged desktop geometry. Optional --output PATH records private synthetic captures and raw descriptive timing samples. No timing threshold is a CI gate. See [Studio architecture and activation boundary](../docs/development/customization-studio.md).

Hosted Actions may be refused before startup by account billing restrictions. Record that as not executed; local Windows/Linux/Docker/browser evidence does not make hosted checks green. Keep workflow definitions and triggers intact for future reactivation.

## P9 secondary screens and feedback

Logo navigation: `python tests/browser/test_logo_navigation.py --browser chromium` (also Firefox/WebKit). It verifies real PIN gates, mouse/Enter/touch, Settings and Help returns without document reload, per-tab target selection, a delayed historical save and all four existing target Studio exit choices. Only synthetic temporary stores are used. The target Studio and Dashboard remain separate documents; that existing authenticated transition is retained, while within-dashboard home actions use the shared section router.

Run `node tests/js/test_experience.js` and `python tests/browser/test_experience.py --browser chromium` (also `firefox`/`webkit`). The runner uses disposable profiles, the existing PIN/WebSocket path and synthetic GSI. It covers optional onboarding/dismissal, native help/focus, four themes, EN/FR, seven widths, import/download faults without parser-content disclosure, diagnostics, real server interruption and demo isolation. `--output PATH` writes synthetic screenshots outside the source tree. Preparing a browser download does not prove it reached disk.

Node checks verify persistent errors/pending states, explicit dismissal and that unrelated success cannot hide an error. Do not regenerate P1 widget fixtures. See [UI responsibilities](../docs/development/user-experience.md) and the separate [activation proposal](../docs/development/target-activation-plan.md).

Also run `python tests/browser/test_experience_edges.py --browser chromium` (Firefox/WebKit supported) for real throttling, unavailable-server/demo transitions, ended-session messaging and keyboard focus under 200% CSS zoom. CSS zoom is a bounded automated check, not certification of every browser/OS zoom mode.

Optional sequential measurements: `python tests/browser/benchmark_experience.py --repeats 5 --output PATH`. Compare the same browser/viewport/fixtures on baseline/candidate. Opening includes HTTP/fonts/automation; named UI samples use real clocks, microtasks and forced layout inside the browser. There is no timing gate or general speedup claim.

Optional sequential Studio measurements: python tests/browser/benchmark_studio.py --repeats 5 --output PATH. This reports native UI timings separately from labelled automation/debounce, IndexedDB put-to-completion, post-GC Chromium heap, serialized history and DOM counts. It uses temporary data and explicitly publishes only to the synthetic target. P7 had no integrated target Studio, so do not present these as a like-for-like P7 Studio speedup.
