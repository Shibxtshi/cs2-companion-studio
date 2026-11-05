# Contributing

Thank you for considering a contribution to this **solo-maintained personal project**.

## Before opening an issue

- Check whether the problem is reproducible on the latest development build and search for existing issues.
- For a bug, describe expected vs actual behavior, your OS, Docker version, CS2 training/demo context, and sanitized diagnostics when relevant.
- **Never post secrets, raw GSI payloads, personal player identifiers, `data/profiles.json`, or raw Docker logs**. See [SUPPORT.md](SUPPORT.md).
- Do **not** post security vulnerabilities publicly; use [SECURITY.md](SECURITY.md).

## Pull requests

1. Open an issue for larger changes to avoid duplicate work; small fixes can be proposed directly.
2. Keep changes scoped. Avoid introducing game-memory readers, injections, FACEIT-specific competitive advantages, or third-party assets without an appropriate license.
3. Add or update tests and documentation. Test locally with `python scripts/run_checks.py`.
4. If you used **AI assistance for substantial code, docs or tests**, describe which parts were AI-assisted and how you reviewed/validated them. AI use is allowed; hiding it is unnecessary.
5. Confirm your right to submit the contribution and provide explicit permission from the person entitled to give it for incorporation, reproduction, modification and redistribution under the Community No-Resale License v1.0 supplied in [LICENSE](LICENSE), including downstream permissions (section 9). Contributors retain ownership; submission or a Git author field alone is not sufficient, and no general permission for future relicensing is presumed. Identify separately licensed material and its notices. See [licensing](docs/legal/licensing.md).

### PR information

- What changed (user-visible)?
- How was it tested? (synthetic fixtures vs real CS2 training)
- Any security/privacy implications?
- Was AI used substantially, and what was manually verified?

This repository is maintained on a best-effort, personal-time basis, with no guaranteed response time.

## Finding your way

Read the [architecture and repository map](docs/development/architecture.md), [code conventions](docs/development/code-style.md), and [test guide](tests/README.md). Add backend code to companion/, browser assets to static/js/ or static/css/, and tests to the appropriate execution category. Keep runtime files and local assistant context out of commits and archives.

For language contributions, use the shared JSON catalogs and the [translation guide](docs/contributing/translations.md).

The [contributor index](docs/contributing/README.md) covers scoped widget, theme, translation, documentation and security changes, with risk-based tests. No review timeline is promised.
