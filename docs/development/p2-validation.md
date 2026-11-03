# P2 validation — 2026-10-28

> HISTORICAL RECORD — this dated phase report/plan is retained for provenance, not current operating instructions or current test evidence. Production is now target-only; historical files are refused without replacement. Use the [documentation index](../README.md) and [current operator procedure](production-activation.md).


## Baseline and scope

Baseline main: cbefcdf477c2e497f4604496ff260b26b647874e, containing P1 #17. All 112 tracked files in the isolated local baseline matched their remote Git blob hashes before P2 edits. The maintainer approved Repère, Tactical Blue as default, the other three complete palettes and Barlow Condensed + Inter.

P2 changes frontend identity, CSS foundations and a temporary theme preview. Backend, profile schema/autosave, protocol, GSI, PIN protections, network defaults, installer, runtime dependencies, project license and software version are unchanged. No later-phase feature is implemented.

## Local checks

- Six standalone backend suites and 87 pytest checks passed on Windows. The existing Starlette/httpx deprecation warning remains.
- Six Node suites passed: profile sync, reconnect, i18n, display formatting, dashboard transport and theme preview. Changed JavaScript syntax checks passed.
- PowerShell 5.1: all eight scripts parsed; synthetic installer helper checks passed. No installation, elevation, firewall change or real CS2 access was performed.
- Existing real Chrome journey passed: authentication, GSI propagation, shared profiles/conflicts, reconnect, demo isolation, editing, import/export, mobile and EN/FR.
- Unmodified P1 widget golden fixtures still pass: all 29 kinds, displayed values, missing/zero data, estimates, bomb states, native demo and FR/EN. Fixtures were not regenerated from P2.
- The theme journey passed on local Chrome at 1280×900, 1024×768, 390×844 and 320×740. Narrow contexts emulate touch; visible controls are checked for 44 px coarse-pointer targets. It also checks keyboard focus, local fonts, EN/FR, all 29 widget outputs, editor/catalog, custom color overrides, per-tab isolation and no profile/storage writes.
- Theme preview tests reject unknown/prototype-like names and forbid storage or transport access. Asset contracts verify WOFF2 hashes and notices, complete palette keys, same-origin references and inert SVG content.

Local snapshots have no Git index, so indexed-file/archive checks belong to CI. Linux, Docker, dependency auditing and Firefox/WebKit are CI evidence, not local results. Consult the PR checks for the exact final head; successful earlier runs do not validate later revisions.

## Visual evidence

Local synthetic evidence includes matched P1/P2 desktop/mobile EN/FR characterization captures, plus four-theme dashboard, login, help and error captures, and editor examples. The P1/P2 characterization comparison uses the same Chrome version, viewport, locale, synthetic state, UTC and fixed clocks; theme captures additionally cover touch contexts. No screenshot contains an entered PIN or personal profile.

The visual changes are intentional: Repère branding, opaque graphite surfaces, complete theme palettes, local typography, shared controls, thin borders and restrained corner radii. Existing widget contents/structures, user-selected colors/backgrounds and solid/glass/outline options remain. The all-widget fixture intentionally mixes those old customization choices; it is not a new default profile or a future widget redesign.

The current header and native flows remain. The existing help dialog is themed; OS/browser-owned select popups and prompt/confirm windows retain native appearance. The new preview selector is visibly temporary and unsaved. A previously untranslated English help paragraph is corrected.

Sampled minimum text contrast across the four palettes: primary body 14.65:1, secondary 7.32:1, primary button 5.18:1, selected text 7.16:1. Field borders measure at least 3.89:1 and keyboard focus 10.92:1 in the sampled contexts. These results do not certify arbitrary user-selected colors, every OS control or full accessibility conformance.

## Performance

Chrome 156.0.8078.49 on the same Windows machine, EN, 1280×900, synthetic fixtures. Final comparison alternates the unchanged P1 server and P2 in one browser process, counterbalancing order over nine pairs. Every trial uses a fresh context and the existing P1 benchmark function. Refresh has 90 samples per version; other operations have nine. No concurrent local test suite ran during the final timing pass. Times are milliseconds.

| Operation | P1 median | P2 median | P1 range | P2 range |
| --- | ---: | ---: | --- | --- |
| Navigation DOMContentLoaded | 69.50 | 73.50 | 58.40–174.60 | 60.20–409.00 |
| Connect to visible dashboard | 158.48 | 159.90 | 138.60–173.57 | 140.44–172.76 |
| Render 29 widgets | 4.60 | 4.60 | 4.00–5.20 | 3.80–7.00 |
| Refresh 29 widgets | 6.24 | 5.96 | 2.88–11.37 | 2.78–10.47 |
| First editor entry, 29 widgets | 14.40 | 20.90 | 12.60–16.70 | 19.00–38.50 |
| Render 60 widgets | 4.70 | 5.40 | 4.40–5.40 | 5.20–7.70 |

Render/editor timings are UI clicks followed by forced layout, not GPU presentation times. Connect/refresh include browser automation and transport overhead. Early sequential and paired runs showed large machine-dependent drift; raw local reports are retained. No speedup, universal latency guarantee or invented pass threshold is claimed. The first editor entry has a measured cost to monitor; mobile CPU/network throttling and physical devices were not benchmarked.

P2 distributes 93,008 bytes of fonts; the two faces used initially total 70,700 bytes. They are served locally and preloaded to reduce late font swaps. Barlow 600 and the standalone outlined lockup are available assets, not required initial downloads. Three new lightweight text resources (tokens, palettes, preview script) are added. No framework, build runtime or external font service is introduced.

An experimental card-containment rule was discarded because it did not provide a repeatable improvement. It is not part of P2. No editor rewrite or backend optimization was added to hide the typography/style cost.

## Remaining limits

Real CS2, competitive-platform authorization, elevated/fresh Windows installation, another LAN machine, physical touch input and OBS were not tested. Existing authenticated-to-demo board behavior and the default-disabled estimated bomb timer remain as characterized by P1. Theme persistence and new profile/navigation/widget/Studio contracts belong to later approved lots. Publication, releases, tags and merging require separate authorization.
