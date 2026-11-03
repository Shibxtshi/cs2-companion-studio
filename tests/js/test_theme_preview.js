'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const listeners = {};
let styleReads = 0;
const root = {dataset: {}};
const select = {value: '', replaceChildren(...items) { this.options = items; }, addEventListener(type, fn) { listeners[type] = fn; }};
const studioSelect = {replaceChildren(...items) { this.options = items; }};
const meta = {content: ''};
const forbidden = () => { throw Error('Theme preview must not access storage or transport'); };
const css = fs.readFileSync('static/css/themes.css', 'utf8');
const colors = Object.fromEntries([...css.matchAll(/data-theme="([a-z-]+)"\] \{[^}]*?--ccs-bg:(#[0-9A-F]+);/g)].map(match => [match[1], match[2]]));
const context = {
  document: {documentElement: root, getElementById: () => select,
    querySelector: () => meta, querySelectorAll: () => [select, studioSelect]},
  Option: function(text, value) { this.text = text; this.value = value; },
  getComputedStyle: () => { styleReads++; return {getPropertyValue: () => colors[root.dataset.theme]}; },
  fetch: forbidden, WebSocket: forbidden
};
context.window = context;
Object.defineProperties(context, {localStorage: {get: forbidden}, sessionStorage: {get: forbidden}});
vm.runInNewContext(fs.readFileSync('static/js/draft-schema.js', 'utf8'), context);
vm.runInNewContext(fs.readFileSync('static/js/theme-preview.js', 'utf8'), context);
assert.equal(root.dataset.theme, 'tactical-blue');
assert.equal(meta.content, '#090E14');
assert.equal(context.CCSThemes.choices.length, 10);
assert.deepEqual(select.options.map(option => option.value), studioSelect.options.map(option => option.value));
for (const entry of context.CCSThemes.choices) {
  listeners.change({target: {value: entry.id}});
  assert.equal(root.dataset.theme, entry.id);
  assert.equal(select.value, entry.id);
  assert.equal(meta.content, colors[entry.id]);
  assert(select.options.some(option => option.text === entry.name));
}
for (const value of ['__proto__', 'constructor', '', 'unknown']) {
  listeners.change({target: {value}});
  assert.equal(root.dataset.theme, 'tactical-blue');
}
assert.equal(styleReads, context.CCSThemes.choices.length + 1);
context.CCSThemes.apply('tactical-blue');
assert.equal(styleReads, context.CCSThemes.choices.length + 1);
console.log('OK: ten generated theme choices, shared CSS colors, meta, fallback, no storage or transport');
