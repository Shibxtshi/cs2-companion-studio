# Production profile activation (P9.5)

> V1-01: normal startup is target-only. A genuinely empty data directory initializes an empty target Dashboard automatically. Historical files are refused and preserved; these offline tools remain available only for deliberate recovery/activation. Restoring historical bytes requires the archived compatible application, not this runtime. See [target startup rules](./target-runtime.md).


This guide describes the implemented offline mechanism. Merging code does not authorize an operator to reset personal profiles. Obtain separate maintainer approval before running any mutating command on an existing installation.

## Runtime composition

`companion.server:app` remains the only ASGI entry point. `companion/profile_runtime.py` validates `data/profiles.json` before loading the only supported composition:

| Validated document | Page | Active writer |
| --- | --- | --- |
| Historical profiles | Startup refused; preserve and inspect offline | None |
| Genuinely empty private directory | Initialize target defaults and serve `static/index.html` | `PublishedProfileProtocol` / `PublishedProfileStore` |
| `ccs-dashboard-store` v1 | `static/index.html` | `PublishedProfileProtocol` / `PublishedProfileStore` |
| Invalid, unknown or interrupted restoration | Startup refused | None |

Existing target data is preserved. Historical data cannot start this runtime without a separately confirmed offline transition. There is no public mode switch, automatic conversion, second active store or dual write. New installations initialize the target format automatically; explicit offline initialization remains available for operators. Do not delete an existing directory to initialize it.

The target page loads `application.js`, the P6 renderer, P8 workspace/lifecycle and P4/P5 controllers. It does not load `studio.js` or `profile-sync.js`. Dashboard and Studio share the authenticated WebSocket and catalogue. Profile selection remains local to each tab. Configuration editing writes IndexedDB; only a confirmed publication writes the server. `/preview` is a same-origin read-only popup and does not authenticate or publish independently. Synthetic test routes are not registered in the application.

The runtime holds the existing recovery lock for its lifespan. Offline tooling refuses that lock while the service is running. This is a local filesystem safeguard, not distributed locking: never run multiple hosts against the same network volume.

## Inventory of readers and writers

- Historical: validation/read primitives in `profile_store.py` remain for offline recovery. The historical writer, browser editor and autosave controller are removed from distribution; historical rollback needs the archived compatible application.
- Target: `profile_contracts.py`, `profile_publication.py`, `profile_protocol.py`, `published-profiles.js`, `profile-publication.js`, P4 draft modules and `studio-lifecycle.js`.
- Target Dashboard: `application.js`, `dashboard-grid.js`, widget renderer/presentation; reads published configurations, never drafts.
- Target Studio: workspace, canvas and lifecycle; edits isolated local configurations, publishes through P5.
- Offline: `profile_activation.py` and `scripts/recover_profiles.py`; must run with the service stopped. The online runtime never calls activation.

## Preparation and backup

1. Record the exact currently compatible application commit and retain its source archive or Docker image locally. A SHA in a manifest identifies a version; it does not download or verify that artifact for you.
2. Stop the CCS service/container and close old browser tabs. Preserve `.env`, credentials, the complete private data directory and the retained application artifact. Do not operate against a running mounted volume from another host.
3. Inspect without displaying contents:

   ```text
   python scripts/recover_profiles.py --data-dir PATH_TO_DATA --inspect
   ```

4. Prepare only, supplying the exact 40-character compatible historical application commit:

   ```text
   python scripts/recover_profiles.py --data-dir PATH_TO_DATA --prepare-activation --application-revision HISTORICAL_COMMIT --service-stopped
   ```

The tool validates both historical profile files when present, creates a unique private `profile-reset-backups/BACKUP_ID/` bundle preserving their original bytes, and verifies lengths, SHA-256 and reread data. It writes a separately hashed validated target candidate and an activation manifest. It rechecks that the source has not changed. It does not modify profiles, `.env`, PIN, GSI token or unrelated files. Restrict access to the data directory; Windows confidentiality depends on inherited ACLs. Keep backups off public shares and outside `static/` and release archives.

Unreadable/corrupt historical data is not eligible for activation. Preserve it and use the existing recovery procedure to restore a valid historical state first. Do not interpret failed validation as permission to erase it.

