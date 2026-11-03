/* Shared theme application; preview is tab-local and never writes a profile. */
(() => {
  'use strict';
  const themes = Object.freeze(CCSDraftSchema.themes.map(entry => Object.freeze({...entry})));
  const known = new Set(themes.map(entry => entry.id));
  const DEFAULT_THEME = 'tactical-blue';
  const select = document.getElementById('theme-preview');
  const meta = document.querySelector('meta[name="theme-color"]');
  let applied = null;
  for (const control of document.querySelectorAll('[data-theme-select]')) {
    control.replaceChildren(...themes.map(entry => new Option(entry.name, entry.id)));
  }
  function apply(value) {
    const theme = known.has(value) ? value : DEFAULT_THEME;
    if (applied !== theme || document.documentElement.dataset.theme !== theme) {
      document.documentElement.dataset.theme = theme;
      // Read the palette only on a theme change, not on every Studio draft repaint.
      if (meta) meta.content = getComputedStyle(document.documentElement).getPropertyValue('--ccs-bg').trim();
      applied = theme;
    }
    if (select) select.value = theme;
    return theme;
  }
  window.CCSThemes = Object.freeze({apply, choices: themes});
  apply(DEFAULT_THEME);
  select?.addEventListener('change', event => apply(event.target.value));
})();
