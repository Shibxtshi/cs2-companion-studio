/* Studio panels and translated controls, independent of persistence and transport. */
(() => {
  'use strict';


  const byId = id => document.getElementById(id);
  const text = key => {
    if (key === 'synthetic' && document.documentElement?.dataset.production === 'target') {
      return CS2I18N.t("studio.data.memoryOnly");
    }
    return CS2I18N.t(CS2I18N.has('studio.' + key) ? 'studio.' + key : 'studio.generic');
  };
  const message = key => CS2I18N.ref(CS2I18N.has('studio.' + key) ? 'studio.' + key : 'studio.generic');
  function choose(title, message, choices, {name = null, review = null} = {}) {
    const dialog = byId('studio-dialog');
    if (dialog.open) CCSDraftContract.fail('dialog_busy');
    for (const node of dialog.querySelectorAll('.studio-dialog-extra')) node.remove();
    if (name !== null) {
      const input = document.createElement('input'); input.id = 'studio-dialog-name'; input.className = 'studio-dialog-extra';
      input.value = name; input.maxLength = 32; input.required = true; CS2I18N.bind(input, 'studio.profileName', {}, 'aria-label');
      byId('studio-dialog-message').after(input);
    }
    if (review) {
      const pre = document.createElement('pre'); pre.className = 'studio-dialog-extra'; pre.tabIndex = 0; pre.textContent = review;
      byId('studio-dialog-message').after(pre);
    }
    CS2I18N.render(byId('studio-dialog-title'), title);
    CS2I18N.render(byId('studio-dialog-message'), message);
    const actions = byId('studio-dialog-actions'); actions.replaceChildren();
    const previousFocus = document.activeElement;
    return new Promise(resolve => {
      function close() {
        dialog.removeEventListener('close', close);
        if (previousFocus?.isConnected) previousFocus.focus();
        resolve(dialog.returnValue || 'cancel');
      }
      dialog.addEventListener('close', close);
      for (const [value, label] of choices) {
        const button = document.createElement('button'); button.type = 'submit'; button.value = value; button.formNoValidate = value === 'cancel';
        CS2I18N.render(button, label); button.setAttribute('translate', 'no'); actions.append(button);
      }
      dialog.returnValue = ''; dialog.showModal();
    });
  }
  window.CCSStudioWorkspace = ({edit, add, remove, duplicate, undo, redo, selectProfile, publish, leave, logout,
                               resolveConflict, profileAction, retry, discardDraft, recoverCopy, openPreview, gesture}) => {
    let content = null;
    let selectedId = null;
    let paintedSelection = null;
    let sessionState = null;
    let saveCode = 'published';
    let publicationCode = null;
    let inspectorMode = 'widget';
    const canvas = CCSStudioCanvas({board: byId('studio-board'),
      select(id) { selectedId = id; paintSelection(); }, gesture,
      report: issue,
      onGeometry(rectangle, code) {
        byId('studio-geometry-state').textContent = code === 'ready'
          ? `X ${rectangle.x} · Y ${rectangle.y} · ${rectangle.width} × ${rectangle.height}` : text(code);
      },
    });
    function issue(code) {
      byId('studio-alert').dataset.code = code;
      byId('studio-alert').textContent = text(code);
      byId('studio-alert').hidden = false;
    }
    function attempt(action) {
      try { const result = action(); result?.catch(error => issue(error.code || 'error')); }
      catch (error) { issue(error.code || 'error'); paintSelection(); }
    }
    function setValue(id, value) {
      const node = byId(id);
      if (document.activeElement === node && selectedId === paintedSelection) return;
      if (node.type === 'checkbox') node.checked = !!value;
      else node.value = value;
    }
    function selected() { return content?.configuration.layout.widgets.find(widget => widget.id === selectedId); }
    function paintSelection() {
      if (!content) return;
      const widget = selected();
      byId('studio-widget-fields').hidden = !widget;
      byId('studio-selection-label').textContent = widget ? CS2WidgetCatalog[widget.kind].title + ' / ' + widget.kind : text('select');
      if (widget) {
        for (const key of ['title', 'variant', 'x', 'y', 'width', 'height', 'color', 'background', 'opacity', 'style']) setValue('studio-' + key, widget[key]);
        byId('studio-opacity-value').textContent = widget.opacity + '%';
        const [width, height] = CCSWidgetPresentation.minimum(widget.kind, widget.variant);
        byId('studio-minimum').textContent = CS2I18N.t('studio.readingMinimum', {width, height});
        byId('studio-geometry-state').textContent = `X ${widget.x} · Y ${widget.y} · ${widget.width} × ${widget.height}`;
      }
      const config = content.configuration;
      for (const [id, value] of [['profile-name', content.name], ['theme', config.theme], ['density', config.appearance.density],
        ['navigation', config.navigation.mode], ['floating', config.navigation.floatingButton], ['connection', config.fullscreen.showConnectionStatus]]) setValue('studio-' + id, value);
      paintedSelection = selectedId;
      canvas.update(content, selectedId, sessionState?.publicationLocked || sessionState?.closed || false);
    }
    function changeWidget(key, value) {
      const widget = selected(); if (!widget) return;
      attempt(() => edit(CCSStudioModel.changeWidget(content, widget.id, {[key]: value},
        {geometry: ['x', 'y', 'width', 'height'].includes(key)})));
      byId('studio-' + key).value = selected()?.[key] ?? '';
    }
    function changeProfile(change) {
      if (!content) return;
      const next = structuredClone(content); change(next); attempt(() => edit(next));
    }
    function library() {
      const list = byId('studio-library-items'); list.replaceChildren();
      const query = byId('studio-search').value.trim().toLocaleLowerCase();
      const category = byId('studio-category').value;
      let previous = null;
      for (const [kind, definition] of Object.entries(CS2WidgetCatalog)) {
        const title = definition.title;
        const description = CS2I18N.t('widgets.description.' + kind);
        if ((category && category !== definition.cat) || !`${title} ${kind} ${description}`.toLocaleLowerCase().includes(query)) continue;
        if (previous !== definition.cat) {
          const label = document.createElement('h3'); label.className = 'studio-library-group';
          label.textContent = CS2I18N.t(definition.cat); list.append(label); previous = definition.cat;
        }
        const row = document.createElement('div'); row.className = 'studio-library-item'; row.dataset.kind = kind;
        const info = document.createElement('div'); const heading = document.createElement('h3'); const detail = document.createElement('p');
        heading.textContent = title; detail.textContent = description; info.append(heading, detail);
        const button = document.createElement('button'); button.type = 'button'; button.textContent = '+';
        button.setAttribute('aria-label', CS2I18N.t('studio.addWidget', {widget: title}));
        button.addEventListener('click', () => attempt(() => add(kind)));
        row.append(info, button); list.append(row);
      }
    }
    function locale() {
      for (const node of document.querySelectorAll('[data-copy]')) { node.setAttribute('translate', 'no'); CS2I18N.bind(node, 'studio.' + node.dataset.copy); }
      byId('studio-search').placeholder = text('search');
      byId('studio-category').setAttribute('aria-label', CS2I18N.t("studio.workspace.category"));
      document.querySelector('.studio-panel-tabs').setAttribute('aria-label', CS2I18N.t("studio.workspace.studioPanels"));
      document.querySelector('.studio-header nav').setAttribute('aria-label', CS2I18N.t("studio.workspace.workspace"));
      for (const [direction, key] of [["-1,0","studio.move.left"],["0,-1","studio.move.up"],["0,1","studio.move.down"],["1,0","studio.move.right"]]) {
        CS2I18N.bind(document.querySelector('[data-nudge="'+direction+'"]'), key, {}, 'aria-label');
      }
      byId('studio-logout').textContent = CS2I18N.t("experience.logout");
      byId('studio-undo').setAttribute('aria-label', CS2I18N.t("studio.workspace.undo"));
      byId('studio-redo').setAttribute('aria-label', CS2I18N.t("studio.workspace.redo"));
      const selectedCategory = byId('studio-category').value;
      byId('studio-category').replaceChildren(new Option(text('all'), ''), ...[...new Set(Object.values(CS2WidgetCatalog).map(widget => widget.cat))].map(cat => new Option(CS2I18N.t(cat), cat)));
      byId('studio-category').value = selectedCategory;
      for (const [id, keys] of [
        ['studio-density', ['studio.density.normal', 'studio.density.compact']],
        ['studio-navigation', ['navigation.full', 'navigation.compact', 'navigation.hidden']],
        ['studio-preview-mode', ['studio.mode.edit', 'studio.mode.dashboard']],
        ['studio-style', ['studio.surface.solid', 'studio.surface.glass', 'studio.surface.outline']],
        ['studio-variant', ['studio.variant.standard', 'studio.variant.compact', 'studio.variant.minimal']]]) {
        [...byId(id).options].forEach((option, index) => CS2I18N.bind(option, keys[index]));
      }
      library(); paintSelection(); status(saveCode, publicationCode);
      if (!byId('studio-alert').hidden) byId('studio-alert').textContent = text(byId('studio-alert').dataset.code);
    }
    function status(localCode, remoteCode = null) {
      saveCode = localCode; publicationCode = remoteCode;
      const code = remoteCode || localCode;
      byId('studio-save-state').textContent = text(code);
      byId('studio-save-state').parentElement.dataset.state = localCode;
      const locked = !content || !!sessionState?.publicationLocked || !!sessionState?.closed;
      byId('studio-publish').disabled = locked;
      for (const node of document.querySelectorAll('.studio-inspector input,.studio-inspector select,#studio-duplicate,#studio-remove,.studio-nudge button,#studio-library-items button')) node.disabled = locked;
      byId('studio-undo').disabled = !sessionState?.canUndo || !!sessionState?.publicationLocked;
      byId('studio-redo').disabled = !sessionState?.canRedo || !!sessionState?.publicationLocked;
    }
    for (const key of ['title', 'variant', 'x', 'y', 'width', 'height', 'color', 'background', 'opacity', 'style']) {
      byId('studio-' + key).addEventListener('change', event => changeWidget(key,
        ['x','y','width','height','opacity'].includes(key) ? Number(event.target.value) : event.target.value));
    }
    byId('studio-profile-name').addEventListener('change', event => changeProfile(next => { next.name = event.target.value.trim(); }));
    byId('studio-theme').addEventListener('change', event => changeProfile(next => { next.configuration.theme = event.target.value; }));
    byId('studio-density').addEventListener('change', event => changeProfile(next => { next.configuration.appearance.density = event.target.value; }));
    byId('studio-navigation').addEventListener('change', event => changeProfile(next => { next.configuration.navigation.mode = event.target.value; }));
    byId('studio-floating').addEventListener('change', event => changeProfile(next => { next.configuration.navigation.floatingButton = event.target.checked; }));
    byId('studio-connection').addEventListener('change', event => changeProfile(next => { next.configuration.fullscreen.showConnectionStatus = event.target.checked; }));
    for (const button of document.querySelectorAll('[data-nudge]')) button.addEventListener('click', () => {
      const widget = selected(); if (!widget) return;
      const [x,y] = button.dataset.nudge.split(',').map(Number);
      attempt(() => edit(CCSStudioModel.changeWidget(content, widget.id, {x: widget.x + x, y: widget.y + y}, {geometry: true})));
    });
    byId('studio-remove').addEventListener('click', () => attempt(() => remove(selectedId)));
    byId('studio-duplicate').addEventListener('click', () => attempt(() => duplicate(selectedId)));
    byId('studio-undo').addEventListener('click', () => attempt(undo)); byId('studio-redo').addEventListener('click', () => attempt(redo));
    byId('studio-profile').addEventListener('change', event => attempt(() => selectProfile(event.target.value)));
    for (const [id, action] of [['studio-create','create'], ['studio-copy-profile','copy'], ['studio-delete-profile','delete'], ['studio-local-drafts','drafts']]) {
      byId(id).addEventListener('click', () => { document.querySelector('.studio-profile-actions').open = false; attempt(() => profileAction(action)); });
    }
    byId('studio-retry').addEventListener('click', () => attempt(retry));
    byId('studio-discard-draft').addEventListener('click', () => attempt(discardDraft));
    byId('studio-recover-copy').addEventListener('click', () => attempt(recoverCopy));
    byId('studio-open-preview').addEventListener('click', () => attempt(openPreview));
    byId('studio-help').addEventListener('click', () => attempt(() => choose(message('help'), CS2I18N.ref("studio.help.workflow"),
      [['cancel', message('close')]])));
    byId('studio-publish').addEventListener('click', () => attempt(publish));
    byId('studio-leave').addEventListener('click', () => attempt(leave)); byId('studio-logout').addEventListener('click', () => attempt(logout));
    for (const action of ['keep','server','local']) byId('studio-conflict-' + action).addEventListener('click', () => attempt(() => resolveConflict(action)));
    byId('studio-search').addEventListener('input', library); byId('studio-category').addEventListener('change', library);
    byId('studio-preview-mode').addEventListener('change', event => canvas.setPreview(event.target.value === 'dashboard'));
    for (const button of document.querySelectorAll('.studio-panel-tabs button[data-panel]')) button.addEventListener('click', () => {
      document.querySelector('.studio-workspace').dataset.panel = button.dataset.panel;
      for (const item of document.querySelectorAll('.studio-panel-tabs button')) item.setAttribute('aria-pressed', String(item === button));
      canvas.refresh();
    });
    function activateAppearance() {
      if (!content) return;
      CCSThemes.apply(content.configuration.theme);
      document.documentElement.style.setProperty('--profile-accent', content.configuration.appearance.accent || 'var(--ccs-accent)');
    }
    function inspector(mode) {
      inspectorMode = mode;
      byId('studio-widget-properties').hidden = mode !== 'widget'; byId('studio-profile-properties').hidden = mode !== 'profile';
      byId('studio-widget-tab').setAttribute('aria-pressed', String(mode === 'widget'));
      byId('studio-profile-tab').setAttribute('aria-pressed', String(mode === 'profile'));
    }
    byId('studio-widget-tab').addEventListener('click', () => inspector('widget'));
    byId('studio-profile-tab').addEventListener('click', () => inspector('profile'));
    const closeMenu = event => {
      const menu = document.querySelector('.studio-profile-actions');
      if (menu.open && !event.target.closest('.studio-profile-actions')) menu.open = false;
    };
    document.addEventListener('pointerdown', closeMenu);
    const keyboard = event => {
      const menu = document.querySelector('.studio-profile-actions');
      if (event.key === 'Escape' && menu.open) { menu.open = false; menu.querySelector('summary').focus(); return; }
      if (event.target.closest('input,textarea,select,[contenteditable="true"]') || byId('studio-dialog').open) return;
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'z') { event.preventDefault(); attempt(event.shiftKey ? redo : undo); }
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'y') { event.preventDefault(); attempt(redo); }
    };
    document.addEventListener('keydown', keyboard);
    document.addEventListener('cs2:locale-changed', locale);
    locale();
    return Object.freeze({canvas, issue, status, choose, text, message, activateAppearance,
      reset() {
        content = null; selectedId = null; paintedSelection = null; sessionState = null;
        canvas.reset(); byId('studio-profile').replaceChildren();
        for (const id of ['studio-title','studio-profile-name','studio-selection-label','studio-remote-review']) {
          const node = byId(id); if (node.matches('input')) node.value = ''; else node.textContent = '';
        }
        byId('studio-widget-fields').hidden = true; byId('studio-conflict').hidden = true; byId('studio-alert').hidden = true;
      },
      clearIssue(code = null) { if (code === null || byId('studio-alert').dataset.code === code) byId('studio-alert').hidden = true; },
      get selectedId() { return selectedId; },
      select(id) { selectedId = id; inspector('widget'); paintSelection(); },
      paint(next, currentState) {
        content = CCSDraftContract.content({name: next.name, configuration: next.configuration}); sessionState = currentState;
        if (!content.configuration.layout.widgets.some(widget => widget.id === selectedId)) selectedId = null;
        // A hidden editor must not override the published Dashboard's appearance.
        if (!byId('studio-app')?.hidden) activateAppearance();
        CS2I18N.bind(byId('studio-grid-caption'), 'studio.columns', {count: content.configuration.layout.columns});
        byId('studio-empty').hidden = content.configuration.layout.widgets.length > 0;
        paintSelection(); status(saveCode, publicationCode);
      },
      recovery({retry = false, discard = false, copy = false, cleanup = false} = {}) {
        byId('studio-retry').hidden = !retry; byId('studio-discard-draft').hidden = !discard; byId('studio-recover-copy').hidden = !copy;
        byId('studio-retry').textContent = cleanup ? CS2I18N.t("studio.workspace.finishLocalCleanup") : text('retry');
      },
      async name(title, initial = '') {
        const result = await choose(title, CS2I18N.ref("studio.dialog.newProfileWarning"),
          [['confirm', CS2I18N.ref("experience.next")], ['cancel', message('cancel')]], {name: initial});
        return result === 'confirm' ? byId('studio-dialog-name').value.trim() : null;
      },
      catalog(catalog, profileId, drafts = []) {
        const menu = byId('studio-profile');
        menu.replaceChildren(...catalog.profiles.map(profile => new Option(profile.name, profile.id)),
          ...drafts.filter(record => !catalog.profiles.some(profile => profile.id === record.profileId)).map(record =>
            new Option((record.draft?.name || record.profileId) + (CS2I18N.t("studio.workspace.localDraft")), record.profileId)));
        menu.value = profileId;
      },
      review(local, published) { byId('studio-remote-review').textContent = JSON.stringify({local, published}, null, 2); },
      conflict(value, message = '') { byId('studio-conflict').hidden = !value; CS2I18N.render(byId('studio-conflict-description'), message); },
      dispose() { canvas.dispose(); document.removeEventListener('pointerdown', closeMenu); document.removeEventListener('keydown', keyboard); document.removeEventListener('cs2:locale-changed', locale); },
    });
  };
})();
