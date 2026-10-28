/* Translation API regressions; no browser or personal storage is needed. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

for (const locale of ['EN', 'FR']) {
 const context = vm.createContext({
  window: {},
  localStorage: {getItem: () => locale},
  document: {addEventListener() {}}
 });
 vm.runInContext(fs.readFileSync('static/js/i18n.js', 'utf8'), context);
 const api = context.window.CS2I18N;
 assert.equal(api.locale(), locale);
 assert.equal(api.message('profile.error'), locale === 'EN'
  ? 'Could not save. Check server storage.'
  : 'Enregistrement impossible. Vérifie le stockage du serveur.');
 assert.equal(api.message('profile.saving'), locale === 'EN' ? 'Saving…' : 'Enregistrement…');
 assert.equal(api.message('unknown'), '');
}
console.log('OK: profile save/error messages follow the EN/FR preference');
