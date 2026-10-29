/* Notification lifetime and bilingual closed-copy contracts without browser dependencies. */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
let language = 'EN';
const listeners = new Map();
const timers = new Map();
let sequence = 0;
function node() {
  return {children: [], dataset: {}, attributes: {}, textContent: '',
    classList: {add() {}, remove() {}},
    replaceChildren(...children) { this.children = children; },
    append(...children) { this.children.push(...children); },
    setAttribute(key, value) { this.attributes[key] = value; },
    addEventListener(key, callback) { this[key] = callback; }};
}
const host = node();
const context = {window: null, document: {
  getElementById: () => host, createElement: node,
  addEventListener: (key, callback) => listeners.set(key, callback),
}, CS2I18N: {locale: () => language, translate: value => value},
setTimeout: callback => { const id = ++sequence; timers.set(id, callback); return id; },
clearTimeout: id => timers.delete(id), addEventListener() {}};
context.window = context;
vm.createContext(context);
for (const file of ['experience-copy.js', 'notifications.js']) {
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../../static/js', file), 'utf8'), context);
}
for (const locale of ['EN', 'FR']) {
  language = locale;
  for (const key of context.CCSExperienceCopy.keys()) {
    assert.notEqual(context.CCSExperienceCopy.text(key), key, `${locale}: ${key}`);
    assert(context.CCSExperienceCopy.text(key).trim());
  }
}
const notifications = context.CCSNotifications;
notifications.show({key: 'importFailed', kind: 'error'});
assert.equal(timers.size, 0, 'Errors must not expire');
assert.equal(host.attributes.role, 'alert');
const error = host.children[0].textContent;
notifications.show({message: 'unrelated success', kind: 'success'});
assert.equal(host.children[0].textContent, error, 'A success must not hide an error');
language = 'EN'; listeners.get('cs2:locale-changed')();
assert(host.children[0].textContent.includes('Could not import'));
host.children[1].click();
notifications.show({key: 'exportPrepared', kind: 'info'});
assert.equal(host.attributes.role, 'status');
assert.equal(timers.size, 1);
notifications.show({message: 'pending', kind: 'pending'});
assert.equal(timers.size, 0, 'Pending actions must not expire');
listeners.get('cs2:logout')();
notifications.show({message: 'success', kind: 'success'});
assert.equal(timers.size, 1);
console.log('OK: complete EN/FR copy, persistent errors/pending states, explicit dismissal, no success masking and logout cleanup');
