# Proposed target activation — separate approval required

> HISTORICAL RECORD — this dated phase report/plan is retained for provenance, not current operating instructions or current test evidence. Production is now target-only; historical files are refused without replacement. Use the [documentation index](../README.md) and [current operator procedure](production-activation.md).


> P9.5 update: these phase boundaries describe their original delivery. The integrated production composition and the explicit, separately authorized transition are documented in [Production activation](production-activation.md). Valid historical installations remain usable until offline confirmation.


Status: P9 planning only. No production activation, migration or reset is implemented or authorized here. P10 must validate the final active composition, so schedule an explicit activation lot after P9 and before P10.

## Verified current boundary

Production companion.server:app still constructs the historical ProfileStore. Production studio.js retains the historical editor and automatic server saving. The guarded tests/browser/publication_server.py composes the P3–P8 target only for disposable synthetic storage. Target frontend modules are not an installation switch.

P3 validates geometry, profile revisions, tombstones and operation receipts. P4 isolates local drafts and history. P5 commits versioned operations atomically and handles uncertain replies. P6/P7 render target geometry and presentations. P8 composes Studio editing, drafts, explicit publication and per-tab selection. These components do not establish that every production entry point is ready for target storage.

## Dependencies and implementation sequence

1. Inventory every production reader/writer: ASGI startup, authenticated catalog, Dashboard, Studio, import/export, recovery scripts, installer, restart/upgrade and Docker packaging. Specify a single supported active target composition and retire the test launcher as an operator path. Keep authentication, Origin checks and message bounds unchanged.
2. Complete target profile import/export UI and server validation. Use P3's dedicated export contract, not a raw server store or a draft. Exclude receipts, tombstones, access context and all secrets. Reject unsupported versions and oversized/malformed documents. Preview the imported content and require explicit create or reviewed replace publication through P5; never overwrite as a side effect of file selection. Historical exports must be recognized and explained, not silently interpreted as target geometry.
3. Integrate the target Dashboard, per-tab selection and full Studio navigation with one authenticated transport lifecycle. Configure profile theme/navigation/fullscreen from published state; edit them only as local drafts. Verify reconnect, deletion fallback and shared configuration without forcing selection in other tabs.
4. Replace historical autosave and its readers in the same activation change. Draft autosave is IndexedDB only; Save and apply is the sole configuration publication path. No dual write or public partial-mode switch.
5. Rehearse the complete offline transition and rollback on synthetic directories before offering it for real data. Package a recoverable previous compatible application version, not just a profile file.

## Reset or migration — decision pending

Recommended: explicit reset to a validated target baseline, retaining a complete private historical snapshot. Existing historical span/order layouts are not target X/Y layouts. A faithful converter is not implemented.

Alternative: a separately implemented deterministic converter with a reviewable preview and preservation of all supported personal configuration. This needs approved placement rules and additional tests; do not advertise migration until implemented and verified. In either case preserve the original bytes and require explicit confirmation. No permanent backward compatibility is promised.

## Operator transaction and private backup

1. Explain exactly which profiles/layouts/settings change, which credentials stay unchanged, and how to restore. Resolve pending server operations and warn about browser-local drafts before stopping the service. Close old tabs and all writers.
2. Inspect the file format while offline. Do not fall back to empty defaults on a read/validation error. Capture one consistent source snapshot under the existing recovery rules, rejecting unsafe paths/symlinks. Preserve the data directory.
3. Create a unique private recovery directory outside static and outside distributed archives. Keep the historical source bytes, schema/version information, application revision and a minimal manifest with byte length and SHA-256 digest. Do not copy PIN, .env, GSI tokens, packets or logs into this profile backup. Enforce owner-appropriate permissions; document the exact path.
4. Reopen the backup and verify its digest, length and supported format against the stopped source. Never overwrite an existing recovery snapshot. If any copy/verification step fails, leave the source unchanged and do not proceed.
5. Show the verified backup location, chosen reset/migration preview and rollback instructions. Require a distinct explicit operator confirmation. Cancellation leaves source bytes untouched.
6. Prepare and validate the complete target document with a new storeId. Atomically replace the intended profile document only with a coordinated target-compatible application version. Preserve all other data/, .env, credentials and backups. Fail closed if the file changed since inspection.
7. Start the one target service and check health, correct PIN, rejection of wrong PIN, authenticated catalog, GSI, render, draft persistence, explicit publication, restart durability, import/export, profile deletion and reconnect. Keep the private snapshot indefinitely until the maintainer chooses otherwise.

## Browser drafts and generations

Do not erase IndexedDB during a source update or reset. Old drafts belong to a storeId/accessId and must not be automatically adopted into a new generation. Present incompatible/orphan records honestly and provide only validated explicit recovery into a new identity. Preserve unknown or corrupt records until the user chooses a supported removal action. Changing PIN alone does not change accessId under the approved storeId-derived policy.

Resolve or retain pending publication intents before transition; never silently resend them into a new generation. An uncertain operation requires reconciliation against the original generation or explicit recovery handling. Confirmed voluntary logout retains its existing warned deletion/revocation policy, distinct from an upgrade.

## Failure and rollback

Before target startup succeeds, retain the failed candidate separately, keep the service stopped, restore the exact verified historical snapshot atomically and use the matching historical application version. Verify restoration before restarting. Never feed a target document to an old reader.

After real target publications, rollback is a new operation: preserve that target state and warn that returning to the historical snapshot omits later changes. Require confirmation, stop writers and restore the compatible application/document pair. Deliberate reuse/reset of a target snapshot must renew generation identity and clear/reconcile receipts under P5 rules so old clients cannot replay stale operations. A live raw file copy is not a safe rollback procedure.

## Acceptance gates before real activation

- Windows/Linux backend/security and JavaScript suites; PowerShell and disposable Docker installation/restart/recovery checks.
- Chromium/Firefox/WebKit: all 29 widgets/87 presentations, four themes, seven supported sizes, keyboard/touch and focus.
- Two tabs and devices: independent selection, same-profile conflict, different-profile publications, local CAS and logout revocation.
- Quota/transaction failure, disk failure, lost acknowledgement, restart, deleted profile, future/corrupt file and unsupported import.
- Verified backup failure/cancellation leaves original bytes unchanged; rollback restores the compatible application/document pair and preserves credentials and unrelated private files.
- Maintainer approval of the transition plan, reset versus migration, synthetic rehearsal results and the final real-data operation. Hosted Actions blocked by billing must be reported as not executed, never green.

The activation lot must deliver an operator guide with concrete commands and fresh evidence before requesting execution approval. P9 supplies this proposal only.
