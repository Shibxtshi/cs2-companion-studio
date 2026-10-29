/* Inactive read-only target host. Production index.html continues to load studio.js. */
(() => {
  'use strict';
  const byId = id => document.getElementById(id);
  const renderer = CS2WidgetRenderer({board: byId('board'), format: CS2DisplayFormat, presentation: CCSWidgetPresentation, onGeometryChange: () => grid.requestRefresh()});
  const grid = CCSDashboardGrid({board: byId('board'), onStatus: code => {
    byId('notice').textContent = code === 'layout_overflow'
      ? (CS2I18N.locale() === 'FR' ? 'Disposition trop grande : widgets restants affichés à la suite.' : 'Layout too large: remaining widgets follow below.') : '';
    byId('notice').classList.toggle('hidden', code !== 'layout_overflow');
  }});
  let pin = '';
  let last = null;
  let anchor = null;
  let disposed = false;
  let displayed = null;
  let selectionContext = null;
  const selection = document.createElement('select');
  selection.className = 'select';
  selection.id = 'dashboard-profile-menu';
  selection.setAttribute('aria-label', 'Dashboard profile / Profil');
  byId('dashboard-fullscreen').before(selection);
  const profiles = CCSPublishedProfiles({
    send: command => client.send(command),
    onChange({catalog, selectedProfileId, selectedProfileChanged}) {
      if (!catalog) { displayed = null; byId('board').replaceChildren(); return; }
      const nextContext = JSON.stringify(profiles.context);
      if (selectionContext !== nextContext) {
        selectionContext = nextContext;
        const preferred = CCSProfileSelection.read(profiles.context);
        if (preferred && preferred !== selectedProfileId && catalog.profiles.some(profile => profile.id === preferred)) { profiles.select(preferred); return; }
      }
      CCSProfileSelection.remember(profiles.context, selectedProfileId);
      selection.replaceChildren(...catalog.profiles.map(profile => {
        const option = new Option(profile.name, profile.id);
        option.setAttribute('translate', 'no');
        return option;
      }));
      selection.value = selectedProfileId;
      if (!selectedProfileChanged) return;
      const profile = profiles.profile(selectedProfileId);
      displayed = profile;
      const cards = profile.configuration.layout.widgets.map(widget =>
        renderer.createCard(widget, CS2WidgetCatalog[widget.kind]));
      byId('board').replaceChildren(...cards);
      byId('board').dataset.view = 'target';
      byId('board').dataset.studioDensity = profile.configuration.appearance.density;
      document.documentElement.style.setProperty('--profile-accent',
        profile.configuration.appearance.accent || 'var(--ccs-accent)');
      if (profile.configuration.appearance.background) byId('board').style.background = profile.configuration.appearance.background;
      else byId('board').style.removeProperty('background');
      grid.setLayout(profile.configuration.layout);
      CCSDashboardShell.setTargetProfile(profile);
      byId('empty-board').classList.toggle('hidden', cards.length > 0);
      updateValues();
    },
  });
  function status(message, kind = '') {
    byId('status').textContent = message;
    byId('status').className = 'badge ' + kind;
    document.dispatchEvent(new CustomEvent('cs2:status', {detail: {message, kind}}));
  }
  function updateValues() {
    renderer.updateValues(last, {modeDemo: false, anchor});
    grid.refreshContent();
  }
  function clearLive() {
    last = {type: 'state', online: false, gsi_connected: false, player: {}, bomb_timer: {status: 'stale'}};
    anchor = null;
    updateValues();
    document.dispatchEvent(new Event('cs2:connection-lost'));
  }
  const client = CS2DashboardClient({
    version: '1.0.0', getPin: () => pin, isDemo: () => false,
    onConnecting: () => status(CS2I18N.locale() === 'FR' ? 'Connexion…' : 'Connecting…'),
    onHealthError: () => status(CS2I18N.locale() === 'FR' ? 'Serveur indisponible' : 'Server unavailable', 'bad'),
    onNetworkError: clearLive,
    onClose({authorized}) {
      profiles.disconnected(); clearLive();
      status(CS2I18N.locale() === 'FR' ? 'Reconnexion…' : 'Reconnecting…', 'bad');
      if (authorized && !disposed) reconnect.failed();
    },
    onMessage(message) {
      if (message.type === 'auth_ok') {
        reconnect.connected(); byId('pin').value = '';
        document.dispatchEvent(new Event('cs2:authenticated'));
      }
      if (message.type === 'auth_error') {
        reconnect.stop();
        byId('loginerror').textContent = CS2I18N.locale() === 'FR' ? 'PIN incorrect.' : 'Incorrect PIN.';
      }
      profiles.receive(message);
      if (message.type === 'profiles_catalog') {
        byId('login').classList.add('hidden');
        byId('view').classList.remove('hidden');
        grid.refresh();
      }
      if (message.type === 'state') {
        document.dispatchEvent(new CustomEvent('cs2:state', {detail: {
          online: !!message.online, gsi_connected: !!message.gsi_connected,
          age_seconds: Number.isFinite(message.age_seconds) ? message.age_seconds : null, demo: false,
        }}));
        last = message;
        anchor = message.bomb_timer?.status === 'active' && Number.isFinite(message.bomb_timer.remaining)
          ? {at: performance.now(), left: message.bomb_timer.remaining} : null;
        updateValues();
        status(CS2I18N.locale() === 'FR'
          ? message.online ? 'Partie connectée' : message.gsi_connected ? 'GSI actif · en attente' : 'CS2 hors ligne'
          : message.online ? 'Match connected' : message.gsi_connected ? 'GSI active · waiting' : 'CS2 offline', message.online ? 'ok' : '');
      }
    },
  });
  const reconnect = CS2Reconnect({connect: isCurrent => client.connect(isCurrent)});
  document.addEventListener('cs2:locale-changed', () => { updateValues(); grid.requestRefresh(); });
  selection.addEventListener('change', () => profiles.select(selection.value));
  function login() {
    pin = byId('pin').value.trim();
    if (pin.length < 6) return;
    reconnect.stop(); client.close(); reconnect.start();
  }
  byId('connect').addEventListener('click', login);
  byId('pin').addEventListener('keydown', event => { if (event.key === 'Enter') login(); });
  byId('logout').addEventListener('click', () => {
    reconnect.stop(); client.close(); profiles.clear(); pin = ''; last = null; anchor = null;
    byId('view').classList.add('hidden'); byId('login').classList.remove('hidden');
    document.dispatchEvent(new Event('cs2:logout'));
  });
  // Demo uses the existing public application, never this authenticated target catalog.
  for (const id of ['demo','demoagain']) byId(id).addEventListener('click', () => { location.href = '/'; });
  document.querySelector('.workspace-head').classList.add('hidden');
  byId('tab-custom').classList.add('hidden');
  byId('profile-save-panel')?.remove();
  byId('empty-board').textContent = CS2I18N.locale() === 'FR' ? 'Ce profil ne contient aucun widget.' : 'This profile has no widgets.';
  const timer = setInterval(() => { if (!document.hidden && last?.bomb_timer?.status === 'active') renderer.paintBomb(last, anchor); }, 100);
  function dispose() { disposed = true; clearInterval(timer); reconnect.stop(); client.close(); grid.dispose(); renderer.dispose(); }
  window.addEventListener('pagehide', event => { if (!event.persisted) dispose(); });
})();
