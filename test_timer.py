"""Simple offline regression tests: run with `python test_timer.py`."""
import os
os.environ.setdefault('GSI_TOKEN', 'local-test-token-1234')
os.environ.setdefault('DASHBOARD_PIN', '123456')
os.environ['BOMB_TIMER_ENABLED'] = 'true'
import app


def clear():
    app.state.clear()
    app.state.update({'map': {}, 'round': {}, 'player': {}})
    app.bomb_started_at = None
    app.bomb_start_unknown = False
    app.last_seen = None
    app.last_game_seen = None


def packet(round_num, bomb=None, phase='live'):
    pkt = {'map': {'name':'de_mirage','round':round_num}, 'round': {'phase': phase}}
    if bomb is not None:
        pkt['round']['bomb'] = bomb
    return pkt


def run():
    clear()
    app.update_from_gsi(packet(7), 100.0)
    assert app.get_bomb_timer(100)['status']=='idle'
    app.update_from_gsi(packet(7,'planted'), 101.0)
    assert app.bomb_started_at == 101.0
    assert app.get_bomb_timer(105)['remaining'] == 36.0
    app.update_from_gsi(packet(7,'planted'), 104.0)
    assert app.bomb_started_at == 101.0, 'repeat planted must not restart countdown'
    app.update_from_gsi(packet(7,'planted'), 120.0)
    assert app.get_bomb_timer(132.0)['remaining'] == 9.0
    app.update_from_gsi(packet(7,'planted'), 135.0)
    assert app.get_bomb_timer(137.0)['remaining'] == 4.0
    app.update_from_gsi(packet(7,'planted'), 140.0)
    assert app.get_bomb_timer(141.0)['status'] == 'expired'
    app.update_from_gsi(packet(7,'defused'), 141.0)
    assert app.get_bomb_timer(141.0)['status'] == 'idle'
    clear()
    app.update_from_gsi(packet(8, 'planted'), 200.0)
    assert app.get_bomb_timer(200.0)['status'] == 'unknown_start'
    assert app.bomb_started_at is None
    clear()
    app.update_from_gsi(packet(5), 300.0)
    app.update_from_gsi(packet(5,'planted'), 301.0)
    app.update_from_gsi(packet(6,phase='freezetime'), 305.0)
    assert app.get_bomb_timer(305.0)['status']=='idle'
    clear()
    app.update_from_gsi(packet(1), 400.0)
    app.update_from_gsi(packet(1,'planted'), 401.0)
    assert app.get_bomb_timer(422)['status']=='stale'
    app.update_from_gsi(packet(1,'planted'), 424.0)
    assert app.get_bomb_timer(424)['status']=='unknown_start'
    clear()
    print('OK: timer transitions, 40/10/5 thresholds, reset, reconnect and invalid late start')


if __name__ == '__main__':
    run()
