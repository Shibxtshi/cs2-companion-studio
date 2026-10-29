# Secondary screens and user feedback — P9

The maintainer approved the first visual direction on 2026-10-29. Identity, fonts, themes and semantic tokens remain those of [P2](design-system.md). P9 does not activate target profiles.

## Responsibilities

- `experience-copy.js`: closed EN/FR secondary-screen vocabulary; no runtime values or secrets.
- `experience.js`: login, optional three-step quick start, native topic-based help, grouped Settings and diagnostics. It consumes machine-readable authentication/state events, never translated status text.
- `notifications.js`: bounded feedback. Errors/warnings/pending states do not expire; unrelated success cannot erase an unresolved error. Explicit dismissal and transient information/success expiry after five seconds. All text uses textContent.
- `experience.css`: P2-token responsive layouts; no widget geometry or profile-writing behavior.
- `studio.js`: historical profiles/autosave/import/export, readable login errors and guarded download preparation. A prepared download is not proof that a file reached disk. Import failures never display parser excerpts or supplied file contents.
- `studio-workspace.js`: P8 native confirmations and local/publication states, context help and translated fallback messages without raw internal error disclosure. Dialogs restore focus to a connected trigger.

## States and privacy

Only public /health is checked before authentication. PIN handling stays with the existing transport; no URL, draft or onboarding credential storage. The server still enforces attempts, Origin and message bounds. A refused pre-authentication WebSocket does not prove a throttle cause; UI mentions temporary limits as a possibility, without inventing a retry countdown.

Diagnostics distinguish the last HTTP health check, authenticated WebSocket, recent GSI and recent match data. The online flag is used only with authenticated, recent GSI reception. Disconnect clears live indicators. Age is server-reported GSI packet age, not a separate client source of truth. Demo never certifies CS2 connectivity. Export remains authenticated and unavailable in demo; no endpoint or export field is added.

Quick start is optional and never blocks connection. Only explicit dismissal/completion stores the local `ccs-quick-start-v1` flag; Help always reopens it. The flag contains no profile, authentication or game data. Storage refusal leaves Help available.

## Active and target preferences

Production Settings explains temporary theme/navigation/fullscreen previews for this tab. Historical density stays in the current editor. Widget presentation and X/Y dimensions are documented as distinct controls in the isolated Studio, not added to historical profiles.

The authenticated target Dashboard reads published preferences; Settings controls remain temporary previews. Persistent changes use P8 drafts/P5 publication. No second writer or activation switch exists.

Current automatic server saving and target local saving/publication remain distinct. Historical native confirmations/prompts stay in place. P8 retains native dialog composition instead of adding a custom focus trap.

## Validation

Run `node tests/js/test_experience.js` and `python tests/browser/test_experience.py --browser chromium` (also firefox/webkit), plus existing suites. Tests use disposable servers, synthetic credentials/GSI, real server termination, malformed files and download faults. No installed profiles are read. Coverage includes bilingual copy, secondary-screen sizes, native focus, onboarding persistence, error privacy and demo isolation.

Hosted Actions absent or blocked must be reported as not executed. Local evidence is not hosted-CI success or accessibility certification. The separate [activation proposal](target-activation-plan.md) needs approval and implementation after P9/before P10.
