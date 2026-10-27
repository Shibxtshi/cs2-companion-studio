# Architecture and repository map

CS2 Companion Studio is a single-process FastAPI service with a browser dashboard. The repository groups files by responsibility while retaining the existing deployment entry points.

```text
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

The only ASGI entry point is companion.server:app. Internal imports use the companion namespace. There is no root-module compatibility bridge because the software has not been deployed. Configuration is validated before runtime directories are created.

The browser loads translations, the widget catalog, profile synchronization, reconnect control, then dashboard/experience code. Canonical assets live under static/js/ and static/css/; old flat asset URLs are not served. The map phase field is map_phase. Personal names and custom widget titles are excluded from DOM translation.

## Stable operational paths

Keep the root Windows launchers, Compose/Docker entry points and documented scripts at their current locations. Project-root resolution is independent of the backend package directory: static/, data/, logs/ and environment-variable overrides retain their meanings. Packaging copies the backend package and web assets, plus the explicit offline recovery command.

Do not put private runtime files under static/. Do not move data/, logs/ or .env during a source-only refactor. Preserve authentication, localhost defaults, version identifiers and the default-disabled bomb timer.

## Development workflow

Run [the tests](../../tests/README.md) and follow [code style](code-style.md). New code should join an existing responsibility before creating another layer. This structure does not introduce multi-worker support, a frontend build chain or a distribution packaging system.

See the [documentation index](../README.md) and [maintenance commands](../../scripts/README.md) for entry points.

## Reproducible environment

Runtime and test dependency versions, including their current transitive sets, are pinned in requirements.txt and requirements-dev.txt for Python 3.12. Docker and Playwright images use the digests verified in CI. Refresh these as a reviewed set and rerun the dependency audit, both OS suites, Docker and all three browsers; do not remove pins merely to resolve an installation failure. Platform-specific uvloop is conditional.

Native development entry point (after generating configuration):

```bash
python -m uvicorn companion.server:app --env-file .env --host 127.0.0.1 --port 8080 --ws-max-size 262144 --ws-max-queue 8
```
