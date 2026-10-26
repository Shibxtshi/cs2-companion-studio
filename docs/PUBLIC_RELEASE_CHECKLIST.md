# Public release checklist (V1P)

The step-9 archive is a **publication candidate**, not a published or security-certified release. Use this checklist **before making the repository public**.

## Ownership, licensing and openness — BLOCKING

- [ ] **Finalize and approve the no-resale source-available license.** `LICENSE` is currently a **non-effective draft**: obtain qualified legal review, confirm the intended distinction between selling copies and permitted commercial use/services, and verify that the confirmed attribution `Copyright (c) 2026 Shibxtshi` correctly identifies the holder entitled to license all original contributions. Check compatibility with third-party dependencies/assets before publication.
- [ ] Confirm the README labels the project **source-available**, not OSI-approved open source, and that [AI disclosure](../AI_DISCLOSURE.md) accurately describes its personal nature and significant ChatGPT contribution. Do **not** erase AI attribution.
- [ ] Confirm names/brands are used only for compatibility descriptions and no affiliation/approval is claimed.
- [ ] Confirm no copied proprietary CS2 assets, Valve logos, FACEIT marks or third-party graphics are distributed without permission.

## Security and privacy — BLOCKING

- [ ] Enable GitHub **Private Vulnerability Reporting** or publish a tested private security-contact mechanism; update [SECURITY.md](../SECURITY.md).
- [ ] Configure a usable private conduct-reporting contact; update [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md).
- [ ] Verify that `.env`, PIN, generated `.cfg`, `data/profiles.json`, `logs/` and `.installer-state/` are **not tracked** in Git or included in the public archive.
- [ ] If a secret has ever been posted in public source or a release, **rotate it**; deleting the file from the tip is not enough to remove it from Git history.
- [ ] Review the repository history and scan release artifacts for personal data and secrets.
- [ ] Confirm firewall rules keep port 8080 on localhost or a **trusted LAN only**; do not publish port 8080 to the Internet.
- [ ] Leave bomb-timer assistance disabled by default and maintain explicit platform-rules guidance.
- [ ] Review support diagnostic exports for unintended identifiers.

## Quality and release process — BLOCKING

- [ ] Push first to a **private GitHub repository** (not public yet); run every CI job and fix failures. Workflow existence is not proof of successful execution.
- [ ] Confirm Windows and Linux Python suites, PowerShell 5.1 parsing/helpers, Chromium/Firefox/WebKit browser tests, Docker smoke tests, and dependency audit/SBOM all pass.
- [ ] Run `python scripts/run_checks.py` locally.
- [ ] Rebuild the Docker image using the pinned runtime dependencies; check startup and authenticated access.
- [ ] Test Windows guided installer with no elevation and the genuine permission-required scenario on a test machine.
- [ ] Validate a fresh install on Windows with Steam/CS2 training and a second device on trusted Wi-Fi.
- [ ] Validate upgrade from existing instance preserving `.env` and `data/`; confirm profiles survive restart and update.
- [ ] Capture **fresh screenshots of the current release** using synthetic/demo values only; do not reuse outdated screenshots.
- [ ] Run `python scripts/check_public_archive.py <your-release-zip>` on the final artifact before upload.

## Publishing

- [ ] Choose a GitHub organization/owner and stable repository name.
- [ ] Fill in repo metadata: description, topics, issue templates, repository settings.
- [ ] Protect the default branch and require relevant checks if appropriate.
- [ ] Tag `v1.0.0` or chosen semantic version **only after** all checks are green.
- [ ] Publish an honest changelog and known limitations; avoid phrases like "VAC safe" or "FACEIT approved".
- [ ] Make repository public once ready; verify links and downloadable archive again.

Uncompleted items are **release blockers**, not warnings to silently ignore.
