# Changelog — user-visible changes

**Current release candidate:** 1.0.0. The previous V1P labels below record internal development milestones; no public release has been published yet.

## 1.0.0 — First release candidate (publication pending)

- CS2 GSI dashboard with 29 customizable widgets and EN/FR interface.
- Shared server-side profiles across authenticated PCs and phones, private demo, imports/exports.
- Game state, economy estimates and optional estimated bomb timer (disabled by default).
- Windows guided installer, Docker, privacy-conscious diagnostics and CI test suite.
- Independent personal project developed with substantial ChatGPT (OpenAI) assistance.

**Release not yet published:** complete the license, confidential reporting and final release checklist before tagging `v1.0.0`.

## Internal development history

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
