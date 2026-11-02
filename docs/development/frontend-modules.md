# Frontend module boundaries

The production document composes one target Dashboard and Customization Studio through application.js.
There is no historical editor or autosave module in the distributed frontend. See [target runtime](target-runtime.md).

| Module | Responsibility |
| --- | --- |
| widgets.js / widget-presentation.js | Catalog, immutable type identifiers, Standard/Compact/Minimal structures |
| display-format.js / widget-renderer.js | Received state projections and incremental card values |
| dashboard-client.js / reconnect.js | Shared PIN-authenticated transport and retry generation |
| published-profiles.js / profile-selection.js | Published catalog and selection local to each tab |
| profile-publication.js / draft-publications.js | Explicit operations, stable intentions and acknowledgements |
| draft-store.js / draft-session.js / edit-history.js | Local configuration-only persistence, CAS and bounded undo/redo |
| studio-model.js / studio-canvas.js / studio-workspace.js / studio-lifecycle.js | Editing model, keyed DOM, inspector and draft lifecycle |
| dashboard-layout.js / dashboard-grid.js / dashboard-shell.js | Responsive projection, grid application and navigation |
| application.js | One production composition, published/draft/game separation and import/export wiring |
| i18n.js / experience-copy.js / experience.js / notifications.js | Localization, help, diagnostics and feedback |

Deferred dependencies load before application.js. Rendering never publishes profiles. The transport owns no widget DOM
or translated text. PIN remains in the caller's session memory; configuration persistence excludes credentials and GSI.
Dashboard values use only published configuration; Studio edits local drafts and Save and apply uses the sole server writer.
Synthetic module hosts remain tests, not product alternatives. Source fixtures retain historical evidence without serving its editor.

The historical P1-P9 delivery boundaries below are superseded by this production map; consult them only for provenance.

## Earlier delivery notes

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

## P5 publication foundations

Target publication uses profile-publication.js, published-profiles.js and the IndexedDB journal in draft-publications.js. It reuses the P1 transport and P4 session contracts while leaving the current profile-sync.js and editor wiring unchanged. The modules remain absent from index.html. See [explicit publication](profile-publication.md) for acknowledgements, tab selection, uncertainty and conflict consent.

## P6 navigation and display

The shared dashboard shell and application.js compose the production Dashboard and Studio. dashboard-layout.js and dashboard-grid.js project X/Y data without writes. tests/browser/dashboard-target.js and tests/browser/studio-target.js are isolated test hosts, served only by publication_server.py and excluded from Docker. See [dashboard.md](dashboard.md). The authenticated-to-demo board is now rebuilt deliberately to prevent private cards remaining visible; all other golden widget cases are preserved.

## P7 widget presentations

See [widget-presentations.md](widget-presentations.md) for the 29-kind, three-variant renderer, shared data nodes, measured minima, preserved legacy Standard path and inactive target persistence.

## P8 isolated Studio

See [Customization Studio](customization-studio.md) for configuration-only model, transient data, keyed canvas, workspace controls, P4/P5 lifecycle composition, transport and same-origin preview responsibilities. These assets are not loaded by production index.html; historical behavior remains active until a separate coordinated transition.
