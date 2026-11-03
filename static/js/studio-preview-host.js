/* Read-only Studio preview using the shared shell; no WebSocket or persistence. */
(() => {
  'use strict';
  const owner = window.opener;
  const byId = id => document.getElementById(id);
  const board = byId('board');
  const densityStyle = document.createElement('link'); densityStyle.rel = 'stylesheet'; densityStyle.href = '/static/css/studio-density.css'; document.head.append(densityStyle);
  const grid = CCSDashboardGrid({board});
  const renderer = CS2WidgetRenderer({board, format: CS2DisplayFormat,
    presentation: CCSWidgetPresentation, onGeometryChange: () => grid.requestRefresh()});
  const data = CCSStudioData({renderer, board});
  byId('login').classList.add('hidden');
  byId('view').classList.remove('hidden');
  for (const node of document.querySelectorAll('#logout,#open-help')) node.hidden = true;
  const label = document.createElement('p');
  label.className = 'tiny'; label.setAttribute('role', 'status');
  board.before(label);
  function receive(event) {
    if (event.origin !== location.origin || event.source !== owner || event.data?.type !== 'studio_preview') return;
    try {
      const content = CCSDraftContract.content(event.data.content);
      CS2I18N.setLocale(event.data.locale);
      CS2I18N.bind(close, "studio.closePreview");
      CS2I18N.bind(label, "studio.preview.notPublished");
      board.replaceChildren(...content.configuration.layout.widgets.map(widget => renderer.createCard(widget, CS2WidgetCatalog[widget.kind])));
      board.dataset.studioDensity = content.configuration.appearance.density;
      document.documentElement.style.setProperty('--profile-accent', content.configuration.appearance.accent || 'var(--ccs-accent)');
      board.style.background = content.configuration.appearance.background;
      CCSDashboardShell.setTargetProfile({id: 'preview', revision: 1, ...content});
      grid.setLayout(content.configuration.layout);
      const demo = event.data.demo === true;
      const state = event.data.state || {online: false, gsi_connected: false, player: {}};
      data.update(state, demo);
      CS2I18N.bind(byId('status'), demo ? 'app.data.synthetic' : 'studio.preview.memoryData');
      document.dispatchEvent(new Event('cs2:status'));
      // Settings are edited in the parent inspector, never in this read-only frame.
      const settings = document.querySelector('[data-section="settings"]');
      if (settings) { settings.disabled = true; CS2I18N.bind(settings, 'studio.preview.editInParent', {}, 'title'); }
    } catch { CS2I18N.bind(label, "studio.preview.invalid"); }
  }
  const refreshLocale = () => { data.refresh(); grid.requestRefresh(); };
  document.addEventListener('cs2:locale-changed', refreshLocale);
  window.addEventListener('message', receive);
  if (owner) owner.postMessage({type: 'studio_preview_ready'}, location.origin);
  const close = document.createElement('button'); close.id = 'studio-preview-exit'; close.className = 'btn';
  close.style.cssText = 'position:fixed;right:16px;top:16px;z-index:1000';
  CS2I18N.bind(close, 'studio.closePreview'); close.addEventListener('click', () => window.close());
  label.before(close);
  window.addEventListener('pagehide', () => { data.dispose(); grid.dispose(); renderer.dispose(); window.removeEventListener('message', receive); document.removeEventListener('cs2:locale-changed', refreshLocale); });
})();
