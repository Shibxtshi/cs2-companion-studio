"""CS2 GSI Companion: LAN receiver + WebSocket dashboard.

Optional estimated C4 countdown for private testing. No process injection or memory reads.
FACEIT approval is NOT implied by using GSI or a secondary device.
"""
import asyncio
import json
import os
import secrets
import time
from contextlib import asynccontextmanager
from companion.security import LoginLimiter, same_origin
from companion.dashboard_delivery import broadcast_text
from companion.gsi_lifecycle import EconomyObserver, cash_projection
from companion.profile_store import ProfileStore
from companion.support_diagnostics import Diagnostics
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[1]
VERSION = '1.0.0'
DATA_DIR = Path(os.getenv('PROFILE_DATA_DIR', str(ROOT / 'data')))
LOG_DIR = Path(os.getenv('DIAGNOSTICS_DIR', str(ROOT / 'logs')))
profile_store = ProfileStore(DATA_DIR / 'profiles.json')
diagnostics = Diagnostics(LOG_DIR, VERSION)
diagnostics.write_summary(len(profile_store.data['profiles']))
GSI_TOKEN = os.environ.get('GSI_TOKEN', '')
DASHBOARD_PIN = os.environ.get('DASHBOARD_PIN', '').strip()
if len(GSI_TOKEN) < 12 or len(DASHBOARD_PIN) < 6:
    raise RuntimeError('Configure GSI_TOKEN (>=12 chars) and DASHBOARD_PIN (>=6 chars).')

# Disabled by default: do not use a timing aid on FACEIT without explicit permission.
BOMB_TIMER_ENABLED = os.getenv('BOMB_TIMER_ENABLED', 'false').strip().lower() in ('true', '1', 'yes', 'on')
try:
    BOMB_DURATION = float(os.getenv('BOMB_DURATION_SECONDS', '40'))
except ValueError as exc:
    raise RuntimeError('BOMB_DURATION_SECONDS must be a number') from exc
if not 10 <= BOMB_DURATION <= 120:
    raise RuntimeError('BOMB_DURATION_SECONDS must be between 10 and 120')

connected: set[WebSocket] = set()
limiter = LoginLimiter(limit=5, window=300, lockout=900)
pending_logins = 0
MAX_WS_CLIENTS = 16
MAX_PENDING_LOGINS = 32
MAX_GSI_SIZE = 262144
state: dict[str, Any] = {'map': {}, 'round': {}, 'player': {}, 'provider': {}}
events: list[dict[str, Any]] = []
economy_observer = EconomyObserver()
last_seen: float | None = None
last_game_seen: float | None = None
bomb_started_at: float | None = None
bomb_start_unknown = False
lock = asyncio.Lock()


def merge(dst: dict[str, Any], src: dict[str, Any]) -> None:
    """Merge partial GSI snapshots; weapon inventory replaces old inventory."""
    for k, v in src.items():
        if k == 'auth':
            continue
        if k == 'weapons' and isinstance(v, dict):
            dst[k] = v
        elif isinstance(v, dict) and isinstance(dst.get(k), dict):
            merge(dst[k], v)
        else:
            dst[k] = v


