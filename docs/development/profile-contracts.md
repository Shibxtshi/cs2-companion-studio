# Profile contracts

These are the active production contracts. The target-only runtime accepts `ccs-dashboard-store` v1; historical/unknown/invalid files are refused without replacement. [Startup rules](target-runtime.md) and [offline recovery](../guides/profile-recovery.md) describe deliberate recovery, not automatic migration.

## Documents, all version 1

companion/profile_contracts.py is the authoritative strict validator. It uses the existing pinned Pydantic dependency; no new dependency or frontend build system is introduced. The production server loads these models through the published-store/runtime composition. No second active store or dual writes exist.

| Document | Format | Contents / boundaries |
| --- | --- | --- |
| Server | ccs-dashboard-store | storeId, catalogRevision, profiles, tombstones, receipts. No activeProfile or device selection. |
| Export | ccs-dashboard-export | Name and complete configuration only; no server identity, revision, receipt or local draft metadata. |
| Local draft | ccs-dashboard-draft | Name/configuration plus storeId, profileId, draftId, baseRevision, localRevision and updatedAt (Unix milliseconds). Persisted by the local draft modules; undo history is session-only. baseRevision 0 denotes a not-yet-created profile. |
| Operation | ccs-dashboard-operation | storeId, unique operationId, profileId, kind, expectedRevision and complete profile content for create/update. Delete has no content. Published through the authenticated WebSocket adapter. |

`inspect_document` classifies recognized, legacy, future, unsupported, invalid and corrupt documents. Recognition identifies a valid declared document kind; only a valid server store is runtime storage. Historical exports are classified separately and not converted. Unknown/future versions, duplicate keys, malformed JSON and non-finite numbers are refused.

All target fields are required, unknown fields are rejected, and scalar types are strict (including rejecting booleans as integer revisions). Printable names/titles must be trimmed and respect their lengths. All numerical revisions/timestamps are non-negative safe JavaScript integers, at most 9,007,199,254,740,991; published profile revisions start at 1.

Identifiers for profiles/widgets are 1–64 ASCII letters, digits, underscore or hyphen. Generation/operation/draft/access identifiers use the specified 32 lowercase hexadecimal form. Names are trimmed printable text, 1–32 characters; widget titles are at most 36 characters. Colors are empty (automatic) or six-digit hex. Opacity is an integer 60–100 in steps of five. Unknown fields and unknown theme/widget identifiers are refused, not silently normalized.

Limits: server 1,000,000 bytes, profile 64,000, export 70,000, draft/operation 80,000; 12 profiles, 60 widgets per profile, 64 persisted operation receipts and 1,024 deletion tombstones. JSON is bounded to depth 24 and 40,000 value nodes. Serialized limits use canonical compact UTF-8 JSON. Callers must bound incoming bytes before decoding, then validate the document; generated JSON Schema alone cannot enforce encoded size or cross-field constraints.

Example published profile inside a server document (synthetic; not a complete store or import file):

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

The example configuration retains current accent/background/density customization while adding theme, navigation, fullscreen and geometry. Empty colors mean automatic theme colors. Theme identifiers and display names are maintained in companion/profile_contracts.py and generated into the browser schema: tactical-blue (default), competitive-red, performance-green, creator-purple, midnight, arctic-white, neon-pink, crimson, solar-orange and monochrome. The format remains v1; existing theme values remain valid, and unknown values are rejected. Widget variant (standard/compact/minimal) is independent of surface style (solid/glass/outline). IDs are unique within each profile, not globally across unrelated profiles. Profile names need not be unique.

### Approved grid decision

The maintainer approved integer cells with columns recorded per profile, 24 by default. The target contract accepts 1–64 columns and 4,096 rows: x/y are non-negative, width/height positive, x+width must fit columns and y+height must fit the row bound. These are storage safety bounds, not promises that every size will be offered by the editor. Overlaps remain valid data. Display rows are 32 px with 8 px gaps; consultation resolves collisions downward and editing rejects occupied destinations. See [layout](dashboard.md) and [Studio](customization-studio.md). Mobile rendering must not overwrite the stored desktop geometry.

## Revisions and pure operations

companion/profile_operations.py implements a pure reducer: validate an immutable input snapshot and command, return a validated new snapshot and receipt, perform no I/O. The published store uses it before committing; the reducer itself performs no I/O.

- Create requires expectedRevision 0 and a new, unused ID. Update/delete requires the current individual profile revision. Successful changes increment that profile revision and catalogRevision. catalogRevision is a delivery/order sequence, not a whole-store CAS precondition.
- Two commands for different profiles can both succeed when each is applied to the latest store. Two stale commands for the same profile conflict. Deletion retains a tombstone, prevents ID reuse, and invalidates an editor's stale base. The last remaining profile cannot be deleted.
- storeId identifies a storage generation. A future reset must change it so stale devices cannot republish into a different generation.
- The same operationId and content replays a persisted receipt without a second mutation. Reuse with different content fails. After the bounded 64-receipt window, an ordinary repeated command fails its stale revision/existence check instead of applying again. There is no unlimited replay journal.
- Tombstones are not silently pruned. At 1,024 deletions further deletion fails explicitly. Compaction or a larger bound would require a later deliberate policy; do not discard deleted identities and permit accidental reuse.
- Stable failure codes include store_changed, revision_conflict, profile_missing, profile_deleted, profile_exists, last_profile, operation_id_reused and resource limits. Invalid private input is not echoed in validation errors.

The published store serializes read-current → reduce → atomic persistence of profiles/revisions/tombstones/receipts → memory swap → acknowledgement/broadcast. A reducer result alone is not a committed save. Disk failure must leave the in-memory published state unchanged. Persisted receipts support lost-response/restart reconciliation at this commit boundary. No multi-process writer support is introduced by P3.

## Runtime and browser ownership

Dashboard reads published configurations only. The Studio uses [local drafts](local-drafts.md), bounded history and [explicit publication](profile-publication.md). Each tab owns its selection; the catalog contains no global active profile. Import/export uses the dedicated export model, never raw server storage. Generated browser schemas come from these Python models; regenerate with `python scripts/generate_profile_schema.py` and verify with `--check`. Cross-field/encoded-size checks also run in the browser validator and server.
