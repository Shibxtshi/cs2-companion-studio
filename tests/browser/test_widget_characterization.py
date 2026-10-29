"""Characterize the unchanged widget UI and collect optional local comparison evidence."""
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import statistics
import time

from playwright.sync_api import expect, sync_playwright
from test_live_browser import PIN, start_server

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).parent / 'fixtures'
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
SNAPSHOT = """() => Array.from(document.querySelectorAll('#board .widget')).map(card => ({
 kind:card.dataset.kind, heading:card.querySelector('.widget-heading').textContent,
 span:card.style.getPropertyValue('--span'), style:card.dataset.style,
 color:card.style.getPropertyValue('--widget-accent'),
 background:card.style.getPropertyValue('--widget-bg'),
 opacity:card.style.getPropertyValue('--widget-opacity'),
 values:Array.from(card.querySelectorAll('[data-v]')).map(n=>[n.dataset.v,n.textContent]),
 bars:Array.from(card.querySelectorAll('[data-p]')).map(n=>[n.dataset.p,n.style.width]),
 list:card.querySelector('[data-list]')?.textContent || '',
 bomb:card.querySelector('[data-bomb-clock]') ? {
   clock:card.querySelector('[data-bomb-clock]').textContent,
   message:card.querySelector('[data-bomb-msg]').textContent,
   color:card.querySelector('[data-bomb-clock]').className,
   width:card.querySelector('[data-bomb-fill]').style.width,
   demo:!card.querySelector('[data-demo-controls]').classList.contains('hidden')
 } : null
}))"""


def profile_document(count=29):
    return {'activeProfile': 'p-characterization', 'profiles': [{
        'id': 'p-characterization', 'name': 'Characterization fixture', 'accent': '#f3ac52',
        'density': 'normal', 'widgets': [
            {'id': 'fixture-' + str(i), 'kind': KINDS[i % len(KINDS)], 'span': 6,
             'title': 'Carte' if i == 0 else '', 'color': '#76bbfd' if i == 0 else '',
             'background': '#182333' if i == 0 else '', 'opacity': 85 if i == 0 else 100,
             'style': ('solid', 'glass', 'outline')[i % 3]}
            for i in range(count)]}]}


class FixtureSocket:
    """Synthetic transport only; the separate live journey exercises real auth and GSI."""
    def __init__(self, page, count=29):
        self.document = profile_document(count)
        self.state = copy.deepcopy(LIVE)
        self.socket = None
        self.revision = 1
        page.route_web_socket('**/ws', self.connect)

    def connect(self, socket):
        self.socket = socket
        socket.on_message(self.receive)

    def receive(self, raw):
        message = json.loads(raw)
        if message['type'] == 'auth':
            assert message['pin'] == PIN
            self.socket.send(json.dumps({'type': 'auth_ok', 'version': '1.0.0', 'session': 'fixture-session'}))
            self.send_profiles()
            self.send_state(self.state)
        elif message['type'] == 'profiles_save':
            self.document = message['document']
            self.revision += 1
            self.send_profiles('fixture-session')

    def send_profiles(self, source=None):
        self.socket.send(json.dumps({'type': 'profiles_state', 'revision': self.revision,
                                     'source': source, **self.document}))

    def send_state(self, state):
        self.state = copy.deepcopy(state)
        self.socket.send(json.dumps(self.state))


def settle(page):
    page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')


def open_fixture(context, url, count=29):
    page = context.new_page()
    faults = []
    page.on('pageerror', lambda error: faults.append(str(error)))
    fixture = FixtureSocket(page, count)
    page.goto(url, wait_until='networkidle')
    page.locator('#pin').fill(PIN)
    page.locator('#connect').click()
    expect(page.locator('#tab-custom')).to_be_visible()
    page.locator('#tab-custom').click()
    expect(page.locator('#board .widget')).to_have_count(count)
    settle(page)
    return page, fixture, faults


def compact_cases(cases):
    """Store one full reference and only changed fields for subsequent states."""
    baseline = cases['complete']
    result = {'complete': baseline}
    for name, cards in cases.items():
        if name == 'complete':
            continue
        if [card['kind'] for card in cards] != [card['kind'] for card in baseline]:
            result[name] = cards
            continue
        result[name] = [
            {'kind': card['kind'], **{key: value for key, value in card.items()
                                     if value != baseline[index][key]}}
            for index, card in enumerate(cards) if card != baseline[index]
        ]
    return result


