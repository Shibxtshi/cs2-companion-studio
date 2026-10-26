# Code quality conventions

These conventions guide incremental refactors; existing public interfaces remain compatible until a tested migration is complete.

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
- Treat Windows `.cmd` launchers, the top-level `app.py`, Docker entry points and CI commands as compatibility surfaces; relocate them only with explicit tests and updated documentation.
- Place historical development documentation in `docs/history/`, and active product documentation at the root of `docs/`.

## Quality gates

Run `python scripts/run_checks.py`, GitHub Actions on Windows and Linux, browser tests (Chromium, Firefox, WebKit), Docker smoke tests and dependency auditing before merging substantive changes.
