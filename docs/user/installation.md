# Windows installation

[Français](installation.fr.md) · [User guides](README.md)

## Before starting

Use Windows PowerShell 5.1 or PowerShell 7, Steam with CS2 installed, and Docker Desktop with Compose v2 running. The guided installer does not require Python and does not silently install Docker. Obtain a trusted source archive; a source version `1.0.0` does not establish that an official release exists. Extract the complete ZIP into a writable folder before running anything.

## Guided installation

1. Start Docker Desktop and wait for its engine.
2. Double-click `INSTALLER_WINDOWS.cmd` in the extracted project root. The launcher uses a process-only PowerShell execution-policy bypass; run only trusted scripts.
3. Choose EN (default) or FR. The browser language can be chosen independently later. Confirm the detected Steam/CS2 folder. Secondary libraries are searched.
4. If detection fails, use Steam → CS2 → Manage → Browse local files to find the folder containing `game/csgo/cfg`. From the project root, substitute its actual path:

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\installer\install.ps1 -Language EN -Cs2Path 'D:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive'
   ```

5. A new installation generates a private PIN and a separate GSI token. An existing `.env` is reused; never post it or the displayed PIN. Keep the estimated bomb timer disabled unless the intended use is explicitly permitted.
6. The installer checks GSI folder access first. Only a filesystem permission problem may offer consent to UAC; Docker failure is not a reason to elevate. Refusing a required operation stops that installation. It asks before replacing a different GSI file and saves its original under private `.installer-state/`. Preserve that directory for uninstall/recovery.
7. Choose local-only access unless you need another device. See [LAN setup](network.md) before opting in. No firewall rule is created automatically.
8. The installer builds/starts CCS. Open `http://localhost:8080` (or your configured port). Use Demonstration for synthetic data, then connect with the PIN. A fresh Dashboard is empty; follow [first use](first-use.md).
9. Restart CS2 after adding/changing `gamestate_integration_companion.cfg`, then start a training session. GSI reception alone does not prove an active match.

English confirms with Y; French with O. Empty/unknown input normally declines a prompt. For automation, inspect the script parameters first; do not use overwrite/noninteractive options to bypass an unexplained conflict.

The installer does not delete or convert incompatible profile storage. Historical data requires [offline recovery](backup.md). Linux/native development is documented separately in the [developer guide](../development/README.md); this is not a claim of a tested Windows hardware/support matrix. See [maintenance](maintenance.md) before updating or uninstalling.
