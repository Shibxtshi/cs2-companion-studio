/* Catalog parameters, plural categories, fallback and personal-text isolation. */
'use strict';
const assert = require('node:assert/strict');
const create = require('./i18n_fixture');
const {api, catalogs, registry, storage} = create('FR');
assert.equal(api.locale(), 'FR');
assert.equal(api.t('studio.publish'), 'Enregistrer et appliquer');
assert(api.setLocale('EN'));
assert.equal(api.t('studio.publish'), 'Save and apply');
assert.equal(storage.get('cs2-companion-language'), 'EN');
assert.equal(api.t('not.a.message'), '[not.a.message]');
assert.equal(api.t('__proto__'), '[__proto__]');
assert.equal(api.t('constructor'), '[constructor]');
assert.equal(api.setLocale('XX'), false);
assert.equal(create('XX').api.locale(), 'EN');
assert.throws(() => api.t('widgets.event.damage'), /locale_parameters/);
assert.throws(() => api.t('widgets.event.damage', {amount: 2, extra: 4}), /locale_parameters/);
for (const language of ['EN', 'FR']) {
  api.setLocale(language);
  for (const amount of [0, 1, 75, 100]) {
    assert.equal(api.t('widgets.event.damage', {amount}), (language === 'FR' ? 'Dégâts reçus · ' + amount + ' HP restants' : 'Damage taken · ' + amount + ' HP remaining'));
    assert.equal(api.t('widgets.event.healing', {amount}), (language === 'FR' ? 'Après soins' : 'After healing') + ' · ' + amount + ' HP');
  }
  assert(api.t('widgets.quantity', {count: 1}).includes(language === 'FR' ? 'objet reçu' : 'item received'));
  assert(api.t('widgets.quantity', {count: 4}).includes(language === 'FR' ? 'objets reçus' : 'items received'));
  assert(api.t('studio.draftChoice.valid', {name: 'studio.publish'}).startsWith('studio.publish · '));
  const personal = 'Santé "Émilie" <img src=x onerror=alert(1)> {amount}';
  assert(api.t('studio.addWidget', {widget: personal}).includes(personal));
  const element = {dataset: {}, textContent: '', matches: () => true, querySelectorAll: () => [], getAttribute: () => null};
  api.bind(element, 'studio.addWidget', {widget: personal});
  assert.equal(element.textContent, api.t('studio.addWidget', {widget: personal}));
  assert(!Object.hasOwn(element, 'innerHTML'));
}
const third = {...catalogs.EN, 'studio.publish': 'Synthetic publish'};
api.initialize({...catalogs, ZZ: third}, [...registry.languages, {code:'ZZ', name:'Synthetic', file:'zz.json'}]);
assert(api.available().includes('ZZ'));
api.setLocale('ZZ');
assert.equal(api.t('studio.publish'), 'Synthetic publish');
assert.throws(() => api.validate(catalogs.EN, {...catalogs.FR, 'widgets.event.damage':'Bad {other}'}), /locale_parameter_mismatch/);
const incomplete = {...catalogs.FR}; delete incomplete['studio.publish'];
assert.throws(() => api.validate(catalogs.EN, incomplete), /incomplete_locale_catalog/);
console.log('OK: shared catalogs, EN/FR/third language, persistence, explicit fallback, named parameters, plurals and text-only personal values');
