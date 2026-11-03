/* Preserve missing/zero/numeric display semantics and keep received state immutable. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {api} = require('./i18n_fixture')();
const context = vm.createContext({CS2I18N: api, window: {CS2I18N: api}});
vm.runInContext(fs.readFileSync('static/js/display-format.js', 'utf8'), context);
const format = context.window.CS2DisplayFormat;
assert.equal(format.fields({}).health, '—');
assert.equal(format.fields({}).money, '—');
assert.equal(format.fields({}).helmet, 'Helmet —');
assert.equal(format.fields({player: {health: 0}}).health, '0');
const state = Object.freeze({player: Object.freeze({
  health: 0, armor: 0, money: 0, kills: 4, deaths: 0,
  helmet: false, defusekit: false, weapon: 'weapon_ak47'
}), economy: Object.freeze({on_loss: null, source: 'unknown'})});
assert.equal(format.fields(state).health, '0');
assert.equal(format.fields(state).money, '0 $');
assert.equal(format.fields(state).kd, '4.00');
assert.equal(format.fields(state).helmet, 'No helmet');
assert.equal(format.fields(state).weapon, 'AK47');
assert.equal(format.percent(-10), '0%');
assert.equal(format.percent(120), '100%');
assert.equal(format.percent(null), '0%');
assert.equal(format.isNum(Infinity), false);
assert.equal(format.isNum('12'), false);
const money = {player: {money: 3200}};
assert.equal(format.fields(money).money, '3,200 $');
api.setLocale('FR');
assert.equal(format.fields(money).money, (3200).toLocaleString('fr-FR') + ' $');
assert.deepEqual(money, {player: {money: 3200}});
console.log('OK: display missing/zero data, K/D, equipment, clamping, localization and immutability');

for (const language of ['EN', 'FR']) {
  api.setLocale(language);
  for (const amount of [0, 1, 75, 100]) {
    for (const [source, key] of [['Dégâts', 'widgets.event.damage'], ['Soins', 'widgets.event.healing']]) {
      assert.equal(format.eventText({category: 'health', message: source + ' · ' + amount + ' HP'}), api.t(key, {amount}));
    }
  }
  for (const message of ['Player Santé', 'widgets.health.title', 'Dégâts · custom HP']) {
    assert.equal(format.eventText({category: 'health', message}), message);
    assert.equal(format.fields({player: {name: message}}).name, message);
  }
  assert.equal(format.eventText({category: 'player', message: 'Dégâts · 4 HP'}), 'Dégâts · 4 HP');
}
