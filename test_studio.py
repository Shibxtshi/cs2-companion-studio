"""Run from project directory: python test_studio.py (needs local requirements installed)."""
import os
os.environ['GSI_TOKEN'] = 'studio-gsi-token-local-test'
os.environ['DASHBOARD_PIN'] = '123456'
os.environ['BOMB_TIMER_ENABLED'] = 'false'
from fastapi.testclient import TestClient
import app


def run():
    app.state.clear()
    app.state.update({'map': {}, 'round': {}, 'player': {}, 'provider': {}})
    app.events.clear()
    app.economy_observer.reset()
    app.bomb_started_at = None
    app.bomb_start_unknown = False
    app.last_seen = None
    app.last_game_seen = None
    with TestClient(app.app) as client:
        hp = client.get('/health')
        assert hp.status_code == 200 and hp.json()['version'] == '1.0.0'
        html = client.get('/')
        assert 'profiles_save' in client.get('/static/studio.js').text
        assert html.status_code == 200
        assert 'Mon dashboard' in html.text
        js = client.get('/static/studio.js').text
        assert all(t in js for t in ['catalog-items', 'data-bomb-clock'])
        with client.websocket_connect('/ws', headers={'origin':'http://testserver'}) as ws:
            ws.send_json({'type': 'auth', 'pin': '123456'})
            assert ws.receive_json()['type'] == 'auth_ok'
            assert ws.receive_json()['type'] == 'profiles_state'
            ws.receive_json()
            msg = {
                'auth': {'token': 'studio-gsi-token-local-test'},
                'provider': {'appid': 730, 'version': 777},
                'map': {'name': 'de_ancient', 'mode': 'competitive', 'phase': 'live', 'round': 11,
                        'team_ct': {'score': 7, 'consecutive_round_losses': 1},
                        'team_t': {'score': 3}, 'round_wins': {'10': 'ct_win'}},
                'round': {'phase': 'live'},
                'player': {'name': 'StudioTester', 'team': 'CT', 'activity': 'playing',
                           'state': {'health': 83, 'armor': 71, 'helmet': True, 'defusekit': True,
                                     'money': 2100, 'equip_value': 4000, 'round_kills': 2,
                                     'round_killhs': 1, 'round_totaldmg': 170,
                                     'flashed': 3, 'smoked': 0, 'burning': 0},
                           'match_stats': {'kills': 9, 'assists': 3, 'deaths': 6, 'mvps': 2, 'score': 23},
                           'weapons': {'weapon_0': {'name': 'weapon_ak47', 'type': 'Rifle',
                                                    'state': 'active', 'ammo_clip': 18,
                                                    'ammo_clip_max': 30, 'ammo_reserve': 70},
                                       'weapon_1': {'name': 'weapon_flashbang', 'type': 'Grenade',
                                                    'state': 'holstered'}}},
            }
            assert client.post('/gsi', json=msg).status_code == 200
            d = ws.receive_json()
            p = d['player']
            assert (p['health'], p['armor'], p['money'], p['round_totaldmg']) == (83, 71, 2100, 170)
            assert p['helmet'] and p['defusekit'] and p['mvps'] == 2
            assert p['ammo_max'] == 30 and len(p['weapons']) == 2
            assert d['recent_wins'][0]['winner'] == 'ct_win'
            assert d['provider']['appid'] == 730
            assert d['economy']['on_loss'] == 4000
            assert d['bomb_timer']['status'] == 'disabled'
            assert 'auth' not in str(d) and 'studio-gsi-token' not in str(d)
            assert client.post('/gsi', json={'auth': {'token': 'wrong'}}).status_code == 401
        with client.websocket_connect('/ws', headers={'origin':'http://testserver'}) as bad:
            bad.send_json({'type': 'auth', 'pin': '000000'})
            assert bad.receive_json()['type'] == 'auth_error'
    print('OK: V1P-C health, page, GSI normalization, 29-widget UI, authenticated WS, token isolation')


if __name__ == '__main__':
    run()
