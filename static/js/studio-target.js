/* Authenticated Studio transport. Target composition remains isolated from production. */
(() => {
  'use strict';
  const byId = id => document.getElementById(id);
  let pin = '';
  let disposed = false;
  let lifecycle = null;
  let preview = null;
  let latestData = null;
  function issue(error) { workspace.issue(typeof error === 'string' ? error : error.code || 'error'); }
  const profiles = CCSPublishedProfiles({send: command => client.send(command),
    onChange({catalog}) {
      if (!catalog) return;
      byId('studio-login').hidden = true; byId('studio-app').hidden = false;
      lifecycle.catalogChanged().catch(issue);
    },
    onStatus(code) { if (code === 'store_changed') issue(code); },
  });
  const workspace = CCSStudioWorkspace({
    edit: next => lifecycle.edit(next),
    add(kind) { const result = CCSStudioModel.add(lifecycle.preview, kind); lifecycle.edit(result.content); workspace.select(result.id); },
    duplicate(id) {
      const widget = lifecycle.preview.configuration.layout.widgets.find(item => item.id === id);
      const result = CCSStudioModel.add(lifecycle.preview, widget.kind, widget); lifecycle.edit(result.content); workspace.select(result.id);
    },
    async remove(id) {
      if (!id) return;
      const answer = await workspace.choose(CS2I18N.locale() === 'FR' ? 'Supprimer ce widget ?' : 'Remove this widget?',
        CS2I18N.locale() === 'FR' ? 'Cette modification reste locale et peut être annulée.' : 'This change stays local and can be undone.',
        [['remove', CS2I18N.locale() === 'FR' ? 'Supprimer' : 'Remove'], ['cancel', workspace.text('cancel')]]);
      if (answer === 'remove') lifecycle.edit(CCSStudioModel.remove(lifecycle.preview, id));
    },
    undo: () => lifecycle.undo(), redo: () => lifecycle.redo(),
    selectProfile: id => lifecycle.selectProfile(id), publish: () => lifecycle.publish(),
    leave: () => lifecycle.leave('keep'), logout: () => lifecycle.logout(),
    resolveConflict: action => lifecycle.resolveConflict(action),
    profileAction: action => lifecycle.profileAction(action), retry: () => lifecycle.retry(),
    discardDraft: () => lifecycle.discardDraft(), recoverCopy: () => lifecycle.recoverCopy(),
    openPreview: () => preview.open(lifecycle.preview, workspace.canvas.previewData()),
    gesture: {begin: () => lifecycle.gesture.begin(), cancel: () => lifecycle.gesture.cancel(),
      commit: next => lifecycle.gesture.commit(next), edit: next => lifecycle.edit(next)},
  });
  function disconnected() {
    reconnect.stop(); client.close(); profiles.clear(); pin = ''; latestData = null;
    byId('studio-board').replaceChildren(); byId('studio-app').hidden = true; byId('studio-login').hidden = false;
  }
  lifecycle = CCSStudioLifecycle({profiles, send: command => client.send(command), workspace,
    exit: () => {
      // Only remember a published selection after the existing leave guard succeeds.
      if (profiles.profile(profiles.selectedProfileId)) CCSProfileSelection.remember(profiles.context, profiles.selectedProfileId);
      location.href = '/__dashboard_test__';
    }, disconnected});
  preview = CCSStudioPreview();
  function values(state, demo) {
    latestData = {state: structuredClone(state), demo};
    workspace.canvas.values(state, demo);
    const label = document.querySelector('.studio-canvas-note span');
    label.removeAttribute('data-copy');
    label.setAttribute('translate','no');
    label.textContent = demo ? CS2I18N.locale() === 'FR' ? 'Données synthétiques · pas de GSI réel' : 'Synthetic data · not live GSI'
      : CS2I18N.locale() === 'FR' ? 'GSI en mémoire · jamais enregistré dans le brouillon' : 'GSI in memory · never stored in the draft';
  }
  function clearLive() {
    if (latestData?.demo) return;
    values({online: false, gsi_connected: false, player: {}, bomb_timer: {status: 'stale'}}, false);
  }
  const client = CS2DashboardClient({version: '1.0.0', getPin: () => pin, isDemo: () => false,
    onConnecting() {}, onHealthError: () => issue('network_error'),
    onNetworkError() { clearLive(); issue('network_error'); },
    onClose({authorized}) {
      profiles.disconnected(); lifecycle.networkLost(); clearLive();
      if (authorized && !disposed) reconnect.failed();
    },
    onMessage(message) {
      try {
        profiles.receive(message);
        if (message.type === 'auth_ok') { workspace.clearIssue('network_error'); reconnect.connected(); byId('pin').value = ''; }
        if (message.type === 'auth_error') { reconnect.stop(); byId('studio-login-error').textContent = CS2I18N.locale() === 'FR' ? 'PIN incorrect.' : 'Incorrect PIN.'; }
        lifecycle.receive(message).catch(issue);
        if (message.type === 'state' && !latestData?.demo) values(message, false);
      } catch (error) { issue(error); }
    },
  });
  const reconnect = CS2Reconnect({connect: isCurrent => client.connect(isCurrent)});
  function login() { pin = byId('pin').value.trim(); if (pin.length < 6) return; reconnect.stop(); client.close(); reconnect.start(); }
  byId('connect').addEventListener('click', login);
  byId('pin').addEventListener('keydown', event => { if (event.key === 'Enter') login(); });
  for (const link of document.querySelectorAll('a[href="/__dashboard_test__"]')) link.addEventListener('click', event => {
    event.preventDefault();
    if (profiles.ready) lifecycle.leave().catch(issue);
  });
  window.addEventListener('beforeunload', event => { if (lifecycle.dirty) { event.preventDefault(); event.returnValue = ''; } });
  const checkContext = () => lifecycle.checkContext().catch(issue);
  window.addEventListener('focus', checkContext);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) checkContext(); });
  document.addEventListener('cs2:locale-changed', () => { if (latestData) values(latestData.state, latestData.demo); });
  window.addEventListener('pagehide', event => {
    if (event.persisted) return;
    disposed = true; preview.dispose(); workspace.dispose(); lifecycle.dispose(); reconnect.stop(); client.close();
  });
  // The inspection surface contains configuration/status only, never PIN or live packets.
  window.CCSStudioTarget = Object.freeze({snapshot: () => ({...lifecycle.snapshot(), connected: profiles.ready}), previewData: values});
})();
