# Security policy

This is a **solo-maintained personal software project** and has **not** received an independent penetration test or formal security certification.

## Supported versions

Security fixes are currently planned only for the **most recent development/release build**. Earlier preview builds are not guaranteed to receive fixes. This policy may change after the first public release.

## Reporting vulnerabilities privately

**Do not post exploitable vulnerabilities, PINs, tokens or private diagnostic data in public issues.**

The maintainer has selected **GitHub Private Vulnerability Reporting** as the security-reporting channel. Once the public repository has this feature enabled, use **Security → Advisories → Report a vulnerability**. A SECURITY.md file alone does not enable the form. See [GitHub's reporting guide](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/report-privately).

**Preparation status:** the repository is still private. GitHub documents this feature for public repositories; activation and a working reporting form have not been verified. At an explicitly authorized publication, the maintainer must enable it under **Settings → Advanced Security → Private vulnerability reporting**, verify the reporting entry point and notification settings, then announce availability. Do not change visibility merely to complete this preparation. See [GitHub's configuration guide](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository).

Until a private reporting route is verified, do not put vulnerability details in public issues. This preparation does not authorize publication or establish a confidential email contact.

When reporting privately, include affected version, reproduction steps with synthetic data, potential impact, and suggested mitigation. Never send working PINs, tokens or player data.

## Trust boundaries

- Local-only by default. LAN mode uses **unencrypted HTTP/WS**; restrict it to a trusted network and do not expose port 8080 to the public Internet.
- Each instance uses a shared dashboard PIN and a separate GSI token. A party knowing the PIN can manage profiles; this is not per-user authorization.
- Do not upload `.env`, generated GSI `.cfg`, `data/profiles.json` or unsanitized Docker logs to GitHub.
- No assurance of FACEIT permission. The bomb timer is optional, estimated and disabled by default.
- Project is **not affiliated with Valve, CS2, FACEIT, or OpenAI**.

See [technical security details](docs/security/technical-notes.md) and [release checks](docs/releases/checklist.md).
