"""Deterministic synthetic widget states shared by target browser suites."""
KINDS = ('score map round score_split match_phase round_history weapon ammo inventory grenades '
         'equip_value gear economy cash forecast stats kd mvp personal_score round_stats '
         'health armor effects player bomb bomb_state connection events provider').split()
FIXED_TIME = 1700000000000
LIVE = {
    'type': 'state', 'online': True, 'gsi_connected': True, 'age_seconds': 0,
    'map': 'de_mirage', 'map_mode': 'competitive', 'map_phase': 'live',
    'round': 14, 'round_phase': 'live', 'ct': 8, 't': 5, 'round_winner': 'CT',
    'recent_wins': [{'round': '12', 'winner': 'ct_win'}, {'round': '13', 'winner': 't_win'}],
    'bomb_state': '', 'bomb_timer': {'enabled': False, 'status': 'disabled', 'duration': 40},
    'economy': {'on_loss': 5600, 'loss_bonus': 2400, 'source': 'gsi'},
    'events': [{'message': 'Nouvelle manche', 'at': FIXED_TIME / 1000, 'category': 'round'}],
    'provider': {'version': 'synthetic-CS2'},
    'player': {'name': 'Carte', 'team': 'CT', 'activity': 'playing', 'health': 87,
               'armor': 94, 'helmet': True, 'defusekit': True, 'money': 3200,
               'equip_value': 4300, 'flashed': 0, 'smoked': 15, 'burning': 0,
               'weapon': 'weapon_ak47', 'ammo_clip': 21, 'ammo_max': 30, 'ammo_reserve': 90,
               'kills': 18, 'assists': 4, 'deaths': 11, 'mvps': 3, 'score': 42,
               'round_kills': 2, 'round_killhs': 1, 'round_totaldmg': 167,
               'weapons': [{'name': 'weapon_ak47', 'type': 'Rifle', 'state': 'active', 'ammo_clip': 21},
                           {'name': 'weapon_smokegrenade', 'type': 'Grenade', 'state': 'holstered'}]},
}
EMPTY = {'type': 'state', 'online': False, 'gsi_connected': False, 'age_seconds': None,
         'player': {}, 'provider': {}, 'bomb_timer': {'status': 'disabled'}}


def settle(page):
    page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