def write_cases(target, cases):
    """Keep one widget per JSON line so reviewed golden diffs remain readable."""
    lines = ['{']
    entries = list(cases.items())
    for index, (name, cards) in enumerate(entries):
        lines.append('  ' + json.dumps(name) + ': [')
        for cardIndex, card in enumerate(cards):
            lines.append('    ' + json.dumps(card, ensure_ascii=False)
                         + (',' if cardIndex + 1 < len(cards) else ''))
        lines.append('  ]' + (',' if index + 1 < len(entries) else ''))
    lines.append('}')
    target.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def characterize(browser, url, record, output):
    for locale in ('EN', 'FR'):
        context = browser.new_context(viewport={'width': 1280, 'height': 900},
                                      locale='en-US', timezone_id='UTC')
        # Freeze synthetic dates and timer anchors, not the benchmark pages.
        context.add_init_script("""(() => {
          const OriginalDate=Date;
          window.Date=class extends OriginalDate {
            constructor(...args){super(...(args.length?args:[1700000000000]));}
            static now(){return 1700000000000;}
          };
          Object.defineProperty(performance,'now',{value:()=>1000});
        })()""")
        page, fixture, faults = open_fixture(context, url)
        assert page.evaluate('Object.keys(window.CS2WidgetCatalog)') == KINDS
        page.locator('#locale-select').select_option(locale)
        cases = {}
        zero = copy.deepcopy(LIVE)
        zero['player'].update(health=0, armor=0, money=0, ammo_clip=0, kills=4, deaths=0,
                              helmet=False, defusekit=False, name='<synthetic-player>')
        zero['economy'] = {'on_loss': None, 'loss_bonus': None, 'source': 'unknown'}
        zero['recent_wins'] = []
        zero['events'] = []
        states = [('complete', LIVE), ('missing', EMPTY), ('zero', zero)]
        history = copy.deepcopy(LIVE)
        history['economy'] = {'on_loss': 4600, 'loss_bonus': 1400, 'source': 'history'}
        states.append(('estimated-economy', history))
        for status, remaining in [('active', 40), ('active', 9), ('active', 4),
                                  ('expired', 0), ('unknown_start', None), ('stale', None),
                                  ('idle', None)]:
            state = copy.deepcopy(LIVE)
            state['bomb_state'] = 'planted' if status != 'idle' else 'defused'
            state['bomb_timer'] = {'enabled': True, 'status': status,
                                   'duration': 40, 'remaining': remaining}
            states.append(('bomb-' + status + '-' + str(remaining), state))
        for name, state in states:
            fixture.send_state(state)
            settle(page)
            cases[name] = page.evaluate(SNAPSHOT)
        fixture.send_state(LIVE)
        settle(page)
        if output:
            for width, height, name in [(1280, 900, 'desktop'), (390, 844, 'mobile')]:
                page.set_viewport_size({'width': width, 'height': height})
                settle(page)
                page.locator('#view').screenshot(path=str(output / (name + '-' + locale + '.png')),
                                                animations='disabled')
            page.set_viewport_size({'width': 1280, 'height': 900})
        # P6 deliberately rebuilds the demo board so authenticated cards cannot remain visible.
        page.locator('#demoagain').click()
        settle(page)
        cases['demo-after-session'] = page.evaluate(SNAPSHOT)
        page.close()
        # A fresh public demo has the existing five default widgets.
        page = context.new_page()
        page.on('pageerror', lambda error: faults.append(str(error)))
        page.goto(url, wait_until='networkidle')
        page.locator('#demo').click()
        settle(page)
        cases['demo-default'] = page.evaluate(SNAPSHOT)
        assert not page.locator('#tab-custom').is_visible()
        for value in ('40', '9', '4', 'stop'):
            page.locator('[data-demo="' + value + '"]').click()
            settle(page)
            cases['demo-bomb-' + value] = page.evaluate(SNAPSHOT)
        assert not faults, faults
        cases = compact_cases(cases)
        target = FIXTURES / ('widgets-' + locale.lower() + '.json')
        if record:
            target.parent.mkdir(parents=True, exist_ok=True)
            write_cases(target, cases)
        else:
            expected = json.loads(target.read_text(encoding='utf-8'))
            assert cases['demo-after-session'] == cases['demo-default']
            expected['demo-after-session'] = expected['demo-default']
            assert cases == expected, 'Widget characterization differs for ' + locale
        context.close()
    print('OK: 29 widgets, complete/missing/zero/estimated data, bomb states, native demo, EN/FR')


