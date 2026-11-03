# Application security boundaries

This is an implementation reference, **not an independent security audit, penetration test or certification**. Read the [security reporting policy](../../SECURITY.md), [LAN guide](../user/network.md) and [usage limits](../guides/usage-and-affiliation.md).

## Authentication and transport

`companion/server.py` requires configured ASCII GSI token (12–256 characters) and Dashboard PIN (6–256). `security.credential_matches` checks input shape and uses constant-time comparison. GSI uses its separate token; browser profile access uses the shared PIN. This is one authorized instance realm, not user accounts or granular per-profile permissions.

The WebSocket requires a matching HTTP/HTTPS Origin/Host, PIN authentication within eight seconds and reserved admission capacity (16 authenticated screens, 32 pending logins). Login throttling defaults to five failed attempts within five minutes and a 15-minute lockout per peer/process. Restart clears in-memory limits; this is not a distributed abuse-prevention service. Non-browser clients can manufacture an Origin, so Origin is not authentication. Reverse proxies require separate review and are not a general supported secure deployment.

GSI request bodies are capped at 256 KiB while streaming. JSON shape, depth/complexity and finite numbers are checked. Binary WebSocket frames close with 1003. The Docker Uvicorn command caps frames at 262144 bytes and queue depth at eight. Authenticated profile commands have their own stricter wire/document limits; see [publication](../development/profile-publication.md) and [contracts](../development/profile-contracts.md). No parser/private payload is echoed as a user-facing error.

## Profiles, drafts and publication

The target-only runtime validates existing storage and refuses unknown, corrupt or historical files without resetting them. Only a genuinely empty directory initializes an empty Dashboard. One cooperative lifespan/recovery lock excludes online/offline writers on the same local filesystem; it is not distributed locking or protection against arbitrary external file edits. Do not use multiple workers or shared network-volume writers.

Server validation is authoritative. Per-profile revisions, tombstones, stable operation identities and bounded receipts prevent ordinary stale overwrites/replays. A single atomic profile-store replacement commits profiles/revisions/receipts together before acknowledgement. Failed writes do not become success. Target recovery renews generation so obsolete clients cannot publish into restored state. See [offline operator procedure](../development/production-activation.md); always stop writers first.

The Dashboard reads published configurations, not Studio drafts. IndexedDB contains configuration-only drafts and operation intentions, never credentials/raw game packets. It is origin-isolated, **not encrypted**. Browser/device access, same-origin script compromise, extensions or storage clearing can expose/remove drafts. Local CAS prevents silent same-profile tab overwrites. Confirmed voluntary logout erases the current context and revokes old handles; network loss does not.

Import/export uses a strict versioned target configuration, excludes authentication, receipts/tombstones and GSI, and never publishes merely on file selection. Custom titles may still be personal. Values use text nodes; translation catalogs/parameters are data, not executable HTML.

## HTTP, browser and private files

Only intended pages/assets and public health are served; private `data/`, `.env`, logs, installer state and recovery bundles are not static assets. CSP restricts scripts/assets to the intended same-origin sources and denies framing; MIME-sniffing and referrer protections apply. Preview is a same-origin read-only popup with checked source/origin messaging, not an iframe exemption or independent writer. Test routes/hosts remain under `tests/browser/` and are not packaged into production Docker.

Demonstration is explicitly synthetic, cannot read private catalogs or publish, and clears the prior private surface. Diagnostics export requires authentication and is unavailable in demo. Its bounded codes/counters/times do not intentionally include credentials or raw GSI, but operators must still inspect exports before sharing. Follow [SUPPORT.md](../../SUPPORT.md).

## Deployment and limitations

Compose binds localhost by default. Opt-in LAN is **unencrypted HTTP/WS**, so the PIN does not protect traffic from network observers. Never expose the service directly to the Internet or forward its port on a router. Firewall/Docker Desktop/WSL2 and Wi-Fi isolation need local verification. No network rule is created automatically.

Docker uses UID 10001, read-only root filesystem, bounded temporary storage/resources, dropped capabilities and no-new-privileges. The Windows guided installer uses native PowerShell and asks before GSI replacement or required filesystem elevation; Docker failure does not justify UAC. Private `.env`, `.installer-state/` and GSI backups remain local. Filesystem permissions depend on the host; SHA-256 checks byte integrity, not authenticity against a writer with access. Backups are not encrypted vaults.

Source/build/archive exclusions reject runtime/credential variants, private context and backups. The [archive checker](../../scripts/README.md) is not a full Git-history scan or legal clearance. Runtime/dependency/action pins still need reviewed updates. Hosted test definitions, old successful runs and synthetic fixtures are not proof of current CI or real CS2/LAN/anti-cheat validation. Bomb timing stays estimated and disabled by default; no FACEIT approval is implied.
