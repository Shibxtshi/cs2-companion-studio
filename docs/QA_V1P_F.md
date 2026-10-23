# V1P-F — Quality assurance and security release gate

This is **stage 8 of the V1P roadmap**, not a claim of penetration-test certification or FACEIT approval. The app processes **only synthetic GSI data** in automated tests.

## What runs automatically after pushing to GitHub

| Gate | Environment | What is checked |
|---|---|---|
| API regressions | Windows + Linux, Python 3.12 | Score, inventory, economy, bomb logic, authentication, storage, GSI lifecycle |
| Security scenarios | Windows + Linux | Private paths, bad tokens, malformed GSI, body limits, WS Origin checks, PIN protection, profile validation, log redaction |
| Browser end-to-end | Chromium, Firefox, WebKit on Linux | Real HTTP+WS login, guest demo isolation, two authenticated devices sharing a profile, synthetic GSI, EN/FR search |
| Windows installer | Windows PowerShell 5.1 | Parse every script and exercise helpers without modifying real CS2 |
| Dependency analysis | GitHub Actions | `pip-audit` on runtime dependencies (includes transitives), JSON report and CycloneDX SBOM. Any reported vulnerability **fails the gate** |
| Docker | Ubuntu runner | Build, start, health, GSI, non-exposure of `/data/`, persistence through restart, UID 10001 |

CI config: `.github/workflows/checks.yml`. The workflow requires read-only repository access and uses generated synthetic secrets that are not uploaded. The GitHub runner uploads an *audit report*, not personal logs.

**Important:** Merely including a workflow does not mean it has run on GitHub. The maintainer must review all checks after the first public/private push. A failed dependency-audit job is a release blocker, not a warning to ignore.

## Run locally

```powershell
python -m pip install -r requirements-dev.txt pytest
python scripts/run_checks.py
```

For a real web/WS E2E against an ephemeral local server:

```powershell
python -m pip install playwright==1.57.0
python -m playwright install chromium
python tests/test_live_browser.py --browser chromium
```

`tests/test_live_browser.py` binds only to `127.0.0.1` and creates disposable test profiles/credentials under a temporary directory. No real `.env`, CS2 installation or match is needed. On systems restricting browser-to-localhost access, this test must run in CI or on an unrestricted development machine.

To test the Docker image manually on a trusted machine, start the app normally using **your private `.env`**, verify `/health`, perform a GSI demo in a bot/training session, then restart the container and check that your stored dashboards remain. Keep `data/` and `.env` during upgrades.

## Release blockers / manual checks

- [ ] GitHub Actions jobs green, including dependency audit and all three browser engines
- [ ] Windows PowerShell install tested without elevation, then with UAC only when needed
- [ ] Docker Desktop installation and migration from V1P-E.1 tested on actual Windows
- [ ] CS2 bot/training GSI round/map changes tested (never necessary to test on FACEIT)
- [ ] Phone/tablet on trusted LAN can authenticate and synchronize a profile
- [ ] Profiles persist through Docker restart and after a full app update preserving `data/`
- [ ] Local Windows Firewall prohibits Internet access to port 8080
- [ ] Dependency advisory results manually triaged, no ignored high-risk vulnerabilities
- [ ] LICENSE and public contact/disclosure procedure added (step 9)

## Current threat boundaries

PIN + WebSocket protect profiles from casual local guests, but **HTTP and WS on LAN are not encrypted**. Someone on a hostile Wi-Fi can read network traffic and credentials. Default bind `127.0.0.1` is recommended; enabling LAN must be restricted to a trusted private network. No default HTTPS termination, multi-user permissions, device revocation, or independent pentest is included yet. The demo shows synthetic data only. A user possessing the shared PIN has full permission to edit all dashboards in the instance. Do not open port 8080 to the Internet.

The bomb timer remains optional and disabled by default. GSI use and absence of injections **do not imply FACEIT approval**. This remains an independent project not affiliated with Valve, Counter-Strike 2, or FACEIT.


**Step 9 note:** Root `SECURITY.md`, README, MIT license draft, AI disclosure and contribution templates now exist. License holder, private contacts and GitHub CI execution remain **publication blockers**; see [`PUBLIC_RELEASE_CHECKLIST.md`](PUBLIC_RELEASE_CHECKLIST.md).
