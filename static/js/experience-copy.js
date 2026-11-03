/* Stable experience-key adapter; all phrases live in the shared JSON catalogs. */
(() => {
  'use strict';
  window.CCSExperienceCopy = Object.freeze({text: (key, params = {}) => CS2I18N.t('experience.' + key, params),
    keys: () => CS2I18N.keys().filter(key => key.startsWith('experience.')).map(key => key.slice(11))});
})();
