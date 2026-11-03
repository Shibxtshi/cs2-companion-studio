/* Load the production translator with real public catalogs, without browser fetching. */
'use strict';
const fs = require('node:fs');
const vm = require('node:vm');
module.exports = (language = 'EN') => {
  const storage = new Map([['cs2-companion-language', language]]);
  const context = {window: {}, Intl, CustomEvent: function(type, options) { this.type=type; this.detail=options.detail; },
    localStorage: {getItem: key => storage.get(key), setItem: (key, value) => storage.set(key,value)},
    document: {documentElement: {lang: ''}, getElementById: () => null, querySelectorAll: () => [], dispatchEvent() {}}};
  vm.runInNewContext(fs.readFileSync('static/js/i18n.js', 'utf8'), context);
  const api = context.window.CS2I18N;
  const registry = JSON.parse(fs.readFileSync('static/locales/languages.json', 'utf8'));
  const catalogs = Object.fromEntries(registry.languages.map(entry => [entry.code, JSON.parse(fs.readFileSync('static/locales/' + entry.file, 'utf8'))]));
  api.initialize(catalogs, registry.languages);
  return {api, catalogs, registry, storage};
};
