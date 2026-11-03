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
| i18n.js / experience-copy.js | Shared JSON catalog loader, explicit message bindings and stable experience-key adapter |
| experience.js / notifications.js | Help, diagnostics and feedback; phrases come from static/locales/ |

Deferred dependencies load before application.js. Rendering never publishes profiles. The transport owns no widget DOM
or translated text. PIN remains in the caller's session memory; configuration persistence excludes credentials and GSI.
Dashboard values use only published configuration; Studio edits local drafts and Save and apply uses the sole server writer.
Synthetic module hosts remain tests, not product alternatives. Source fixtures retain historical evidence without serving its editor.

## Loading and test hosts

The shared UTF-8 catalog loader starts the ordered `data-ccs-src` modules under the CSP. It translates explicit keys/parameters, not personal/free text. See [translations](../contributing/translations.md).

`tests/browser/dashboard-target.js`, `studio-target.js` and their HTML hosts belong only to synthetic tests and are excluded from production Docker. The production composition is `static/index.html` plus `application.js`; `/preview` is read-only. Characterization fixtures are historical observations, not another runtime. See [tests](../../tests/README.md), [Dashboard](dashboard.md), [Studio](customization-studio.md) and [presentations](widget-presentations.md).
