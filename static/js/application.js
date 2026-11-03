/* One authenticated production composition. Published data, drafts and game values stay separate. */
(() => {
  'use strict';
  const byId = id => document.getElementById(id);
  document.documentElement.dataset.production = 'target';
   byId('studio-app').classList.add('studio-page');
   byId('studio-dialog').classList.add('studio-page');
  let pin = '';
  let loginErrorKey = null;
  let demo = false;
  let section = 'dashboard';
  let studio = null;
  let studioInitialized = false;
  let studioHint = null;
  let preferenceContext = null;
  let displayed = null;
  let game = {online: false, gsi_connected: false, player: {}, bomb_timer: {status: 'stale'}};
  let anchor = null;
  let navigating = false;
  let disposed = false;
   let preview = CCSStudioPreview({url: '/preview'});
  const renderer = CS2WidgetRenderer({board: byId('board'), format: CS2DisplayFormat,
    presentation: CCSWidgetPresentation, onGeometryChange: () => grid.requestRefresh()});
  const grid = CCSDashboardGrid({board: byId('board'), onStatus: code => {
    if (code === 'layout_overflow') notice("app.dashboard.layoutOverflow");
  }});
  const dashboardData = CCSStudioData({board: byId('board'), onDemo: values, renderer: {
    updateValues(state, options) { if (section === 'dashboard') renderer.updateValues(state, options); },
    paintBomb(state, timerAnchor) { if (section === 'dashboard') renderer.paintBomb(state, timerAnchor); },
  }});
  function showLoginError(key = null) {
    loginErrorKey = key;
    byId('loginerror').textContent = key ? CCSExperienceCopy.text(key) : '';
  }
  function notice(messageKey, kind = 'error') { CCSNotifications.show({messageKey, kind}); }
  function issue(error) {
    const code = typeof error === 'string' ? error : error?.code || 'error';
    if (studio && section === 'studio') studio.workspace.issue(code);
    else notice(code === 'legacy_export'
      ? "app.import.legacyUnsupported"
      : "app.action.failedUnchanged");
  }
  function status(code, message = '') {
    const badge = byId('status'); badge.textContent = message || CS2I18N.t("application.disconnected");
    badge.className = 'badge ' + (demo ? 'ok' : '');
    document.dispatchEvent(new CustomEvent('cs2:status', {detail: {code}}));
  }
  function values(next) {
    game = structuredClone(next);
    anchor = next.bomb_timer?.status === 'active' && Number.isFinite(next.bomb_timer.remaining)
      ? {at: performance.now(), left: next.bomb_timer.remaining} : null;
    dashboardData.update(game, demo);
    if (section === 'studio') studio?.workspace.canvas.values(game, demo);
    document.dispatchEvent(new CustomEvent('cs2:state', {detail: {online: !!game.online,
      gsi_connected: !!game.gsi_connected, demo, age_seconds: Number.isFinite(game.age_seconds) ? game.age_seconds : null}}));
    byId('status').textContent = demo ? CS2I18N.t("navigation.demo") : game.online
      ? CS2I18N.t("application.matchDataAvailable") : game.gsi_connected ? CS2I18N.t("application.gsiActiveWaiting") : CS2I18N.t("application.cs2Offline");
  }
  function clearLive() { if (!demo) values({online: false, gsi_connected: false, player: {}, bomb_timer: {status: 'stale'}}); }
  const menu = document.createElement('select'); menu.id = 'dashboard-profile-menu'; menu.className = 'select';
  menu.setAttribute('translate', 'no'); byId('dashboard-fullscreen').before(menu);
  const profiles = CCSPublishedProfiles({send: command => send(command), isDemo: () => demo,
    onStatus(code) { if (['store_changed', 'profile_deleted'].includes(code)) issue(code); },
    onChange({catalog, selectedProfileId, selectedProfileChanged}) {
      if (!catalog) return;
      const key = JSON.stringify(profiles.context);
      if (preferenceContext !== key) {
        preferenceContext = key;
        const preferred = CCSProfileSelection.read(profiles.context);
        if (preferred && preferred !== selectedProfileId && profiles.profile(preferred)) { profiles.select(preferred); return; }
      }
      CCSProfileSelection.remember(profiles.context, selectedProfileId);
      menu.replaceChildren(...catalog.profiles.map(profile => new Option(profile.name, profile.id)));
      menu.value = selectedProfileId;
      if (selectedProfileChanged) {
        if (section !== 'studio') studioHint = selectedProfileId;
        renderPublished();
      }
      byId('login').classList.add('hidden'); byId('view').classList.remove('hidden');
      if (studioInitialized) studio.lifecycle.catalogChanged().catch(issue);
      preferences();
    },
  });
  function send(command) {
    if (!profiles.ready || demo || !client.isOpen) CCSDraftContract.fail('access_required');
    client.send(command);
  }
  const transfer = CCSProfileTransfer({send});
  function render(profile) {
    const widgets = profile.configuration.layout.widgets;
    byId('board').replaceChildren(...widgets.map(widget => renderer.createCard(widget, CS2WidgetCatalog[widget.kind])));
    byId('board').dataset.view = 'target';
    byId('board').dataset.studioDensity = profile.configuration.appearance.density;
    byId('board').style.background = profile.configuration.appearance.background;
    document.documentElement.style.setProperty('--profile-accent', profile.configuration.appearance.accent || 'var(--ccs-accent)');
    grid.setLayout(profile.configuration.layout);
    byId('empty-board').classList.toggle('hidden', widgets.length > 0);
    renderer.updateValues(game, {modeDemo: demo, anchor});
  }
  function renderPublished() {
    const profile = profiles.profile(profiles.selectedProfileId);
    if (!profile) return;
    if (!displayed || displayed.id !== profile.id || displayed.revision !== profile.revision) { render(profile); displayed = profile; }
    if (section !== 'studio') CCSDashboardShell.setTargetProfile(profile);
  }
  function ensureStudio() {
    if (studio) return studio;
    let lifecycle;
    const workspace = CCSStudioWorkspace({
      edit: next => lifecycle.edit(next),
      add(kind) { const result = CCSStudioModel.add(lifecycle.preview, kind); lifecycle.edit(result.content); workspace.select(result.id); },
      duplicate(id) {
        const widget = lifecycle.preview.configuration.layout.widgets.find(item => item.id === id);
        const result = CCSStudioModel.add(lifecycle.preview, widget.kind, widget); lifecycle.edit(result.content); workspace.select(result.id);
      },
      async remove(id) {
        if (await workspace.choose(CS2I18N.ref("application.removeWidget"), CS2I18N.ref("studio.widget.removeNotice"),
          [['remove', CS2I18N.ref("application.remove")], ['cancel', workspace.message('cancel')]]) === 'remove') lifecycle.edit(CCSStudioModel.remove(lifecycle.preview, id));
      },
      undo: () => lifecycle.undo(), redo: () => lifecycle.redo(),
      selectProfile: id => lifecycle.selectProfile(id), publish: () => lifecycle.publish(),
      leave: () => lifecycle.leave('keep'), logout: () => lifecycle.logout(),
      resolveConflict: action => lifecycle.resolveConflict(action), profileAction: action => lifecycle.profileAction(action),
      retry: () => lifecycle.retry(), discardDraft: () => lifecycle.discardDraft(), recoverCopy: () => lifecycle.recoverCopy(),
      openPreview: () => preview.open(lifecycle.preview, workspace.canvas.previewData()),
      gesture: {begin: () => lifecycle.gesture.begin(), cancel: () => lifecycle.gesture.cancel(),
        commit: next => lifecycle.gesture.commit(next), edit: next => lifecycle.edit(next)},
    });
    lifecycle = CCSStudioLifecycle({profiles, send, workspace, sharedSelection: true,
      exit: () => showDashboard(), disconnected: disconnect});
    studio = {workspace, lifecycle};
    return studio;
  }
  function showDashboard() {
    studioHint = studio?.lifecycle.snapshot().selectedProfileId || studioHint;
    section = 'dashboard'; byId('studio-app').hidden = true;
    renderPublished(); renderer.updateValues(game, {modeDemo: demo, anchor});
    CCSDashboardShell.navigate('dashboard');
  }
  CCSDashboardShell.setNavigationGuard(async next => {
    if (navigating) return false;
    if (byId('view').classList.contains('hidden')) return false;
    if (next === 'studio' && (demo || (!profiles.ready && !studioInitialized))) return false;
    navigating = true;
    try {
      if (section === 'studio' && next !== 'studio' && !await studio.lifecycle.requestLeave()) return false;
      if (section === 'studio' && next !== 'studio') studioHint = studio.lifecycle.snapshot().selectedProfileId;
      if (next === 'studio') {
        const current = ensureStudio();
        studioInitialized = true;
        await current.lifecycle.enter(studioHint || profiles.selectedProfileId);
        current.workspace.canvas.values(game, demo);
      }
      section = next; byId('studio-app').hidden = next !== 'studio';
      if (next === 'studio') studio.workspace.activateAppearance();
      if (next !== 'studio') { renderPublished(); renderer.updateValues(game, {modeDemo: demo, anchor}); }
      return true;
    } catch (error) { issue(error); return false; }
    finally { navigating = false; }
  });
  function disconnect() {
     reconnect.stop(); client.close(); transfer.cancel(); preview.dispose();
     preview = CCSStudioPreview({url: '/preview'});
    studio?.lifecycle.releaseContext(); studio?.workspace.reset(); studioInitialized = false;
    profiles.clear(); displayed = null; studioHint = null; preferenceContext = null; pin = ''; demo = false;
    byId('board').replaceChildren(); menu.replaceChildren(); byId('pin').value = ''; showLoginError();
    byId('view').classList.add('hidden'); byId('login').classList.remove('hidden');
    byId('studio-app').hidden = true; section = 'dashboard';
    byId('download-support').classList.add('hidden');
    document.dispatchEvent(new Event('cs2:logout')); clearLive(); preferences();
  }
  async function logout() {
    if (demo) { disconnect(); return; }
    if (studioInitialized) { await studio.lifecycle.logout(); return; }
    if (!profiles.ready) { disconnect(); return; }
    if (!confirm(CS2I18N.t("app.logout.confirmDraftRemoval"))) return;
    const store = await CCSDraftStore.open({context: profiles.context});
    try { await CCSDraftSession.logout({store, confirmed: true}); }
    finally { store.close(); }
    disconnect();
  }
  function downloadDiagnostics(report) {
    let url;
    try {
      url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], {type: 'application/json'}));
      const link = document.createElement('a'); link.href = url; link.download = 'CS2_Companion_support.json'; link.click();
      CCSNotifications.show({key: 'exportPrepared', kind: 'info'});
    } catch { CCSNotifications.show({key: 'exportFailed', kind: 'error'}); }
    finally { if (url) setTimeout(() => URL.revokeObjectURL(url), 1000); }
  }
  const client = CS2DashboardClient({version: '1.0.0', getPin: () => pin, isDemo: () => demo,
    onConnecting: () => status('connecting', CS2I18N.t("application.connecting")),
    onHealthError: (error, versionMismatch) => { showLoginError(versionMismatch ? 'version' : 'unavailable'); },
    onNetworkError() { clearLive(); document.dispatchEvent(new Event('cs2:network-error')); },
    onClose({authorized, failed}) {
      profiles.disconnected(); transfer.cancel(); studio?.lifecycle.networkLost(); clearLive();
      document.dispatchEvent(new Event('cs2:connection-lost'));
      if (!authorized && !failed) showLoginError('refused');
      if (!failed && !disposed && !demo) reconnect.failed();
    },
    onMessage(message) {
      try {
        if (message.type === 'auth_ok') {
          reconnect.connected(); byId('pin').value = ''; showLoginError();
          byId('pin').setAttribute('aria-invalid', 'false');
          byId('download-support').classList.remove('hidden');
          document.dispatchEvent(new Event('cs2:authenticated'));
        }
        if (message.type === 'auth_error') {
          reconnect.stop(); showLoginError('invalidPin');
          byId('pin').setAttribute('aria-invalid', 'true');
        }
        profiles.receive(message);
        if (transfer.receive(message)) return;
        studio?.lifecycle.receive(message).catch(issue);
        if (message.type === 'state') values(message);
        if (message.type === 'diagnostics_data') downloadDiagnostics(message.report);
      } catch (error) { issue(error); }
    },
  });
  const reconnect = CS2Reconnect({connect: isCurrent => client.connect(isCurrent)});
  function login() {
    demo = false; pin = byId('pin').value.trim(); showLoginError();
    if (pin.length < 6) { showLoginError('shortPin'); return; }
    reconnect.stop(); client.close(); reconnect.start();
  }
  async function startDemo() {
    if (section === 'studio' && !await studio.lifecycle.requestLeave()) return;
    studio?.lifecycle.releaseContext(); studio?.workspace.reset(); studioInitialized = false;
     preview.dispose(); preview = CCSStudioPreview({url: '/preview'});
    reconnect.stop(); client.close(); transfer.cancel(); profiles.clear(); pin = ''; byId('pin').value = ''; displayed = null;
    demo = true; section = 'dashboard'; byId('studio-app').hidden = true;
    byId('download-support').classList.add('hidden');
    byId('login').classList.add('hidden'); byId('view').classList.remove('hidden'); menu.replaceChildren();
    const widgets = ['score','weapon','economy','stats','bomb'].map((kind, index) => ({
      id: 'demo-' + index, kind, x: index % 3 * 8, y: Math.floor(index / 3) * 8, width: 8, height: 8,
      variant: 'standard', title: '', color: '', background: '', opacity: 100, style: 'solid'}));
    const configuration = {theme: 'tactical-blue', appearance: {accent: '', background: '', density: 'normal'},
      navigation: {mode: 'compact', floatingButton: true}, fullscreen: {showConnectionStatus: true}, layout: {columns: 24, widgets}};
    render({configuration}); CCSDashboardShell.setTargetProfile({name: CS2I18N.t("navigation.demo"), configuration});
    values(CCSDemoState()); preferences(); CCSNotifications.dismiss(); CCSDashboardShell.navigate('dashboard');
  }
  async function importFile(file) {
    const current = ensureStudio();
    const content = await transfer.validateFile(file);
    for (;;) {
      const answer = await current.workspace.choose(CS2I18N.ref("app.import.title"),
        CS2I18N.ref("app.import.reviewNotice"),
        [['create', CS2I18N.ref("application.createLocalDraft")], ['replace', CS2I18N.ref("application.replaceCurrentDraft")],
          ['preview', CS2I18N.ref("application.openVisualPreview")], ['cancel', current.workspace.message('cancel')]],
        {review: JSON.stringify(content, null, 2)});
      if (answer === 'preview') { preview.open(content, current.workspace.canvas.previewData()); continue; }
      if (answer === 'create' || answer === 'replace') await current.lifecycle.importProfile(content, answer === 'replace');
      return;
    }
  }
  function preferences() {
     CCSDashboardShell.setStudioAvailable(!demo && (profiles.ready || studioInitialized));
    const summary = byId('production-profile-preferences'); if (!summary) return;
    const profile = profiles.profile(profiles.selectedProfileId);
    const modes = {full: CS2I18N.t("navigation.full"), compact: CS2I18N.t("navigation.compact"), hidden: CS2I18N.t("navigation.hidden")};
    summary.textContent = profile ? CS2I18N.t('app.profilePreferences', {profile: profile.name, theme: profile.configuration.theme,
      density: CS2I18N.t(profile.configuration.appearance.density === 'compact' ? 'studio.density.compact' : 'studio.density.normal'),
      navigation: modes[profile.configuration.navigation.mode]}) : CS2I18N.t('application.noPrivateProfileSelected');
    byId('settings-edit-profile').textContent = CS2I18N.t("application.editProfileInStudio");
    byId('settings-edit-profile').disabled = !profiles.ready || demo;
    menu.setAttribute('aria-label', CS2I18N.t("navigation.profile"));
    byId('production-import').textContent = CS2I18N.t("application.importProfile");
    byId('production-export').textContent = CS2I18N.t("application.exportPublishedProfile");
  }
  byId('connect').addEventListener('click', login);
  byId('pin').addEventListener('keydown', event => { if (event.key === 'Enter') login(); });
  for (const id of ['demo','demoagain']) byId(id).addEventListener('click', () => startDemo().catch(issue));
  byId('logout').addEventListener('click', () => logout().catch(issue));
  byId('download-support').addEventListener('click', () => { try { send({type: 'diagnostics_request'}); } catch { CCSNotifications.show({key: 'diagnosticsFailed', kind: 'error'}); } });
  menu.addEventListener('change', () => { studioHint = menu.value; profiles.select(menu.value); });
  document.addEventListener('cs2:locale-changed', () => { showLoginError(loginErrorKey); preferences(); values(game); });
  CS2I18N.mount( () => {
    const appearance = byId('settings-appearance');
    const summary = document.createElement('p'); summary.id = 'production-profile-preferences'; summary.setAttribute('translate', 'no');
    const edit = document.createElement('button'); edit.id = 'settings-edit-profile'; edit.className = 'btn';
    edit.textContent = CS2I18N.t("application.editProfileInStudio");
    edit.addEventListener('click', async () => { await CCSDashboardShell.navigate('studio'); if (section === 'studio') byId('studio-profile-tab').click(); });
    appearance.append(summary, edit);
    const controls = document.createElement('div'); controls.className = 'production-transfer';
    controls.innerHTML = '<button class="btn" id="production-import" type="button"></button><button class="btn" id="production-export" type="button"></button><input id="production-import-file" type="file" accept="application/json,.json" hidden>';
    byId('studio-app').querySelector('.studio-commandbar').after(controls);
    byId('production-import').onclick = () => byId('production-import-file').click();
    byId('production-import-file').onchange = event => { const file = event.target.files?.[0]; event.target.value = ''; if (file) importFile(file).catch(issue); };
    byId('production-export').onclick = () => { try { transfer.exportProfile(profiles.profile(studio.lifecycle.snapshot().selectedProfileId)); } catch (error) { issue(error); } };
    preferences();
  });
  window.addEventListener('beforeunload', event => { if (studio?.lifecycle.dirty) { event.preventDefault(); event.returnValue = ''; } });
  const checkContext = () => studio?.lifecycle.checkContext().catch(issue);
  window.addEventListener('focus', checkContext);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) checkContext(); });
  window.addEventListener('pagehide', event => {
    if (event.persisted) return;
    disposed = true; dashboardData.dispose(); studio?.lifecycle.dispose(); studio?.workspace.dispose();
    preview.dispose(); transfer.cancel(); reconnect.stop(); client.close(); renderer.dispose(); grid.dispose();
  });
})();
