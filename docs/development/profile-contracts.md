# Profile contracts and staged transition (P3)

> Runtime status after P9.5: the delivery status and "current" behavior below describe the original phase baseline. A validated target store now activates these contracts in the production application. Historical storage remains usable before explicit transition. See [Production activation](production-activation.md) for the active composition and operator procedure.


Status: inactive foundations, verified against main after P2 / PR #18 on 2026-10-28. P3 does not activate a new store, change autosave, or reset any profiles at startup. See [architecture](architecture.md), [frontend boundaries](frontend-modules.md) and [offline recovery](../guides/profile-recovery.md).

## Current behavior verified in code

| Concern | Current implementation |
| --- | --- |
| Storage | companion/profile_store.py reads unversioned data/profiles.json: profiles, activeProfile, revision. Each profile has id, name, accent, density and widgets. |
| Limits | 200,000 encoded bytes; 1–12 profiles; at most 60 widgets each; IDs 1–64 ASCII letters/digits/underscore/hyphen. Names are sanitized/truncated to 32 characters, widget titles to 36. |
| Widgets | 29 catalog kinds; span in 3/4/6/8/12; optional color/background, opacity 60–100 in steps of 5; surface style solid/glass/outline. No X/Y or variant. Multiple instances have distinct IDs. |
| Validation | Current validation normalizes optional fields, removes unknown fields and rejects invalid identities/kinds. P3 additionally rejects explicit format/version/schemaVersion markers rather than silently stripping a future contract. Valid current documents keep their behavior. |
| Revisions | One global compare-and-swap revision. Different-profile changes can conflict. activeProfile is shared with all clients. |
| Persistence | Same-directory temporary file, file flush/fsync and os.replace. The previous normalized document is written to profiles.json.bak before the new current file. Memory changes only after successful writes. These are two separate file replacements, not one transaction. |
| Corruption | Bounded reads and JSON depth/finite-number checks. Invalid storage prevents startup before HTTP/WebSocket becomes available; there is no automatic reset. |
| Frontend | static/js/profile-sync.js queues/debounces current autosave (180 ms), with one in-flight save and explicit conflict handling. Pending changes are in memory, not persistent drafts. Existing WebSocket profiles_save/state/error messages remain unchanged. |
| Import/export | studio.js uses cs2-companion-layout version 2, maximum import file 150,000 bytes, at most 60 widgets. Imported IDs are regenerated; unsupported kinds are filtered. This is not the server storage contract. |
| Recovery | scripts/recover_profiles.py --restore validates the rotating .bak and preserves the previous current bytes in a distinct .corrupt-* file. P3 adds separate verified reset snapshots. |

## Target documents, all version 1

companion/profile_contracts.py is the authoritative strict validator. It uses the existing pinned Pydantic dependency; no new dependency or frontend build system is introduced. companion.server does not import or activate the target models. No second active store or dual writes exist.

| Document | Format | Contents / boundaries |
| --- | --- | --- |
| Server | ccs-dashboard-store | storeId, catalogRevision, profiles, tombstones, receipts. No activeProfile or device selection. |
| Export | ccs-dashboard-export | Name and complete configuration only; no server identity, revision, receipt or local draft metadata. |
| Local draft | ccs-dashboard-draft | Name/configuration plus storeId, profileId, draftId, baseRevision, localRevision and updatedAt (Unix milliseconds). Data contract only; no browser persistence/history yet. baseRevision 0 denotes a not-yet-created profile. |
| Operation | ccs-dashboard-operation | storeId, unique operationId, profileId, kind, expectedRevision and complete profile content for create/update. Delete has no content. No route/controller yet. |

Recognized means valid for its declared target document kind, not loadable by the current runtime store. inspect_document distinguishes recognized, legacy, future, unsupported, invalid and corrupt. The current server remains unversioned; legacy is a classification, not an automatic migration. Current export v2 is classified separately. Unknown/future versions are never normalized into current data. Malformed JSON, duplicate keys and non-finite numbers are refused. No permanent support for arbitrary historical versions is promised.

All target fields are required, unknown fields are rejected, and scalar types are strict (including rejecting booleans as integer revisions). Printable names/titles must be trimmed and respect their lengths. All numerical revisions/timestamps are non-negative safe JavaScript integers, at most 9,007,199,254,740,991; published profile revisions start at 1.

Limits: server 1,000,000 bytes, profile 64,000, export 70,000, draft/operation 80,000; 12 profiles, 60 widgets per profile, 64 persisted operation receipts and 1,024 deletion tombstones. JSON is bounded to depth 24 and 40,000 value nodes. Serialized limits use canonical compact UTF-8 JSON. Callers must bound incoming bytes before decoding, then validate the document; generated JSON Schema alone cannot enforce encoded size or cross-field constraints.

Example target profile (synthetic, not the current on-disk format):

~~~json
{
  "id": "p-competitive",
  "name": "Competitive",
  "revision": 1,
  "configuration": {
    "theme": "tactical-blue",
    "appearance": {"accent": "", "background": "", "density": "normal"},
    "navigation": {"mode": "compact", "floatingButton": true},
    "fullscreen": {"showConnectionStatus": true},
    "layout": {
      "columns": 24,
      "widgets": [{
        "id": "w-health", "kind": "health",
        "x": 0, "y": 0, "width": 6, "height": 2,
        "variant": "standard", "style": "solid", "title": "",
        "color": "", "background": "", "opacity": 100
      }]
    }
  }
}
~~~

