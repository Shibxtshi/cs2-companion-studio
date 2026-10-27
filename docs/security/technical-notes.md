# Security notes — V1P-A

Scope: FastAPI receiver, WebSocket, LAN, browser layout import and Docker image. This is a code-level hardening pass, **not** an independent security audit or penetration test.

## Implemented

- Secrets generated per user; `.env` / generated CS2 `.cfg` excluded from Git and Docker build context.
- API token checked with constant-time comparison. GSI body limited to 256 KiB during streaming and invalid core object shapes rejected.
- WebSockets require same-origin browser requests, initial PIN auth within 8 seconds, per-peer throttling after 5 failures within 5 minutes (15-minute lockout), max 16 dashboard connections / 32 pending logins.
- Static frontend served with CSP restricting scripts to same-origin files, plus anti-framing, MIME-sniffing and referrer headers.
- Docker runs as UID 10001, read-only, without capabilities, with resource limits. Localhost-bound unless the user opts into LAN.
- Layout JSON import is size-bounded and sanitized against a fixed widget catalog; displayed GSI strings use `textContent`.

## Known limitations / future work

- LAN access currently uses **HTTP + WS without TLS**: suitable only for a trusted local network. Strongly advise against direct Internet exposure. Same-origin checks do not replace TLS or authentication.
- PIN lockout is per-process and per-peer IP; restarting Docker resets it. Reverse-proxy installations need separate authentication and proxy-aware network controls.
- No device revocation/session management or general central settings store. Profiles have a private one-generation backup and explicit offline recovery; broader backup retention remains outside the current scope.
- Dependency audit, SBOM and three-browser end-to-end tests are implemented in CI. Check the exact revision; a fresh release build and real Windows/CS2 validation remain required.
- A PIN-protected screen is not evidence of FACEIT anti-cheat approval. Automated bomb timing might be disallowed: disable until written approval.
- Secrets from any older archive that was posted publicly must be rotated, including the in-game GSI token.

## Reporting

Until the public release, report issues privately to the maintainer; do not post live PINs, tokens, player IDs or game state dumps in public bug reports. A root `SECURITY.md` reporting policy is now included. Before public release, the maintainer must enable a usable private reporting channel.


### Windows installer security (V1P-C)

PowerShell setup is local and interactive; it does not require elevated rights, install dependencies silently, create firewall rules or expose a port without opt-in. The Windows `.cmd` launcher uses a one-process PowerShell execution-policy bypass, which should only be used for a verified source. Config files and original GSI backups are stored locally (`.env` and `.installer-state/`) and ignored by Git; these contain secrets. Reusing credentials from V1P-B is intentional for migrations but rotate them if previously disclosed. LAN access is HTTP/WS without transport encryption and subject to firewall/WSL2 behavior; limit it to a trusted private network or prefer local-only. No FACEIT approval is implied.


## Diagnostic and private layouts (V1P-E.1)

Share only `logs/support-summary.json`, `logs/events.jsonl` and (if present)
`logs/events.previous.jsonl` after checking them. Never share `.env`, GSI files,
`data/profiles.json`, raw Docker logs or screenshots containing the PIN.
Profile files are accessible solely to the running application and are not exposed
as public static files. Anyone who knows the shared dashboard PIN can edit the
instance profiles, so use a strong unique PIN and restrict LAN access.


## Step 8 audit status — V1P-F

- Added a stronger WS Origin check, including the browser page's HTTP/HTTPS scheme. A TLS-terminating reverse proxy should be retested separately; localhost and LAN remain the documented supported setup.
- Added synthetic security regression tests for missing/forged Origin, unauthenticated WS access, bad PINs, invalid GSI object shapes, request size limits, profile injection payloads and private-path isolation.
- Added full GitHub CI tests (Windows, Linux, Chromium, Firefox, WebKit, Docker) and dependency-vulnerability audit with CycloneDX SBOM. **The eight CI jobs passed on main 3db5d855605e7285a534db16bfdcd57c7e737b6c after PR #7. New changes and release artifacts require their own checks**.
- Runtime pins were upgraded for the initial security-audit candidate. The pinned runtime passed that main CI run. The maintainer reports local PC operation, without a fully specified fresh-install/upgrade/LAN validation matrix; those release checks remain pending. Do not describe this as penetration-tested or security-certified.
- Private runtime directories and credentials remain excluded from the distributed source archive and Git.

See `docs/history/QA_V1P_F.md` for the historical quality checklist, and `docs/releases/checklist.md` for current release blockers.


## Step 9 repository preparation

The public security-reporting policy is at [security policy](../../SECURITY.md). Ensure a private reporting channel is actually enabled before making the repository public. An independent security audit has **not** occurred.

Profile backups and recovery files in data/ contain private layouts. They are never static assets and must not be distributed. See the [Windows guide](../guides/windows-installation.md) for explicit offline restoration.

## Dashboard delivery

Authenticated dashboard broadcasts run concurrently with serialized sends per peer and a two-second delivery deadline (including time waiting for that peer's previous broadcast). A failing or timed-out peer is removed and closed with a bounded best-effort close; healthy peers receive without waiting for it. This does not add multi-worker support or change authentication/protocol fields.
