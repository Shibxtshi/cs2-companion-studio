/* Widget DOM and live values only; editing and persistence belong to the host controllers. */
(() => {
  'use strict';

  window.CS2WidgetRenderer = ({board, format, presentation = null, onGeometryChange = () => {}, headingLevel = 2}) => {
    const {isNum, percent, weaponName, fields} = format;
    const WRAPPING_FIELDS = new Set(['name','weapon','map','map_mode','provider','activity','round',
      'round_phase','round_winner','map_phase','bomb_state','connection','econ_note']);
    const bindings = new WeakMap();
    const listCache = new WeakMap();
    const bombLayoutKeys = new WeakMap();
    let accessibilityFrame = null;

    function createCard(widget, definition) {
      const article = document.createElement('article');
      article.className = 'widget w-' + widget.kind;
      article.dataset.id = widget.id;
      article.dataset.kind = widget.kind;
      article.style.setProperty('--span', widget.span);
      if (widget.color) article.style.setProperty('--widget-accent', widget.color);
      if (widget.background) article.style.setProperty('--widget-bg', widget.background);
      article.style.setProperty('--widget-opacity', (widget.opacity ?? 100) + '%');
      article.dataset.style = widget.style || 'solid';

      const top = document.createElement('div');
      top.className = 'widget-top';
      const title = document.createElement('div');
      title.className = 'widget-heading';
      title.id = 'widget-heading-' + widget.id;
      title.setAttribute('role','heading');
      title.setAttribute('aria-level',String(headingLevel));
      article.setAttribute('aria-labelledby',title.id);
      title.textContent = widget.title || definition.title;
      if (widget.title) title.setAttribute('translate', 'no');
      const icon = document.createElement('span');
      icon.className = 'widget-icon';
      icon.textContent = definition.icon;
      top.append(title, icon);
      article.append(top);

      const body = document.createElement('div');
      body.className = 'widget-body';
      // HTML comes only from the shipped catalog, never from profiles or GSI.
      body.innerHTML = definition.html;
      article.append(body);
      presentation?.decorate(article, widget);
      return article;
    }

    function addItem(parent, label, active = false) {
      const item = document.createElement('div');
      item.className = 'item' + (active ? ' active' : '');
      item.textContent = label;
      parent.append(item);
    }

    function renderInventory(list, player) {
      const items = format.inventory(player, list.dataset.list);
      if (!items.length) addItem(list, 'Aucune donnée');
      for (const weapon of items) {
        const ammo = isNum(weapon.ammo_clip) && weapon.type !== 'Grenade' ? ' · ' + weapon.ammo_clip : '';
        addItem(list, weaponName(weapon.name) + ammo, weapon.state === 'active');
      }
    }

    function renderWins(list, state) {
      const items = state.recent_wins || [];
      if (!items.length) addItem(list, 'Historique indisponible');
      for (const win of items) addItem(list, presentation?.roundLabel ? presentation.roundLabel(win) : '#' + win.round + ' · ' + win.winner);
    }

    function renderEvents(list, state) {
      const items = state.events || [];
      if (!items.length) addItem(list, 'Aucun événement enregistré');
      for (const event of items.slice(0, 8)) {
        const item = document.createElement('div');
        item.className = 'item';
        const text = document.createElement('span');
        text.textContent = event.message;
        const when = document.createElement('span');
        when.className = 'tiny';
        when.textContent = isNum(event.at)
          ? new Date(event.at * 1000).toLocaleTimeString(
            window.CS2I18N?.locale() === 'FR' ? 'fr-FR' : 'en-US',
            {hour: '2-digit', minute: '2-digit', second: '2-digit'})
          : '';
        item.append(text, when);
        list.append(item);
      }
    }

    function updateBars(nodes, player) {
      nodes.forEach(node => {
        let amount = 0;
        if (node.dataset.p === 'ammo' && isNum(player.ammo_max)
            && player.ammo_max > 0 && isNum(player.ammo_clip)) {
          amount = player.ammo_clip / player.ammo_max * 100;
        }
        if (node.dataset.p === 'health') amount = player.health;
        if (node.dataset.p === 'armor') amount = player.armor;
        node.style.width = percent(amount);
      });
    }

    function paintBomb(state, anchor) {
      if (!state) return;
      let left = null;
      let kind = '';
      let message = 'En attente';
      const timer = state.bomb_timer || {};
      if (timer.status === 'active' && anchor) {
        left = Math.max(0, anchor.left - (performance.now() - anchor.at) / 1000);
        if (left > 10) {
          kind = 'yellow';
          message = 'Désamorçage possible sans kit';
        } else if (left > 5) {
          kind = 'orange';
          message = 'Kit nécessaire pour commencer';
        } else {
          kind = 'red';
          message = 'Trop tard pour commencer';
        }
        if (left === 0) message = 'Explosion estimée';
      } else if (timer.status === 'expired') {
        left = 0;
        kind = 'red';
        message = 'Explosion estimée';
      } else if (timer.status === 'disabled') {
        message = 'Minuteur désactivé';
      } else if (timer.status === 'stale') {
        message = 'Données interrompues';
      } else if (timer.status === 'unknown_start') {
        message = 'Heure de pose inconnue';
      } else if (state.bomb_state === 'defused') {
        message = 'Bombe désamorcée';
      } else if (state.bomb_state === 'exploded') {
        message = 'Bombe explosée';
      } else {
        message = 'En attente d’une pose';
      }

      let geometryChanged = false;
      for (const card of board.querySelectorAll('.widget.w-bomb')) {
        const clock = card.querySelector('[data-bomb-clock]');
        const bar = card.querySelector('[data-bomb-fill]');
        const label = card.querySelector('[data-bomb-msg]');
        if (!clock || !bar || !label) continue;
        clock.textContent = left === null ? '--.- s' : left.toFixed(1) + ' s';
        if (clock.className !== 'bomb-clock ' + kind) clock.className = 'bomb-clock ' + kind;
        bar.style.width = left === null ? '0%' : percent(100 * left / (timer.duration || 40));
        if (bar.className !== 'bomb-fill ' + kind) bar.className = 'bomb-fill ' + kind;
        const translated = window.CS2I18N?.translate(message) || message;
        if (label.textContent !== message && label.textContent !== translated) label.textContent = message;
        const layoutKey = message + ':' + clock.textContent.length;
        if (bombLayoutKeys.get(card) !== layoutKey) { bombLayoutKeys.set(card,layoutKey); geometryChanged = true; }
      }
      if (geometryChanged) { scheduleAccessibility(); onGeometryChange(); }
    }

    function updateValues(state, {modeDemo, anchor}) {
      if (!state) return;
      const values = fields(state, {modeDemo});
      const player = state.player || {};
      let geometryChanged = false;
      const signatures = {};
      const listSignature = type => signatures[type] ??= JSON.stringify([
        window.CS2I18N?.locale(), type === 'wins' ? state.recent_wins
          : type === 'events' ? state.events : player.weapons]);
      for (const card of board.children) {
        let binding = bindings.get(card);
        if (!binding) {
          binding = {values: [...card.querySelectorAll('[data-v]')], bars: [...card.querySelectorAll('[data-p]')],
            list: card.querySelector('[data-list]'), controls: card.querySelector('[data-demo-controls]'), shape: ''};
          bindings.set(card,binding);
        }
        const shape = [];
        binding.values.forEach(node => {
          const next = values[node.dataset.v] ?? '—';
          const expected = node.closest('[translate="no"]') ? next : window.CS2I18N?.translate(next) || next;
          shape.push(WRAPPING_FIELDS.has(node.dataset.v) ? next : next.length);
          if (node.textContent !== next && node.textContent !== expected) node.textContent = next;
        });
        const nextShape = JSON.stringify(shape);
        if (binding.shape !== nextShape) { binding.shape = nextShape; geometryChanged = true; }
        updateBars(binding.bars, player);
        const list = binding.list;
        if (list && listCache.get(list) !== listSignature(list.dataset.list)) {
          listCache.set(list,listSignature(list.dataset.list));
          geometryChanged = true;
          list.replaceChildren();
          if (list.dataset.list === 'weapons' || list.dataset.list === 'grenades') {
            renderInventory(list, player);
          } else if (list.dataset.list === 'wins') {
            renderWins(list, state);
          } else if (list.dataset.list === 'events') {
            renderEvents(list, state);
          }
        }
        const previousState = card.dataset.dataState;
        presentation?.update(card, state, {modeDemo});
        if (previousState !== card.dataset.dataState) geometryChanged = true;
        if (card.dataset.kind === 'bomb') {
          const controls = binding.controls;
          if (controls) controls.classList.toggle('hidden', !modeDemo);
        }
      }
      paintBomb(state, anchor);
      if (geometryChanged) { scheduleAccessibility(); onGeometryChange(); }
    }

    function refreshAccessibility() {
      accessibilityFrame = null;
      for (const list of board.querySelectorAll('[data-list]')) {
        const overflow = list.scrollHeight > list.clientHeight + 1 || list.scrollWidth > list.clientWidth + 1;
        if (overflow) {
          list.tabIndex = 0;
          list.setAttribute('role','region');
          const title = list.closest('.widget')?.querySelector('.widget-heading')?.textContent || '';
          if (list.getAttribute('aria-label') !== title) list.setAttribute('aria-label',title);
        } else {
          list.removeAttribute('tabindex'); list.removeAttribute('role'); list.removeAttribute('aria-label');
        }
      }
    }
    function scheduleAccessibility() {
      if (accessibilityFrame === null) accessibilityFrame = requestAnimationFrame(refreshAccessibility);
    }
    const observer = new ResizeObserver(scheduleAccessibility);
    observer.observe(board);
    const onToggle = () => { scheduleAccessibility(); onGeometryChange(); };
    board.addEventListener('toggle', onToggle, true);
    return {createCard, updateValues, paintBomb, refreshAccessibility,
      dispose() {
        observer.disconnect();
        board.removeEventListener('toggle',onToggle,true);
        if (accessibilityFrame !== null) cancelAnimationFrame(accessibilityFrame);
      },
      setVariant(card, variant) { presentation?.setVariant(card, variant); scheduleAccessibility(); onGeometryChange(); }};
  };
})();