def number(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return None


def get_bomb_timer(now: float | None = None) -> dict[str, Any]:
    if now is None:
        now = time.monotonic()
    base = {'enabled': BOMB_TIMER_ENABLED, 'duration': BOMB_DURATION,
            'estimated': True, 'remaining': None, 'status': 'idle'}
    if not BOMB_TIMER_ENABLED:
        base['status'] = 'disabled'
        return base
    if bomb_started_at is not None:
        if last_game_seen is None or now - last_game_seen > 20:
            base['status'] = 'stale'
            return base
        base['remaining'] = round(max(0, BOMB_DURATION - (now - bomb_started_at)), 2)
        base['status'] = 'active' if base['remaining'] > 0 else 'expired'
    elif bomb_start_unknown:
        base['status'] = 'unknown_start'
    return base


def next_round_economy(mp: dict[str, Any], player: dict[str, Any]) -> dict[str, Any]:
    """Expose source-labelled projections without inventing an absent bonus."""
    return cash_projection(mp, player, economy_observer)


def flags(v: Any) -> bool | None:
    if isinstance(v, bool):
        return v
    if v in (0, 1):
        return bool(v)
    return None


def add_event(message: str, category: str = 'info') -> None:
    """Ephemeral, derived from visible personal GSI state, never from opponents."""
    events.insert(0, {'message': message[:100], 'category': category,
                      'at': round(time.time(), 1)})
    del events[18:]


def summary() -> dict[str, Any]:
    now = time.monotonic()
    online = last_game_seen is not None and now - last_game_seen < 20
    p = (state.get('player') or {}) if online else {}
    ps = p.get('state') or {}
    stats = p.get('match_stats') or {}
    mp = state.get('map') or {}
    rnd = (state.get('round') or {}) if online else {}
    prov = state.get('provider') or {}
    weapons = p.get('weapons') or {}
    inventory = []
    for item in weapons.values():
        if isinstance(item, dict):
            inventory.append({
                'name': str(item.get('name') or ''),
                'type': str(item.get('type') or ''),
                'state': str(item.get('state') or ''),
                'ammo_clip': number(item.get('ammo_clip')),
                'ammo_max': number(item.get('ammo_clip_max')),
                'ammo_reserve': number(item.get('ammo_reserve')),
            })
    inventory = inventory[:24]
    active = next((item for item in inventory if item['state'] == 'active'), {})
    bomb = rnd.get('bomb')
    wins = mp.get('round_wins') or {}
    # map_round_wins is optional and can have variable keys / values.
    recent_wins = []
    if isinstance(wins, dict):
        for key in sorted(wins, key=lambda k: number(k) if number(k) is not None else -1)[-12:]:
            recent_wins.append({'round': str(key), 'winner': str(wins[key])})
    return {
        'type': 'state',
        'online': online,
        'gsi_connected': last_seen is not None and now - last_seen < 20,
        'age_seconds': None if last_seen is None else min(999, round(now - last_seen, 1)),
        'map': str(mp.get('name') or ''),
        'map_mode': str(mp.get('mode') or ''),
        'mapPhase': str(mp.get('phase') or ''),
        'round': number(mp.get('round')),
        'round_phase': str(rnd.get('phase') or ''),
        'round_winner': str(rnd.get('win_team') or ''),
        'recent_wins': recent_wins,
        'bomb_state': str(bomb) if bomb is not None else None,
        'bomb_timer': get_bomb_timer(),
        'economy': next_round_economy(mp, p),
        'ct': number((mp.get('team_ct') or {}).get('score')) if online else None,
        't': number((mp.get('team_t') or {}).get('score')) if online else None,
        'provider': {'version': val_if_str(prov.get('version')), 'appid': number(prov.get('appid'))},
        'events': list(events),
        'player': {
            'name': str(p.get('name') or ''), 'team': str(p.get('team') or ''),
            'activity': str(p.get('activity') or ''),
            'health': number(ps.get('health')), 'armor': number(ps.get('armor')),
            'helmet': flags(ps.get('helmet')), 'defusekit': flags(ps.get('defusekit')),
            'money': number(ps.get('money')),
            'equip_value': number(ps.get('equip_value')),
            'flashed': number(ps.get('flashed')),
            'smoked': number(ps.get('smoked')),
            'burning': number(ps.get('burning')),
            'round_kills': number(ps.get('round_kills')),
            'round_killhs': number(ps.get('round_killhs')),
            'round_totaldmg': number(ps.get('round_totaldmg')),
            'kills': number(stats.get('kills')), 'assists': number(stats.get('assists')),
            'deaths': number(stats.get('deaths')), 'mvps': number(stats.get('mvps')),
            'score': number(stats.get('score')),
            'weapon': active.get('name') or '',
            'ammo_clip': active.get('ammo_clip'),
            'ammo_max': active.get('ammo_max'),
            'ammo_reserve': active.get('ammo_reserve'),
            'weapons': inventory,
        },
    }


def val_if_str(v: Any) -> str:
    return str(v)[:60] if v is not None else ''


async def send_state() -> None:
    # Do not serialize game state while no authenticated dashboards are connected.
    if not connected:
        return
    msg = json.dumps(summary(), ensure_ascii=False)
    await broadcast_text(connected, msg)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async def periodic():
        while True:
            await asyncio.sleep(2)
            await send_state()
    task = asyncio.create_task(periodic())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
# Preserve the original asset URLs and StaticFiles HTTP semantics.
_static_files = StaticFiles(directory=ROOT / 'static')
_LEGACY_ASSETS = {
    'styles.css': 'css/styles.css',
    **{name: 'js/' + name for name in (
        'studio.js', 'widgets.js', 'i18n.js', 'experience.js', 'profile-sync.js'
    )},
}


def _legacy_asset(relativePath):
    async def serve(request: Request):
        return await _static_files.get_response(relativePath, request.scope)
    return serve


for assetName, relativePath in _LEGACY_ASSETS.items():
    app.add_api_route('/static/' + assetName, _legacy_asset(relativePath), methods=['GET', 'HEAD'], include_in_schema=False)

app.mount('/static', _static_files, name='static')

@app.middleware('http')
async def privacy_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
        "connect-src 'self' ws: wss:; font-src 'self'; "
        "object-src 'none'; frame-ancestors 'none'; form-action 'none'; base-uri 'none'"
    )
    return response



