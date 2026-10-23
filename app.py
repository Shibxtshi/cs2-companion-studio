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
from security import LoginLimiter, same_origin
from gsi_lifecycle import EconomyObserver, cash_projection
from profile_store import ProfileStore
from support_diagnostics import Diagnostics
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent
VERSION = '1p-f'
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
    online = last_game_seen is not None and time.monotonic() - last_game_seen < 20
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
        'gsi_connected': last_seen is not None and time.monotonic() - last_seen < 20,
        'age_seconds': None if last_seen is None else min(999, round(time.monotonic() - last_seen, 1)),
        'map': str(mp.get('name') or ''),
        'map_mode': str(mp.get('mode') or ''),
        'map_phase': str(mp.get('phase') or ''),
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
    msg = json.dumps(summary(), ensure_ascii=False)
    gone = []
    for ws in tuple(connected):
        try:
            await ws.send_text(msg)
        except Exception:
            gone.append(ws)
    for ws in gone:
        connected.discard(ws)


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
app.mount('/static', StaticFiles(directory=ROOT / 'static'), name='static')

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
    old_map = state.get('map') or {}
    old_round = state.get('round') or {}
    old_player = state.get('player') or {}
    incoming_map = incoming.get('map') if isinstance(incoming.get('map'), dict) else {}
    incoming_round = incoming.get('round') if isinstance(incoming.get('round'), dict) else {}
    incoming_player = incoming.get('player') if isinstance(incoming.get('player'), dict) else {}
    incoming_bomb = incoming.get('bomb') if isinstance(incoming.get('bomb'), dict) else {}
    old_map_name = old_map.get('name')
    new_map_name = incoming_map.get('name')
    old_number, new_number = number(old_map.get('round')), number(incoming_map.get('round'))
    map_switched = bool(old_map_name and new_map_name and new_map_name != old_map_name)
    mode_switched = bool(old_map.get('mode') and incoming_map.get('mode') and
                         incoming_map['mode'] != old_map['mode'])
    rewind = old_number is not None and new_number is not None and new_number < old_number
    phase_restarted = (old_map.get('phase') == 'gameover' and
                       incoming_map.get('phase') in ('warmup', 'live'))
    fresh_match = map_switched or mode_switched or rewind or phase_restarted
    changed_round = old_number is not None and new_number is not None and new_number != old_number
    old_id = old_player.get('steamid')
    new_id = incoming_player.get('steamid')
    identity_changed = bool(old_id and new_id and old_id != new_id)
    old_team = old_player.get('team')
    new_team = incoming_player.get('team')
    side_switched = bool(old_team and new_team and old_team != new_team)
    recent = last_game_seen is not None and 0 <= now - last_game_seen <= 20
    old_bomb_state = str(old_round.get('bomb') or '').lower()
    old_ps = old_player.get('state') if isinstance(old_player.get('state'), dict) else {}
    old_stats = old_player.get('match_stats') if isinstance(old_player.get('match_stats'), dict) else {}
    prev_health = number(old_ps.get('health'))
    prev_kills = number(old_stats.get('kills'))

    if fresh_match:
        state.clear()
        state.update({'map': {}, 'round': {}, 'player': {}, 'provider': {}})
        events.clear()
        economy_observer.reset()
        bomb_started_at = None
        bomb_start_unknown = False
    elif changed_round:
        state['round'] = {}
        p = state.setdefault('player', {})
        p.pop('state', None)
        p.pop('weapons', None)
        bomb_started_at = None
        bomb_start_unknown = False
        if old_map_name:
            add_event('Nouvelle manche', 'round')
    if not recent and last_game_seen is not None and not (fresh_match or changed_round):
        p = state.setdefault('player', {})
        for transient in ('state', 'weapons', 'match_stats'):
            p.pop(transient, None)
        prev_health = prev_kills = None
    if identity_changed:
        state['player'] = {}
        prev_health = prev_kills = None
    if side_switched and not changed_round:
        # Never mix weapons and health from two sides (e.g. spectator/team swap).
        p = state.setdefault('player', {})
        p.pop('state', None)
        p.pop('weapons', None)
        prev_health = None
    if fresh_match or changed_round or identity_changed:
        prev_health = prev_kills = None

    for section in ('map', 'round', 'player', 'provider'):
        if isinstance(incoming.get(section), dict):
            merge(state.setdefault(section, {}), incoming[section])
    # Never blindly trust a cached direct bonus from the prior round.
    economy_observer.ingest(incoming_map, state.get('map') or {})

    new_ps = (state.get('player') or {}).get('state') or {}
    new_stats = (state.get('player') or {}).get('match_stats') or {}
    current_health = number(new_ps.get('health'))
    current_kills = number(new_stats.get('kills'))
    if prev_health is not None and current_health is not None and prev_health != current_health:
        add_event(('Soins' if current_health > prev_health else 'Dégâts') + f' · {current_health} HP', 'health')
    if prev_kills is not None and current_kills is not None and current_kills > prev_kills:
        add_event(f'Élimination · {current_kills} au total', 'kill')

    new_bomb_state = incoming_round.get('bomb')
    if new_bomb_state is None:
        new_bomb_state = incoming_bomb.get('state')
    if isinstance(new_bomb_state, str):
        new_bomb_state = new_bomb_state.lower()
        if new_bomb_state == 'planted' and old_bomb_state != 'planted':
            add_event('Bombe plantée', 'bomb')
            # An actively observed round *before* this packet is required.
            observed_live = bool(old_round) and old_round.get('phase') == 'live' and recent and not (fresh_match or changed_round)
            if observed_live:
                bomb_started_at = now
                bomb_start_unknown = False
            else:
                bomb_started_at = None
                bomb_start_unknown = True
        elif new_bomb_state in ('defused', 'exploded'):
            if new_bomb_state != old_bomb_state:
                add_event('Bombe ' + ('désamorcée' if new_bomb_state == 'defused' else 'explosée'), 'bomb')
            bomb_started_at = None
            bomb_start_unknown = False
        if new_bomb_state in ('planted', 'defused', 'exploded'):
            state.setdefault('round', {})['bomb'] = new_bomb_state

    new_phase = (state.get('round') or {}).get('phase')
    map_phase = (state.get('map') or {}).get('phase')
    if new_phase in ('over', 'freezetime') or map_phase == 'gameover':
        if new_phase in ('over', 'freezetime') and (state.get('round') or {}).get('bomb') == 'planted':
            state['round']['bomb'] = None
        bomb_started_at = None
        bomb_start_unknown = False
    if map_phase in ('gameover', 'warmup') and old_map.get('phase') not in ('gameover', 'warmup'):
        # An ended match must not show the previous player's weapon/cash/HP.
        state['player'] = {}
        state['round'] = {}
        economy_observer.reset()
        bomb_started_at = None
        bomb_start_unknown = False
    if not recent and last_game_seen is not None and old_bomb_state == 'planted' and not (fresh_match or changed_round):
        bomb_started_at = None
        bomb_start_unknown = True
    last_seen = now
    if incoming_map or incoming_round or incoming_player:
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
        session_id = secrets.token_hex(8)
        await websocket.send_json({'type': 'auth_ok', 'version': VERSION, 'session': session_id})
        authenticated = True
        connected.add(websocket)
        pending_logins -= 1
        await websocket.send_json(profile_store.snapshot())
        await websocket.send_text(json.dumps(summary(), ensure_ascii=False))
        while True:
            raw_msg = await websocket.receive_text()
            if len(raw_msg) > 225_000:
                await websocket.close(code=1009)
                break
            try:
                command = json.loads(raw_msg)
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
                    snapshot = profile_store.snapshot(source=session_id)
                    for client in tuple(connected):
                        try:
                            await client.send_json(snapshot)
                        except Exception:
                            connected.discard(client)
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
