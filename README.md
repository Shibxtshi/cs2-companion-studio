# CS2 Companion Studio

**Personal, source-available dashboard project for Counter-Strike 2 (CS2)** — customizable widgets, live Game State Integration (GSI), and a responsive interface for phones, tablets, and PCs.

> **Independent personal project, developed with AI assistance.** CS2 Companion Studio is shared by a solo maintainer and was developed iteratively with help from **ChatGPT by OpenAI**, including suggestions and generated code for the interface, backend, tests, and documentation. AI-assisted code can contain mistakes; this project has **not** received an independent security audit. Read the [full development disclosure](AI_DISCLOSURE.md).
>
> **Not affiliated with or endorsed by Valve, Counter-Strike 2, FACEIT, or OpenAI.** The game and company names are used solely to describe compatibility. Use of GSI or an external display does **not** mean any competitive platform has approved the tool. Check applicable rules before competitive use.

**Software version:** `1.0.0` (first-release candidate). A source version does not mean that the GitHub release has been published; check [GitHub Releases](https://github.com/Shibxtshi/cs2-companion-studio/releases) for published packages. Before public launch, the maintainer must complete the license and private-reporting requirements in the [release checklist](docs/releases/checklist.md).

**Languages:** English (default), French (available). [Documentation en français](docs/README.fr.md).

## What it does

- Live personal GSI dashboard over HTTP/WebSocket — **no game memory reading, DLL injection, or in-game overlay**.
- 29 customizable widgets (weapons, ammunition, score, economy estimates, match statistics, equipment, round state, etc.). Some widgets depend on available GSI fields.
- Personalizable layouts: drag, resize, choose styles, create and rename profiles.
- **Server-side profiles** in `data/` shared by PIN-authenticated browsers and devices.
- Demo mode with synthetic values; private profiles are not accessible in demo mode.
- EN/FR interface and guided Windows installer for Steam + Docker Desktop.
- Support diagnostics designed to avoid writing secrets and raw GSI packets. Inspect logs before sharing them.
- Optional **estimated** bomb countdown for private testing; **disabled by default**. Its use in competitive matches may be prohibited. Do not use it on FACEIT without explicit permission.

## Getting started on Windows

**Requirements:** Windows, CS2 installed via Steam, and running Docker Desktop. You do **not** need Python for guided installation.

1. Download the source ZIP **from a trusted release/source**, unpack it into an ordinary folder (not directly from within the ZIP).
2. Start Docker Desktop.
3. Double-click **`INSTALLER_WINDOWS.cmd`**. Choose English or French, confirm the detected CS2 directory, choose whether to enable the estimated bomb countdown (No by default), and follow the prompts.
4. The installer creates a **unique private PIN and GSI token**, writes the game GSI configuration (with backup when replacing an existing one), and starts Docker.
5. Restart CS2 if a GSI config was newly installed; start a training match. Open **`http://localhost:8080`** and enter your PIN.
6. To use your phone, opt into trusted-LAN mode during setup. Connect the phone to the same private Wi-Fi and open `http://YOUR-PC-LAN-IP:8080`.

The installer does not silently install Docker, alter the Windows firewall, or guarantee anti-cheat compatibility. Administrative elevation should only be requested if needed for filesystem access. Detailed instructions: [Windows installation](docs/guides/windows-installation.md).

### Manual installation (advanced)

```powershell
python scripts/generate_config.py
# Ensure generated cs2_cfg/gamestate_integration_companion.cfg is installed under CS2 game/csgo/cfg
# Restart CS2 after adding/changing that file.
docker compose up -d --build
```

**Do not commit** the generated `.env`, PIN, GSI `.cfg`, personal `data/`, or local `logs/`. The public repo contains only `.env.example` and GSI config examples. When updating, keep both **`.env` and `data/`**; profiles live on the server, not in the browser.

### Change settings without rebuilding the image

To enable the optional countdown after installation, set `BOMB_TIMER_ENABLED=true` in your local `.env` (use `false` to disable it). Double-click **`APPLIQUER_REGLAGES_WINDOWS.cmd`**, or run from the project folder:

```powershell
docker compose up -d --no-build --pull never --force-recreate --wait --wait-timeout 120 cs2-companion-studio
```

This reloads the environment by recreating the container using its existing image. A brief interruption resets live match state; saved profiles in `data/` and credentials in `.env` are preserved. Reload the dashboard afterwards. Editing `.env` alone or running `docker compose restart` does not reload container environment variables. The image must already have been built by the initial installation.

The installer asks about the timer only for a new installation. Enter/No and noninteractive installation keep it disabled; rerunning the installer preserves the existing choice. For changes to the PIN, GSI token, port or networking, follow the [Windows guide](docs/guides/windows-installation.md).

## Networking and safety

- Docker binds to **127.0.0.1** by default. LAN mode (`BIND_HOST=0.0.0.0`) is optional: allow port 8080 only on a trusted private network via the host firewall.
- LAN uses **unencrypted HTTP and WebSocket**. Anyone able to observe that network could capture traffic or credentials. Never forward port 8080 from your router or expose it directly to the Internet.
- A single PIN grants dashboard/profile access to the instance. It is not a multi-user account system.
- The `/health` endpoint reports service health, not your private match state. Never post `.env`, live GSI tokens, `data/profiles.json`, or raw Docker logs to a GitHub issue.
- Economy predictions and bomb timing are **estimates** and may be unavailable or inaccurate. The bomb timer is a training/authorized-environment feature, not an approved FACEIT aid.

See [SECURITY.md](SECURITY.md), [technical security notes](docs/security/technical-notes.md), and [rules/limitations](docs/guides/usage-and-affiliation.md).

## Troubleshooting and reporting bugs

- First check `http://localhost:8080/health`; then use the authenticated in-app **Diagnostics** at the bottom of the page.
- Verify `game/csgo/cfg/gamestate_integration_companion.cfg` is installed and CS2 has restarted if GSI stays offline.
- You can optionally attach the **redacted diagnostic export**, after inspecting it manually. **Never attach** `.env`, PIN, generated `.cfg`, `data/profiles.json`, raw Docker logs, or player-identifying screenshots.
- Report bugs through [GitHub Issues](.github/ISSUE_TEMPLATE/bug_report.yml); send security vulnerabilities **privately** according to [SECURITY.md](SECURITY.md).

## Contributing and transparency

This is a **solo personal project being shared with the community**, not an official product or service. Contributions and respectful feedback are welcome, with no promise of a particular response time or feature roadmap.

AI-assisted work is welcome, but please be transparent in pull requests about substantial AI-generated content, what you personally reviewed, and what you tested. See [AI disclosure](AI_DISCLOSURE.md), [contributing guide](CONTRIBUTING.md), and [code of conduct](CODE_OF_CONDUCT.md).

**Local checks:**

```powershell
python -m pip install -r requirements-dev.txt pytest
python scripts/run_checks.py
```

The CI configuration adds Windows/Linux tests, browser tests, PowerShell checks, a Docker smoke test and a dependency audit. See [GitHub Actions](https://github.com/Shibxtshi/cs2-companion-studio/actions) for the current result; earlier successful runs do not validate newer commits. See [release checklist](docs/releases/checklist.md).

## License and credits

**Proposed license: Community No-Resale (custom, draft).** You may use, modify, and redistribute the software free of charge, including for professional use, but may not sell copies or modified versions. Professional use, monetized coaching and paid commissioned development are intended to remain permitted; charging for setup, hosting or support is still under legal review. This is **source-available, not OSI-approved open source**. The `LICENSE` draft is not effective yet; the rights holder, legal wording, and third-party compatibility must be confirmed before publication.

Credits: independent maintainer and community contributors (once any exist); **OpenAI's ChatGPT** for substantial development assistance. OpenAI is **not** the owner, publisher or endorser of this project.

[Functional changelog](CHANGELOG.md) · [Windows setup](docs/guides/windows-installation.md) · [Roadmap](docs/ROADMAP.md) · [Release preparation](docs/releases/checklist.md)

## Project layout

The backend lives in `companion/`, web assets in `static/css/` and `static/js/`, and automated checks in `tests/` (including Docker and Windows verification). Operational Windows scripts are indexed in [installer/](installer/README.md), maintenance commands in [scripts/](scripts/README.md), and safe configuration examples in [examples/](examples/README.md). The server entry point is `companion.server:app`; Docker/Compose and Windows launchers start it. Start with the [documentation index](docs/README.md) or the [architecture guide](docs/development/architecture.md) to find the relevant component.

## Identity and theme preview

CCS uses the Repère identity and local Inter / Barlow Condensed fonts. Tactical Blue is the default; the header offers Competitive Red, Performance Green and Creator Purple previews. The choice is not saved, affects only this tab and resets on reload. Existing profile/widget color choices remain intact; theme persistence will be connected to a later profile contract. See [design foundations](docs/development/design-system.md) and [font licenses/provenance](static/fonts/README.md).

### Dashboard navigation

Use Dashboard for viewing, Customization Studio for the current automatically saved editor, and Settings for display previews, help and diagnostics. Full, compact and hidden navigation plus native/fallback fullscreen are available. Navigation previews are not saved in legacy profiles. The X/Y target renderer and per-tab profile selection remain isolated test foundations until the coordinated storage transition; see [P6 boundaries](docs/development/dashboard.md). Streamer Studio is explicitly marked coming soon.

### Widget presentations

The main dashboard uses the modern Standard presentation for all 29 widgets. Compact and Minimal are supported by the existing target profile contract and isolated renderer tests; their final Studio selection/persistence awaits the coordinated transition. Surface styles remain independent, and estimates/source warnings stay visible. See [widget presentation boundaries](docs/development/widget-presentations.md).

### Target Customization Studio foundations

The isolated P8 Studio composes local IndexedDB drafts, undo/redo, per-widget variants, X/Y editing and explicit versioned publication. It is exercised only with authenticated synthetic target storage. The distributed application still uses its current editor and automatic server save; this PR does not migrate, convert or reset personal profiles. Activation requires a separately reviewed, backed-up and explicitly confirmed transition, including target import/export. See [Studio boundaries](docs/development/customization-studio.md).
