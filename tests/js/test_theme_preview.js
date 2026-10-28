'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const listeners = {};
const root = {dataset: {}};
const select = {value: '', addEventListener: (type, fn) => { listeners[type] = fn; }};
const meta = {content: ''};
const forbidden = () => { throw Error('Theme preview must not access storage or transport'); };
const context = {
  document: {
    documentElement: root,
    getElementById: id => id === 'theme-preview' ? select : null,
    querySelector: () => meta
  },
  fetch: forbidden,
  WebSocket: forbidden
};
Object.defineProperties(context, {
  localStorage: {get: forbidden},
  sessionStorage: {get: forbidden}
});
vm.runInNewContext(fs.readFileSync('static/js/theme-preview.js', 'utf8'), context);
assert.equal(root.dataset.theme, 'tactical-blue');
assert.equal(meta.content, '#090E14');
for (const [theme, color] of Object.entries({
  'competitive-red': '#0B0D11', 'performance-green': '#0A100E',
  'creator-purple': '#100C16', 'tactical-blue': '#090E14'
})) {
  listeners.change({target: {value: theme}});
  assert.equal(root.dataset.theme, theme);
  assert.equal(select.value, theme);
  assert.equal(meta.content, color);
}
for (const value of ['__proto__', 'constructor', '', 'unknown']) {
  listeners.change({target: {value}});
  assert.equal(root.dataset.theme, 'tactical-blue');
}
console.log('OK: tab-local theme preview, allowlist, fallback, no storage or transport');
