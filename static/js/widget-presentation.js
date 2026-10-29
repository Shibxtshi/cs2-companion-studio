/* P7 presentations reuse the existing catalog nodes and data projection. */
(() => {
  'use strict';
  const VARIANTS = Object.freeze(['standard', 'compact', 'minimal']);
  const MINIMUMS = Object.freeze({
    score: [[300, 192], [260, 152], [220, 112]],
    health: [[200, 152], [180, 112], [150, 72]],
    weapon: [[260, 192], [240, 152], [220, 112]],
    inventory: [[280, 272], [240, 192], [220, 152]],
    economy: [[320, 232], [280, 192], [260, 192]],
    stats: [[300, 192], [240, 152], [220, 112]],
    round_history: [[280, 192], [240, 152], [220, 152]],
    bomb: [[300, 272], [280, 232], [260, 192]],
    connection: [[260, 192], [240, 152], [220, 112]],
    map: [[220,152],[200,112],[180,112]],
    round: [[220,192],[200,152],[180,152]],
    score_split: [[280,192],[240,152],[220,152]],
    match_phase: [[240,152],[220,112],[200,112]],
    ammo: [[240,192],[220,152],[200,112]],
    grenades: [[280,232],[240,192],[220,152]],
    equip_value: [[240,152],[220,112],[200,112]],
    gear: [[260,192],[240,152],[220,152]],
    cash: [[240,152],[220,112],[200,112]],
    forecast: [[300,232],[280,192],[260,192]],
    kd: [[220,152],[200,112],[180,112]],
    mvp: [[200,152],[180,112],[160,112]],
    personal_score: [[240,152],[220,112],[200,112]],
    round_stats: [[300,192],[260,152],[240,152]],
    armor: [[200,152],[180,112],[150,72]],
    effects: [[300,232],[260,192],[240,192]],
    player: [[280,192],[240,152],[220,152]],
    bomb_state: [[240,152],[220,112],[200,112]],
    events: [[320,272],[280,232],[260,192]],
    provider: [[240,152],[220,112],[200,112]],
  });
  const ICONS = Object.freeze({
    score: 'M4 5h16v4a8 8 0 0 1-16 0V5Zm8 12v4m-4 0h8',
    health: 'M4 12h4l2-6 4 12 2-6h4',
    weapon: 'M4 12h16M8 8v8m8-8v8',
    inventory: 'M5 5h14v14H5zM9 5v14m6-14v14M5 10h14',
    economy: 'M12 3v18m5-14H9a3 3 0 0 0 0 6h6a3 3 0 0 1 0 6H6',
    stats: 'M5 20V10m7 10V4m7 16v-7',
    round_history: 'M5 5h14v14H5zM9 9h6m-6 4h6',
    bomb: 'M14 5l2-3m-2 3 3 2M19 14a7 7 0 1 1-14 0 7 7 0 0 1 14 0Z',
    map: 'M3 5l6-2 6 2 6-2v16l-6 2-6-2-6 2V5Zm6-2v16m6-14v16',
    round: 'M12 3a9 9 0 1 0 9 9m-9-5v5l4 3',
    score_split: 'M4 4v16m16-16v16M8 8h2v8H8zm6 0h2v8h-2z',
    match_phase: 'M6 3h12M6 21h12M8 3v5l8 8v5M16 3v5l-8 8v5',
    ammo: 'M6 5l2-2 2 2v16H6V5Zm8 0 2-2 2 2v16h-4V5Z',
    grenades: 'M9 3h6v4H9zm3 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14Zm3-4h4v4',
    equip_value: 'M4 7l8-4 8 4v10l-8 4-8-4V7Zm0 0 8 4 8-4m-8 4v10',
    gear: 'M12 3l8 4v6c0 4-8 8-8 8s-8-4-8-8V7l8-4Z',
    cash: 'M3 6h18v12H3zm9 3a3 3 0 1 0 0 6 3 3 0 0 0 0-6Z',
    forecast: 'M4 19l6-6 4 2 6-10m-6 0h6v6',
    kd: 'M5 19 19 5M7 5h2v4H5V7m10 8h4v4h-4v-4Z',
    mvp: 'M12 3l3 6 6 1-4 5 1 6-6-3-6 3 1-6-4-5 6-1 3-6Z',
    personal_score: 'M5 20V9l4 3 3-8 3 8 4-3v11H5Z',
    round_stats: 'M4 20V12m8 8V4m8 16V8',
    armor: 'M12 3l8 3v7c0 5-8 8-8 8s-8-3-8-8V6l8-3Z',
    effects: 'M12 3v3m0 12v3M3 12h3m12 0h3M6 6l2 2m8 8 2 2M6 18l2-2m8-8 2-2M8 12a4 4 0 1 0 8 0 4 4 0 0 0-8 0Z',
    player: 'M8 7a4 4 0 1 0 8 0 4 4 0 0 0-8 0Zm-4 14v-2a8 8 0 0 1 16 0v2',
    bomb_state: 'M12 4a8 8 0 1 0 0 16 8 8 0 0 0 0-16Zm0 4v5m0 3h.01',
    events: 'M6 5h12M6 10h12M6 15h12M6 20h8',
    provider: 'M8 3v4m8-4v4M3 8h4m-4 8h4m10-8h4m-4 8h4M8 17v4m8-4v4M7 7h10v10H7Z',
    connection: 'M4 9a12 12 0 0 1 16 0M7 13a8 8 0 0 1 10 0m-7 4a3 3 0 0 1 4 0m-2 3h.01',
  });
  function roundLabel(win) {
    const labels = {ct_win:'CT',t_win:'T'};
    const winner = Object.hasOwn(labels,win.winner) ? labels[win.winner] : win.winner;
    return '#' + win.round + ' · ' + winner;
  }
  const SINGLE_VALUES = Object.freeze({
    map:'map', round:'round_number', match_phase:'map_phase', equip_value:'equip_value',
    cash:'money', kd:'kd', mvp:'mvps', personal_score:'personal_score',
    player:'name', bomb_state:'bomb_state', provider:'provider',
  });
  const TILE_FIELDS = Object.freeze({
    stats:[['kills','K'],['assists','A'],['deaths','D']],
    score_split:[['ct','CT'],['t','T']],
    round_stats:[['round_kills','K'],['round_hs','HS'],['round_damage','DMG']],
    effects:[['flash','Flash'],['smoke','Smoke'],['fire','Feu']],
  });
  const records = new WeakMap();
  const node = (tag, className, text = '') => {
    const element = document.createElement(tag);
    element.className = className;
    element.textContent = text;
    return element;
  };
  function minimum(kind, variant = 'standard') {
    const index = VARIANTS.indexOf(variant);
    return Object.hasOwn(MINIMUMS,kind) ? [...MINIMUMS[kind][Math.max(0, index)]] : null;
  }
  function setText(element, value) {
    const expected = window.CS2I18N?.translate(value) || value;
    if (element.textContent !== value && element.textContent !== expected) element.textContent = value;
  }
  function field(card, key) { return card.querySelector('[data-v="' + key + '"]'); }

  function decorate(card, widget) {
    if (!Object.hasOwn(MINIMUMS, widget.kind)) return;
    card.classList.add('presented-widget');
    const body = card.querySelector('.widget-body');
    const icon = card.querySelector('.widget-icon');
    icon.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="' + ICONS[widget.kind] + '"/></svg>';
    const status = node('div', 'widget-data-status');
    status.hidden = true;
    card.append(status);
    const detail = document.createElement('details');
    detail.className = 'widget-more';
    const summary = node('summary', '', 'Plus de détails');
    const detailBody = node('div', 'widget-more-content');
    detail.append(summary, detailBody);
    body.append(detail);
    const record = {detail, detailBody, status, secondary: []};
    records.set(card, record);
    function secondary(element) {
      const anchor = document.createComment('Variant secondary-content position');
      element.before(anchor);
      record.secondary.push({element, anchor});
    }

    if (widget.kind === 'score') {
      const scores = body.querySelector('.score-side');
      for (const [key, label] of [['ct', 'CT'], ['t', 'T']]) {
        const value = field(card, key);
        const group = node('div', 'score-team');
        value.before(group);
        group.append(node('span', 'score-team-label', label), value);
      }
      scores.classList.add('score-values');
      const context = field(card, 'map').parentElement;
      context.classList.add('score-context');
      const wrapper = scores.parentElement;
      body.prepend(scores, context);
      wrapper.remove();
      secondary(context);
    } else if (['health','armor'].includes(widget.kind)) {
      const value = field(card, widget.kind);
      const reading = node('div', 'health-reading');
      value.before(reading);
      reading.append(value, node('span', 'health-unit', widget.kind === 'health' ? 'HP' : 'AP'));
      const meter = body.querySelector('.bar');
      meter.setAttribute('role', 'progressbar');
      meter.setAttribute('aria-label', widget.kind === 'health' ? 'Santé' : 'Armure');
      meter.setAttribute('aria-valuemin', '0');
      meter.setAttribute('aria-valuemax', '100');
    } else if (widget.kind === 'weapon') {
      const ammo = field(card, 'ammo_clip').parentElement;
      ammo.classList.add('weapon-ammunition');
      body.classList.add('weapon-presentation');
      ammo.append(node('span', 'ammo-unit', 'Munitions'));
    } else if (widget.kind === 'inventory') {
      const summaryLine = node('div', 'inventory-summary');
      const current = node('strong', 'inventory-current');
      current.dataset.inventoryCurrent = '';
      current.setAttribute('translate', 'no');
      const quantity = node('span', 'inventory-count');
      const count = node('b', '');
      count.dataset.inventoryCount = '';
      count.setAttribute('translate', 'no');
      quantity.append(count, document.createTextNode(' '), node('span', '', 'objets reçus'));
      const activeLabel = node('span', 'tiny', 'Arme active');
      const currentGroup = node('div', 'inventory-active');
      currentGroup.append(activeLabel, current);
      summaryLine.append(currentGroup, quantity);
      body.prepend(summaryLine);
      secondary(body.querySelector('[data-list="weapons"]'));
    } else if (widget.kind === 'economy') {
      field(card, 'money').parentElement.classList.add('money-current');
      const forecast = field(card, 'nextmoney').parentElement;
      forecast.classList.add('money-forecast');
      forecast.style.removeProperty('text-align');
      body.querySelector('.flex').classList.add('economy-values');
      const source = field(card, 'econ_note');
      source.classList.add('economy-source');
      secondary(field(card, 'lossbonus'));
    } else if (Object.hasOwn(TILE_FIELDS, widget.kind)) {
      card.classList.add('tile-widget');
      for (const [key, label] of TILE_FIELDS[widget.kind]) {
        const tile = field(card, key).parentElement;
        const short = node('span', 'stat-short', label);
        short.setAttribute('aria-hidden', 'true');
        tile.prepend(short);
      }
    } else if (widget.kind === 'round_history') {
      const latest = node('div', 'history-summary');
      const label = node('span', 'tiny', 'Dernière manche reçue');
      const value = node('strong', '');
      value.dataset.latestRound = '';
      value.setAttribute('translate', 'no');
      latest.append(label, value);
      body.prepend(latest);
      secondary(body.querySelector('[data-list="wins"]'));
    } else if (widget.kind === 'bomb') {
      const controls = body.querySelector('[data-demo-controls]');
      const options = document.createElement('details');
      options.className = 'bomb-demo-options';
      controls.before(options);
      options.append(node('summary', '', 'Scénarios de démo'), controls);
    } else if (widget.kind === 'connection') {
      const indicator = node('span', 'connection-indicator');
      indicator.setAttribute('aria-hidden', 'true');
      field(card, 'connection').before(indicator);
    }
    if (Object.hasOwn(SINGLE_VALUES, widget.kind)) {
      card.classList.add('single-reading-widget');
      field(card, SINGLE_VALUES[widget.kind]).classList.add('single-reading');
      for (const caption of body.querySelectorAll(':scope > .muted,:scope > .tiny')) caption.classList.add('presentation-caption');
      if (widget.kind === 'map') secondary(field(card,'map_mode'));
      if (widget.kind === 'round') secondary(field(card,'round_winner'));
      if (widget.kind === 'player') secondary(field(card,'activity'));
    }
    if (widget.kind === 'ammo') {
      body.querySelector('.rowgap').classList.add('ammo-reading');
      secondary(field(card,'weapon'));
    } else if (widget.kind === 'grenades') {
      const summary = node('div','grenade-summary');
      const count = node('strong','big'); count.dataset.grenadeCount='';
      summary.append(count,node('span','muted','grenades reçues'));
      body.prepend(summary);
      secondary(body.querySelector('[data-list="grenades"]'));
    } else if (widget.kind === 'gear') {
      card.classList.add('gear-widget');
      secondary(field(card,'armor_line'));
    } else if (widget.kind === 'forecast') {
      body.prepend(node('span','estimate-label','Si défaite · estimation'));
      field(card,'econ_note').classList.add('economy-source');
      secondary(field(card,'lossbonus'));
    } else if (widget.kind === 'events') {
      const latest = node('div','event-preview medium');
      latest.dataset.latestEvent='';
      body.prepend(latest);
      secondary(body.querySelector('[data-list="events"]'));
    }
    if (!record.secondary.length) { detail.remove(); record.detail = null; record.detailBody = null; }
    setVariant(card, widget.variant || 'standard');
  }

  function setVariant(card, variant) {
    const record = records.get(card);
    if (!record) return;
    if (!VARIANTS.includes(variant)) throw new Error('invalid_variant');
    card.dataset.variant = variant;
    const [width, height] = minimum(card.dataset.kind, variant);
    card.style.setProperty('--widget-min-width', width + 'px');
    card.style.setProperty('--widget-min-height', height + 'px');
    const collapsed = variant === 'minimal' && record.secondary.length > 0;
    for (const {element, anchor} of record.secondary) {
      if (collapsed) record.detailBody.append(element);
      else anchor.after(element);
    }
    if (record.detail) {
      record.detail.hidden = !collapsed;
      if (!collapsed) record.detail.open = false;
    }
  }

  function update(card, state, {modeDemo}) {
    const record = records.get(card);
    if (!record) return;
    const player = state.player || {};
    const kind = card.dataset.kind;
    const primary = SINGLE_VALUES[kind] || (['health','armor'].includes(kind) ? kind : null);
    const primaryValue = primary ? field(card,primary)?.textContent : null;
    const unavailable = primary ? primaryValue === '—' : false;
    const stale = !state.gsi_connected && CS2DisplayFormat.isNum(state.age_seconds);
    const status = modeDemo ? 'Données simulées'
      : !state.online ? state.gsi_connected ? 'GSI actif · match en attente'
        : stale ? 'Données périmées · hors ligne' : 'Hors ligne — données indisponibles'
        : unavailable ? 'Valeur indisponible' : '';
    const hideStatus = !status || (kind === 'connection' && modeDemo);
    if (record.status.hidden !== hideStatus) record.status.hidden = hideStatus;
    if (record.lastStatus !== status) { record.status.textContent = status; record.lastStatus = status; }
    const dataState = modeDemo ? 'demo' : !state.online ? stale ? 'stale' : state.gsi_connected ? 'waiting' : 'offline' : unavailable ? 'unavailable' : 'live';
    if (card.dataset.dataState !== dataState) card.dataset.dataState = dataState;
    if (kind === 'bomb') {
      const options = card.querySelector('.bomb-demo-options');
      if (options.hidden !== !modeDemo) options.hidden = !modeDemo;
    }
    if (['health','armor'].includes(kind)) {
      const meter = card.querySelector('[role="progressbar"]');
      if (unavailable) { meter.removeAttribute('aria-valuenow'); meter.setAttribute('aria-valuetext', window.CS2I18N?.translate('Valeur indisponible') || 'Valeur indisponible'); }
      else {
        const value = String(Math.max(0, Math.min(100, player[kind])));
        if (meter.getAttribute('aria-valuenow') !== value) meter.setAttribute('aria-valuenow',value);
        meter.removeAttribute('aria-valuetext');
      }
    } else if (kind === 'inventory') {
      const weapons = player.weapons || [];
      const active = weapons.find(weapon => weapon.state === 'active');
      const current = card.querySelector('[data-inventory-current]');
      setText(current,active ? CS2DisplayFormat.weaponName(active.name) : '—');
      setText(card.querySelector('[data-inventory-count]'),weapons.length ? String(weapons.length) : '—');
    } else if (kind === 'grenades') {
      setText(card.querySelector('[data-grenade-count]'),player.weapons?.length
        ? String(CS2DisplayFormat.inventory(player,'grenades').length) : '—');
    } else if (kind === 'events') {
      setText(card.querySelector('[data-latest-event]'),state.events?.[0]?.message || 'Aucun événement enregistré');
    } else if (kind === 'round_history') {
      const recent = state.recent_wins || [];
      const last = recent.at(-1);
      setText(card.querySelector('[data-latest-round]'),last ? roundLabel(last) : '—');
    }
  }
  window.CCSWidgetPresentation = Object.freeze({decorate, setVariant, update, minimum, roundLabel,
    kinds: Object.freeze(Object.keys(MINIMUMS)), variants: VARIANTS});
})();
