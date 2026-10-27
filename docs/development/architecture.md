# Architecture and repository map

CS2 Companion Studio is a single-process FastAPI service with a browser dashboard. The repository groups files by responsibility while retaining the existing deployment entry points.

```text
app.py                     Stable app:app compatibility entry point
companion/                 Backend implementation
  server.py                Routes, authentication, GSI state and orchestration
  gsi_lifecycle.py          Pure GSI observations and economy projections
  profile_store.py         Validated profiles, revisions, atomic persistence
  security.py              Origin checks and login throttling
  support_diagnostics.py   Privacy-conscious event counters and summaries
  dashboard_delivery.py    Bounded, ordered dashboard fan-out
static/
  index.html               Dashboard document
  css/                     Styles
  js/                      UI, translations, catalog and profile controller
installer/                 Windows installation, status and uninstall scripts
scripts/                   Development, configuration and recovery commands
tests/
  unit/                    Focused persistence and delivery tests
  integration/             HTTP, WebSocket and security boundaries
  contracts/               Assets, documentation and release invariants
  browser/                 Real three-browser desktop/mobile journeys
  js/                      DOM-independent JavaScript behavior tests
  standalone/              Backend suites requiring isolated Python processes
  legacy_browser/          Historical offline Chromium checks
docs/                      Guides, development, security, releases and history
cs2_cfg/                   Safe GSI configuration example
data/ and logs/            Private writable runtime state; never public assets
```

## Ownership and dependencies

The server composes the smaller backend modules. Economy inference, validation and delivery logic should remain independent of browser markup. The package initializer does not start the server; explicitly importing companion.server initializes the application.

The root app.py resolves to the same server module, rather than copying its attributes. Existing app:app launches and Python callers therefore share one state object, including tests that patch app attributes. Internal imports use the companion namespace.

The browser loads translations, the widget catalog, the profile synchronization controller, then dashboard/experience code. Profile/WS payloads and widget IDs remain stable. The original /static/*.js and /static/styles.css URLs are served from an explicit fixed compatibility map; canonical files now live under js/ and css/. No user-provided filesystem path is accepted by that map.

## Stable operational paths

Keep the root Windows launchers, Compose/Docker entry points and documented scripts at their current locations. Project-root resolution is independent of the backend package directory: static/, data/, logs/ and environment-variable overrides retain their meanings. Packaging copies the backend package and web assets, plus the explicit offline recovery command.

Do not put private runtime files under static/. Do not move data/, logs/ or .env during a source-only refactor. Preserve authentication, localhost defaults, version identifiers and the default-disabled bomb timer.

## Development workflow

Run [the tests](../../tests/README.md) and follow [code style](code-style.md). New code should join an existing responsibility before creating another layer. This structure does not introduce multi-worker support, a frontend build chain or a distribution packaging system.

See the [documentation index](../README.md) and [maintenance commands](../../scripts/README.md) for entry points.
