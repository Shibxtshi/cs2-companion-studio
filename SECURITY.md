# Security policy

This is a **solo-maintained personal software project** and has **not** received an independent penetration test or formal security certification.

## Supported versions

Security fixes are currently planned only for the **most recent development/release build**. Earlier preview builds are not guaranteed to receive fixes. This policy may change after the first public release.

## Reporting vulnerabilities privately

**Do not post exploitable vulnerabilities, PINs, tokens or private diagnostic data in public issues.**

Before opening the public repository, the maintainer must enable **GitHub private vulnerability reporting** (Repository → Settings → Code security and analysis / Private vulnerability reporting, if available). Once enabled, use the repository's private "Report a vulnerability" option.

**Release blocker:** if private vulnerability reporting is unavailable, the maintainer must publish a suitable private security contact method **before** releasing this repository. No private contact address has been configured in this draft, so avoid public disclosure of exploit details.

When reporting privately, include affected version, reproduction steps with synthetic data, potential impact, and suggested mitigation. Never send working PINs, tokens or player data.

## Trust boundaries

- Local-only by default. LAN mode uses **unencrypted HTTP/WS**; restrict it to a trusted network and do not expose port 8080 to the public Internet.
- Each instance uses a shared dashboard PIN and a separate GSI token. A party knowing the PIN can manage profiles; this is not per-user authorization.
- Do not upload `.env`, generated GSI `.cfg`, `data/profiles.json` or unsanitized Docker logs to GitHub.
- No assurance of FACEIT permission. The bomb timer is optional, estimated and disabled by default.
- Project is **not affiliated with Valve, CS2, FACEIT, or OpenAI**.

See [technical security details](docs/SECURITY.md) and [release checks](docs/PUBLIC_RELEASE_CHECKLIST.md).
