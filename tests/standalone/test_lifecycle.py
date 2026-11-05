"""Step 4: synthetic GSI sequences covering real-world failure boundaries."""
import os
os.environ['GSI_TOKEN'] = 'lifecycle-local-test-token-1234'
os.environ['DASHBOARD_PIN'] = '654321'
os.environ['BOMB_TIMER_ENABLED'] = 'true'

from fastapi.testclient import TestClient
from companion import server as app
from companion.gsi_lifecycle import history_loss_level, cash_projection, EconomyObserver


def reset():
    app.state.clear()
    app.state.update({'map': {}, 'round': {}, 'player': {}, 'provider': {}})
    app.events.clear()
    app.economy_observer.reset()
    app.bomb_started_at = None
    app.bomb_start_unknown = False
    app.last_seen = None
    app.last_game_seen = None


def pkt(mapname='de_mirage', rnd=3, cash=2300, team='CT', **more):
    obj = {'map': {'name': mapname, 'round': rnd, 'phase': 'live', 'mode': 'competitive'},
           'round': {'phase': 'live'},
           'player': {'team': team, 'steamid': 'player1', 'state': {'money': cash, 'health': 87},
                      'weapons': {'weapon_0': {'name': 'weapon_ak47', 'state': 'active', 'ammo_clip': 12}},
                      'match_stats': {'kills': 4}}}
    for key, value in more.items():
        obj[key].update(value)
    return obj


