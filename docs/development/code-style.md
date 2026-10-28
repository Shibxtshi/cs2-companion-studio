# Code quality conventions

These conventions guide scoped changes. Update callers, tests and documentation together when an interface changes; backward compatibility is not required for the current undeployed project.

## Naming

- Use `camelCase` for new local variables in JavaScript, PowerShell and project-owned Python code when doing so does not break interfaces.
- Use `PascalCase` for class names and `UPPER_SNAKE_CASE` for constants.
- Preserve protocol-defined fields, environment variables, HTTP/WebSocket payload keys, CSS class names, and third-party API names verbatim (for example `gsi_connected`, `BIND_HOST`, `activeProfile`).
- Python function names and published module attributes currently follow existing Python conventions; migrate only with matching call-site and regression-test updates. Python's usual PEP 8 guidance prefers `snake_case`; this project deliberately favors `camelCase` for internal variables at the maintainer's request.

## Language

- Write code comments and developer-facing docstrings in English.
- Localized strings may be in French or English. Keep user-visible text and translation resources separate from business logic when touching the affected component, preserving current language switching behavior.
- Do not change the semantics of security messages, Game State Integration payloads or persistent profiles just to translate strings.

## Maintainability and performance

- Prefer readable, formatted source over dense single-line JavaScript, CSS or HTML.
- Keep WebSocket/authentication, profiles and game-state lifecycle boundaries explicit; add tests before moving entry points or persisted data paths.
- Avoid timers or DOM refreshes without work to perform; preserve timer accuracy and the default-disabled setting.
- Update all launchers, callers, tests and documentation when an interface changes. The software is not deployed: do not retain aliases or add migrations solely for backward compatibility.
- Place historical development documentation in `docs/history/`; use the current guide, development, security and release sections indexed by `docs/README.md`.
- Keep pytest tests in `tests/unit/`, `tests/integration/` and `tests/contracts/`; browser journeys in `tests/browser/`; JavaScript tests in `tests/js/`; isolated CLI regressions in `tests/standalone/`; historical browser checks in `tests/browser/legacy/`, disposable Docker runners in `tests/docker/`, and PowerShell verification in `tests/windows/`. See `tests/README.md` for the different invocation methods.
- Keep widget template definitions in `static/js/widgets.js` and ensure it loads before `static/js/studio.js`.

## Quality gates

Run `python scripts/run_checks.py`, GitHub Actions on Windows and Linux, browser tests (Chromium, Firefox, WebKit), Docker smoke tests and dependency auditing before merging substantive changes.

Profile synchronization belongs in static/js/profile-sync.js. It emits stable state codes; UI text is resolved by the translation API. Exercise the controller behavior with node tests/js/test_profile_sync.js before changing save/conflict behavior.

Keep backend implementations inside companion/. Use companion.server:app as the single ASGI entry point. Keep Windows launchers, Compose, requirements and the documented scripts at their stable entry paths. See [architecture](architecture.md) for ownership and compatibility rules.
