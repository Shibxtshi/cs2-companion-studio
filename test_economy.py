"""Offline tests: python test_economy.py. No CS2 or Docker required."""
import os
os.environ.setdefault('GSI_TOKEN','local-test-token-1234')
os.environ.setdefault('DASHBOARD_PIN','123456')

from fastapi.testclient import TestClient
import app


def run():
    def proj(team, cash, streak=None):
        mp = {}
        if streak is not None:
            mp['team_ct' if team == 'CT' else 'team_t'] = {'consecutive_round_losses': streak}
        app.economy_observer.reset()
        if streak is not None:
            mp['round'] = 1
            app.economy_observer.ingest(mp, mp)
        return app.next_round_economy(mp, {'team': team, 'state': {'money': cash}})

    assert proj('CT', 3200, 2)['on_loss'] == 5600
    assert proj('T', 3200)['source'] == 'unknown'
    assert proj('CT', 15800, 4)['on_loss'] == 16000
    assert proj('CT', 1000, 0)['loss_bonus'] == 1400
    assert proj('T', 1000, 1)['loss_bonus'] == 1900
    assert proj('CT', 1000, 3)['loss_bonus'] == 2900
    assert proj('CT', 1000, 4)['loss_bonus'] == 3400
    assert proj('?', 1000)['on_loss'] is None
    assert proj('CT', None)['on_loss'] is None

    app.economy_observer.reset()
    with TestClient(app.app) as client:
        assert client.get('/health').json()['version'] == '1p-f'
        with client.websocket_connect('/ws', headers={'origin':'http://testserver'}) as ws:
            ws.send_json({'type': 'auth', 'pin': '123456'})
            assert ws.receive_json()['type'] == 'auth_ok'
            assert ws.receive_json()['type'] == 'profiles_state'
            ws.receive_json()  # initial state
            packet = {
                'auth': {'token':'local-test-token-1234'},
                'map': {'name':'de_mirage','round':8,'team_ct':{'score':4,'consecutive_round_losses':2},'team_t':{'score':3}},
                'round': {'phase':'live'},
                'player': {'name':'Tester','team':'CT','state':{'money':3200},'match_stats':{'kills':12,'assists':4,'deaths':8},
                           'weapons':{'weapon_1':{'state':'active','name':'weapon_ak47','ammo_clip':21,'ammo_reserve':90}}}
            }
            assert client.post('/gsi',json=packet).status_code == 200
            state = ws.receive_json()
            assert state['economy']['on_loss'] == 5600
            assert state['player']['weapon'] == 'weapon_ak47'
            assert state['ct'] == 4 and state['t'] == 3
            assert state['player']['armor'] is None and state['player']['health'] is None
    print('OK: economy loss bonus 0..4, cap, unknown-value handling, GSI HTTP, WS and extended player payload')


if __name__=='__main__':
    run()