def run():
    reset()
    app.update_from_gsi(pkt(), 100.)
    assert app.state['player']['weapons']
    # Partial weapon payload should replace inventory rather than retaining AK.
    app.update_from_gsi({'player': {'weapons': {'weapon_2': {'name': 'weapon_glock','state':'active'}}}}, 101.)
    assert len(app.state['player']['weapons']) == 1
    # Round boundary should erase personal ephemeral data absent from the packet.
    app.update_from_gsi({'map': {'round': 4}, 'round': {'phase': 'freezetime'}}, 102.)
    assert 'weapons' not in app.state['player']
    assert 'state' not in app.state['player']
    assert app.state['round']['phase'] == 'freezetime'
    assert not any(e['category'] == 'health' for e in app.events)
    app.update_from_gsi({'player': {'state': {'money': 2300}}}, 103.)
    assert app.state['player']['state']['money'] == 2300
    assert 'health' not in app.state['player']['state']

    # Mid-round lapse must not generate imaginary kills or retain stale equipment.
    app.update_from_gsi({'player': {'state': {'health': 55}, 'match_stats': {'kills': 5}}}, 104.)
    before = len(app.events)
    app.update_from_gsi({'player': {'state': {'money': 1600}, 'match_stats': {'kills': 10}}}, 129.)
    assert 'health' not in app.state['player']['state']
    assert len(app.events) == before

    # A map change resets all per-match data even if CS2 sends a partial first packet.
    app.update_from_gsi({'map': {'name': 'de_nuke', 'round': 1, 'mode': 'competitive'}}, 130.)
    assert not app.state['player'] and not app.state['round']
    assert app.state['map']['name'] == 'de_nuke'
    assert not app.events
    # A same-map round counter rewind also means a new match/session.
    app.update_from_gsi(pkt(mapname='de_nuke', rnd=18), 131.)
    app.update_from_gsi({'map': {'round': 1, 'phase': 'warmup'}}, 132.)
    assert app.state['map']['round'] == 1 and not app.state['player']

    reset()
    # GSI-provided loss count is precise as a reported field (not the payout).
    p = pkt(rnd=7)
    p['map']['team_ct'] = {'consecutive_round_losses': 3}
    app.update_from_gsi(p, 100.)
    direct = app.next_round_economy(app.state['map'], app.state['player'])
    assert direct['source'] == 'gsi' and direct['loss_bonus'] == 2900
    # If next round does not send new streak, do not re-use old direct claim.
    app.update_from_gsi({'map': {'round': 8}}, 101.)
    assert app.next_round_economy(app.state['map'], app.state['player'])['source'] == 'unknown'

    # Historical reconstruction requires complete current-half results.
    h = {'mode': 'competitive', 'round': 4, 'round_wins': {
        '1': 'ct_win_elimination', '2': 't_win_bomb', '3': 't_win_elimination'}}
    assert history_loss_level(h, 'CT') == 2  # start 1 -> 0 -> 1 -> 2
    assert history_loss_level(h, 'T') == 0
    m = dict(h, round_wins={'1': 'ct_win_elimination', '3': 't_win_bomb'})
    assert history_loss_level(m, 'CT') is None
    assert history_loss_level(dict(h, mode='casual'), 'CT') is None
    assert history_loss_level(dict(h, round=25), 'CT') is None
    half = {'mode': 'competitive', 'round': 13, 'round_wins': {str(i):'ct_win' for i in range(1,13)}}
    assert history_loss_level(half, 'CT') == 1 # halftime reset, not old 0
    assert history_loss_level(half, 'T') == 1
    assert history_loss_level({'mode':'competitive','round':13,'round_wins':{}}, 'CT') is None
    obs = EconomyObserver()
    econ = cash_projection(h, {'team': 'CT', 'state': {'money': 2500}}, obs)
    assert econ['source'] == 'history' and econ['confidence'] == 'estimated'
    assert econ['loss_bonus'] == 2400 and econ['on_loss'] == 4900
    unknown = cash_projection(m, {'team': 'CT', 'state': {'money': 2500}}, obs)
    assert unknown['on_loss'] is None and unknown['source'] == 'unknown'

    # Late plant is never treated as an exact freshly detected plant.
    reset()
    app.update_from_gsi({'map': {'name': 'de_mirage', 'round': 3},
                         'round': {'phase':'live', 'bomb':'planted'}}, 100.)
    assert app.get_bomb_timer(101)['status'] == 'unknown_start'
    app.update_from_gsi({'round': {'phase': 'over', 'bomb':'exploded'}}, 105.)
    assert app.get_bomb_timer(105)['status'] == 'idle'

    # Heartbeat-only provider packets must not keep outdated match telemetry alive.
    reset()
    app.update_from_gsi(pkt(rnd=8), 10.)
    app.update_from_gsi({'provider': {'appid': 730}}, 40.)
    assert app.last_seen == 40. and app.last_game_seen == 10.
    with_heartbeat = app.time.monotonic
    app.time.monotonic = lambda: 41.
    try:
        stale = app.summary()
        assert stale['gsi_connected'] and not stale['online']
        assert stale['player']['money'] is None
    finally:
        app.time.monotonic = with_heartbeat

    # No stale personal HUD after GSI silent period, even with the WS still active.
    reset()
    app.update_from_gsi(pkt(rnd=8), 10.)
    real_monotonic = app.time.monotonic
    app.time.monotonic = lambda: 35.
    try:
        stale = app.summary()
        assert not stale['online'] and stale['player']['money'] is None
        assert stale['ct'] is None and stale['t'] is None
    finally:
        app.time.monotonic = real_monotonic

    # End-to-end authentication + recovery to another map via a WebSocket.
    reset()
    with TestClient(app.app) as client:
        assert client.get('/health').json()['version'] == '1.1.0'
        with client.websocket_connect('/ws',headers={'origin': 'http://testserver'}) as ws:
            ws.send_json({'type': 'auth', 'pin': '654321'})
            assert ws.receive_json()['type'] == 'auth_ok'
            assert ws.receive_json()['type'] == 'profiles_catalog'
            ws.receive_json()
            first = pkt(rnd=4)
            first['auth'] = {'token': os.environ['GSI_TOKEN']}
            assert client.post('/gsi', json=first).status_code == 200
            assert ws.receive_json()['player']['money'] == 2300
            newmap = {'auth': first['auth'], 'map': {'name': 'de_ancient', 'round': 1}}
            assert client.post('/gsi', json=newmap).status_code == 200
            msg = ws.receive_json()
            assert msg['map'] == 'de_ancient'
            assert msg['player']['weapon'] == '' and msg['player']['money'] is None
    print('OK: match/round lifecycle, partial state, reconnect, source-labelled economy, halftime, stale expiry, timer, HTTP/WS')


if __name__ == '__main__':
    run()
