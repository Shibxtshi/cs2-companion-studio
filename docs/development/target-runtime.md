# Target-only production runtime

V1-01 distributes one Dashboard and one Customization Studio through companion.server:app.
The service accepts only a validated ccs-dashboard-store version 1. It never chooses a historical frontend.

## Native first start

An absent data directory is created after credential validation. Under the cooperative recovery lock,
only an empty directory (optionally containing an empty .gitkeep and the lock file) can initialize profiles.json.
The validated defaults contain a fresh storeId, revision-1 profile, Tactical Blue, compact navigation
and an empty 24-column Dashboard. No game values or credentials enter that document.

The initializer atomically writes a unique staging file in the same directory, flushes it, then publishes
it with a no-replace hard link. A competing profiles.json cannot be overwritten. The staging link is
removed afterwards and the directory is synced where supported. If the filesystem does not support
this operation, startup fails rather than falling back to an overwrite. Interrupted staging artifacts
without a main document prevent a later startup from treating the directory as new.

An existing valid target document is read without reinitialization. The ASGI lifespan acquires the same
cooperative lock and rechecks the document before serving; a second writer or offline recovery is refused.
This does not authorize multiple server workers or protect against arbitrary non-cooperating external tools.

## Existing and interrupted data

Historical, corrupt, future or unknown documents stop startup with an inspection/recovery instruction.
The document and rotating backup are not replaced. A missing main file with any backup, activation,
restore, initialization or unrelated private artifact also stops initialization. A pending restore blocks
startup even when a valid main file exists. Preserve every artifact; never delete markers to force startup.

Run the official offline inspector against the identified stopped installation. Existing historical data
requires separately confirmed backup/activation, or the archived compatible application for a historical
rollback. This is not a migration and no operation is triggered by startup, upgrade or PR merge.
See [production activation and rollback](production-activation.md) and [offline recovery](../guides/profile-recovery.md).
New installations do not need P10-B activation or an operator confirmation to create an empty Dashboard.

## Active ownership

- profile_runtime.py: safe native initialization, strict loading and lifespan lease.
- profile_publication.py / profile_protocol.py: the sole published store and authenticated operation path.
- profile_store.py: shared atomic IO, catalog bounds and historical validation for offline tools; no active historical writer.
- profile_activation.py / profile_recovery.py: explicit offline backups, activation and recovery only.
- application.js: shared authenticated Dashboard/Studio composition and per-tab selection.
- Studio lifecycle, draft modules and publication controller: local drafts and explicit Save and apply.

Historical profiles_save messages are rejected by the target protocol; no autosave branch remains in the server.
Legacy HTML and editor/sync scripts are not distributed. Synthetic test hosts remain outside production routes
and packaging. Test-only historical fixture builders are never shipped in Docker.

## Regression checks

Run python scripts/run_checks.py for backend/security/storage checks, including test_target_runtime.py.
The fresh production browser journey starts the real server with no profile file and verifies initialization,
PIN, Studio, explicit publication, synthetic GSI and missing legacy assets. Production acceptance/resilience,
rendering and widget suites retain coverage of drafts, publication, variants and responsive behavior.
