# P1 validation — 2026-10-28

> HISTORICAL RECORD — this dated phase report/plan is retained for provenance, not current operating instructions or current test evidence. Production is now target-only; historical files are refused without replacement. Use the [documentation index](../README.md) and [current operator procedure](production-activation.md).


## Scope and baseline

Baseline: main commit 38cb111c5790166e9f82fe87e98710762add9b11, including PR #16. All 101 tracked source files in the isolated baseline matched their Git blob hashes before application edits. P1 extracts three frontend responsibilities; no backend, CSS, widget catalog, profile schema, runtime dependency or security setting changes.

## Functional evidence

- Before and after: six standalone backend suites and 84 pytest tests passed on local Windows; one existing Starlette/httpx deprecation warning remains.
- After: five Node suites (display formatting, dashboard transport, profile sync, reconnect and i18n) and JavaScript syntax checks passed.
- Before and after: the existing real Chromium HTTP/WebSocket journey passed, covering synthetic PIN authentication, GSI, profile synchronization/conflicts, reconnect, editor operations, EN/FR and mobile layout.
- New characterization: all 29 widget identifiers, displayed strings, missing/zero values, lists, bars, styles, economy estimates, bomb statuses and native demo match fixtures captured before extraction. EN and FR both pass. The fixture transport does not replace the separate real-server journey.
- Local PowerShell 5.1 helper tests and parsing of all eight PowerShell scripts passed.
- Linux, Docker build/startup/isolation, dependency reporting, and Firefox/WebKit are CI checks, not local test results. Consult the PR checks for the exact final revision. The archived legacy browser runner was adapted for script loading but was not run locally.
- Local source snapshots have no Git index; indexed-file privacy checks run in CI against its checkout. Real CS2, elevated installer flows, physical mobile touch, and other LAN installations were not tested.

## Visual comparison

Chrome 156.0.8078.49, identical synthetic data, UTC, fixed characterization clocks, same locales and viewports: 1280×900 and 390×844. Dashboard-only screenshots contain no PIN or personal profile. Four before/after PNGs are byte-identical; no visual difference was detected. Screenshots and raw measurements remain local evidence.

| Capture | SHA-256, identical before/after |
| --- | --- |
| Desktop EN | 504cc55cde4c502a503a7099567874890fc7eced423d6007d86dbf7b081c634d |
| Desktop FR | 559b4b33e79a7c3ebb1e4befad53bd17e123248e9c7937f504de4e25fc502819 |
| Mobile EN | 1c5dcaf8184cc806504638e7a4ed75966fb08c3d586685c5ab94797e5fd59ed8 |
| Mobile FR | 628c3a366ab2d630763a947332e9050993fc4e321088e497503589f457d1a686 |

## Performance reference

Same Windows machine, Chrome version, synthetic fixtures and 1280×900 viewport. Sequential runs A1/B1/A2/B2, nine fresh browser contexts per batch: 18 repetitions per version, 180 updates per version. Real clocks; screenshots use a separate fixed-clock characterization pass. Times below are milliseconds and medians, not guarantees or pass thresholds.

| Operation | Before | After | Range before / after |
| --- | ---: | ---: | --- |
| Navigation to DOMContentLoaded | 41.00 | 66.30 | 29.10–72.50 / 56.70–78.50 |
| Connect click to visible dashboard | 158.23 | 169.50 | 141.62–172.99 / 144.23–178.60 |
| Render 29 widgets | 4.10 | 4.15 | 3.80–4.60 / 3.60–6.20 |
| Update 29 widgets | 5.97 | 7.35 | 3.21–12.26 / 3.90–13.42 |
| Enter existing editor, 29 widgets | 12.55 | 14.00 | 11.70–15.40 / 12.80–15.90 |
| Render 60 widgets | 4.50 | 4.70 | 4.00–5.70 / 4.40–5.30 |

Render/editor timings measure the existing UI click followed by forced board layout, not frame presentation or GPU time. Connect and update measurements include Playwright and transport overhead. Source extraction adds three deferred script requests; the measured navigation overhead is a cost to watch, not an optimization claim. Attribution solely to the refactor is not established: baseline batch medians themselves changed from 142.79 to 169.79 ms for connect and 4.16 to 7.29 ms for updates. No mobile CPU throttling, network throttling or production workload was measured.

Reproduce with the commands and environment options in [tests/README.md](../../tests/README.md), running the same harness on the unchanged baseline and candidate sequentially. Do not regenerate golden fixtures from the candidate to hide differences.

## Preserved limitation

The current authenticated-to-demo transition does not immediately rebuild the existing board. The test captures this observed main behavior, while a fresh public demo correctly starts with five default widgets. P1 does not introduce or fix this behavior. Larger dashboards remain a synthetic load reference; this is not a claim that every supported layout contains 60 widgets.
