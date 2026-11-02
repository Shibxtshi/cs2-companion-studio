# Architecture and repository map

CS2 Companion Studio is a single-process FastAPI service with a browser dashboard. The repository groups files by responsibility while retaining the existing deployment entry points.

```text
companion/                 Backend implementation
  server.py                Routes, authentication, GSI state and orchestration
  gsi_lifecycle.py          Pure GSI observations and economy projections
  profile_store.py         Historical profiles and shared atomic-write primitives
  profile_contracts.py     Target data models and strict validation
  profile_operations.py    Pure per-profile target publication transitions
  profile_recovery.py      Explicit offline snapshots, reset and recovery
  profile_publication.py   Target atomic commit service and recovery generation
  profile_protocol.py      Authenticated target WebSocket adapter
  profile_runtime.py       Format detection, exclusive writer and lifespan lock
  profile_activation.py    Verified offline activation and historical rollback
  profile_wire.py          Closed catalog wire model
  security.py              Origin checks and login throttling
  support_diagnostics.py   Privacy-conscious event counters and summaries
  dashboard_delivery.py    Bounded, ordered dashboard fan-out
static/
  index.html               Integrated target Dashboard and Studio
  legacy.html              Compatible historical Dashboard/editor
  preview.html             Read-only Studio preview
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

The target browser composition loads shared rendering/transport, draft/publication and Studio modules, then application.js. The historical document loads profile-sync.js and studio.js instead; it does not run a target writer. Canonical assets live under static/js/ and static/css/; old flat asset URLs are not served. The map phase field is map_phase. Personal names and custom widget titles are excluded from DOM translation.

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

Display projections, widget DOM rendering and HTTP/WebSocket transport are shared modules. application.js composes the target Dashboard and Studio on one authenticated connection. The Studio lifecycle owns local edits and explicit publication; studio.js and profile-sync.js own historical editing/autosave only. Read [frontend responsibilities and approved future boundaries](frontend-modules.md) before extending them.

The approved identity, token ownership, target profile themes and historical temporary theme preview are documented in [design-system.md](design-system.md).

## Profile transition

The validated on-disk format selects the reader, writer and frontend together. A historical document keeps its compatible store, editor and autosave. A target ccs-dashboard-store document selects the published store, X/Y Dashboard and Studio with explicit versioned operations. Target operations never use historical autosave messages. Invalid or interrupted storage stops safely; startup never converts or resets existing profiles. Read [profile contracts](profile-contracts.md) and [production activation](production-activation.md). The stable offline command and private snapshot procedure are documented in [profile recovery](../guides/profile-recovery.md); they can operate when invalid storage blocks server startup.

## Local drafts

The target Studio uses configuration-only IndexedDB drafts, bounded session history and a publication-intent journal. A local save is not publication. The Dashboard reads only published profiles; each tab retains its own selection. The historical editor remains independent of these drafts. See [local draft boundaries and lifecycle](local-drafts.md).

## Explicit publication foundations

The production runtime validates the on-disk format and selects either the compatible historical composition or the integrated target composition. Exactly one store and writer are active. The target uses the existing authenticated `/ws` handler, P5 publication and P8 lifecycle; no synthetic launcher, public toggle or second ASGI entry point is needed. The lifespan recovery lock excludes offline activation. See [publication architecture](profile-publication.md) and [production activation](production-activation.md).

## Dashboard and Studio boundary

Both formats use the shared navigation shell with compatible data adapters. The target Dashboard uses the [X/Y projection](dashboard.md), 29 widget types and per-widget presentations; the separate [Customization Studio](customization-studio.md) edits drafts and publishes explicitly. Synthetic test hosts remain regression tools, not production launchers. Existing historical data requires separately confirmed offline activation with verified backups; see the [operator procedure](production-activation.md).
