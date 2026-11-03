# Export, backup and recovery

[Français](backup.fr.md) · [User guides](README.md)

## Profile transfer is not a complete backup

Studio exports the selected **published** profile as `ccs-dashboard-export` v1: name and complete configuration, including theme, widgets, variants and geometry. It excludes store/access IDs, server revisions, receipts, tombstones, authentication, local draft metadata and game data. Custom titles can still be personal: review the file before sharing. An uncommitted draft is not included.

Import requires a valid target export (maximum 70,000 encoded bytes; bounded JSON/profile limits also apply). Unknown/future/malformed files are refused. Old `cs2-companion-layout` exports are recognized but incompatible: no conversion is provided. In Studio, select Import, inspect the review/visual preview, then explicitly create a local draft or replace the current draft. Replacing a draft is not replacing the published server profile. Only a separate Save and apply publishes. Keep existing work before a deliberate replacement and review any revision conflict.

## Complete private backup

**Before copying active profile storage, stop all writers.** Close editing tabs after keeping their drafts, run `docker compose stop cs2-companion-studio` from the installed project root, and verify `docker compose ps --all`. Do not copy a live file and describe it as a consistent backup.

Copy `.env`, the complete `data/` directory (including `.bak`, private bundles and markers), `.installer-state/` and any generated GSI configuration needed for recovery to a distinct private location outside the installation and web assets. Preserve the application source/image revision as well. Do not upload these files. Ordinary filesystem copying is a private operator action, not an automatic CCS full-backup feature. Check sizes and SHA-256 (`Get-FileHash -Algorithm SHA256 -LiteralPath <file>` with a real path), reread copies and retain originals. A hash detects changed bytes, not protection against an attacker who can modify the bundle. Browser drafts are separate IndexedDB records; this server backup does not include them.

A current target document preserves its generation/revisions during a compatible update. Do not hand-edit storeId or replay old operations after a rollback. `profiles.json.bak` is a rotating previous accepted document, not an independent archive. Restoring target state deliberately creates a new generation and clears old receipts.

## Offline recovery

Use the [official operator reference](../development/production-activation.md) and [offline command guide](../guides/profile-recovery.md). Identify the actual data directory and retained compatible application before any replacement. Keep the service stopped, inspect first, back up and obtain explicit confirmation. Never delete `.pending` or `.attempted` markers to bypass an error.

- Damaged target current file with a valid target backup: the explicit `--restore-target --service-stopped` path preserves failed state, validates the backup and installs a new generation. Later publications may be absent.
- Historical storage: current startup refuses it without changing files. The explicit verified preparation/activation resets to an empty target Dashboard; **it does not migrate** old layouts/names/customizations. Retain exact original bytes, the historical `.bak` and a compatible archived application/image before approving it.
- Returning to historical bytes requires that archived historical application; the current target-only runtime cannot serve them.

The recovery tools operate only on profile files/bundles, not the PIN or GSI token. They do not replace the need to keep `.env` and installation/GSI backups separately. Invalid backups or changed sources must stop recovery, not justify erasing data. Unknown/corrupt local drafts are not silently adopted or deleted. Intentional logout has its separate warned deletion policy.
