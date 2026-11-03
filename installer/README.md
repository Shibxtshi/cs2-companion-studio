# Windows operations

Start commands from the project root. These scripts operate on an installed instance; synthetic verification lives in [tests/windows/](../tests/README.md#windows-checks).

| Root launcher / command | Implementation | Purpose |
| --- | --- | --- |
| `INSTALLER_WINDOWS.cmd` | `install.ps1` | Guided installation or update; preserve existing private settings |
| `APPLIQUER_REGLAGES_WINDOWS.cmd` | `apply-settings.ps1` | Reload .env by recreating the container without rebuilding its image |
| `DESINSTALLER_WINDOWS.cmd` | `uninstall.ps1` | Restore/remove the managed GSI configuration |
| `powershell -File installer/status.ps1` | `status.ps1` | Inspect local service status |

`common.ps1` contains shared filesystem, configuration, Docker and installation helpers; `i18n.ps1` adapts the shared `static/locales/` JSON catalogs for installer messages. Neither is a standalone launcher.

Use the [Windows installation guide](../docs/guides/windows-installation.md) for prerequisites, LAN choices, credentials, backups and recovery. Never upload .env, generated GSI files, installation state or personal profiles.