def measure_click(page, selector):
    return page.evaluate("""selector => {
        const start=performance.now();
        document.querySelector(selector).click();
        document.querySelector('#board').getBoundingClientRect();
        return performance.now()-start;
    }""", selector)


def benchmark(browser, url, output, repeats):
    timings = {key: [] for key in ('pageLoad', 'initialDashboard', 'render29', 'update29',
                                   'enterEditor29', 'render60')}
    for _ in range(repeats):
        context = browser.new_context(viewport={'width': 1280, 'height': 900},
                                      locale='en-US', timezone_id='UTC')
        page = context.new_page()
        fixture = FixtureSocket(page)
        page.goto(url, wait_until='networkidle')
        timings['pageLoad'].append(page.evaluate(
            "performance.getEntriesByType('navigation')[0].domContentLoadedEventEnd"))
        page.locator('#pin').fill(PIN)
        started = time.perf_counter()
        page.locator('#connect').click()
        expect(page.locator('#view')).to_be_visible()
        timings['initialDashboard'].append((time.perf_counter() - started) * 1000)
        page.locator('#tab-custom').click()
        settle(page)
        page.locator('#tab-default').click()
        timings['render29'].append(measure_click(page, '#tab-custom'))
        settle(page)
        timings['enterEditor29'].append(measure_click(page, '#edit'))
        page.locator('#edit').click()
        settle(page)
        # Include browser message dispatch, formatting and DOM writes.
        # The fixture socket is page-local and cannot reach a personal installation.
        for index in range(10):
            sample = copy.deepcopy(LIVE)
            sample['player']['health'] = 80 + index
            started = time.perf_counter()
            fixture.send_state(sample)
            expect(page.locator('[data-kind="health"] [data-v="health"]')).to_have_text(str(80 + index))
            timings['update29'].append((time.perf_counter() - started) * 1000)
        fixture.document = profile_document(60)
        fixture.revision += 1
        fixture.send_profiles()
        expect(page.locator('#board .widget')).to_have_count(60)
        settle(page)
        page.locator('#tab-default').click()
        timings['render60'].append(measure_click(page, '#tab-custom'))
        assert not page.locator('#profile-save-panel').is_visible()
        context.close()
    report = {
        'browser': browser.version, 'viewport': [1280, 900], 'repeats': repeats,
        'units': 'milliseconds', 'cache': 'fresh browser context per repetition',
        'method': 'DCL navigation; UI click+forced layout; initial/update29 include Playwright and transport latency',
        'samples': timings,
        'operations': {key: {'count': len(values), 'median': statistics.median(values),
                             'min': min(values), 'max': max(values)}
                       for key, values in timings.items()},
    }
    if output:
        (output / 'performance.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browser', choices=['chromium', 'firefox', 'webkit'], default='chromium')
    parser.add_argument('--record', action='store_true', help='Rebuild fixtures only from a reviewed baseline')
    parser.add_argument('--output', type=Path, help='Local synthetic screenshots and performance report')
    parser.add_argument('--benchmark', action='store_true')
    parser.add_argument('--repeats', type=int, default=9)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error('--repeats must be positive')
    if args.output:
        args.output.mkdir(parents=True, exist_ok=True)
    runtime, proc, url = start_server()
    try:
        with sync_playwright() as playwright:
            options = {'headless': True}
            if args.browser == 'chromium' and os.environ.get('CS2_CHROMIUM_BIN'):
                options.update(executable_path=os.environ['CS2_CHROMIUM_BIN'], args=['--no-sandbox'])
            browser = getattr(playwright, args.browser).launch(**options)
            characterize(browser, url, args.record, args.output)
            if args.benchmark:
                benchmark(browser, url, args.output, args.repeats)
            browser.close()
    finally:
        proc.terminate()
        proc.wait(timeout=10)
        runtime.cleanup()


if __name__ == '__main__':
    run()
