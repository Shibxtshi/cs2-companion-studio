# Explicit profile publication

Production uses this publication path through `companion.server:app`, one authenticated WebSocket and one published store. Local drafts never publish automatically. [Contracts](profile-contracts.md), [drafts](local-drafts.md), [runtime](target-runtime.md) and [recovery](production-activation.md) define the related boundaries.

## Components

| Component | Responsibility |
| --- | --- |
| companion/profile_publication.py | Existing-file-only target store, immutable committed snapshots, serialized atomic publication and public context identity |
| companion/profile_protocol.py | Target commands, acknowledgements, explicit errors and ordered bounded fan-out |
| companion/profile_wire.py | Closed catalog wire model, reusing P3 profile/tombstone validation |
| static/js/draft-publications.js | Configuration-only operation journal in P4's IndexedDB database |
| static/js/profile-publication.js | Explicit publication, retry, uncertainty, conflict consent and cleanup controller |
| static/js/published-profiles.js | Authenticated catalog convergence and independent per-tab selection |
| static/js/draft-session.js | P4 lifecycle plus publication leases and exact captured-state cleanup |

The production `/ws` handler delegates authenticated profile messages to `PublishedProfileProtocol`. PIN, Origin, throttle and connection capacity checks run before catalogs or operations are available. Test-only hosts under `tests/browser/` are excluded from Docker and are not production routes or operator entry points.

The target store requires a pre-existing, valid ccs-dashboard-store v1 document. The store itself never creates or repairs files; `profile_runtime.py` initializes only a genuinely empty installation under the recovery lock. It refuses legacy/future/corrupt storage and paths under static or linked paths. Only one target writer/process is supported; multiple Uvicorn workers or external live file edits are not supported.

## Commit boundary and receipts

Under a target publication lock: decode bounded strict JSON; validate the P3 operation; reduce the latest committed document; validate the complete result; replace the previous valid .bak; atomically replace the complete main document; then swap the in-memory published reference. Profiles, individual revisions, catalog sequence, tombstones and receipts are in that same main replacement. A failed backup/main write produces no success or catalog broadcast and leaves the main published file and memory unchanged. The rotating backup may already contain the current published document if the main write fails.

The reducer is unchanged from P3. Different-profile operations use independent expectedRevision checks; catalogRevision is delivery order, never a global precondition. Deleted IDs remain tombstoned and at least one profile remains. The bounds remain 12 profiles, 60 widgets each, 64 receipts and 1,024 tombstones. Full configuration is validated again server-side, regardless of client validation.

The receipt is persisted before acknowledgement. Repeating an identical operationId/content replays it without another disk write or global broadcast. Reusing that ID with other content fails. A lost reply or process death after replacement can be reconciled by resending the same persisted operation after authentication. If its receipt has been evicted, stale revision/existence/tombstone checks prevent ordinary reapplication, but the client cannot prove whether that old operation previously committed. It keeps an uncertain state and requires explicit review; it never infers success merely from similar content. A confirmed old receipt can also be superseded by a newer published revision; the controller exposes superseded/currentRevision rather than claiming its older snapshot is still current.

Disk work runs outside the event loop and target serialization does not hold the GSI ingestion lock. Published documents are replaced, never mutated; readers copy one committed reference. Slow-peer delivery is concurrent and bounded by the existing fan-out helper. The initiating client receives its acknowledgement before the new full catalog is broadcast. If that acknowledgement fails, healthy peers still receive the committed catalog. Disconnected screens converge after authentication/reconnection, not at one simultaneous instant.

Atomicity is one-file replacement with file flush/fsync, not a multi-file transaction or certification against every filesystem/power-loss failure. Never continue using a simulated crashed in-memory store; restart and read the committed main file.

## Wire protocol

All target commands use the existing authenticated /ws connection. The target adapter caps UTF-8 command bytes at 81,000 (including envelope); the P3 operation cap remains 80,000. Existing binary/transport frame closures, strict numeric/depth limits and client limits remain. Duplicate JSON keys and malformed target documents are rejected.

| Direction | Message |
| --- | --- |
| Server after real authentication | profiles_catalog with catalog: format ccs-dashboard-catalog v1, storeId/accessId, catalogRevision, profiles and tombstones |
| Client | profile_catalog_request (type only) |
| Client / server | profile_import_validate / profile_import_validated or profile_import_error; read-only validated export review, no publication |
| Client | profile_operation with a complete P3 operation |
| Server on commit/replay | profile_operation_ack with storeId, P3 receipt and replayed boolean |
| Server on refusal | profile_operation_error with a sanitized code, valid operationId or null, and latest catalog when available |

Catalogs contain neither activeProfile nor receipts, secrets or live GSI. The existing diagnostics request remains available. Legacy profiles_save is refused by the target adapter; no legacy online writer remains. Import validation has a separate 150,000-byte wire envelope cap and 70,000-byte export cap to allow escaped JSON. It does not mutate storage. There are no public HTTP profile/publication endpoints and the demo never obtains private catalogs.

## Authenticated context

The maintainer approved accessId tied to storeId on 2026-10-28. accessId is the first 32 hexadecimal characters of SHA-256 over the constant public namespace ccs-shared-pin-realm-v1: followed by storeId. No PIN, PIN hash, GSI token, credential or other secret is an input. Both IDs are identifiers, not authorization. The catalog provides them only after actual authentication; P4's access assertion is constructed only then. A PIN change alone does not change the draft realm.

