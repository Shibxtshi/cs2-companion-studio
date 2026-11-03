# Maintenance and troubleshooting

[Français](maintenance.fr.md) · [User guides](README.md)

Run commands in PowerShell from the actual installed project root with Docker Desktop running. Read the effects before executing; these commands are not instructions to change someone else’s installation. Never delete `data/` to fix a startup error.

## Check or restart

```powershell
powershell -NoProfile -File .\installer\status.ps1
docker compose ps --all
```

These inspect status. Open `http://localhost:8080/health` (adapt the host port); a response proves HTTP health, not a functioning match or the exact source commit. After keeping local drafts, `docker compose restart cs2-companion-studio` interrupts connections and clears in-memory match state, preserving mounted files. It does **not** reload changed environment variables.

To reload intentionally changed `.env` settings, double-click `APPLIQUER_REGLAGES_WINDOWS.cmd`, or use:

```powershell
docker compose up -d --no-build --pull never --force-recreate --wait --wait-timeout 120 cs2-companion-studio
```

This recreates the container from its existing image and configuration; no build/pull. It requires that image to exist. Profiles and `.env` remain, but all `.env` changes take effect: PIN changes require reconnection; GSI token/host-port changes require matching CS2 configuration and restart. Do not rotate credentials or enable the estimated bomb timer casually. Editing `.env` alone does not apply settings.

## Compatible target update versus reinstall

1. Review the candidate’s documented format requirements. Keep the previous compatible source/image. There is no general historical migration promise.
2. Keep drafts, close editing tabs and stop CCS. Make and verify a complete [private backup](backup.md), including `.env`, `data/`, `.installer-state/` and GSI recovery files.
3. Extract trusted new application files into a separate folder. Restore copies of private configuration/data only when the new version explicitly supports their target format. Keep the old installation/backup intact and do not run both against the same data or host port.
4. Build/start the new application from its folder with `docker compose up -d --build`. This builds an image and may download its required base/dependencies. It is different from applying settings without a build. Verify PIN, profile, Studio, explicit publication, reload and a training session.
5. If validation fails, stop the new writer and follow the verified [recovery procedure](backup.md). Do not copy files over a running service.

A fresh reinstall is a new private instance, not automatic profile conversion or draft transfer. Import transfers a reviewed configuration, not credentials/server history. Historical recovery uses the offline tools and matching archived application. `docker compose down` stops/removes the project containers and default network; without `--volumes` it does not request named-volume removal, and it does not erase host bind-mounted `data/`, `logs/` or `.env`. Never add deletion flags as a generic troubleshooting step.

## Diagnose without exposing secrets

| Symptom | Check |
|---|---|
| Server unavailable | Docker engine, Compose status, configured port and another instance occupying it |
| PIN rejected | Correct instance and locally retained PIN; wait after repeated failures (temporary rate limiting), never post the code |
| GSI waiting | CS2 restarted after installing its CFG; matching URI/token/port locally; training session, not just menu |
| Missing widget values | Field may not be provided; compare match/GSI freshness and diagnostics, not a guessed zero |
| Stale data | Stop treating it as current; check CS2 and WebSocket reconnect |
| LAN failure | Use [LAN checks](network.md), not disabling the firewall or exposing the router |
| Draft saving error | Keep the tab/work, inspect storage permissions/quota; do not clear browser data as a first step |
| Publication uncertain/conflict | Preserve draft, review server version and use the offered explicit reconciliation |
| Incompatible storage | Stop and inspect offline; do not delete or reset files to force startup |

Settings → Diagnostics distinguishes server, authenticated WebSocket, GSI and active match. Help/quick start can be reopened. Demonstration is not proof of real GSI. `docker compose logs --tail=30` can help **locally**, but raw output may contain sensitive information; never attach it unreviewed. Only share manually inspected diagnostic exports as described in [SUPPORT.md](../../SUPPORT.md). Security reports follow [SECURITY.md](../../SECURITY.md).

## Uninstall

Keep private backups first. Close CCS tabs and run `DESINSTALLER_WINDOWS.cmd` (or `powershell -NoProfile -File .\installer\uninstall.ps1`) from the installation. It restores the backed-up GSI file or removes the managed new file only if it still matches the recorded installed hash. A manually modified GSI file is retained; a missing required backup causes refusal. Successful GSI cleanup can remove its installer state record; keep your backup. Unless `-KeepDocker` is chosen, it calls Compose down. It does not automatically erase `.env`, profile data, logs or private backup directories. Restart CS2 after GSI removal/restoration. Deleting retained private files is a separate deliberate action after verifying recovery needs.
