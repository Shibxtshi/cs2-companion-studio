# V1P-F.1 — Local security check correction

> Historical archive: retained descriptions and commands concern the dated version only. For current operation use the [documentation index](../README.md); this is not current validation evidence.


This is a maintenance update to V1P-F. The dashboard, GSI endpoints, PIN,
profiles, WebSocket, and Docker configuration are unchanged (`/health` still
reports `1p-f`).

## User-visible change

- `python scripts/run_checks.py` now succeeds on an installed copy that has a
  **local `.env`** and local `data/profiles.json`.
- A `.env` accidentally staged or tracked in Git is still rejected.
- Public distribution ZIPs are still validated by
  `python scripts/check_public_archive.py path/to/release.zip`.
- Three regression tests added; the quality gate now runs 22 pytest tests.

## Upgrading an existing V1P-F installation

Replace only `scripts/check_secrets.py` with the file from this update. If you
also want the additional tests, update `scripts/run_checks.py` and add
`tests/contracts/test_secret_hygiene.py`. **Do not delete `.env`, `data/`, or `logs/`.**

Run `python scripts/run_checks.py` from the project root. No Docker rebuild or
CS2 restart is required for this maintenance fix.

Note: a third-party Starlette/httpx deprecation warning may still appear in
some Python environments; it is independent of this security-check fix.
