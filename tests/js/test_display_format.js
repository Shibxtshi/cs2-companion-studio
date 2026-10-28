/* Preserve missing/zero/numeric display semantics and keep received state immutable. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
let locale = 'EN';
const context = vm.createContext({window: {CS2I18N: {locale: () => locale}}});
vm.runInContext(fs.readFileSync('static/js/display-format.js', 'utf8'), context);
const format = context.window.CS2DisplayFormat;
assert.equal(format.fields({}).health, '—');
assert.equal(format.fields({}).money, '—');
assert.equal(format.fields({}).helmet, 'Casque —');
assert.equal(format.fields({player: {health: 0}}).health, '0');
const state = Object.freeze({player: Object.freeze({
  health: 0, armor: 0, money: 0, kills: 4, deaths: 0,
  helmet: false, defusekit: false, weapon: 'weapon_ak47'
}), economy: Object.freeze({on_loss: null, source: 'unknown'})});
assert.equal(format.fields(state).health, '0');
assert.equal(format.fields(state).money, '0 $');
assert.equal(format.fields(state).kd, '4.00');
assert.equal(format.fields(state).helmet, 'Sans casque');
assert.equal(format.fields(state).weapon, 'AK47');
assert.equal(format.percent(-10), '0%');
assert.equal(format.percent(120), '100%');
assert.equal(format.percent(null), '0%');
assert.equal(format.isNum(Infinity), false);
assert.equal(format.isNum('12'), false);
const money = {player: {money: 3200}};
assert.equal(format.fields(money).money, '3,200 $');
locale = 'FR';
assert.equal(format.fields(money).money, (3200).toLocaleString('fr-FR') + ' $');
assert.deepEqual(money, {player: {money: 3200}});
console.log('OK: display missing/zero data, K/D, equipment, clamping, localization and immutability');
