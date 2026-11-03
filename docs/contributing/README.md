# Contributor guide

[Documentation home](../README.md) · [Contribution policy](../../CONTRIBUTING.md)

CCS is a solo-maintained personal project. Small focused fixes can be proposed directly; discuss larger behavior/contract changes first. No response time or acceptance is promised. The [license](../../LICENSE) is a non-effective draft: do not assume a final grant or that contribution rights are already settled. Confirm your rights and discuss terms with the maintainer before supplying third-party code/assets or contributions requiring a licensing agreement.

## Issue and pull request workflow

1. Reproduce on the relevant revision using synthetic data if possible. Search existing reports. Give expected/actual behavior, steps, OS/browser/Docker versions and the exact commit when known. A UI version alone is not a commit.
2. Never attach credentials, private profiles, raw GSI packets/logs or identifying screenshots. Follow [support](../../SUPPORT.md); exploitable security issues belong to the [private reporting policy](../../SECURITY.md), not public issues.
3. Create a focused branch, preserve authentication/storage/publication boundaries and update current callers, documentation and targeted tests together. Avoid unrelated cleanup.
4. Describe the concrete change, tests actually run, skipped/unavailable checks, risks and substantial AI assistance in the PR. No invented hosted CI or real CS2 claims.
5. Wait for review. Merge, release, visibility and license decisions remain with the maintainer.

## Find the responsible code

Use the [architecture map](../development/architecture.md) and [code style](../development/code-style.md). Backend lives in `companion/`, UI assets in `static/`, operational Windows scripts in `installer/`, maintenance in `scripts/`, synthetic test hosts in `tests/browser/`. Developer comments/docstrings are English. New project-owned internal variables use camelCase where compatible, classes PascalCase and constants UPPER_SNAKE_CASE. Preserve external API/protocol names.

| Change | Update and check |
|---|---|
| Widget | Catalog `widgets.js`, renderer/format/presentation and minima as needed; preserve public IDs/source meaning; synthetic complete/missing/zero/stale/demo data, variants, long text and repeated instances |
| Theme/style | Follow [design system](../development/design-system.md); Python theme registry → official generated schema, CSS tokens and shared controls; computed styles, custom overrides, contrast, light/native controls and responsive preview |
| Translation | Shared JSON only, [translator guide](translations.md), locale validator, hot switching and named parameters; never translate personal data |
| Profile/draft/publication | Strict Python/browser contract parity, generator check, CAS/receipt/concurrency/failure tests and real production browser integration |
| Auth/GSI/security | Backend gate and affected malformed input, Origin, access/freshness/privacy tests; no real personal packets |
| Installer/Docker | Corresponding PowerShell/disposable Docker checks; distinguish emulation from real Windows/UAC/CS2 |
| Documentation | Verify code/CLI flags, local links/files, EN/FR safety equivalence and [documentation checker](../../scripts/README.md) |

Start with targeted tests for the change and expand across affected security, GSI, persistence or platform boundaries. [tests/README.md](../../tests/README.md) provides exact invocations/prerequisites. Preserve test scripts/workflows even when hosted runners are unavailable. Public distribution has separate stronger [release gates](../releases/checklist.md).

## Documentation, AI and assets

User pages use `.fr.md` companions; technical reference is English. Prefer links to a canonical source over duplicate explanations. Historical documents must say so; do not treat old results as current evidence.

Disclose substantial ChatGPT/Codex or other AI assistance and describe your review/validation. Read [AI disclosure](../../AI_DISCLOSURE.md). Keep original third-party license notices, font provenance and asset permissions; do not import game artwork or marks merely because they are visible online. No Valve, FACEIT or OpenAI affiliation is implied. The project license cannot replace third-party terms.
