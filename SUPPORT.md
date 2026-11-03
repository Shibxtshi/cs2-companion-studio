# Support and diagnostic reporting

CS2 Companion Studio is an **independent personal project**, offered as-is, without guaranteed support.

## Before creating a GitHub issue

1. Reproduce the problem in **demo or CS2 training** if possible; avoid FACEIT gameplay tests.
2. Check `/health` for server status and use the authenticated Diagnostics in Settings.
3. Verify Docker Desktop is running and the CS2 GSI config was installed/reloaded.
4. In a new issue, provide your application version, OS, Docker version, steps to reproduce, expected vs actual behavior, and **sanitized** diagnostic output if needed.

## What you may share after review

- `logs/support-summary.json`
- `logs/events.jsonl`
- `logs/events.previous.jsonl` (if present)
- The exported support diagnostics, **after inspecting it manually**

## Never share

- `.env`, `PIN.txt`, generated `gamestate_integration_*.cfg`, private tokens, PINs.
- `data/profiles.json`, full network captures, raw Docker logs without redaction.
- Steam IDs, names, IP addresses, match-sensitive screenshots, authentication URLs.

Do not assume a diagnostic export is guaranteed anonymous. Check every file and redact anything identifying before publication. Security concerns must follow [SECURITY.md](SECURITY.md), not public issues.

Start with [troubleshooting](docs/user/maintenance.md) / [dépannage](docs/user/maintenance.fr.md). The [backup guide](docs/user/backup.md) explains why a profile export is not a complete private backup.
