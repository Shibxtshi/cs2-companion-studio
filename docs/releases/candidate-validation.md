# Private candidate validation before publication

This is an operator procedure, not a release announcement, permission to deploy, or a completed acceptance report. Use the [release checklist](checklist.md), [draft release notes](release-notes-1.0.0.md) and [test guide](../../tests/README.md). Keep artifacts/results private until reviewed. The [LICENSE](../../LICENSE) is still a non-effective draft; technical success cannot grant legal or publication approval.

## Record evidence

For each gate record ID, requirement, severity, method, environment, command, exact source commit, expected/observed result, evidence, residual risk and decision. Use only PASS, FAIL, BLOCKED, NOT_RUN or NOT_APPLICABLE (with justification). An old run, mocked installation or HTTP 200 alone does not validate the final product. Record intermediate failures and rerun affected checks after changes. Keep secrets out of reports.

## Synthetic test instance

1. Work from a clean candidate commit and produce a private source ZIP outside the checkout. Check it with `python scripts/check_public_archive.py PATH_TO_ZIP`, record SHA-256/size, extract and verify required files. The source archive intentionally includes reproducible tests/documentation; Docker must package only production assets and its explicit recovery tool, not test routes or harnesses.
2. Use a distinct extraction, synthetic credentials, synthetic CS2 folder when applicable, empty data/log directories, free host port and unique Compose project. Never reuse personal files/volumes, an existing browser profile or the usual CCS container. Review bind paths before every mutating command.
3. Run Windows PowerShell parsing/helpers/locales. They mock Docker/HTTP and cannot prove real Docker Desktop or UAC. Real permission tests need an authorized disposable machine/VM, writable and permission-denied folders, explicit consent/refusal, existing/managed/manually edited GSI files, backup/restoration and Docker failure without unjustified elevation. Never alter a real Steam installation to complete a checkbox.
4. Build from the exact extracted candidate. Use `docker compose -p UNIQUE_TEST_PROJECT -f PATH_TO_TEST_COMPOSE up -d --build --wait --wait-timeout 120` only after verifying its isolated environment and free port. Builds can download pinned bases/dependencies. `compose config --quiet` is only configuration validation.
5. Verify the first Windows bind-mount startup with genuinely empty data. Check PIN, empty Dashboard, Studio add/edit/variant, explicit publication, restart/recreate and unchanged published content. Recheck mounts, UID 10001, read-only filesystem, private HTTP paths, GSI synthetic reception and absence of packaged test hosts. Native Windows or Linux-only startup does not substitute for Windows Docker bind-mount evidence.
6. Stop/remove only the named test project when finished. Retain its private data/evidence as needed; no automatic retention cleanup or personal service action. Never run broad prune or delete commands.

## Compatible target update

Use synthetic profiles/themes/widgets/revisions, a draft and a private verified backup. Keep the browser origin and context when checking draft persistence. Stop the baseline writer, preserve exact .env/data/installer/GSI bytes and the compatible application artifact, install the candidate files, then restart only the isolated instance. Verify credentials, storeId/revisions, published widgets/theme/customization, retained draft, explicit next publication and restart. No file-selection/import step publishes automatically. Historical data is refused unchanged; recovery is a separate stopped-service, verified-backup, explicit-confirmation procedure, not automatic migration. See [backup guidance](../user/backup.md) and [offline recovery](../guides/profile-recovery.md).

## Real Windows, CS2 and LAN acceptance

These need an authorized test machine/network and human observations. Mark NOT_RUN until performed; do not use synthetic packets or browser emulation as real-world proof. Record PASS/FAIL and notes for every row.

| Action | Expected result / evidence |
|---|---|
| Trusted archive, Windows guided installer, EN/FR | Actual Steam/CS2 path reviewed; local credentials/config generated privately; no Python required for guided setup |
| Writable folder and genuine permission failure; refuse/accept UAC | Consent only for the required filesystem action; Docker failure does not elevate; no unexplained overwrite |
| Existing/managed/manually edited GSI config; uninstall | Backup before unmanaged replacement; modified file retained; correct restore/remove based on recorded hash; private data preserved |
| Restart CS2, enter an authorized training match | Distinguish server connected, GSI active and match active; no competitive-platform approval implied |
| Health/armor, weapon/ammo, money, map/round/score, received stats and bomb states | Compare actual available game fields, not invented data; forecasts stay estimates and bomb countdown stays disabled by default |
| Leave/rejoin game, stop signals | Current freshness expires after the implemented 20-second window plus broadcast; provider/identity packets do not keep old game values live |
| Explicit trusted-LAN opt-in and second device | Correct PC IPv4/configured port, PIN authentication, same published catalog, independent tab selections and browser-local drafts |
| Publish from one device and reconnect another | Acknowledged published change synchronizes affected profiles without unsolicited selection changes |
| Return isolated test to localhost | No router exposure, firewall disabling or silent network rule; plaintext HTTP/WS and PIN-not-encryption limits remain understood |

Do not post PIN/token, generated GSI CFG, profiles, raw packets/logs or identifying screenshots. Use manually inspected diagnostic exports and a minimal synthetic reproduction. Preserve unresolved recovery markers and backups.

## Separate decisions

- Technical: no open P0/P1 and required installation/runtime/browser/persistence/security evidence available; list limitations explicitly.
- Legal: qualified review and maintainer approval of effective terms, contribution/asset rights and third-party compatibility; Codex review is not legal clearance.
- PR merge: review the scoped changes and exact-HEAD local/hosted evidence; merge requires maintainer consent.
- Publication: all blocking checklist criteria, verified private-reporting readiness at an approved public transition, final artifact/capture/notes approval and explicit tag/release/visibility authorization. A merged PR is not that authorization.