@app.get('/')
async def index():
    return FileResponse(ROOT / 'static' / 'index.html', media_type='text/html',
                        headers={'Cache-Control': 'no-store'})


@app.get('/health')
async def health():
    return {'service': 'ok', 'version': VERSION}


def update_from_gsi(incoming: dict[str, Any], now: float) -> None:
    """Apply partial GSI data with explicit match/round boundaries.

    Round-specific sections are invalidated at boundaries; a prolonged gap
    invalidates timer synchronization. A match/map reset must not carry over
    events, weapons, money or loss-level observations from the old session.
    """
    global last_seen, last_game_seen, bomb_started_at, bomb_start_unknown
    oldMap = state.get('map') or {}
    oldRound = state.get('round') or {}
    oldPlayer = state.get('player') or {}
    incomingMap = incoming.get('map') if isinstance(incoming.get('map'), dict) else {}
    incomingRound = incoming.get('round') if isinstance(incoming.get('round'), dict) else {}
    incomingPlayer = incoming.get('player') if isinstance(incoming.get('player'), dict) else {}
    incomingBomb = incoming.get('bomb') if isinstance(incoming.get('bomb'), dict) else {}
    oldMapName = oldMap.get('name')
    newMapName = incomingMap.get('name')
    oldNumber, newNumber = number(oldMap.get('round')), number(incomingMap.get('round'))
    mapSwitched = bool(oldMapName and newMapName and newMapName != oldMapName)
    modeSwitched = bool(oldMap.get('mode') and incomingMap.get('mode') and
                         incomingMap['mode'] != oldMap['mode'])
    rewind = oldNumber is not None and newNumber is not None and newNumber < oldNumber
    phaseRestarted = (oldMap.get('phase') == 'gameover' and
                       incomingMap.get('phase') in ('warmup', 'live'))
    freshMatch = mapSwitched or modeSwitched or rewind or phaseRestarted
    changedRound = oldNumber is not None and newNumber is not None and newNumber != oldNumber
    oldId = oldPlayer.get('steamid')
    newId = incomingPlayer.get('steamid')
    identityChanged = bool(oldId and newId and oldId != newId)
    oldTeam = oldPlayer.get('team')
    newTeam = incomingPlayer.get('team')
    sideSwitched = bool(oldTeam and newTeam and oldTeam != newTeam)
    recent = last_game_seen is not None and 0 <= now - last_game_seen <= 20
    oldBombState = str(oldRound.get('bomb') or '').lower()
    oldPlayerState = oldPlayer.get('state') if isinstance(oldPlayer.get('state'), dict) else {}
    oldStats = oldPlayer.get('match_stats') if isinstance(oldPlayer.get('match_stats'), dict) else {}
    prevHealth = number(oldPlayerState.get('health'))
    prevKills = number(oldStats.get('kills'))

    if freshMatch:
        state.clear()
        state.update({'map': {}, 'round': {}, 'player': {}, 'provider': {}})
        events.clear()
        economy_observer.reset()
        bomb_started_at = None
        bomb_start_unknown = False
    elif changedRound:
        state['round'] = {}
        p = state.setdefault('player', {})
        p.pop('state', None)
        p.pop('weapons', None)
        bomb_started_at = None
        bomb_start_unknown = False
        if oldMapName:
            add_event('Nouvelle manche', 'round')
    if not recent and last_game_seen is not None and not (freshMatch or changedRound):
        p = state.setdefault('player', {})
        for transient in ('state', 'weapons', 'match_stats'):
            p.pop(transient, None)
        prevHealth = prevKills = None
    if identityChanged:
        state['player'] = {}
        prevHealth = prevKills = None
    if sideSwitched and not changedRound:
        # Never mix weapons and health from two sides (e.g. spectator/team swap).
        p = state.setdefault('player', {})
        p.pop('state', None)
        p.pop('weapons', None)
        prevHealth = None
    if freshMatch or changedRound or identityChanged:
        prevHealth = prevKills = None

    for section in ('map', 'round', 'player', 'provider'):
        if isinstance(incoming.get(section), dict):
            merge(state.setdefault(section, {}), incoming[section])
    # Never blindly trust a cached direct bonus from the prior round.
    economy_observer.ingest(incomingMap, state.get('map') or {})

    newPlayerState = (state.get('player') or {}).get('state') or {}
    newStats = (state.get('player') or {}).get('match_stats') or {}
    currentHealth = number(newPlayerState.get('health'))
    currentKills = number(newStats.get('kills'))
    if prevHealth is not None and currentHealth is not None and prevHealth != currentHealth:
        add_event(('Soins' if currentHealth > prevHealth else 'Dégâts') + f' · {currentHealth} HP', 'health')
    if prevKills is not None and currentKills is not None and currentKills > prevKills:
        add_event(f'Élimination · {currentKills} au total', 'kill')

    newBombState = incomingRound.get('bomb')
    if newBombState is None:
        newBombState = incomingBomb.get('state')
    if isinstance(newBombState, str):
        newBombState = newBombState.lower()
        if newBombState == 'planted' and oldBombState != 'planted':
            add_event('Bombe plantée', 'bomb')
            # An actively observed round *before* this packet is required.
            observedLive = bool(oldRound) and oldRound.get('phase') == 'live' and recent and not (freshMatch or changedRound)
            if observedLive:
                bomb_started_at = now
                bomb_start_unknown = False
            else:
                bomb_started_at = None
                bomb_start_unknown = True
        elif newBombState in ('defused', 'exploded'):
            if newBombState != oldBombState:
                add_event('Bombe ' + ('désamorcée' if newBombState == 'defused' else 'explosée'), 'bomb')
            bomb_started_at = None
            bomb_start_unknown = False
        if newBombState in ('planted', 'defused', 'exploded'):
            state.setdefault('round', {})['bomb'] = newBombState

    newPhase = (state.get('round') or {}).get('phase')
    mapPhase = (state.get('map') or {}).get('phase')
    if newPhase in ('over', 'freezetime') or mapPhase == 'gameover':
        if newPhase in ('over', 'freezetime') and (state.get('round') or {}).get('bomb') == 'planted':
            state['round']['bomb'] = None
        bomb_started_at = None
        bomb_start_unknown = False
    if mapPhase in ('gameover', 'warmup') and oldMap.get('phase') not in ('gameover', 'warmup'):
        # An ended match must not show the previous player's weapon/cash/HP.
        state['player'] = {}
        state['round'] = {}
        economy_observer.reset()
        bomb_started_at = None
        bomb_start_unknown = False
    if not recent and last_game_seen is not None and oldBombState == 'planted' and not (freshMatch or changedRound):
        bomb_started_at = None
        bomb_start_unknown = True
    last_seen = now
    if incomingMap or incomingRound or incomingPlayer:
        last_game_seen = now


