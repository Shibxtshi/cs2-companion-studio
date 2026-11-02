/* Secondary-screen composition. Authentication, profiles and GSI stay with their owners. */
(() => {
  'use strict';
  const byId = id => document.getElementById(id);
  const text = key => CCSExperienceCopy.text(key);
  let socketState = 'disconnected';
  let state = {online: false, gsi_connected: false, demo: false};
  let healthState = 'unknown';
  let checking = false;
  let fromHelp = null;
  let topic = 'start';
  let step = 0;
  let dismissed = false;
  let mounted = false;
  let sessionEnded = false;
  const ONBOARDING_KEY = 'ccs-quick-start-v1';
  try { dismissed = localStorage.getItem(ONBOARDING_KEY) === 'dismissed'; } catch { /* Help remains available without browser storage. */ }

  function put(element, value) {
    if (element.textContent !== value) element.textContent = value;
  }
  function label(element, key) {
    if (element.getAttribute('translate') !== 'no') element.setAttribute('translate', 'no');
    if (element.dataset.experienceText !== key) element.dataset.experienceText = key;
    put(element, text(key));
  }
  function element(tag, key, className = '') {
    const node = document.createElement(tag);
    node.className = className;
    if (key) label(node, key);
    return node;
  }
  function openHelp(next = 'start') {
    fromHelp = document.activeElement;
    topic = next;
    step = 0;
    renderHelp();
    const dialog = byId('help-dialog');
    if (!dialog.open) dialog.showModal();
    byId('help-close').focus();
  }
  function closeHelp() { byId('help-dialog').close(); }
  function renderHelp() {
    for (const button of document.querySelectorAll('[data-help-topic]')) {
      button.setAttribute('aria-pressed', String(button.dataset.helpTopic === topic));
    }
    const container = byId('help-topic-content');
    container.replaceChildren();
    const section = element('section');
    if (topic === 'start') {
      const progress = element('p', null, 'quick-progress');
      progress.textContent = `${step + 1} / 3`;
      section.append(progress, element('h3', 'setup' + (step + 1)), element('p', 'setup' + (step + 1) + 'Body'));
      const actions = element('div', null, 'quick-actions');
      if (step > 0) {
        const back = element('button', 'back', 'btn');
        back.type = 'button';
        back.onclick = () => { step--; renderHelp(); byId('help-topic-content').focus(); };
        actions.append(back);
      }
      const next = element('button', step === 2 ? 'done' : 'next', 'btn primary');
      next.type = 'button';
      next.onclick = () => {
        if (step < 2) { step++; renderHelp(); byId('help-topic-content').focus(); return; }
        dismissWelcome(); closeHelp();
      };
      actions.append(next);
      section.append(actions);
    } else {
      const definitions = {
        connection: ['connectionTopic', 'pinBody', 'gsiBody'],
        dashboard: ['dashboardTopic', 'navBody', 'themesBody'],
        studio: ['studioTopic', 'studioBody', 'localPolicy', 'draftPolicy', 'conflictBody'],
        recovery: ['recovery', 'recoveryBody'],
        privacy: ['privacy', 'privacyBody', 'disclosure'],
      };
      const [heading, ...paragraphs] = definitions[topic];
      section.append(element('h3', heading), ...paragraphs.map(key => element('p', key)));
    }
    container.append(section);
  }
  function dismissWelcome() {
    dismissed = true;
    try { localStorage.setItem(ONBOARDING_KEY, 'dismissed'); } catch { /* Dismissal is best effort, not a profile setting. */ }
    document.querySelector('.welcome-steps').hidden = true;
  }
  function createLogin() {
    const login = byId('login');
    const form = element('div', null, 'login-form');
    while (login.firstChild) form.append(login.firstChild);
    const story = element('div', null, 'login-story');
    const mark = element('div', null, 'brandmark');
    mark.setAttribute('aria-hidden', 'true');
    story.append(mark, element('h2', 'product'), element('p', 'intro'), element('p', 'private', 'login-proof'));
    login.append(story, form);
    label(byId('login-title'), 'login');
    label(byId('pin-help'), 'pinHelp');
    label(byId('connect'), 'connect');
    label(byId('demo'), 'demo');
    byId('pin').removeAttribute('inputmode');
    const status = element('p', null, 'login-service');
    status.id = 'login-service'; status.setAttribute('role', 'status'); status.setAttribute('translate', 'no');
    form.prepend(status);
    byId('demo').after(element('p', 'demoHelp', 'login-demo-help'));
    const welcome = form.querySelector('.welcome-steps');
    const helpButton = byId('help-from-login');
    label(helpButton, 'start');
    welcome.replaceChildren(element('strong', 'first'), element('p', 'firstHelp'));
    const actions = element('div', null, 'welcome-actions');
    const later = element('button', 'later', 'text-link'); later.type = 'button';
    later.onclick = dismissWelcome;
    actions.append(helpButton, later); welcome.append(actions); welcome.hidden = dismissed;
    const helpLink = element('button', 'connectionTopic', 'text-link'); helpLink.type = 'button';
    helpLink.onclick = () => openHelp('connection'); form.append(helpLink);
  }
  function createHelp() {
    const dialog = byId('help-dialog');
    label(byId('help-title'), 'help');
    const body = dialog.querySelector('.help-body'); body.replaceChildren();
    const navigation = element('nav', null, 'help-topics');
    navigation.setAttribute('aria-label', text('topics')); navigation.id = 'help-topics';
    for (const [id, key] of [['start','start'], ['connection','connectionTopic'], ['dashboard','dashboardTopic'], ['studio','studioTopic'], ['recovery','recovery'], ['privacy','privacy']]) {
      const button = element('button', key); button.type = 'button'; button.dataset.helpTopic = id;
      button.setAttribute('aria-controls', 'help-topic-content');
      button.onclick = () => { topic = id; renderHelp(); byId('help-topic-content').focus(); };
      navigation.append(button);
    }
    const content = element('div', null, 'help-topic-content');
    content.id = 'help-topic-content'; content.tabIndex = -1; content.setAttribute('translate', 'no');
    body.append(navigation, content);
    const reopen = element('button', 'reopen', 'text-link'); reopen.type = 'button';
    reopen.onclick = () => { topic = 'start'; step = 0; renderHelp(); content.focus(); };
    dialog.querySelector('.help-footer').prepend(reopen);
    label(byId('help-done'), 'done');
    byId('help-close').onclick = closeHelp;
    byId('help-done').onclick = closeHelp;
    byId('help-close').setAttribute('aria-label', text('close'));
    byId('open-help').onclick = () => openHelp('start');
    byId('help-from-login').onclick = () => openHelp('start');
    dialog.addEventListener('close', () => { if (fromHelp?.isConnected) fromHelp.focus(); });
    renderHelp();
  }
  function createSettings() {
    const settings = byId('dashboard-settings');
    const appearance = element('section', null, 'settings-card');
    appearance.id = 'settings-appearance';
    appearance.append(element('h2', 'appearance'), element('p', 'appearanceHelp', 'settings-intro'), settings.querySelector('.display-preferences'), byId('shell-theme-control'));
    const definitions = element('dl', null, 'settings-explainer');
    for (const key of ['density','variant','geometry']) {
      const item = element('div'); item.append(element('dt', key), element('dd', key + 'Help')); definitions.append(item);
    }
    appearance.append(definitions);
    const connection = element('section', null, 'settings-card');
    connection.append(element('h2', 'connection'), byId('shell-support'));
    const about = element('section', null, 'settings-card settings-about');
    const description = element('div');
    const helpButton = byId('settings-help');
    label(helpButton, 'help');
    description.append(element('h2', 'about'), element('p', 'edition'), element('p', 'disclosure'), helpButton);
    const version = element('span', null, 'settings-version'); version.textContent = 'v1.0.0';
    about.append(description, version);
    settings.replaceChildren(appearance, connection, about);
    const diagnosticGrid = document.querySelector('.diagnostics-grid');
    for (const [id, key] of [['match','match'], ['freshness','freshness']]) {
      const row = element('div', null, 'diagnostic-line');
      row.innerHTML = '<span aria-hidden="true">○</span><div><strong></strong><p></p></div>';
      label(row.querySelector('strong'), key); row.querySelector('p').id = 'diag-' + id;
      row.querySelector('span').id = 'diag-' + id + '-icon';
      row.querySelector('p').setAttribute('translate', 'no'); diagnosticGrid.append(row);
    }
    for (const [id, key] of [['http','server'], ['ws','socket'], ['gsi','gsi']]) label(byId('diag-' + id).previousElementSibling, key);
    label(document.querySelector('.diag-help'), 'liveHelp');
    byId('diagnostics-toggle').onclick = () => {
      const open = byId('diagnostics-panel').classList.toggle('hidden') === false;
      byId('diagnostics-toggle').setAttribute('aria-expanded', String(open));
      if (open) checkHealth();
    };
    byId('diagnostics-refresh').onclick = checkHealth;
  }
  function render() {
    if (!mounted) return;
    const demo = state.demo;
    const authorized = socketState === 'authenticated';
    const recent = authorized && !demo && state.gsi_connected && state.online;
    const gsi = authorized && !demo && state.gsi_connected;
    const service = byId('login-service');
    service.dataset.state = healthState;
    put(service, (sessionEnded ? text('sessionEnded') + ' ' : '') + text(checking ? 'checking' : healthState === 'ok' ? 'available' : healthState === 'bad' ? 'unavailable' : 'unknown'));
    const kind = demo ? 'demo' : recent ? 'live' : ['lost','error'].includes(socketState) ? 'error' : 'waiting';
    const heading = demo ? 'simulated' : recent ? 'active' : gsi ? 'gsiWaiting' : authorized ? 'waiting' : socketState === 'connecting' ? 'connecting' : 'disconnected';
    byId('session-banner').dataset.state = kind;
    label(byId('session-title'), heading);
    label(byId('session-description'), demo ? 'noLive' : ['lost','error'].includes(socketState) ? 'lost' : 'liveHelp');
    const values = {
      http: healthState === 'ok' ? 'available' : healthState === 'bad' ? 'unavailable' : 'unknown',
      ws: demo ? 'simulated' : authorized ? 'connected' : socketState === 'connecting' ? 'connecting' : 'disconnected',
      gsi: demo ? 'simulated' : gsi ? 'gsiActive' : 'noGsi',
      match: demo ? 'simulated' : recent ? 'active' : 'stale',
    };
    for (const [id, key] of Object.entries(values)) {
      label(byId('diag-' + id), key);
      const icon = byId('diag-' + id + '-icon');
      if (icon) put(icon, demo ? '○' : (id === 'http' ? healthState === 'ok' : id === 'ws' ? authorized : id === 'match' ? recent : gsi) ? '✓' : '○');
    }
    put(byId('diag-freshness'), demo ? text('simulated') : !authorized ? text('stale') : Number.isFinite(state.age_seconds) && state.age_seconds >= 0 ? `${state.age_seconds} ${text('seconds')}` : text('noAge'));
    const button = byId('connect');
    put(button, text(socketState === 'connecting' ? 'connecting' : 'connect'));
    label(byId('logout'), demo ? 'exitDemo' : 'logout');
    byId('download-support').disabled = !authorized || demo;
    button.setAttribute('aria-busy', String(socketState === 'connecting'));
    const intro = document.querySelector('#settings-appearance .settings-intro');
    label(intro, byId('dashboard-profile-menu') ? 'targetHelp' : 'appearanceHelp');
  }
  async function checkHealth() {
    if (checking) return;
    checking = true; byId('diagnostics-refresh').disabled = true; render();
    try {
      const response = await fetch('/health', {cache: 'no-store', credentials: 'same-origin', signal: AbortSignal.timeout(5000)});
      const data = response.ok ? await response.json() : null;
      healthState = data?.service === 'ok' ? 'ok' : 'bad';
    } catch { healthState = 'bad'; }
    checking = false; byId('diagnostics-refresh').disabled = false; render();
  }
  document.addEventListener('cs2:status', event => {
    if (event.detail?.code === 'connecting') sessionEnded = false;
    if (['connecting','error','lost'].includes(event.detail?.code)) socketState = event.detail.code;
    render();
  });
  document.addEventListener('cs2:authenticated', () => { socketState = 'authenticated'; healthState = 'ok'; render(); });
  document.addEventListener('cs2:state', event => {
    state = {...event.detail};
    if (state.demo) socketState = 'demo';
    render();
  });
  document.addEventListener('cs2:connection-lost', () => { socketState = 'lost'; healthState = 'unknown'; state = {}; render(); });
  document.addEventListener('cs2:network-error', () => { socketState = 'error'; healthState = 'unknown'; state = {}; render(); });
  document.addEventListener('cs2:logout', () => { sessionEnded = true; socketState = 'disconnected'; state = {}; render(); });
  document.addEventListener('cs2:locale-changed', () => {
    if (!mounted) return;
    for (const node of document.querySelectorAll('[data-experience-text]')) node.textContent = text(node.dataset.experienceText);
    byId('help-close').setAttribute('aria-label', text('close'));
    byId('help-topics').setAttribute('aria-label', text('topics'));
    renderHelp(); render();
  });
  document.addEventListener('DOMContentLoaded', () => {
    if (!byId('login') || !byId('dashboard-settings')) return;
    createLogin(); createHelp(); createSettings(); mounted = true; render(); checkHealth();
  });
})();
