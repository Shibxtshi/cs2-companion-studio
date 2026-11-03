# Customization Studio

Production `application.js` composes the three-panel workspace, persistent local drafts and explicit publication on the Dashboard’s authenticated transport. No historical editor or autosave writer is active. See the [user walkthrough](../user/studio.md), [runtime](target-runtime.md) and [offline recovery](production-activation.md).

## Responsibilities

| Module | Responsibility |
| --- | --- |
| studio-model.js | Pure validated configuration changes, bounded placement, additions and duplication |
| studio-data.js | Transient GSI/synthetic preview data, bomb anchor and existing demo controls; no persistence |
| studio-canvas.js | Keyed P7 cards, P6 projection, selection and one operation per pointer gesture |
| studio-workspace.js | Library/search/categories, inspector, panel navigation, EN/FR labels and native dialogs |
| studio-lifecycle.js | Compose P4 sessions and P5 controllers; profiles, recovery, conflicts, exit and logout |
| profile-selection.js | Shared per-tab published selection and last-used hint; no cross-tab forced switch |
| tests/browser/studio-target.js | Test-only PIN/Origin transport harness, reconnect and authenticated catalog composition; excluded from Docker |
| studio-preview.js / studio-preview-host.js | Read-only same-origin preview window using the actual P6 shell/grid and P7 renderer |
| customization-studio.css / studio-density.css | P2-token layout and global padding density, independent of presentation and geometry |

The guarded `tests/browser/publication_server.py` remains a synthetic regression host only. Its special routes are absent from production; no launcher is needed to use the integrated Studio.

Existing contracts remain authoritative: [P3](profile-contracts.md), [drafts/history](local-drafts.md), [publication](profile-publication.md), [grid](dashboard.md) and [widgets](widget-presentations.md). No schema/version or backend business calculation changes.

## Editing and layout

Whole-cell snapping, no neighbour pushing, occupied destinations rejected on release, Escape cancellation and preservation of inherited overlaps were explicitly approved. Validation uses saved rectangles. P6 retains its independent reading projection: intrinsic content expansion, responsive layout and downward collision resolution never modify saved coordinates.

Drag/resize moves a ghost rather than rebuilding the board on every pointer event. A valid release commits one P4 operation. Invalid/cancelled release restores the baseline. Numeric fields, arrow controls and keyboard handles are alternatives. Pointer editing is refused when the displayed column count differs from saved geometry. Desktop edit mode has a 960-pixel reference surface inside an internal scroller; narrow layouts remain usable through panel tabs and explicit coordinates.

Rows stay 32 pixels and grid gaps eight. Dashboard density changes global card padding, not variant, numerical meaning or saved dimensions. The same target-density rule is used by Studio and preview. Each widget independently chooses Standard/Compact/Minimal and surface solid/glass/outline. Reading minima can grow for long content, qualified estimates or open details; some Minimal cards can be as tall as Compact. User-selected colors remain overrides and do not guarantee contrast for arbitrary combinations.

## Drafts and profile operations

The existing P4 session accepts either a validated published profile or an explicit creation descriptor (id/name/configuration), never both. Creation starts at baseRevision 0 using the existing P3 contract. It is not a fabricated published profile and cannot reuse a tombstoned identity. New/duplicated/recovered profiles stay local until the P5 create operation is explicitly confirmed. Catalog and local creation counts are checked against 12; server validation remains authoritative.

Native store.list() enumerates only the current storeId/accessId scope, returns decoded records and refuses more than 128 records without deleting anything. It finds local creations after reload/browser closure and retains incompatible/corrupt/orphan records. A valid orphan/stale/in-memory conflict can be copied into a fresh identity after explicit naming; the recovery copy is persisted before old in-memory work is released. Invalid data is never interpreted as a valid configuration. Known records may be explicitly discarded with CAS; unrecoverable malformed metadata can require confirmed context logout.

An unchanged published baseline uses optional persistOnStart:false. Its session state is pristine with hasPersistedDraft:false; no transaction is claimed. The first edit, explicit flush, keep or publication creates and confirms the local record. Existing P4 callers retain their default eager creation. Saved means transaction completion; quota/abort/CAS errors retain memory and the previous valid record. History remains 50 operations / 2 MiB serialized snapshot content, not a total heap ceiling.

Each tab owns selection. Tab sessionStorage remembers that selection; a store-generation-scoped localStorage preference initializes a new tab. There is no storage listener forcing existing tabs to switch. Configurations remain shared. Profile name/theme/navigation/fullscreen edits are local draft changes. Published deletion is separately and explicitly confirmed through P5; it preserves local drafts for recovery and cannot remove the final profile.

## Publication and recovery

Save and apply calls the same P5 publicationSnapshot/lease/journal path. No server write occurs while editing. The UI waits for server acknowledgement, distinguishes local persistence from publication, and blocks normal editing during the ordinary in-flight request. Repeated attempts reuse the persisted operation. Pending intents are reconciled before ordinary resume after reload; retry cannot silently publish a new snapshot.

A timeout/network loss is uncertain, not successful. Keep draft releases editing without cancelling a sent operation. A late acknowledgement is finalized too: only the captured record can be removed; newer edits remain with their original base revision. Retained work is exposed for explicit reviewed resolution, not silently rebased. Server-committed/local-cleanup-failed has a separate local cleanup retry.

Conflict actions show complete local and latest published content, plus the exact reviewed revision. Use local replaces the complete remote profile only after confirmation with a new versioned operation. Use server explicitly discards the captured local version. CAS/revision changes during review fail safely. No field merge or automatic overwrite exists.

Controlled exit offers publish, keep, discard and continue. Keep awaits local completion. Discard confirms and CAS-checks the relevant draft; a pending publication must be reconciled/resolved first. Voluntary logout confirms erasure of the current context's drafts/intents and revokes old handles atomically before closing authentication. Failed erasure leaves the session open. Network loss/reload never erases drafts. A revoked tab must explicitly close its old in-memory session and authenticate again; it cannot silently reopen a new write epoch.

Preview opens a same-origin window instead of weakening frame-ancestors 'none'. Pop-up denial is reported. Only the controlled opener supplies a validated configuration and transient in-memory values using checked origin/source messaging. The preview has no WebSocket or storage writer; it uses the actual P6 navigation and fullscreen recovery controls. Its persistent close button remains above revealed navigation. Preview settings are edited in the parent inspector.

IndexedDB is origin-isolated, not encrypted. Browser eviction/clearing can remove drafts; abrupt process closure can interrupt an unconfirmed write. Unload warns about dirty work but cannot promise an asynchronous flush. No PIN, GSI token, packet or diagnostics are part of the P3 draft or operation.

## Verification

See [test commands](../../tests/README.md). Three real browser journeys cover Studio editing/resume/conflict resolution, profile and transaction/network/disk faults, and 87 combinations/seven resolutions/representative themes/60 instances/keyboard/touch. Production and theme journeys additionally exercise the real ASGI composition and all ten themes. Backend/security, JavaScript, PowerShell and Docker checks remain available. Fixtures are synthetic and P1 golden data is not regenerated.

Optional matrix output provides raw operation timings including automation/debounce where labelled. Measure standalone performance sequentially with real clocks; no arbitrary timing gate or general speedup is claimed. Hosted Actions can be refused before startup for billing restrictions and must not be described as successful. Exact local results and limitations accompany the PR.
