# Historical baseline (V1P-A–D) — see README for current profile storage

# V3 baseline / V1P-A compatibility contract

Original source: `CS2_GSI_Companion_Studio_v3_Docker.zip` (snapshot kept separate from public distribution).

Core functions and expectations:

| Area | Behavior to preserve | Regression |
|---|---|---|
| HTTP GSI | `/gsi` receives signed-by-token JSON and normalizes personal/map state | `test_studio.py`, `test_security.py` |
| WebSocket | Authenticated clients receive state updates, no token leakage | `test_studio.py`, `test_security.py` |
| Dashboard | default panel score / weapon / economy / stats / bomb; custom panel with 29 widgets | `test_studio.py` and manual smoke test |
| Layouts | editable reorder, resize, styling; export/import; saved in localStorage | Manual browser test; automated tests pending |
| Economy | loss streak + loss bonus when known; uncertain fallback | `test_economy.py` |
| Bomb | private-test timer estimates, repeated planted does not reset; stale/unknown handled | `test_timer.py` |
| LAN safety | distinct PIN and GSI secret; no public health telemetry; non-root Docker | `test_security.py` plus Docker review |

Changes intentionally made in V1P-A:
- Frontend CSS and JavaScript moved to separate static files to support Content Security Policy.
- `/health` no longer reveals `gsi_online` or timer status to unauthenticated LAN clients (dashboard still shows connection state).
- HTTP/Docker port binds to localhost by default. Phone access requires explicit opt-in.
- WebSocket connection requests without a valid same-origin `Origin` header are rejected. Existing browsers work; handcrafted clients must supply this header.
- Version exposed by `/health` and WebSocket `auth_ok` is `1p-a`; normal dashboard UI is unchanged.

**Not yet validated** on live CS2/FACEIT nor on the user's Windows Docker installation.

## V1P-B / step 4 changes

- `/health` now returns `version: 1p-b`; the browser JS must use the matching version.
- The game state invalidates round-only `state` and `weapons` on round changes and prolonged GSI silence; resets player/session at map switches, rewinds and match restarts.
- Offline/stale-match clients (including heartbeat-only provider packets) see blank **live** player fields and score (rather than stale values) while the header indicates CS2 is offline.
- Economy `source` is `gsi`, `history`, or `unknown`. `gsi` means CS2 supplied `consecutive_round_losses` in the current round; it is not a promise of eventual money. `history` is estimated under standard competitive MR12 assumptions and only when that half's history is complete. `unknown` renders `—` instead of assuming an unverified +$1,400.
- Existing widget types and localStorage keys remain untouched. The timer deliberately stays opt-in, private-test only and approximate.
- New `test_lifecycle.py` covers map transitions, round boundaries, gaps, history inference, server/WS and no stale HUD; rerun original four tests as well.

**Still unverified**: true GSI behavior on the user's Windows + CS2 + FACEIT setup, Docker build in this environment, and the standard-match assumptions on custom servers.


## V1P-C baseline extension

No GSI endpoints, dashboard widget IDs or browser localStorage keys were changed by stage 5; only version reporting advances to `1p-c`. The Windows installer is opt-in, preserves existing `.env`, and backs up a conflicting GSI before replacing it. Test on a real Windows PC before treating installer support as production ready.
