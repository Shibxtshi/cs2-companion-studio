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
 for (const amount of [0, 1, 75, 100]) {
  for (const [source, translated] of [['Dégâts', 'Damage'], ['Soins', 'Healing']]) {
   assert.equal(api.translate(source + ' · ' + amount + ' HP'),
    (locale === 'FR' ? source : translated) + ' · ' + amount + ' HP');
  }
 }
 for (const personal of ['Player Health', 'Soins de Player', 'Dégâts · custom HP', 'My HP widget']) {
  assert.equal(api.translate(personal), personal);
 }
}
console.log('OK: profile save/error messages follow the EN/FR preference');