## Explicit activation after approval

P10 uses version 2 of the **private activation preparation manifest**, not a new profile/export/draft contract. Version 1 preparations remain readable for inspection and rollback but must be prepared again before activation. Every confirmed installation attempt writes an exclusive, flushed `.profiles-activation-ID.attempted` marker before replacing the profile file. Never remove this marker or reuse that ID after failure, interruption or historical rollback: prepare a new unique ID and generation. Cancellation before the installation attempt does not consume the candidate. All historical snapshots remain available.

```text
python scripts/recover_profiles.py --data-dir PATH_TO_DATA --activate BACKUP_ID --service-stopped
```

The warning explains that ALL old profile names, layouts and customizations are replaced by one empty target dashboard. This is reset, not migration. Confirmation requires `ACTIVATE BACKUP_ID`. Cancellation preserves the original bytes. The tool revalidates the backup, candidate and unchanged source after confirmation, then installs and validates the new document atomically. A new `storeId` establishes a separate browser draft context. The verified historical backup remains distinct from the rotating `.bak`.

Start the compatible P9.5 application normally. No test launcher is required. Verify PIN, Dashboard, Studio, a local draft, explicit publication, profile/variant after reload and server restart, another tab, GSI, demo privacy, diagnostics and import/export. Do not resume old tabs after switching generations. Never adopt old IndexedDB drafts or pending intents automatically; they remain in their old context. Recover a valid configuration only through an explicitly reviewed target import and a new publication.

## Target import/export

An export is `ccs-dashboard-export` v1 containing only name and complete configuration. Server revisions, store/access IDs, receipts, tombstones, GSI and authentication are excluded. The native file picker does not publish. The authenticated server strictly validates bounded JSON and returns content for review. Users may preview, create a local draft or explicitly replace the current draft, then separately Save and apply. Old `cs2-companion-layout` exports are recognized and refused; no span-to-X/Y conversion is claimed.

## Rollback and interrupted operations

Stop the service/container before restoration. Preserve any target publications; they cannot appear in the historical document. Inspect:

```text
python scripts/recover_profiles.py --data-dir PATH_TO_DATA --inspect-activation BACKUP_ID
python scripts/recover_profiles.py --data-dir PATH_TO_DATA --restore-activation BACKUP_ID --service-stopped
```

The tool creates a distinct verified safety snapshot of current profile files, rechecks source integrity and requires explicit restoration confirmation. If target publication has occurred, the confirmation warns about that loss of visibility. It restores both original filenames and verifies exact original hashes. A pending marker blocks startup if restoration stops between the two files; retain every backup and rerun the same restoration with the service stopped. Do not remove the marker manually to start a partially restored state.

Select the retained historical application/image matching the recorded commit before restarting. Neither restore nor activation edits credentials or installs application binaries. Verify the restored application, GSI and profiles. An unsuccessful activation before replacement leaves the original document intact. After an uncertain interruption, inspect state first; never blindly repeat publication operations across generations.

Inspection classifies file contents; `prepared_or_restored` does not mean an attempted candidate can be reused. Prepare a fresh activation after rollback. An interrupted restoration must be resumed with its own ID before any other preparation, activation or target-backup recovery.

## Synthetic validation only

For a damaged target current document with a valid target rotating backup, stop the service and use `python scripts/recover_profiles.py --data-dir PATH_TO_DATA --restore-target --service-stopped`. This separately confirmed recovery preserves the failed current bytes, restores validated backup configurations into a **new** generation, and clears operation receipts. Publications after that backup are not included. Old drafts and intents are not automatically adopted. Do not use historical raw-reset tools for target recovery.

Backend: `python scripts/run_checks.py`. Production browser composition: `python tests/browser/test_production_studio.py --browser chromium --output PRIVATE_OUTPUT_DIRECTORY` (also Firefox/WebKit when installed). On systems using installed Chrome, set `CCS_CHROMIUM_EXECUTABLE` to its executable path.

The browser suite starts `uvicorn companion.server:app` against a temporary target document; it never substitutes a synthetic ASGI app. Offline tests use pytest temporary directories. Production assets do not depend on the test launchers. Hosted Actions results must be reported separately from local results.
