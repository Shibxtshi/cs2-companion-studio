# Maintenance commands

Run commands from the repository root. These entry points stay stable across the source reorganization.

| Command | Purpose |
| --- | --- |
| `python scripts/generate_config.py` | Generate private local credentials and a GSI config |
| `python scripts/run_checks.py` | Run isolated backend suites, pytest checks and source-secret hygiene |
| `python scripts/check_secrets.py` | Check exclusions and tracked/source files without reading personal secrets |
| `python scripts/check_public_archive.py <archive.zip>` | Reject private runtime files in a distribution archive |
| `python scripts/recover_profiles.py --restore` | Explicitly restore a validated private backup; stop the service first |
| `python scripts/docker_smoke.py` | CI integration check against an already running synthetic Docker instance |

Generation and recovery can change private local files; consult the [Windows guide](../docs/guides/windows-installation.md). Never run Docker smoke checks against a personal instance: they create synthetic profiles/state. See [tests](../tests/README.md), [architecture](../docs/development/architecture.md) and [release gates](../docs/releases/checklist.md).
