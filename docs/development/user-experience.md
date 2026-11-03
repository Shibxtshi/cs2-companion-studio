# Secondary screens and user feedback

Production `application.js` composes Dashboard/Studio; common screens use the same tokens, ten themes and shared JSON translations.

## Responsibilities

- `experience-copy.js`: stable experience-key adapter to shared catalogs, not a separate translation dictionary.
- `experience.js`: sign-in, optional quick start, topic-based help, grouped Settings and diagnostics. Machine-readable authentication/state events drive status, not translated text comparisons.
- `notifications.js`: bounded feedback. Errors/warnings/pending states persist until resolution or explicit dismissal. An unrelated success cannot clear an unresolved error. Information/success can expire after five seconds. Content is text, never parser HTML.
- `experience.css`: token-based responsive secondary screens, without geometry or profile writes.
- `studio-workspace.js`: native confirmations, explicit draft/publication status, translated error codes and focus restoration.

Before authentication only public `/health` is checked; PIN stays in session memory, never an URL, draft or onboarding preference. A refused pre-authentication socket does not prove throttling: copy explains possible temporary limits without inventing a countdown.

Diagnostics distinguishes HTTP health, authenticated WebSocket, recent GSI and recent match data. Packet age is server-reported. Disconnect clears live indicators; demonstration never certifies real CS2 reception. Diagnostic export is authenticated and unavailable in demo. No raw packet, PIN or token belongs in diagnostics.

Quick start is optional. Explicit dismissal/completion stores only the local `ccs-quick-start-v1` preference. Help can reopen it, including when storage is unavailable. Settings describes the selected published profile and offers temporary appearance previews where available. Persistent theme/density/navigation/fullscreen changes are Studio edits followed by explicit publication; there is no second settings writer or historical autosave.

Native dialogs support cancel, keyboard and focus return. Guarded navigation/logo exits use the Studio lifecycle, never automatic publication. Confirmed logout warns and erases current-context local drafts/intents before authentication closes; an erasure failure is not complete logout. Network loss does not erase drafts.

## Verification

See [tests](../../tests/README.md): experience, edge, logo, production and localization journeys use disposable data/credentials. They cover server loss, privacy, bilingual messages, native focus, responsive layouts and demo isolation. These are synthetic checks, not global accessibility certification or proof of hosted CI execution.