storeId stays stable during one generation and must change on effective reset or intentional rollback/restoration of a target generation. renewed_generation is a pure, explicit helper that validates a document, creates a new generation and drops old receipts while preserving profiles/revisions/tombstones. It performs no I/O, backup or reset itself. Offline activation/recovery must stop the service, verify a private backup, obtain confirmation and install the validated result deliberately. Raw exact-byte recovery remains possible through P3 tooling, but do not resume stale clients against a rolled-back target generation without renewing its identity: an older file may lack receipts for already committed operations.

## Local journal and publication lifecycle

IndexedDB ccs-local-drafts moves from database version 1 to 2 by adding publications; existing contexts/drafts are preserved without conversion. P3 draft v1 is unchanged. The journal stores a validated operation, local captured draft identity/revision/token, optional explicitly reviewed revision and its own write token. Its local capture token is a non-secret compare-and-swap write identifier, not a login/session credential. It contains configuration only, never authentication or network frames. One pending intent per context/profile prevents silent replacement by another tab. Context logout atomically erases drafts and journal entries of every version and invalidates open writer handles.

Publication is explicit:

1. Confirm the authenticated generation and context.
2. Await publicationSnapshot(), then hold a lease on that exact persisted draft.
3. Validate a new operation and commit its stable ID/content/capture to IndexedDB before sending.
4. Send only that immutable operation; wait for the server acknowledgement.
5. Validate operation identity, kind, profile and expected resulting revision. The backend verifies the canonical SHA-256 request digest against its receipt; the client also checks the exact local captured configuration before cleanup.
6. Atomically remove the matching draft and journal after confirmation, then reset history. If the draft has changed, retain it and report published_draft_retained. If cleanup fails, report published_cleanup_error with serverCommitted true; retry cleanup locally rather than declaring server publication failed.

Local saved is never published. Errors carry distinct local/server/network scopes. Important states include draft_ready, validating, publishing, published, local_error, local_conflict, server_error, network_error, revision_conflict, profile_deleted, store_changed, publication_uncertain, reconciliation_required, published_draft_retained and published_cleanup_error. The Studio resolves these codes through the shared JSON translations.

Normal publication blocks editing/undo/discard in that tab until acknowledgement/refusal. Explicit keepDraft releases editing but cannot cancel a request already sent: the journal remains, and its outcome may be uncertain. A late acknowledgement cleans only the original capture; later in-memory edits or another tab's new write token prevent deletion. Their baseRevision is not silently changed. The cleanup transaction itself also blocks same-tab editing until it finishes.

On browser reload, reconcile a pending journal before offering a stale draft for normal editing: its old base may simply reflect a successful publication whose reply was lost. restorePending exposes the persisted operation and retry resends its exact identity/content after authentication. Reconnection never creates a new ID or silently changes expectedRevision. No draft is published merely because it was restored or locally saved.

## Explicit conflict actions

- Keep draft: release editing and preserve configuration/journal; no new network request.
- Use server: require confirmation and the currently reviewed server revision. Discard only a captured local token and its pending intent atomically; concurrent newer work causes a local conflict, never blind deletion.
- Use local: require confirmation, the exact reviewed latest server revision and an unchanged local capture. Create a new operationId with that reviewed expectedRevision; replace only the pending journal entry under compare-and-swap. The stored draft's baseRevision remains its original base. This is explicit whole-profile replacement, not an automatic merge or silent rebase.

After reload without an open session, resolution additionally requires the reviewed local draft token. A deleted profile cannot be recreated by resolving an update; creation needs a new permitted identity. Generic create/delete operations use P3 contracts and the same journal/receipts. Deletion never removes other devices' local drafts; inspection marks them profile_deleted.

## Tab selection and synchronization

Each CCSPublishedProfiles instance owns its selected profile. A full catalog update preserves that selection if it still exists; deletion chooses the first remaining profile locally and emits a status. Another tab is not forced to select it. Old catalog revisions are ignored within a generation; identical catalogs do not trigger redundant change notifications. selectedProfileChanged tells the renderer whether the displayed profile actually changed, even when another profile caused a catalog update. `profile-selection.js` supplies per-tab persistence and a generation-scoped last-used hint for new tabs.

## Tests and measurements

Offline reset/recovery requires stopped writers, verified backup, explicit confirmation and a fresh generation; see [operator procedure](production-activation.md). A PR merge is never an activation command.

See [test commands](../../tests/README.md). Unit/integration tests cover atomic failure/crash/restart, receipts/limits/concurrency, authentication/Origin/frame validation, lost acknowledgement delivery and GSI ingestion while disk work waits. Real browser tests use the canonical app with an explicit synthetic adapter, native IndexedDB, two tabs/devices, reload/restart, confirmed logout, v1→v2 preservation, explicit conflicts and retained newer work. No personal profile or browser data is used.

Optional tests/benchmarks/profile_publication.py reports nine-sample validation, reducer, two-write publication, atomic replacement and fan-out scheduling costs with 12 profiles × 60 widgets and 64 receipts. Fan-out peers there are in memory, not a LAN simulation. The browser runner reports seven explicit 60-widget publications with three real clients at 1280×900, en-US/UTC. Run measurements sequentially on the same machine. Neither is a CI latency gate or a demonstrated performance improvement over the legacy editor.