@app.post('/gsi')
async def gsi(request: Request):
    # Enforce the cap DURING streaming rather than after buffering all input.
    declared = request.headers.get('content-length')
    if declared is not None:
        try:
            if int(declared) > MAX_GSI_SIZE:
                raise HTTPException(status_code=413, detail='Payload trop grand')
        except ValueError:
            raise HTTPException(status_code=400, detail='Content-Length invalide')
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > MAX_GSI_SIZE:
            diagnostics.record('gsi_too_large')
            raise HTTPException(status_code=413, detail='Payload trop grand')
    try:
        incoming = json.loads(body)
    except (ValueError, UnicodeDecodeError):
        diagnostics.record('gsi_bad_json')
        raise HTTPException(status_code=400, detail='JSON invalide')
    if not isinstance(incoming, dict) or not isinstance(incoming.get('auth'), dict):
        diagnostics.record('gsi_bad_token')
        raise HTTPException(status_code=401, detail='Jeton GSI invalide')
    token = incoming['auth'].get('token')
    if not isinstance(token, str) or not secrets.compare_digest(token, GSI_TOKEN):
        diagnostics.record('gsi_bad_token')
        raise HTTPException(status_code=401, detail='Jeton GSI invalide')
    # GSI only needs these documented data roots in active-player mode.
    for section in ('map', 'round', 'player', 'provider', 'bomb'):
        if section in incoming and not isinstance(incoming[section], dict):
            raise HTTPException(status_code=400, detail='Section GSI invalide')
    for outer, nested in (('player', ('state', 'match_stats', 'weapons')),
                          ('map', ('team_ct', 'team_t', 'round_wins'))):
        payload = incoming.get(outer) or {}
        for field in nested:
            if field in payload and not isinstance(payload[field], dict):
                raise HTTPException(status_code=400, detail='Champ GSI invalide')
    async with lock:
        update_from_gsi(incoming, time.monotonic())
    diagnostics.record('gsi_received')
    await send_state()
    return JSONResponse({'ok': True})


