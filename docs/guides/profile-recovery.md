# Offline profile recovery

This procedure is for the local maintainer. It works even when invalid profile storage prevents HTTP/WebSocket startup. It never runs automatically. The runtime selects either historical storage or the [target contracts](../development/profile-contracts.md) from the validated document format. The reset commands below concern historical storage only. For target activation, manifest v2, interrupted activation/restore markers and target recovery, follow the [production operator procedure](../development/production-activation.md); do not apply a historical reset to target data.

## Before any write

1. Stop the native service, or stop the Compose service below. Close CCS tabs on all devices so pending legacy autosaves cannot overwrite a recovered configuration after restart.
2. Keep data/, .env and logs/ in place. Do not delete the data directory. Use the same data directory as the stopped instance (PROFILE_DATA_DIR or --data-dir).
3. Run --inspect to classify the file without printing its content. A classification is not permission to erase it. Prefer restoring a valid rotating backup when appropriate; otherwise prepare a distinct reset snapshot.

The --service-stopped flag is an explicit operator acknowledgement, not a running-service detector. The cooperative OS lock serializes recovery tools and is also held for the production server lifespan. It excludes cooperating offline writers while the runtime is active, but cannot identify every external writer or replace a clean service shutdown. Never run reset/restore against a live service, even when the flag is supplied.

## Native Windows / Python

Run from the repository root using the installation's Python environment:

~~~powershell
python scripts/recover_profiles.py --inspect
python scripts/recover_profiles.py --prepare-reset --service-stopped
~~~

The second command prints a randomly generated backup ID; it does not reset anything. Copy that ID, for example into a PowerShell variable:

~~~powershell
$backupId = '<ID printed by prepare-reset>'
python scripts/recover_profiles.py --reset $backupId --service-stopped
~~~

Read the warning and type exactly RESET followed by a space and that ID at the prompt. Enter, an unmatched response or EOF cancels without changing profiles. The snapshot remains. On success, profiles.json contains the historical default profile (five widgets, revision 1). This command does not activate the target format.

Verify the state before restarting the service:

~~~powershell
python scripts/recover_profiles.py --inspect-reset $backupId
python scripts/recover_profiles.py --inspect
~~~

If PROFILE_DATA_DIR is customized but not present in the shell environment, pass --data-dir '<absolute private data path>' to every command. The recovery command does not load .env automatically. Do not paste profile contents, credentials or raw backups into an issue/PR.

## Docker / Compose

Use the existing image with its mounted data volume. No web UI is required. Run from the Compose project directory:

~~~powershell
docker compose stop cs2-companion-studio
docker compose run --rm --no-deps --entrypoint python cs2-companion-studio scripts/recover_profiles.py --inspect
docker compose run --rm --no-deps --entrypoint python cs2-companion-studio scripts/recover_profiles.py --prepare-reset --service-stopped
$backupId = '<ID printed by prepare-reset>'
docker compose run --rm --no-deps --entrypoint python cs2-companion-studio scripts/recover_profiles.py --reset $backupId --service-stopped
docker compose run --rm --no-deps --entrypoint python cs2-companion-studio scripts/recover_profiles.py --inspect-reset $backupId
~~~

The reset command is interactive; type RESET and the ID only after reviewing the operation. These commands require an image containing this recovery implementation. They do not build an image or modify secrets. After a successful current-format validation, restart normally:

~~~powershell
docker compose up -d --no-build --pull never --wait
~~~

## What is preserved

Snapshots are stored under data/profile-reset-backups/<ID>/ (or the configured private data directory), never under static/. Each unique folder contains exact profiles.json bytes, profiles.json.bak bytes when present, and a manifest with sizes/SHA-256 digests. The rotating .bak is not replaced during reset or raw snapshot restore. Reset adds a durable reset-intent.json before replacing the current file; it is not profile content. A prior snapshot is never overwritten or automatically deleted.

Only those two profile files are copied. .env, GSI tokens, PIN, diagnostics and unrelated files are neither copied nor modified. Profiles may themselves contain private names/custom content: keep snapshots private. The implementation refuses static/ paths, linked files/directories, unsafe IDs and sources larger than 16 MiB per file. Incomplete or altered snapshots are refused. Git, Docker context and the archive checker exclude reset snapshots and recovery lock files even if copied outside data/.

POSIX snapshots use private directory/file modes (0700/0600); Windows inherits the private data folder's ACL. This is not encryption or protection against an attacker who can modify that folder. SHA-256 detects changed bytes, not authenticity against such an attacker. Verify appropriate local filesystem permissions.

## Interrupted or failed operation

Keep the service stopped and all snapshot folders. --inspect-reset ID reports:

| State | Meaning / next action |
| --- | --- |
| prepared | The current file matches the original verified snapshot. Review and retry the confirmed reset if still intended. |
| applied | The current file matches the recorded reset target and validates in the current format. Review before restart. |
| changed | The current file differs from both recorded states. Do not force another reset; inspect the situation locally or restore deliberately. |
| missing | The current file is absent. Preserve snapshots and use an explicit restore. |

Backup/confirmation/source-check failure performs no reset. An incomplete snapshot may remain for diagnosis but cannot authorize a reset. Write or validation failure attempts to restore the original bytes; if that rollback also fails, rollback_required explicitly requires manual recovery from the retained verified snapshot. The tool does not claim success on an unverified result. os.replace avoids partial-file exposure; files and POSIX directories are fsynced where supported. Crash tests cover interruptions around replacement, not a guarantee against every hardware/power-loss scenario.

To restore the exact original bytes from a reset snapshot:

~~~powershell
python scripts/recover_profiles.py --restore-reset $backupId --service-stopped
~~~

For Docker, use the same stopped-service compose run prefix as above. Type RESTORE followed by the ID. Before replacement the tool preserves the current file in another distinct snapshot when present and prints its ID, even if the operation is cancelled. The original snapshot and rotating .bak remain. Restoring incompatible/corrupt bytes is deliberate byte recovery, not repair; those bytes may require the software version that originally wrote them and may still prevent this version from starting.

The existing validated rotating-backup workflow remains available:

~~~powershell
python scripts/recover_profiles.py --restore
~~~

Stop the service first. This historical command validates profiles.json.bak against the historical format and preserves any current file as profiles.json.corrupt-<unique ID> before replacing it. There is no automatic fallback to a future/unknown schema. Do not delete recovery files until you have independently confirmed the desired data is retained.
