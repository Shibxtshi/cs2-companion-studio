/* Temporary, tab-local preview. Profile persistence belongs to a later phase. */
(() => {
  'use strict';

  const THEME_BACKGROUNDS = Object.freeze({
    'tactical-blue': '#090E14',
    'competitive-red': '#0B0D11',
    'performance-green': '#0A100E',
    'creator-purple': '#100C16'
  });
  const DEFAULT_THEME = 'tactical-blue';
  const select = document.getElementById('theme-preview');
  const meta = document.querySelector('meta[name="theme-color"]');

  function applyTheme(value) {
    const theme = Object.prototype.hasOwnProperty.call(THEME_BACKGROUNDS, value)
      ? value : DEFAULT_THEME;
    document.documentElement.dataset.theme = theme;
    if (select) select.value = theme;
    if (meta) meta.content = THEME_BACKGROUNDS[theme];
  }

  applyTheme(DEFAULT_THEME);
  select?.addEventListener('change', event => applyTheme(event.target.value));
})();