@app.websocket('/ws')
async def ws(websocket: WebSocket):
    """Authenticate each same-origin WebSocket, including LAN phone browsers."""
    global pending_logins
    # Require same-origin browsers; any explicit reverse proxy should preserve Host.
    if not same_origin(websocket.headers.get('origin'), websocket.headers.get('host'), secure=websocket.url.scheme == 'wss'):
        await websocket.close(code=1008)
        return
    ip = websocket.client.host if websocket.client else 'unknown'
    if not limiter.allowed(ip, time.monotonic()):
        diagnostics.record('login_blocked')
        await websocket.close(code=1008)
        return
    if len(connected) >= MAX_WS_CLIENTS or pending_logins >= MAX_PENDING_LOGINS:
        diagnostics.record('ws_capacity')
        await websocket.close(code=1013)
        return
    pending_logins += 1
    authenticated = False
    try:
        await websocket.accept()
        raw = await asyncio.wait_for(websocket.receive_text(), timeout=8.0)
        if len(raw) > 512:
            limiter.fail(ip, time.monotonic())
            diagnostics.record('login_failed')
            await websocket.send_json({'type': 'auth_error', 'message': 'Message de connexion invalide.'})
            await websocket.close(code=1008)
            return
        try:
            received = json.loads(raw)
        except json.JSONDecodeError:
            received = None
        provided = received.get('pin') if isinstance(received, dict) and received.get('type') == 'auth' else None
        if not isinstance(provided, str) or not secrets.compare_digest(provided.strip(), DASHBOARD_PIN):
            limiter.fail(ip, time.monotonic())
            diagnostics.record('login_failed')
            await websocket.send_json({'type': 'auth_error', 'message': 'Code PIN incorrect.'})
            await websocket.close(code=1008)
            return
        limiter.success(ip)
        diagnostics.record('login_success')
        sessionId = secrets.token_hex(8)
        await websocket.send_json({'type': 'auth_ok', 'version': VERSION, 'session': sessionId})
        authenticated = True
        connected.add(websocket)
        pending_logins -= 1
        await websocket.send_json(profile_store.snapshot())
        await websocket.send_text(json.dumps(summary(), ensure_ascii=False))
        while True:
            rawMsg = await websocket.receive_text()
            if len(rawMsg) > 225_000:
                await websocket.close(code=1009)
                break
            try:
                command = json.loads(rawMsg)
            except (ValueError, UnicodeDecodeError):
                continue
            if not isinstance(command, dict):
                continue
            if command.get('type') == 'profiles_save':
                async with lock:
                    try:
                        saved = profile_store.put(command.get('document'), command.get('revision'))
                    except ValueError:
                        diagnostics.record('profiles_rejected')
                        await websocket.send_json({'type': 'profiles_error', 'code': 'invalid'})
                        continue
                    except OSError:
                        diagnostics.record('profiles_storage_error')
                        await websocket.send_json({'type': 'profiles_error', 'code': 'disk'})
                        continue
                    if not saved:
                        diagnostics.record('profiles_conflict')
                        await websocket.send_json({'type': 'profiles_error', 'code': 'conflict'})
                        await websocket.send_json(profile_store.snapshot())
                        continue
                    diagnostics.record('profiles_saved')
                    diagnostics.write_summary(len(profile_store.data['profiles']))
                    snapshot = profile_store.snapshot(source=sessionId)
                    await broadcast_text(connected, json.dumps(snapshot, ensure_ascii=False))
            elif command.get('type') == 'diagnostics_request':
                await websocket.send_json({'type': 'diagnostics_data',
                                          'report': diagnostics.snapshot(len(profile_store.data['profiles']))})
    except (WebSocketDisconnect, RuntimeError, asyncio.TimeoutError):
        pass
    finally:
        if authenticated:
            diagnostics.record('ws_disconnected')
        if not authenticated:
            pending_logins -= 1
        connected.discard(websocket)
