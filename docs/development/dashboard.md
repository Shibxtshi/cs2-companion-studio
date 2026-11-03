# Dashboard layout and navigation

The production Dashboard is consultative and uses `application.js`, the published catalog and the X/Y projection. It never reads a local draft as published state. The integrated Studio is the only editor. [Startup rules](target-runtime.md) explain target-only storage.

## Navigation

Dashboard is read-only. Settings offers temporary display controls, help and diagnostics; permanent profile choices are Studio draft edits followed by explicit publication. Streamer Studio is unavailable/coming soon, without a working destination.

Full navigation shows labels, compact navigation shows accessible labelled icons, and hidden navigation retains a focusable/touchable edge button. The floating button is optional. Alt+M toggles navigation outside text/select editing; Escape closes a revealed menu or exits immersive mode. Browser interception can prevent a shortcut, so the edge button is always the independent recovery mechanism. Mobile full navigation uses a horizontally scrollable top row.

The selected published profile supplies navigation/fullscreen preferences. Each tab owns selection through `profile-selection.js`; a remote publication refreshes affected profiles without switching other tabs. An unrelated profile update does not rebuild the selected Dashboard.

Fullscreen requests the native API and retains an immersive page fallback on rejection/absence. Its two presentations are widgets only or widgets plus connection status. A small exit control and the edge recovery control remain available; essential recovery controls are intentionally not removed. Native Escape and the in-page Escape handler both permit exit. Geometry is unaffected.

## Display projection

The saved layout remains immutable. Rows are 32 CSS pixels with 8-pixel gaps. A four-row card is 152 pixels tall. Type-specific minimum width/height accommodate the current content; these depend on type/presentation and do not modify the storage validator. Long content can scroll inside the body; only overflow regions enter the tab order.

Desktop mode uses the saved column count when the actual board width can provide 32 pixels per column plus gaps. Widgets are ordered by saved Y, X and original array order. An available position is retained. A collision moves the later card below intersecting cards, preserving its column and width where the minimum content width permits. Larger content minima may expand its visual footprint and clamp its column into the container. Saved rectangles are never changed.

Below that width, available board width of at least 600 pixels uses up to 12 columns; narrower boards use one column. Widths scale proportionally with content minima. Packing is stable row-major order, with later cards never inserted before an earlier one. Desktop gaps are compacted only in these calculated responsive modes. Returning to desktop recomputes from the original positions.

The 600-pixel threshold is a presentation value checked at the required seven resolutions, not a new profile field. Up to 60 widgets are supported. Collision searches jump below existing rectangles and have at most the placed-card count plus one iterations. Computed geometry is limited to 8,192 display rows, independently of P3's 4,096 saved rows. If no position fits, remaining widgets follow in full-width accessible fallback cards and a translated warning is shown. No widget is omitted, no coordinate is persisted, and no unbounded row scan is used.

ResizeObserver watches only container width, coalesces work through requestAnimationFrame and is disconnected on disposal. Replaced-card style references are pruned. GSI updates paint existing values; they do not run the geometry engine or reconstruct the board.

## Data freshness and demo

A lost live connection clears displayed game values and the running bomb anchor rather than retaining player data behind a reconnect label. A deliberate demo switch rebuilds the public five-widget board; authenticated custom cards and titles cannot remain on the demo surface. This intentionally supersedes the historical P1 authenticated-to-demo observation. All other golden widget values remain checked without regenerating the fixtures. The bomb estimate remains disabled by default.

## Modules and verification

`dashboard-layout.js` is a pure bounded projection; `dashboard-grid.js` applies/coalesces layout and intrinsic-size changes; `dashboard-shell.js` owns navigation/fullscreen. `application.js` composes published rendering and guarded Studio exits. `tests/browser/dashboard-target.js` is a test-only host, not a production asset.

Run `node tests/js/test_dashboard_layout.js` and the production browser journeys in [tests/README.md](../../tests/README.md). Coverage includes collisions, bounds/fallback, responsive restoration, 60 widgets, keyboard/touch recovery and per-tab publication selection. Results must identify the exact tested revision/environment; historical reports are not fresh execution. See [widget presentations](widget-presentations.md).
