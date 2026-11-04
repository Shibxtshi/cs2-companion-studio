# Changelog — user-visible changes

## Unreleased — V1-06 candidate validation

- Restore help-dialog focus to its explicit opener on browsers that do not focus clicked buttons, including WebKit; preserve Settings help return.
- Repair the isolated Dashboard test composition after the shared catalog loader change. Update storage-error expectations to the shared catalog and make rendering checks wait for loader readiness and compare low-alpha painted colors correctly.
- Add candidate validation guidance without marking unperformed installation, legal or publication gates complete.

## Earlier V1 preparation

- V1-01 removes the historical Dashboard/editor and autosave. Fresh private installations initialize an empty target layout; incompatible storage is refused without replacement or migration.
- V1-02 simplifies source/test boundaries; synthetic browser hosts live under tests/browser and are not production routes.
- V1-03 centralizes browser, installer and maintenance translations in shared EN/FR JSON catalogs.
- V1-04 provides ten complete themes, including Arctic White, with generated profile/browser validation parity.
- PR #34 fixes CI syntax-check paths for the relocated test harnesses.
- V1-05 prepares current bilingual user guides, contributor/developer indexes and offline documentation-link checks for review. This entry does not mark that PR merged.

The code reports 1.0.0; no public release is announced. License approval, third-party/contribution rights and final release gates remain open.

## Earlier development milestones (historical)

The phase descriptions below record behavior at their original delivery date, including now-retired historical editors and inactive foundations. They are not current operating instructions; use the [current documentation](docs/README.md).

## Unreleased — P10 stabilization

- Preserve game-data freshness when CS2 sends only player identity/activity; do not present old match values as current.
- Prevent reuse of an attempted activation generation after rollback and block unrelated recovery operations during interrupted restoration. Existing private activation preparations remain inspectable/restorable; activation requires a fresh preparation. Profile document versions are unchanged.
- Keep Studio publication status readable on tablets, clear stale PIN field errors after successful authentication, and explain incompatible server versions correctly.
- Add native production acceptance/fault/persistence suites, reproducible performance and bounded stability measurements, and a separate manual CS2/personal-installation acceptance guide. No personal activation is performed.

## P9.5

- Integrate the target Dashboard and Customization Studio into the real authenticated application, with per-tab profiles, persistent local drafts and explicit publication.
- Add reviewed target profile import/export and verified offline activation/rollback tools. Existing historical files remain unchanged until explicit operator confirmation.
- Add production-composition and synthetic activation regression tests.


## P9 — Secondary screens and feedback

- Unify sign-in, optional quick start, topic-based help and grouped Settings using the approved CCS identity and four themes.
- Distinguish server, WebSocket, GSI, match freshness and synthetic demonstration; keep errors actionable and persistent, and avoid exposing import parser content.
- Clarify dashboard density, widget presentation and geometry, preserve the historical editor/autosave, and document a separately approved target activation lot before P10.
- Preserve the requested Settings destination when leaving the current editor.

## P8 — Isolated Customization Studio

- Add a three-panel target Studio with search/categories, per-instance properties, cell-snapped move/resize, undo/redo and responsive panel navigation.
- Compose persistent local drafts and explicit versioned publication, profile creation/duplication/deletion, recovery copies and reviewed conflict actions.
- Preserve uncertain operations, newer tab work and confirmed-logout cleanup; preview the same dashboard shell in a same-origin window without weakening frame protection.
- Keep the production historical editor/store/autosave unchanged; no real conversion or reset is activated.

## P7 — Widget presentation variants

- Modernize all 29 kinds with Standard/Compact/Minimal using shared value nodes and preserved source warnings.
- Activate Standard on legacy dashboards; target variants remain isolated without storage conversion.
- Add measured display minima and accessible detail/list handling while preserving saved X/Y geometry.
- Cache unchanged lists/value bindings and label demonstration connections correctly; preserve all GSI calculations.

## P6 — Dashboard and navigation

- Shared full/compact/hidden navigation, current-editor entry, grouped settings and native/fallback fullscreen.
- Bounded display-only X/Y projection and inactive P5 target catalog host; legacy storage/autosave remain active.
- Clear stale live values after disconnect and rebuild the public demo board on entry.
- Add collision/reflow, navigation and multi-screen target checks without resetting real profiles.

**Current release candidate:** 1.0.0. The previous V1P labels below record internal development milestones; no public release has been published yet.

## Unreleased

- Prepare inactive explicit profile publication with atomic commits, per-profile conflicts, persisted operation retries, authenticated catalogs and independent tab selection. Preserve the current editor/autosave; no real profile transition or reset is activated.

- Prepare inactive browser-only IndexedDB drafts, bounded undo/redo and coherent gesture history for the future Studio. Current editor/autosave remain unchanged; no draft publication is activated.

- Prepare inactive, versioned dashboard profile/export/draft contracts and per-profile revision validation for the upcoming editor; current profiles and autosave remain active.
- Add explicit offline profile inspection, verified private reset snapshots and confirmed current-format recovery, including interrupted-operation status. No automatic profile reset or target-format activation.

- Adopt the Repère identity and locally served Inter / Barlow Condensed fonts.
- Add complete Tactical Blue (default), Competitive Red, Performance Green and Creator Purple theme previews for the current interface. The preview affects only this tab, resets on reload and does not change shared profiles or autosave.

- Reject unsupported binary WebSocket frames cleanly and handle corrupt/deep profile files with controlled recovery errors.
- Translate save failures in English, avoid UAC prompts for Docker availability failures, and verify tracked-source archive privacy in CI.
- Pin CI actions to verified commit revisions and document GitHub reporting choices without publishing the project.

- Group Docker and Windows verification under tests/, consolidate historical browser checks, and separate distributable GSI examples from generated private configuration. Update CI and navigation to the new locations.

- Fresh Windows installs ask whether to enable the estimated bomb countdown (disabled by default); reruns preserve existing settings.
- Apply local .env changes with APPLIQUER_REGLAGES_WINDOWS.cmd, recreating the container with its existing image and preserving saved profiles.

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
- Earlier preparation proposed MIT; this was superseded by a draft no-resale, source-available license after clarifying the intended redistribution terms.
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

Older technical details: [functional changelog](docs/history/CHANGELOG_FONCTIONNEL.md).