The example configuration retains current accent/background/density customization while adding theme, navigation, fullscreen and geometry. Empty colors mean automatic theme colors. Themes are tactical-blue (default), competitive-red, performance-green and creator-purple. Widget variant (standard/compact/minimal) is independent of surface style (solid/glass/outline). IDs are unique within each profile, not globally across unrelated profiles. Profile names need not be unique.

### Approved grid decision

The maintainer approved integer cells with columns recorded per profile, 24 by default. The target contract accepts 1–64 columns and 4,096 rows: x/y are non-negative, width/height positive, x+width must fit columns and y+height must fit the row bound. These are storage safety bounds, not promises that every size will be offered by the editor. Overlaps remain valid data. Pixel row height, collision handling, snapping and mobile reflow are deliberately undecided until P6/P8. Mobile rendering must not overwrite the stored desktop geometry.

## Revisions and pure operations

companion/profile_operations.py implements a pure reducer: validate an immutable input snapshot and command, return a validated new snapshot and receipt, perform no I/O. It is exercised by tests but is not an active publication service.

- Create requires expectedRevision 0 and a new, unused ID. Update/delete requires the current individual profile revision. Successful changes increment that profile revision and catalogRevision. catalogRevision is a delivery/order sequence, not a whole-store CAS precondition.
- Two commands for different profiles can both succeed when each is applied to the latest store. Two stale commands for the same profile conflict. Deletion retains a tombstone, prevents ID reuse, and invalidates an editor's stale base. The last remaining profile cannot be deleted.
- storeId identifies a storage generation. A future reset must change it so stale devices cannot republish into a different generation.
- The same operationId and content replays a persisted receipt without a second mutation. Reuse with different content fails. After the bounded 64-receipt window, an ordinary repeated command fails its stale revision/existence check instead of applying again. There is no unlimited replay journal.
- Tombstones are not silently pruned. At 1,024 deletions further deletion fails explicitly. Compaction or a larger bound would require a later deliberate policy; do not discard deleted identities and permit accidental reuse.
- Stable failure codes include store_changed, revision_conflict, profile_missing, profile_deleted, profile_exists, last_profile, operation_id_reused and resource limits. Invalid private input is not echoed in validation errors.

P5 must serialize read-current → reduce → atomic persistence of profiles/revisions/tombstones/receipts → memory swap → acknowledgement/broadcast. A reducer result alone is not a committed save. Disk failure must leave the in-memory published state unchanged. Persisted receipts handle lost responses/restarts only once this commit boundary exists. No multi-process writer support is introduced by P3.

## Approved future behavior and activation dependencies

These are maintainer requirements for later lots, not P3 features:

- Each tab independently selects its displayed profile, using tab-owned state. A local last-used preference may initialize a new tab without switching existing tabs. The server shares configurations only. If a selected profile is deleted, choose a deterministic remaining profile locally and notify the user; preserve an open draft separately for explicit recovery/copy, never recreate a deleted ID silently.
- P4 stores validated local drafts separately from published state, with undo/redo. Drafts contain no PIN, GSI token, match packet or runtime logs. Reload/normal browser closure retain drafts. Server generation/profile/base revision identifies stale drafts. JavaScript consumers must validate the same semantic constraints as the backend, not just trust local storage.
- Voluntary logout asks before erasing local drafts; cancel leaves drafts and session intact. Leaving the future Studio offers save/apply, keep draft and leave, discard, or continue. Keeping a draft does not change the published dashboard. Exact cross-tab draft ownership and local storage failure UX belong to P4.
- P5 introduces explicit publication, error/conflict resolution, receipt-aware retries and synchronized published snapshots. It must retire current autosave only when the coordinated frontend path is ready.
- Activation requires compatible readers/writers, import/export, backend validation, tab-local selection, sync and a renderer that understands the new geometry. The current span renderer cannot read the target layout. Coordinate P5/P6 boundaries rather than activating a target server format against the existing frontend; use a staged inactive path if needed, never two active stores.
- P6/P8 must obtain approval for collision/reflow rules before implementing them; P7 supplies actual widget variants. P2's temporary theme preview is unchanged in P3 and is not yet profile persistence.

Before activating an incompatible format: stop the service and close old CCS tabs; warn the operator; prepare and verify a private snapshot; require explicit confirmation; install/validate the agreed new default; keep recovery bytes. P3's recovery reset intentionally installs only the current usable format. A future target-format reset must be a separate reviewed activation change, not a silent alteration to this command.

## P5 implementation status

P5 implements the previously required atomic commit/acknowledgement boundary, persistent client operation journal and authenticated target catalog as an inactive composition. The default server and legacy frontend remain unchanged. Read [explicit publication and transition gates](profile-publication.md) for operation receipts, conflicts, accessId policy, recovery generations and remaining P6/P8 activation requirements. The P3 storage/export/draft/operation versions and reducer are unchanged.
