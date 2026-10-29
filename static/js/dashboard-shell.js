/* Shared navigation shell. Legacy storage and editing remain owned by studio.js. */
(() => {
  'use strict';
  const byId = id => document.getElementById(id);
  const root = document.documentElement;
  const view = byId('view');
  const translations = {
    en: {
      dashboard: 'Dashboard', studio: 'Customization Studio', settings: 'Settings',
      streamer: 'Streamer Studio', coming: 'Coming soon', navigation: 'Navigation',
      full: 'Full', compact: 'Compact', hidden: 'Hidden', floating: 'Floating button',
      temporary: 'Preview for this tab · not saved in profiles',
      legacy: 'Current editor · automatic saving remains active',
      profile: 'Displayed profile', default: 'Default dashboard', demo: 'Demonstration',
      fullscreen: 'Fullscreen', exit: 'Exit fullscreen', status: 'Show connection in fullscreen',
      reveal: 'Show navigation', shortcut: 'Show navigation: Alt+M. Escape closes menus or exits immersive mode.',
      preferences: 'Display preferences', help: 'Connection and help', shared: 'Current profile selection is shared between connected screens.',
      target: 'Target profile · independent selection in this tab',
    },
    fr: {
      dashboard: 'Dashboard', studio: 'Customization Studio', settings: 'Paramètres',
      streamer: 'Streamer Studio', coming: 'À venir', navigation: 'Navigation',
      full: 'Complète', compact: 'Compacte', hidden: 'Masquée', floating: 'Bouton flottant',
      temporary: 'Aperçu pour cet onglet · non enregistré dans les profils',
      legacy: 'Éditeur actuel · sauvegarde automatique active',
      profile: 'Profil affiché', default: 'Dashboard par défaut', demo: 'Démonstration',
      fullscreen: 'Plein écran', exit: 'Quitter le plein écran', status: 'Afficher la connexion en plein écran',
      reveal: 'Afficher la navigation', shortcut: 'Afficher la navigation : Alt+M. Échap ferme les menus ou quitte le mode immersif.',
      preferences: 'Préférences d’affichage', help: 'Connexion et aide', shared: 'La sélection actuelle du profil est partagée entre les écrans connectés.',
      target: 'Profil cible · sélection indépendante dans cet onglet',
    },
  };
  const locale = () => window.CS2I18N?.locale() === 'FR' ? 'fr' : 'en';
  const text = key => translations[locale()][key];
  let section = 'dashboard';
  let navigation = 'compact';
  let floating = true;
  let immersive = false;
  let showConnection = true;
  let target = false;
  let targetName = '';
  let revealed = false;
  const nav = document.createElement('nav');
  nav.className = 'dashboard-navigation';
  nav.id = 'dashboard-navigation';
  nav.innerHTML = '<a class="nav-brand" href="#main-content" aria-label="CCS"><span class="brandmark" aria-hidden="true"></span><strong translate="no">CCS</strong></a><div class="nav-items"></div><div class="nav-bottom"><span class="nav-edition" translate="no">PLAYER EDITION</span></div>';
  document.body.prepend(nav);
  const icons = {dashboard: '▦', studio: '✎', settings: '⚙', streamer: '◫'};
  for (const name of ['dashboard', 'studio', 'streamer', 'settings']) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'nav-item';
    button.dataset.section = name;
    button.innerHTML = '<span class="nav-icon" aria-hidden="true"></span><span class="nav-label"></span>';
    button.querySelector('.nav-icon').textContent = icons[name];
    if (name === 'streamer') button.disabled = true;
    else button.addEventListener('click', () => open(name));
    nav.querySelector('.nav-items').append(button);
  }
  const heading = document.createElement('div');
  heading.className = 'dashboard-heading';
  heading.innerHTML = '<div><div class="dashboard-eyebrow" translate="no">MATCH CENTER / PLAYER EDITION</div><h1 id="dashboard-title"></h1><p id="dashboard-context" class="tiny"></p></div><button type="button" id="dashboard-fullscreen" class="btn"></button>';
  byId('session-banner').before(heading);
  const settings = document.createElement('section');
  settings.id = 'dashboard-settings';
  settings.hidden = true;
  settings.innerHTML = '<button type="button" class="btn" id="settings-help">Help / Aide</button><h2 data-shell-text="preferences"></h2><div class="display-preferences"><label><span data-shell-text="navigation"></span><select class="select" id="navigation-mode"><option value="full" data-shell-text="full"></option><option value="compact" data-shell-text="compact"></option><option value="hidden" data-shell-text="hidden"></option></select></label><label class="check-label"><input type="checkbox" id="navigation-floating" checked><span data-shell-text="floating"></span></label><label class="check-label"><input type="checkbox" id="fullscreen-status" checked><span data-shell-text="status"></span></label><p class="tiny" data-shell-text="temporary"></p><p class="tiny" data-shell-text="shortcut"></p></div><div id="shell-theme-control"></div><h2 data-shell-text="help"></h2><div id="shell-support"></div>';
  heading.after(settings);
  settings.querySelector('#shell-theme-control').append(document.querySelector('.theme-preview'));
  byId('settings-help').addEventListener('click', () => byId('open-help').click());
  const support = settings.querySelector('#shell-support');
  support.append(byId('session-banner'), document.querySelector('.diagnostics-footer'));
  const editorNotice = document.createElement('p');
  editorNotice.className = 'editor-transition';
  editorNotice.dataset.shellText = 'legacy';
  byId('custom-tools').before(editorNotice);
  const edge = document.createElement('button');
  edge.type = 'button';
  edge.className = 'navigation-edge';
  edge.textContent = '›';
  edge.setAttribute('aria-controls', nav.id);
  const float = document.createElement('button');
  float.type = 'button';
  float.className = 'navigation-float btn';
  float.textContent = '☰';
  float.setAttribute('aria-controls', nav.id);
  const exit = document.createElement('button');
  exit.type = 'button';
  exit.className = 'immersive-exit btn';
  exit.textContent = '↙';
  document.body.append(edge, float, exit);
  const reveal = () => {
    revealed = !revealed;
    paint();
    if (revealed) nav.querySelector('[aria-current="page"]')?.focus();
  };
  edge.addEventListener('click', reveal);
  float.addEventListener('click', reveal);
  function open(next) {
    if (immersive) leaveFullscreen();
    if (next === 'studio' && target) return;
    section = next;
    revealed = false;
    if (next === 'studio') {
      byId('tab-custom').click();
      if (byId('edit').getAttribute('aria-pressed') !== 'true') byId('edit').click();
    } else if (byId('edit').getAttribute('aria-pressed') === 'true') byId('edit').click();
    paint();
    byId('dashboard-title').focus({preventScroll: true});
  }
  async function leaveFullscreen() {
    if (document.fullscreenElement) {
      try { await document.exitFullscreen(); } catch { /* The page fallback still remains escapable. */ }
    }
    immersive = false;
    revealed = false;
    paint();
  }
  async function enterFullscreen() {
    immersive = true;
    section = 'dashboard';
    revealed = false;
    paint();
    try { if (document.documentElement.requestFullscreen) await document.documentElement.requestFullscreen(); }
    catch { /* Keep the same accessible immersive layout when native fullscreen is refused. */ }
  }
  byId('dashboard-fullscreen').addEventListener('click', enterFullscreen);
  exit.addEventListener('click', leaveFullscreen);
  document.addEventListener('fullscreenchange', () => {
    if (!document.fullscreenElement) { immersive = false; paint(); }
  });
  document.addEventListener('keydown', event => {
    const input = event.target.closest('input:not([type="checkbox"]):not([type="radio"]),textarea,select,[contenteditable="true"]');
    if (event.altKey && event.key.toLowerCase() === 'm' && !input) {
      event.preventDefault(); reveal();
    } else if (event.key === 'Escape') {
      if (immersive) { event.preventDefault(); leaveFullscreen(); }
      else if (revealed) { revealed = false; paint(); edge.focus(); }
    }
  });
  byId('navigation-mode').addEventListener('change', event => { navigation = event.target.value; revealed = false; paint(); });
  byId('navigation-floating').addEventListener('change', event => { floating = event.target.checked; paint(); });
  byId('fullscreen-status').addEventListener('change', event => { showConnection = event.target.checked; paint(); });
  document.addEventListener('cs2:locale-changed', paint);
  byId('edit').addEventListener('click', () => {
    section = byId('edit').getAttribute('aria-pressed') === 'true' ? 'studio' : 'dashboard';
    paint();
  });
  byId('dashboard-title').tabIndex = -1;
  function paint() {
    const active = !view.classList.contains('hidden');
    const theme = document.querySelector('.theme-preview');
    const themeParent = active ? byId('shell-theme-control') : document.querySelector('.header-controls');
    if (theme.parentElement !== themeParent) themeParent.prepend(theme);
    root.dataset.shellActive = String(active);
    root.dataset.section = section;
    root.dataset.navigation = navigation;
    root.dataset.navigationRevealed = String(revealed);
    root.dataset.immersive = String(immersive);
    root.dataset.fullscreenStatus = String(showConnection);
    nav.hidden = !active;
    edge.hidden = !active || (!immersive && navigation !== 'hidden');
    float.hidden = !active || !floating || immersive || navigation !== 'hidden';
    exit.hidden = !active || !immersive;
    settings.hidden = section !== 'settings';
    byId('navigation-mode').value = navigation;
    byId('navigation-floating').checked = floating;
    byId('fullscreen-status').checked = showConnection;
    const custom = byId('tab-custom').getAttribute('aria-selected') === 'true';
    const demo = byId('status').textContent.match(/demo|démo/i);
    const name = target ? targetName : demo ? text('demo') : custom
      ? byId('profile-select').selectedOptions[0]?.textContent || text('default') : text('default');
    byId('dashboard-title').textContent = section === 'dashboard' ? name : text(section);
    byId('dashboard-context').textContent = section === 'dashboard'
      ? target ? text('target') : custom ? text('shared') : text('dashboard') : section === 'studio' ? text('legacy') : text('temporary');
    byId('dashboard-fullscreen').textContent = text('fullscreen');
    byId('dashboard-fullscreen').hidden = section !== 'dashboard';
    edge.setAttribute('aria-label', text('reveal'));
    float.setAttribute('aria-label', text('reveal'));
    edge.setAttribute('aria-expanded', String(revealed));
    float.setAttribute('aria-expanded', String(revealed));
    exit.setAttribute('aria-label', text('exit'));
    nav.setAttribute('aria-label', text('navigation'));
    for (const button of nav.querySelectorAll('[data-section]')) {
      const key = button.dataset.section;
      button.querySelector('.nav-label').textContent = text(key) + (key === 'streamer' ? ' · ' + text('coming') : '');
      button.title = text(key) + (key === 'streamer' ? ' · ' + text('coming') : '');
      button.setAttribute('aria-label', button.title);
      if (section === key) button.setAttribute('aria-current', 'page'); else button.removeAttribute('aria-current');
      if (key === 'studio') button.disabled = target || byId('tab-custom').classList.contains('hidden');
    }
    for (const element of document.querySelectorAll('[data-shell-text]')) element.textContent = text(element.dataset.shellText);
  }
  new MutationObserver(paint).observe(view, {attributes: true, attributeFilter: ['class']});
  new MutationObserver(paint).observe(byId('profile-select'), {childList: true, subtree: true});
  document.addEventListener('cs2:status', paint);
  document.addEventListener('cs2:board-rendered', paint);
  document.addEventListener('cs2:logout', () => { section = 'dashboard'; leaveFullscreen(); });
  // Inactive target host uses this same shell; it never changes the legacy profile document.
  window.CCSDashboardShell = Object.freeze({
    setTargetProfile(profile) {
      target = true; targetName = profile.name;
      const theme = byId('theme-preview');
      theme.value = profile.configuration.theme;
      theme.dispatchEvent(new Event('change'));
      navigation = profile.configuration.navigation.mode;
      floating = profile.configuration.navigation.floatingButton;
      showConnection = profile.configuration.fullscreen.showConnectionStatus;
      paint();
    },
    refresh: paint,
  });
  paint();
})();
