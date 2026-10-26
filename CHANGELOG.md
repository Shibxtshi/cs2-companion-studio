# Changelog — user-visible changes

Development-stage names are retained as historical milestones. **v1.0.0 is a release candidate and has not yet been publicly released.**

## v1.0.0 — release candidate (unpublished)

- First proposed public stable version of the independent, AI-assisted CS2 GSI dashboard.
- 29 configurable widgets, bilingual interface, authenticated WebSocket live data, shared server-side profiles, Windows installer and Docker deployment.
- Verified eight private CI checks on `main`: Windows/Linux, PowerShell, Chromium/Firefox/WebKit, Docker and dependency auditing.
- Fixed Docker restart readiness, Firefox CSP-safe browser test assertions and Firefox container HOME; used prebuilt Playwright image to avoid slow Ubuntu dependency downloads.
- Preserved localhost default, isolated public demo mode and disabled-by-default estimated bomb timer.
- Known limitations: no independent security audit, unencrypted trusted-LAN HTTP/WS, and no guarantee of approval for competitive platforms.



## V1P-G — Step 9: public repository preparation

- Reorganized the README around installation, features, limitations, support and public release status.
- Added **explicit, prominent disclosure** of the personal/solo nature of the project and extensive ChatGPT (OpenAI) development assistance, including an in-app Help note.
- Added GitHub issue / PR templates, contribution and community guidance, security reporting draft, release checklist and French overview.
- Documented the proposed MIT license; maintainer holder must be confirmed before public publication.
- **No planned changes to GSI behavior, profiles, widgets, Docker configuration or the Windows installer.**

## V1P-F / V1P-F.1 — Step 8: quality and security

- Added broader security tests and GitHub CI definitions for Windows, Linux, browsers, Docker and dependency audit.
- Improved WebSocket Origin checking.
- Fixed secret scanning so local `.env` does not fail checks, while tracked secrets and public ZIPs remain prohibited.

## V1P-E / V1P-E.1 — Step 7: experience and sharing

- Improved onboarding, diagnostics, help, mobile UI and translations.
- Centralized profiles on the server, with multi-device sync and renaming.
- Kept private profiles inaccessible in public demo mode.
- Added sanitized support diagnostics and bilingual widget search.

## V1P-D — Step 6: widget studio

- Added dashboard templates, widget resizing and visual styles.

## V1P-C and corrections — Step 5: guided Windows setup

- Added native Windows installation, Steam/CS2 detection, automatic credentials and GSI configuration backups.
- Added EN/FR prompts and safer UAC handling; fixed Windows PowerShell 5.1 translation parsing.

## V1P-B — Step 4: resilient GSI

- Improved recovery from game/round changes, stale data handling and economic projections.

## V1P-A — Steps 1–3

- Stabilized project structure and introduced secret handling and network protections.

Older technical details: [functional changelog](docs/CHANGELOG_FONCTIONNEL.md).
