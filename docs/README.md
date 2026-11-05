# CCS documentation

[Français](README.fr.md) · [Project overview](../README.md)

CCS is an independent personal project developed with substantial ChatGPT/Codex (OpenAI) assistance. No Valve/FACEIT/OpenAI affiliation, independent security audit or competitive approval is claimed. Code version `1.0.0` does not announce a published release. The [Community No-Resale License v1.0](../LICENSE) is source-available, not OSI-approved open source; see [licensing](legal/licensing.md) for terms and integration status.

## Choose a path

- [User documentation](user/README.md): installation, first widget, Dashboard, Studio, 29 widgets, ten themes, LAN, backups and troubleshooting.
- [Contributor guide](contributing/README.md): issues, PRs, targeted tests, conventions, rights and AI assistance.
- [Translations](contributing/translations.md): shared EN/FR JSON catalogs, parameters and adding a language.
- [Developer reference](development/README.md): architecture, modules, flows, contracts, storage, publication and tests.

User pages use `page.md` / `page.fr.md` with language links. Technical references are maintained in English to avoid conflicting copies.

## Operation and publication

- [Private backups and recovery](user/backup.md), [unencrypted LAN](user/network.md), [maintenance](user/maintenance.md).
- [Support](../SUPPORT.md) and [private security reporting](../SECURITY.md).
- [Offline operator procedure](development/production-activation.md) and [recovery tools](guides/profile-recovery.md).
- [Tests](../tests/README.md), [Windows scripts](../installer/README.md), [maintenance commands](../scripts/README.md).
- [Roadmap](ROADMAP.md), [release checklist](releases/checklist.md), [unpublished release notes](releases/release-notes-1.0.0.md).
- [Historical records](history/README.md): provenance, not current operating instructions.

Never expose CCS directly to the Internet. The PIN does not encrypt HTTP/WebSocket. No guide authorizes changes to another person’s installation.
