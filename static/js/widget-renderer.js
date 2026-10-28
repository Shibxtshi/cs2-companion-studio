/* Widget DOM and live values only. Editing and profile persistence stay in studio.js. */
(() => {
  'use strict';

  window.CS2WidgetRenderer = ({board, format}) => {
    const {isNum, percent, weaponName, fields} = format;

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
      return article;
    }

    function addItem(parent, label, active = false) {
      const item = document.createElement('div');
      item.className = 'item' + (active ? ' active' : '');
      item.textContent = label;
      parent.append(item);
    }

    function renderInventory(list, player) {
      const items = (player.weapons || []).filter(weapon =>
        list.dataset.list === 'weapons' || weapon.type === 'Grenade'
        || /grenade|flashbang|molotov|incgrenade|decoy|smokegrenade/.test(weapon.name));
      if (!items.length) addItem(list, 'Aucune donnée');
      for (const weapon of items) {
        const ammo = isNum(weapon.ammo_clip) && weapon.type !== 'Grenade' ? ' · ' + weapon.ammo_clip : '';
        addItem(list, weaponName(weapon.name) + ammo, weapon.state === 'active');
      }
    }

    function renderWins(list, state) {
      const items = state.recent_wins || [];
      if (!items.length) addItem(list, 'Historique indisponible');
      for (const win of items) addItem(list, '#' + win.round + ' · ' + win.winner);
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

    function updateBars(card, player) {
      card.querySelectorAll('[data-p]').forEach(node => {
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

      for (const card of document.querySelectorAll('.widget.w-bomb')) {
        const clock = card.querySelector('[data-bomb-clock]');
        const bar = card.querySelector('[data-bomb-fill]');
        const label = card.querySelector('[data-bomb-msg]');
        if (!clock || !bar || !label) continue;
        clock.textContent = left === null ? '--.- s' : left.toFixed(1) + ' s';
        clock.className = 'bomb-clock ' + kind;
        bar.style.width = left === null ? '0%' : percent(100 * left / (timer.duration || 40));
        bar.className = 'bomb-fill ' + kind;
        label.textContent = message;
      }
    }

    function updateValues(state, {modeDemo, anchor}) {
      if (!state) return;
      const values = fields(state);
      const player = state.player || {};
      for (const card of board.children) {
        card.querySelectorAll('[data-v]').forEach(node => {
          node.textContent = values[node.dataset.v] ?? '—';
        });
        updateBars(card, player);
        const list = card.querySelector('[data-list]');
        if (list) {
          list.replaceChildren();
          if (list.dataset.list === 'weapons' || list.dataset.list === 'grenades') {
            renderInventory(list, player);
          } else if (list.dataset.list === 'wins') {
            renderWins(list, state);
          } else if (list.dataset.list === 'events') {
            renderEvents(list, state);
          }
        }
        if (card.dataset.kind === 'bomb') {
          const controls = card.querySelector('[data-demo-controls]');
          if (controls) controls.classList.toggle('hidden', !modeDemo);
        }
      }
      paintBomb(state, anchor);
    }

    return {createCard, updateValues, paintBomb};
  };
})();
