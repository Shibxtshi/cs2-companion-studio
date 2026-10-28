# Frontend boundaries — P1

P1 prepares the existing frontend for later work without changing the current UI, profiles or protocol. There is no new framework, build step, runtime dependency or backend refactor.

| Module | Responsibility |
| --- | --- |
| static/js/widgets.js | Existing catalog: identifiers, metadata and shipped markup |
| static/js/display-format.js | Pure projection of received state into display strings and percentages |
| static/js/widget-renderer.js | Card shells, values, lists, bars and the estimated bomb display |
| static/js/dashboard-client.js | Health/version check, WebSocket authentication gating, messages and socket lifecycle |
| static/js/profile-sync.js | Existing autosave, revisions, in-memory pending edits and conflict choices |
| static/js/reconnect.js | Existing retry timing and cancellation generation |
| static/js/studio.js | Application state, editor controls, profiles, demo, UI events and service wiring |
| static/js/i18n.js / experience.js | Existing localization, onboarding and diagnostic UI |

index.html loads the dependencies before studio.js using the existing deferred-script model. Rendering receives the normalized state and timer anchor explicitly; it does not save profiles. The transport receives callbacks and does not own DOM elements, translated text, retries or profile persistence. PIN values are read from the caller's memory only when authenticating; no new browser storage is introduced.

## Preserved behavior

The 29 widget IDs/templates, CSS, profile schema, shared active profile, autosave, import/export version, existing editor operations, FR/EN, demo, diagnostics, authentication, HTTP/WS messages and default-disabled estimated bomb timer remain unchanged. Unsupported/missing data is displayed as before; this refactor does not correct labels, estimates or pre-existing UI behavior.

## Approved future specification — not implemented by P1

The maintainer approved the following decisions on 2026-10-28:

- Desktop layouts will have grid X/Y positions, width and height. Collision/reflow rules need approval before implementation, and mobile reflow must preserve the saved desktop layout.
- Each tab will choose its profile independently. A last-used local preference must not switch already-open tabs; profile configurations remain shared.
- Future local drafts survive reload and ordinary browser closure. Voluntary logout warns and deletes drafts only after confirmation; cancellation preserves them.
- Future Studio exit actions are apply, keep draft and leave, discard, or continue editing. Keeping a draft never changes the published dashboard.

These are later-lot requirements, not current runtime guarantees. P2–P10 and O1–O4 are outside this PR. No migration, persistent draft, new grid, theme, navigation, Studio or OBS feature is added here.

## Characterization and comparisons

See [the test guide](../../tests/README.md). The browser characterization records the current 29-widget output for complete, missing, zero and estimated data, bomb statuses and native demo in EN/FR. Checked-in fixtures were captured from unchanged main 38cb111c5790166e9f82fe87e98710762add9b11 before extraction. The separate live journey retains real synthetic HTTP/WebSocket authentication, GSI, profile sync, conflict, reconnect and editor coverage.

Optional screenshots and timing reports are local evidence, not distributed application assets. Compare the same browser, viewport, locale, timezone, fixtures and machine; timing runs should be sequential and repeated. Initial/update round-trip measurements include browser automation overhead and are not pure render timings.

The existing authenticated-to-demo transition does not immediately rebuild the board. Its observed output is characterized, without treating it as a desired future behavior; changing it belongs to a separately approved functional fix.

Measured P1 results and limitations: [validation record](p1-validation.md).

## P4 draft foundations

The future draft path is separate from profile-sync and studio.js. Its generated contract, native IndexedDB store, session-only history and lifecycle modules are documented in [local-drafts.md](local-drafts.md). They are not loaded by index.html or connected to current autosave.
