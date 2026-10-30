# Dashboard and navigation — P6

> P9.5 update: these phase boundaries describe their original delivery. The integrated production composition and the explicit, separately authorized transition are documented in [Production activation](production-activation.md). Valid historical installations remain usable until offline confirmation.


The maintainer approved the first visual direction on 2026-10-29. Repère, Tactical Blue, the four P2 palettes and the existing widget markup remain the foundations. P7 variants and P8 editing interactions are not implemented.

## Modules and active boundary

| Module | Responsibility |
| --- | --- |
| dashboard-shell.js | Shared navigation, current editor entry, Settings controls and native/fallback fullscreen |
| dashboard-layout.js | Pure bounded geometry projection, without storage or DOM access |
| dashboard-grid.js | ResizeObserver-based target layout adapter; live values do not recreate cards |
| dashboard-target.js | Inactive read-only target host using the authenticated P5 catalog and P1 transport |
| dashboard.css | Shell and target geometry rules using the P2 tokens |
| studio.js | Active legacy profiles, editor, autosave and existing import/export |

Production index.html loads the shell/layout helpers and still loads studio.js. It never loads dashboard-target, published-profiles or the draft/publication modules. The server still instantiates its single legacy ProfileStore. No storage conversion, reset, generation renewal, dual writer or public activation switch exists.

The test-only /__dashboard_test__ route substitutes the frontend host only inside the existing disposable P5 target composition. It uses the same HTML, shell, renderer, PIN/Origin gates and canonical ASGI app. The test route and launcher are absent from the Docker image. A normal production client cannot activate the target host through a command.

## Navigation

Dashboard is read-only: editing controls are shown only in Customization Studio, whose notice identifies the current automatically saved editor. Settings groups existing display controls, theme preview, help and diagnostics. Streamer Studio is explicitly disabled and labelled coming soon, with no empty destination.

Full navigation shows labels, compact navigation shows accessible labelled icons, and hidden navigation retains a focusable/touchable edge button. The floating button is optional. Alt+M toggles navigation outside text/select editing; Escape closes a revealed menu or exits immersive mode. Browser interception can prevent a shortcut, so the edge button is always the independent recovery mechanism. Mobile full navigation uses a horizontally scrollable top row.

Legacy navigation/fullscreen choices are unsaved tab-local previews. The P5 target host reads those preferences from each selected profile. They are never written to the legacy format or treated as global device preferences. Current activeProfile selection remains shared in production; only the target host supports independent selection in each tab. An unrelated profile update does not rebuild the selected target dashboard.

Fullscreen requests the native API and retains an immersive page fallback on rejection/absence. Its two presentations are widgets only or widgets plus connection status. A small exit control and the edge recovery control remain available; essential recovery controls are intentionally not removed. Native Escape and the in-page Escape handler both permit exit. Geometry is unaffected.

## Display projection

The saved layout remains immutable. Rows are 32 CSS pixels with 8-pixel gaps. A four-row card is 152 pixels tall. Type-specific minimum width/height accommodate the current content; these are presentation minima, not P7 variants or modifications to the P3 validator. Long content can scroll inside the body; only overflow regions enter the tab order.

Desktop mode uses the saved column count when the actual board width can provide 32 pixels per column plus gaps. Widgets are ordered by saved Y, X and original array order. An available position is retained. A collision moves the later card below intersecting cards, preserving its column and width where the minimum content width permits. Larger content minima may expand its visual footprint and clamp its column into the container. Saved rectangles are never changed.

Below that width, available board width of at least 600 pixels uses up to 12 columns; narrower boards use one column. Widths scale proportionally with content minima. Packing is stable row-major order, with later cards never inserted before an earlier one. Desktop gaps are compacted only in these calculated responsive modes. Returning to desktop recomputes from the original positions.

The 600-pixel threshold is a presentation value checked at the required seven resolutions, not a new profile field. Up to 60 widgets are supported. Collision searches jump below existing rectangles and have at most the placed-card count plus one iterations. Computed geometry is limited to 8,192 display rows, independently of P3's 4,096 saved rows. If no position fits, remaining widgets follow in full-width accessible fallback cards and a translated warning is shown. No widget is omitted, no coordinate is persisted, and no unbounded row scan is used.

ResizeObserver watches only container width, coalesces work through requestAnimationFrame and is disconnected on disposal. Replaced-card style references are pruned. GSI updates paint existing values; they do not run the geometry engine or reconstruct the board.

## Data freshness and demo

A lost live connection clears displayed game values and the running bomb anchor rather than retaining player data behind a reconnect label. A deliberate demo switch rebuilds the public five-widget board; authenticated custom cards and titles cannot remain on the demo surface. This intentionally supersedes the historical P1 authenticated-to-demo observation. All other golden widget values remain checked without regenerating the fixtures. The bomb estimate remains disabled by default.

## Activation gates still outstanding

P6 does not activate target storage. A future coordinated change still needs target-compatible profile creation/editing and import/export, P8 Studio with draft/resume/logout/exit/error choices, P5 explicit publication wired to that UI, and a warned/verified-private-backup/explicitly confirmed generation transition. Retire the legacy writer/autosave only as part of that same switch. Preserve .env, credentials, data and recovery copies. Read [publication](profile-publication.md), [contracts](profile-contracts.md) and [drafts](local-drafts.md).

## Verification

See tests/README.md. Pure Node tests cover stable ordering, collision freedom, 60 widgets, bounds, responsive restoration and fallback. Browser tests cover real historical HTTP/GSI/WS/auth/autosave/import/export, golden widget values, theme isolation, keyboard/touch recovery, fullscreen fallback, and the isolated target with two tabs plus another device and remote P5 publication/deletion. Screenshots and raw timing evidence remain private local artifacts outside the source tree. No real personal profile is used by the tests.

## P7 widget presentations

See [widget-presentations.md](widget-presentations.md) for the 29-kind, three-variant renderer, shared data nodes, measured minima, preserved legacy Standard path and inactive target persistence.
