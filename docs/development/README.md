# Developer documentation

[Documentation index](../README.md) · [Index français](../README.fr.md)

Technical references are maintained in English. Start with [architecture and data flows](architecture.md), then follow the responsible component rather than duplicating its contract. Production has one ASGI entry point, one target-only published store and one frontend composition.

| Area | Reference |
|---|---|
| Repository/backend/frontend map and data flows | [Architecture](architecture.md), [frontend modules](frontend-modules.md) |
| Startup, empty directories, locks and incompatible data | [Target runtime](target-runtime.md) |
| Formats, limits, IDs, revisions and generated schema | [Profile contracts](profile-contracts.md) |
| Atomic commits, receipts, protocol and conflicts | [Publication](profile-publication.md) |
| IndexedDB, CAS, history and logout | [Local drafts](local-drafts.md) |
| X/Y projection, collisions and responsive geometry | [Dashboard](dashboard.md) |
| Model/canvas/inspector/lifecycle/preview | [Studio](customization-studio.md) |
| Widget source semantics and presentation families | [GSI/data lifecycle](game-data.md), [user catalog](../user/widgets.md), [presentations](widget-presentations.md) |
| Tokens, ten palettes, light theme, contrast and assets | [Design system](design-system.md) |
| JSON catalogs and adding a language | [Translations](../contributing/translations.md) |
| Login/help/settings/diagnostic boundaries | [User experience](user-experience.md) |
| PIN, Origin, request limits, CSP and LAN | [Security notes](../security/technical-notes.md) |
| Offline activation, recovery and incompatible historic data | [Operator procedure](production-activation.md), [recovery tools](../guides/profile-recovery.md) |
| Style, synthetic tests and release preparation | [Code style](code-style.md), [tests](../../tests/README.md), [release checklist](../releases/checklist.md) |

## Native development

Use a separate checkout/temporary instance, Python 3.12 and a virtual environment. From its root install `requirements-dev.txt` (includes runtime dependencies), then `python scripts/generate_config.py` to generate **private** credentials/GSI configuration. This writes local files; never run it against another installation. The [Windows installer](../user/installation.md) needs no Python, unlike native development.

```powershell
python -m pip install -r requirements-dev.txt
python scripts/generate_config.py --help
```

After generating configuration deliberately in that disposable instance:

```text
python -m uvicorn companion.server:app --env-file .env --host 127.0.0.1 --port 8080 --ws-max-size 262144 --ws-max-queue 8
```

The command reads its private `.env` and starts the single-process service. Use a separate port/data directory for concurrent tests; never use multiple workers sharing one store. Empty directories initialize an empty Dashboard, while incompatible existing data stops startup. Browser assets need no build framework. Docker/Windows helper and test entry points are indexed in [installer](../../installer/README.md), [scripts](../../scripts/README.md) and [tests](../../tests/README.md).

Private runtime directories, secrets and local assistant context must stay out of Git/build contexts/archives. A successful synthetic run is not a public release or real CS2 test.
