/* Key-based shared JSON catalogs. Only explicitly marked UI messages are translated. */
(() => {
  'use strict';
  const STORAGE = 'cs2-companion-language';
  const catalogs = new Map();
  let languages = [];
  let code = 'EN';
  let booting = true;
  const mounts = [];
  const parameters = value => new Set([...value.matchAll(/\{([A-Za-z][A-Za-z0-9]*)\}/g)].map(match => match[1]));
  function validate(reference, catalog) {
    if (!catalog || Array.isArray(catalog) || typeof catalog !== 'object') throw new Error('invalid_locale_catalog');
    if (Object.keys(reference).length !== Object.keys(catalog).length) throw new Error('incomplete_locale_catalog');
    for (const [key, value] of Object.entries(reference)) {
      if (!/^[a-z][A-Za-z0-9]*(?:\.[A-Za-z0-9_]+)+$/.test(key)) throw new Error('invalid_locale_key');
      if (typeof catalog[key] !== 'string' || !catalog[key].trim()) throw new Error('invalid_locale_message:' + key);
      if (/[{}]/.test(catalog[key].replace(/\{([A-Za-z][A-Za-z0-9]*)\}/g, ''))) throw new Error('malformed_locale_parameter:' + key);
      if ([...parameters(value)].sort().join() !== [...parameters(catalog[key])].sort().join()) throw new Error('locale_parameter_mismatch:' + key);
    }
  }
  function initialize(values, registry, loading = false) {
    booting = loading;
    if (!Array.isArray(registry) || new Set(registry.map(entry => entry.code)).size !== registry.length
        || !registry.some(entry => entry.code === 'EN')
        || registry.some(entry => typeof entry.name !== 'string' || !entry.name.trim())) throw new Error('invalid_locale_registry');
    const reference = values.EN;
    if (!reference) throw new Error('missing_reference_locale');
    validate(reference, reference);
    catalogs.clear();
    for (const entry of registry) {
      validate(reference, values[entry.code]);
      catalogs.set(entry.code, Object.freeze({...values[entry.code]}));
    }
    languages = registry.map(entry => Object.freeze({...entry}));
    try { const saved = localStorage.getItem(STORAGE); code = catalogs.has(saved) ? saved : 'EN'; } catch { code = 'EN'; }
  }
  function has(key) { return Object.hasOwn(catalogs.get('EN') || {}, key); }
  function t(key, params = {}) {
    let resolved = key;
    if (Object.hasOwn(params, 'count') && has(key + '.other')) {
      const plural = new Intl.PluralRules(code.toLowerCase()).select(params.count);
      resolved = has(key + '.' + plural) ? key + '.' + plural : key + '.other';
    }
    const selected = catalogs.get(code) || {};
    const reference = catalogs.get('EN') || {};
    const template = Object.hasOwn(selected, resolved) ? selected[resolved] : Object.hasOwn(reference, resolved) ? reference[resolved] : undefined;
    if (template === undefined) return '[' + key + ']';
    const required = parameters(template);
    if ([...required].some(name => !Object.hasOwn(params, name)) || Object.keys(params).some(name => !required.has(name))) {
      throw new Error('locale_parameters:' + resolved);
    }
    return template.replace(/\{([A-Za-z][A-Za-z0-9]*)\}/g, (_match, name) => String(params[name]));
  }
  function ref(key, params = {}) { return Object.freeze({messageKey: key, params: {...params}}); }
  function render(element, value) {
    if (value && typeof value === 'object' && typeof value.messageKey === 'string') bind(element, value.messageKey, value.params);
    else { delete element.dataset.i18n; delete element.dataset.i18nParams; element.textContent = value ?? ''; }
  }
  function bind(element, key, params = {}, attribute = null) {
    if (attribute) element.setAttribute('data-i18n-' + attribute, key);
    else element.dataset.i18n = key;
    if (Object.keys(params).length) element.dataset.i18nParams = JSON.stringify(params);
    else delete element.dataset.i18nParams;
    apply(element);
  }
  function apply(root = document) {
    const selector = '[data-i18n],[data-i18n-title],[data-i18n-placeholder],[data-i18n-aria-label],[data-i18n-aria-description]';
    const nodes = [...(root.matches?.(selector) ? [root] : []), ...root.querySelectorAll?.(selector) || []];
    for (const element of nodes) {
      const params = element.dataset.i18nParams ? JSON.parse(element.dataset.i18nParams) : {};
      if (element.dataset.i18n) {
        const next = t(element.dataset.i18n, params);
        if (element.textContent !== next) element.textContent = next;
      }
      for (const attr of ['title', 'placeholder', 'aria-label', 'aria-description']) {
        const key = element.getAttribute('data-i18n-' + attr);
        if (key) { const next = t(key, params); if (element.getAttribute(attr) !== next) element.setAttribute(attr, next); }
      }
    }
  }
  function setLocale(next) {
    if (!catalogs.has(next)) return false;
    code = next;
    document.documentElement.lang = code.toLowerCase();
    try { localStorage.setItem(STORAGE, code); } catch { /* Storage denial does not prevent translation. */ }
    const select = document.getElementById('locale-select'); if (select) select.value = code;
    apply();
    document.dispatchEvent(new CustomEvent('cs2:locale-changed', {detail: {locale: code}}));
    return true;
  }
  function mount(callback) {
    if (booting) mounts.push(callback);
    else if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', callback, {once: true});
    else callback();
  }
  async function boot() {
    const embedded = window.CCSLocaleResources;
    let registry = embedded?.registry;
    let values = embedded?.catalogs;
    if (!embedded) {
      const response = await fetch('/static/locales/languages.json');
      if (!response.ok) throw new Error('locale_registry_unavailable');
      registry = await response.json();
      values = {};
      await Promise.all(registry.languages.map(async entry => {
        if (!/^[A-Z][A-Z0-9-]*$/.test(entry.code) || !/^[a-z0-9-]+\.json$/.test(entry.file)) throw new Error('invalid_locale_registry');
        const result = await fetch('/static/locales/' + entry.file);
        if (!result.ok) throw new Error('locale_catalog_unavailable');
        values[entry.code] = await result.json();
      }));
    }
    initialize(values, registry.languages, true);
    const select = document.getElementById('locale-select');
    if (select) {
      select.replaceChildren(...languages.map(entry => new Option(entry.code + ' — ' + entry.name, entry.code)));
      select.addEventListener('change', event => setLocale(event.target.value));
    }
    setLocale(code);
    for (const entry of document.querySelectorAll('script[data-ccs-src]')) {
      await new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = entry.dataset.ccsSrc;
        script.onload = resolve; script.onerror = () => reject(new Error('application_module_unavailable'));
        document.head.append(script);
      });
    }
    booting = false;
    for (const callback of mounts.splice(0)) callback();
    setLocale(code);
    apply();
    const observer = new MutationObserver(records => {
      for (const record of records) for (const node of record.addedNodes) if (node.nodeType === 1) apply(node);
    });
    observer.observe(document.body, {subtree: true, childList: true});
    document.documentElement.dataset.i18nReady = 'true';
    window.addEventListener('pagehide', event => { if (!event.persisted) observer.disconnect(); });
  }
  window.CS2I18N = Object.freeze({t, ref, render, has, bind, apply, initialize, validate, setLocale, mount,
    locale: () => code, available: () => languages.map(entry => entry.code),
    numberLocale: () => code.toLowerCase(), keys: () => Object.keys(catalogs.get('EN') || {})});
  if (window.CCSLocaleResources) initialize(window.CCSLocaleResources.catalogs, window.CCSLocaleResources.registry.languages);
  if (typeof fetch === 'function') {
    const start = () => boot().catch(() => {
    // The application must not initialize with missing or malformed language resources.
    document.body.textContent = 'CCS could not load its language files. Reload the page or check the installation.';
    document.documentElement.dataset.i18nReady = 'error';
    });
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, {once: true}); else start();
  }
})();
