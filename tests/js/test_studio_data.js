/* Transient demo state, timer replacement and listener ownership. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const timers = new Map();
const listeners = new Map();
let nextTimer = 0;
const paints = [];
const values = [];
const context = vm.createContext({window: {}, structuredClone, performance: {now: () => 10},
 document: {hidden: false}, setInterval(callback) { timers.set(++nextTimer, callback); return nextTimer; },
 clearInterval(id) { timers.delete(id); }});
vm.runInContext(fs.readFileSync('static/js/studio-data.js', 'utf8'), context);
const board = {addEventListener: (name, fn) => listeners.set(name, fn),
 removeEventListener(name, fn) { assert.equal(listeners.get(name), fn); listeners.delete(name); }};
const renderer = {updateValues: (state, options) => values.push({state, options}),
 paintBomb: (state, anchor) => paints.push({state, anchor})};
let controller;
const input = {player: {health: 87}, bomb_timer: {enabled: false, status: 'disabled'}};
const frozen = JSON.stringify(input);
const selected = [];
controller = context.window.CCSStudioData({board, renderer,
 onDemo(next) { selected.push(next); controller.update(next, true); }});
function click(value) { listeners.get('click')({target: {closest: () => ({dataset: {demo: value}})}}); }
controller.update(input, false);
click('9'); assert.equal(selected.length, 0); assert.equal(timers.size, 0);
controller.update(input, true);
for (const seconds of [40, 9, 4]) {
 click(String(seconds));
 assert.equal(selected.at(-1).bomb_timer.remaining, seconds);
 assert.equal(timers.size, 1);
 [...timers.values()][0](); assert.equal(paints.at(-1).anchor.left, seconds);
}
click('invalid'); assert.equal(selected.length, 3);
click('stop'); assert.equal(timers.size, 0); assert.equal(selected.at(-1).bomb_state, 'defused');
click('9'); assert.equal(timers.size, 1);
controller.update(input, false); assert.equal(timers.size, 0);
click('4'); assert.equal(selected.length, 5);
assert.equal(JSON.stringify(input), frozen);
controller.dispose(); assert.equal(timers.size, 0); assert.equal(listeners.size, 0);
const plain = context.window.CCSStudioData({board, renderer});
plain.update(input, true); click('4'); assert.equal(plain.snapshot().state.bomb_timer.remaining, 4);
plain.dispose(); assert.equal(timers.size, 0); assert.equal(listeners.size, 0);
console.log('PASS: demo-only state, immutable input, one active timer, real-state reset and disposal');
