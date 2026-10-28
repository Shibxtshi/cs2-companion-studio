# Maintenance commands

Run these commands from the repository root.

| Command | Purpose |
| --- | --- |
| `python scripts/generate_config.py` | Generate private local credentials and a GSI config |
| `python scripts/recover_profiles.py --inspect` | Classify profile storage without revealing its content |
| `python scripts/recover_profiles.py --prepare-reset --service-stopped` | Prepare a distinct verified private snapshot; no reset |
| `python scripts/recover_profiles.py --restore` | Explicitly restore a validated private backup; stop the service first |
| `python scripts/run_checks.py` | Run isolated backend suites, pytest and source-secret hygiene |
| `python scripts/check_secrets.py` | Check exclusions and tracked/source files without reading personal secrets |
| `python scripts/check_public_archive.py <archive.zip>` | Reject private runtime files in a distribution archive |

The confirmed reset/restore workflow, stopped-service requirement and interruption handling are documented in [offline profile recovery](../docs/guides/profile-recovery.md).

Generation and recovery can change private local files; consult the [Windows guide](../docs/guides/windows-installation.md). Docker and Windows test runners belong in [tests/](../tests/README.md), while operational PowerShell commands belong in [installer/](../installer/README.md).

The archive checker rejects data/log contents, credential variants, backups, symlinks/unsafe paths and private assistant guides. Only empty runtime .gitkeep scaffolding and explicit example configurations are distributable. See [architecture](../docs/development/architecture.md) and [release gates](../docs/releases/checklist.md).
