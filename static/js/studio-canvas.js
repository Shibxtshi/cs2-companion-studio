/* Keyed canvas reconciliation and one history operation per pointer gesture. */
(() => {
  'use strict';
  window.CCSStudioCanvas = ({board, select, gesture, onGeometry, report}) => {
    const renderer = CS2WidgetRenderer({board, format: CS2DisplayFormat,
      presentation: CCSWidgetPresentation, onGeometryChange: () => grid.requestRefresh(), headingLevel: 3});
    const grid = CCSDashboardGrid({board});
    const data = CCSStudioData({renderer, board});
    let content = null;
    let selectedId = null;
    let active = null;
    let preview = false;
    let disabled = false;
    let frame = null;
    let layoutSignature = null;
    const ghost = document.createElement('div');
    ghost.className = 'studio-placement-ghost';
    ghost.setAttribute('aria-hidden', 'true');
    function tools(card) {
      const controls = document.createElement('div');
      controls.className = 'studio-edit-tools';
      for (const [kind, symbol, label] of [['move', '✥', 'Move widget'], ['resize', '⤢', 'Resize widget']]) {
        const button = document.createElement('button');
        button.type = 'button'; button.dataset.studioGesture = kind;
        button.textContent = symbol; button.setAttribute('aria-label', label);
        controls.append(button);
      }
      card.append(controls);
    }
    function update(next, selection, locked = false) {
      content = structuredClone(next); selectedId = selection; disabled = locked;
      const widgets = next.configuration.layout.widgets;
      const current = new Map([...board.querySelectorAll(':scope > .widget')].map(card => [card.dataset.id, card]));
      for (const [id, card] of current) if (!widgets.some(widget => widget.id === id)) card.remove();
      let replacementFocus = null;
      for (const widget of widgets) {
        let card = current.get(widget.id);
        const previous = card;
        const focused = card?.contains(document.activeElement) ? document.activeElement : null;
        if (card && card.dataset.kind !== widget.kind) {
          card = null;
        }
        if (!card) {
          card = renderer.createCard(widget, CS2WidgetCatalog[widget.kind]);
          card.tabIndex = 0;
          tools(card);
          if (previous) previous.replaceWith(card); else board.append(card);
          if (focused) replacementFocus = focused.dataset.studioGesture
            ? card.querySelector(`[data-studio-gesture="${focused.dataset.studioGesture}"]`) : card;
        }
        if (card.dataset.variant !== widget.variant) renderer.setVariant(card, widget.variant);
        const title = card.querySelector('.widget-heading');
        const value = widget.title || CS2WidgetCatalog[widget.kind].title;
        if (title.textContent !== value && title.textContent !== CS2I18N.translate(value)) title.textContent = value;
        if (widget.title) title.setAttribute('translate', 'no'); else title.removeAttribute('translate');
        for (const [key, value] of [['--widget-accent', widget.color], ['--widget-bg', widget.background]]) {
          if (value) card.style.setProperty(key, value); else card.style.removeProperty(key);
        }
        card.style.setProperty('--widget-opacity', widget.opacity + '%');
        card.dataset.style = widget.style;
        card.dataset.selected = String(widget.id === selection);
        for (const button of card.querySelectorAll('.studio-edit-tools button')) {
          button.disabled = locked;
          const moving = button.dataset.studioGesture === 'move';
          button.setAttribute('aria-label', CS2I18N.locale() === 'FR'
            ? moving ? 'Déplacer le widget' : 'Redimensionner le widget'
            : moving ? 'Move widget' : 'Resize widget');
        }
      }
      board.dataset.preview = preview ? 'dashboard' : 'edit';
      board.dataset.studioDensity = next.configuration.appearance.density;
      if (next.configuration.appearance.background) board.style.background = next.configuration.appearance.background;
      else board.style.removeProperty('background');
      const signature = CCSDraftContract.canonical(next.configuration.layout);
      if (layoutSignature !== signature) { layoutSignature = signature; grid.setLayout(next.configuration.layout); }
      data.refresh();
      replacementFocus?.focus({preventScroll: true});
    }
    function selectCard(event) {
      const card = event.target.closest('.widget');
      if (card && !preview) select(card.dataset.id);
    }
    function paintGhost() {
      frame = null;
      if (!active) return;
      const cell = (board.clientWidth + 8) / content.configuration.layout.columns;
      const rectangle = active.rectangle;
      Object.assign(ghost.style, {left: rectangle.x * cell + 'px', top: rectangle.y * 40 + 'px',
        width: rectangle.width * cell - 8 + 'px', height: rectangle.height * 40 - 8 + 'px'});
      ghost.dataset.valid = String(active.result.valid);
      onGeometry(rectangle, active.result.code);
    }
    function begin(event) {
      const handle = event.target.closest('[data-studio-gesture]');
      if (!handle || preview || disabled || event.button !== 0) return;
      const layout = content.configuration.layout;
      if (board.clientWidth < layout.columns * 32 + (layout.columns - 1) * 8) {
        report('precise_controls'); return;
      }
      const id = handle.closest('.widget').dataset.id;
      const initial = layout.widgets.find(widget => widget.id === id);
      select(id);
      gesture.begin();
      active = {id, initial: {...initial}, rectangle: {...initial}, result: {valid: true, code: 'ready'},
        x: event.clientX, y: event.clientY, kind: handle.dataset.studioGesture, handle, pointerId: event.pointerId};
      handle.setPointerCapture(event.pointerId);
      board.append(ghost); paintGhost(); event.preventDefault();
    }
    function move(event) {
      if (!active || event.pointerId !== active.pointerId) return;
      const cell = (board.clientWidth + 8) / content.configuration.layout.columns;
      const dx = Math.round((event.clientX - active.x) / cell);
      const dy = Math.round((event.clientY - active.y) / 40);
      active.rectangle = {...active.initial, ...(active.kind === 'move'
        ? {x: active.initial.x + dx, y: active.initial.y + dy}
        : {width: active.initial.width + dx, height: active.initial.height + dy})};
      active.result = CCSStudioModel.placement(content.configuration.layout, active.id, active.rectangle);
      if (frame === null) frame = requestAnimationFrame(paintGhost);
    }
    function finish(cancel = false) {
      if (!active) return;
      const finished = active;
      active = null; ghost.remove();
      if (frame !== null) cancelAnimationFrame(frame);
      frame = null;
      if (finished.handle.hasPointerCapture(finished.pointerId)) finished.handle.releasePointerCapture(finished.pointerId);
      if (cancel || !finished.result.valid) {
        gesture.cancel(); report(cancel ? 'gesture_cancelled' : finished.result.code);
      } else {
        gesture.commit(CCSStudioModel.changeWidget(content, finished.id, finished.rectangle, {geometry: true}));
      }
    }
    function keydown(event) {
      if (event.key === 'Escape' && active) { finish(true); event.preventDefault(); return; }
      const handle = event.target.closest('[data-studio-gesture]');
      if (!handle || !['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(event.key) || disabled) return;
      event.preventDefault();
      const widget = content.configuration.layout.widgets.find(item => item.id === handle.closest('.widget').dataset.id);
      const delta = {ArrowLeft: [-1,0], ArrowRight: [1,0], ArrowUp: [0,-1], ArrowDown: [0,1]}[event.key];
      const changes = handle.dataset.studioGesture === 'move'
        ? {x: widget.x + delta[0], y: widget.y + delta[1]}
        : {width: widget.width + delta[0], height: widget.height + delta[1]};
      try { gesture.edit(CCSStudioModel.changeWidget(content, widget.id, changes, {geometry: true})); }
      catch (error) { report(error.code); }
    }
    const cancel = () => finish(true);
    const end = () => finish(false);
    board.addEventListener('click', selectCard);
    board.addEventListener('focusin', selectCard);
    board.addEventListener('pointerdown', begin);
    board.addEventListener('pointermove', move);
    board.addEventListener('pointerup', end);
    board.addEventListener('pointercancel', cancel);
    board.addEventListener('lostpointercapture', cancel);
    document.addEventListener('keydown', keydown);
    return Object.freeze({update,
      reset() {
        cancel(); content = null; selectedId = null; layoutSignature = null;
        board.replaceChildren(); grid.setLayout({columns: 24, widgets: []});
        data.update({online: false, gsi_connected: false, player: {}, bomb_timer: {status: 'stale'}}, false);
      },
      values: data.update,
      previewData: data.snapshot,
      setPreview(value) { preview = value; if (content) { update(content, selectedId, disabled); grid.requestRefresh(); } },
      refresh: () => grid.refresh(), cancel,
      dispose() {
        finish(true); data.dispose(); grid.dispose(); renderer.dispose();
        board.removeEventListener('click', selectCard); board.removeEventListener('focusin', selectCard);
        board.removeEventListener('pointerdown', begin); board.removeEventListener('pointermove', move);
        board.removeEventListener('pointerup', end); board.removeEventListener('pointercancel', cancel);
        board.removeEventListener('lostpointercapture', cancel); document.removeEventListener('keydown', keydown);
      },
    });
  };
})();
