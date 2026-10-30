# Architecture and repository map

CS2 Companion Studio is a single-process FastAPI service with a browser dashboard. The repository groups files by responsibility while retaining the existing deployment entry points.

```text
companion/                 Backend implementation
  server.py                Routes, authentication, GSI state and orchestration
  gsi_lifecycle.py          Pure GSI observations and economy projections
  profile_store.py         Current active profiles, revisions, atomic persistence
  profile_contracts.py     Inactive target data models and strict validation
  profile_operations.py    Pure target transitions; no active publication path
  profile_recovery.py      Explicit offline snapshots, reset and recovery
  profile_publication.py   Inactive target commit service and recovery generation
  profile_protocol.py      Inactive authenticated target WebSocket adapter
  profile_wire.py          Closed catalog wire model
  security.py              Origin checks and login throttling
  support_diagnostics.py   Privacy-conscious event counters and summaries
  dashboard_delivery.py    Bounded, ordered dashboard fan-out
static/
  index.html               Dashboard document
  css/                     Styles
  js/                      UI, translations, catalog and profile controller
installer/                 Operational Windows scripts and their shared helpers
scripts/                   Maintenance, configuration, recovery and quality commands
tests/
  unit/                    Focused persistence and delivery tests
  integration/             HTTP, WebSocket and security boundaries
  contracts/               Assets, documentation and release invariants
  browser/                 Real three-browser desktop/mobile journeys
  js/                      DOM-independent JavaScript behavior tests
  standalone/              Backend suites requiring isolated Python processes
  docker/                  Disposable container integration runners
  windows/                 PowerShell parsing and synthetic helper tests
  browser/legacy/          Consolidated historical offline Chromium check
docs/                      Guides, development, security, releases and history
examples/gsi/              Distributable GSI example (no real credentials)
cs2_cfg/                   Generated private GSI config; ignored, created on demand
data/ and logs/            Private writable runtime state; never public assets
```

The root intentionally retains the README, changelog, license/community policies, Docker/Compose configuration, dependency/configuration files and three Windows launchers. GitHub discovers the policy files here, and users can start installation/settings/uninstallation without browsing the implementation.

## Ownership and dependencies

The server composes the smaller backend modules. Economy inference, validation and delivery logic should remain independent of browser markup. The package initializer does not start the server; explicitly importing companion.server initializes the application.

The only ASGI entry point is companion.server:app. Internal imports use the companion namespace. There is no root-module compatibility bridge because the software has not been deployed. Configuration is validated before runtime directories are created.

The browser loads translations, the widget catalog, profile synchronization, reconnect control, then dashboard/experience code. Canonical assets live under static/js/ and static/css/; old flat asset URLs are not served. The map phase field is map_phase. Personal names and custom widget titles are excluded from DOM translation.

## Stable operational paths

Keep the root Windows launchers and Compose/Docker entry points at their current locations. Operational Python commands live in scripts/; platform-specific test runners live in tests/docker/ and tests/windows/. Installer implementation lives in installer/; its index is [Windows operations](../../installer/README.md). Project-root resolution is independent of the backend package directory: static/, data/, logs/ and environment-variable overrides retain their meanings. Packaging copies the backend package and web assets, plus the explicit offline recovery command.

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

Profile files use the same depth/finite-number checks as network JSON and are read with a byte cap before parsing. Unsupported binary WebSocket frames close with code 1003. CI actions are pinned to reviewed commit SHAs; refresh them deliberately and rerun the complete matrix. Docker availability failures do not trigger UAC; elevation remains limited to the existing explicit GSI-folder permission workflow.

## Frontend module boundaries

P1 separates display projections, widget DOM rendering and HTTP/WebSocket transport from studio.js. Profile/editor state, current autosave and retry policy retain their existing owners. Read [frontend responsibilities and approved future boundaries](frontend-modules.md) before extending them.

The approved identity, token ownership and temporary theme preview are documented in [design-system.md](design-system.md).

## Profile transition

P3 prepares strict target contracts and pure per-profile revision transitions without activating them. The current store, autosave and WebSocket messages remain active. Read [profile contracts and staged transition](profile-contracts.md) before P4/P5 work. The stable offline command and private snapshot procedure are documented in [profile recovery](../guides/profile-recovery.md); they can operate when invalid storage blocks server startup.

## Local drafts

P4 supplies inactive, configuration-only IndexedDB persistence and bounded session history. The current editor/autosave are not connected to it. See [local draft boundaries, lifecycle and integration requirements](local-drafts.md) before P5/P8.

## Explicit publication foundations

The production runtime validates the on-disk format and selects either the compatible historical composition or the integrated target composition. Exactly one store and writer are active. The target uses the existing authenticated `/ws` handler, P5 publication and P8 lifecycle; no synthetic launcher, public toggle or second ASGI entry point is needed. The lifespan recovery lock excludes offline activation. See [publication architecture](profile-publication.md) and [production activation](production-activation.md).

## P6 dashboard boundary

The active legacy frontend now uses the shared navigation shell. The X/Y projection and inactive read-only target host are described in [dashboard.md](dashboard.md); target storage and explicit Studio publication remain inactive.
