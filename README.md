# CS2 Companion Studio

**CCS — Match Center / Player Edition** is an independent Personal project: a Dashboard for Counter-Strike 2. View available game information in a browser on a PC, tablet or phone, and customize the layout in a separate visual Studio.

Developed with substantial ChatGPT (OpenAI) assistance; see [AI disclosure](AI_DISCLOSURE.md).

[English documentation](docs/README.md) · [Documentation en français](docs/README.fr.md) · [Windows installation](docs/user/installation.md)

> **Version 1.1.0 candidate.** V1.0.0 has been published; this source prepares the next release. The [Community No-Resale License v1.0](LICENSE) sets the source-available terms, **not OSI-approved open source**. License adoption was integrated through an expressly authorized merge; no legal certification is claimed. See [licensing and redistribution](docs/legal/licensing.md), the [informative French translation](docs/legal/LICENSE.fr.md) and [V1.1.0 release notes](docs/releases/release-notes-1.1.0.md).

## Available now

- Read-only Dashboard with responsive X/Y layouts and an independently selected profile in each tab.
- Three-panel **Customization Studio**: widget library, canvas and inspector; move/resize, undo/redo and preview.
- [29 widget types](docs/user/widgets.md), each with Standard, Compact and Minimal presentations. Solid, Glass and Outline surfaces are separate settings.
- [Ten themes](docs/user/themes.md), including the light Arctic White theme; individual widget colors remain overrides.
- Persistent **local browser drafts**. Only **Save and apply** explicitly publishes a configuration to the server and synchronizes authenticated clients.
- Interface, help, Settings, diagnostics and installer in English, French, Russian, Polish, Ukrainian, Czech and Romanian; isolated synthetic demonstration.
- Native Windows guided installer for Steam/CS2 and Docker Desktop; no Python installation required for that installer.

CCS receives Game State Integration (GSI) messages. It does not read game memory, inject code or provide an in-game overlay. Streamer Mode and Overlay Studio are future work. Some fields may be unavailable; economy forecasts and optional bomb timing are estimates. The estimated bomb timer is **disabled by default**.

## Start on Windows

Prerequisites: Windows PowerShell 5.1 or PowerShell 7, Steam/CS2 installed, Docker Desktop with Compose v2 installed and running. Real-machine compatibility beyond recorded tests is not guaranteed.

1. Obtain a trusted source archive and extract it completely into a writable folder. Do not run it inside the ZIP. Use the source ZIP attached to the official GitHub release.
2. Start Docker Desktop, then double-click `INSTALLER_WINDOWS.cmd`.
3. Choose EN, FR, RU, PL, UK, CS or RO, verify the detected CS2 folder and follow the prompts. Keep the locally displayed PIN private. The installer generates/reuses credentials and asks before replacing an unrecognized different GSI file, retaining a backup.
4. Open `http://localhost:8080` (or the configured port). Demonstration works without a running match and cannot access private profiles.
5. Connect with your PIN. A new Dashboard is **empty**. Open Customization Studio, add widgets and choose **Save and apply**. A locally saved draft alone does not change the Dashboard.
6. Restart CS2 after installing/changing GSI configuration, then use a training session to check real data.

Follow the [full Windows guide](docs/user/installation.md), [first-use walkthrough](docs/user/first-use.md) and [Studio guide](docs/user/studio.md). Linux/native development and disposable tests are described in the [developer index](docs/development/README.md); the guided installer is Windows-only.

## Network and privacy

Localhost is the default. Other PCs, tablets and phones require explicit trusted-LAN setup; see [LAN access](docs/user/network.md). HTTP/WebSocket traffic is **not encrypted** and the PIN does not encrypt it. Never expose CCS directly to the Internet or forward its port from a router. Docker Desktop/WSL2, firewalls and Wi-Fi isolation can prevent LAN access.

One shared PIN authorizes access to the instance’s published profiles; this is not a multi-user account system. Preserve `.env`, `data/` and private recovery files. Never share credentials, generated GSI configuration, personal profiles or raw runtime logs. See [security](SECURITY.md), [backups/recovery](docs/user/backup.md) and [troubleshooting](docs/user/maintenance.md).

## Documentation and participation

- [User guides](docs/user/README.md): installation, Dashboard, Studio, widgets, themes and maintenance.
- [Contributors](docs/contributing/README.md): scoped issues/PRs, widgets, themes, translations and tests.
- [Developer reference](docs/development/README.md): architecture, contracts, data flows, security and checks.
- [Support](SUPPORT.md), [security reporting](SECURITY.md), [roadmap](docs/ROADMAP.md) and [unpublished release checklist](docs/releases/checklist.md).

A solo maintainer reviews work on a best-effort basis; no response time is promised. Contributions require the explicit permissions described in LICENSE section 9; no transfer of ownership or general future relicensing permission is presumed. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Independence, AI assistance and credits

CCS was developed with substantial **ChatGPT/Codex by OpenAI** assistance across code, UI, tests and documentation, with iterative maintainer testing. AI-generated work can contain errors; no independent security audit or competitive-platform approval is claimed. Read the [full AI disclosure](AI_DISCLOSURE.md).

CCS is **not affiliated with or endorsed by Valve, Counter-Strike 2, FACEIT or OpenAI**. Check applicable competitive rules; GSI access does not establish permission to use an aid. See [usage limitations](docs/guides/usage-and-affiliation.md).

The Repère identity is project artwork. Local Inter and Barlow Condensed fonts retain their [SIL OFL notices and provenance](static/fonts/README.md). Third-party components retain their own terms; the CCS license does not replace them. [Changelog](CHANGELOG.md) · [Code of conduct](CODE_OF_CONDUCT.md).
