/* Display-only projections of received state; protocol field names remain unchanged. */
(() => {
  'use strict';

  const isNum = value => typeof value === 'number' && Number.isFinite(value);
  const valueText = (value, fallback = '—') =>
    value === null || value === undefined || value === '' ? fallback : String(value);
  const locale = () => CS2I18N.numberLocale();
  const cash = value => isNum(value) ? value.toLocaleString(locale()) + ' $' : '—';
  const percent = value => isNum(value) ? Math.max(0, Math.min(100, value)) + '%' : '0%';
  const weaponName = value => valueText(value).replace(/^weapon_/, '').replaceAll('_', ' ').toUpperCase();
  const capitalize = value => valueText(value).replace(/^./, character => character.toUpperCase());

  function inventory(player, type = 'weapons') {
    return (player.weapons || []).filter(weapon => type === 'weapons' || weapon.type === 'Grenade'
      || /grenade|flashbang|molotov|incgrenade|decoy|smokegrenade/.test(weapon.name));
  }

  function fields(state, {modeDemo = false} = {}) {
    const player = state.player || {};
    const economy = state.economy || {};
    const map = valueText(state.map).replace(/^de_/, '').toUpperCase();
    const activities = {playing: 'widgets.activity.playing', menu: 'widgets.activity.menu', textinput: 'widgets.activity.textinput'};
    return {
      map,
      round: CS2I18N.t('widgets.value.round', {round: valueText(state.round), phase: valueText(state.round_phase, state.map_phase || '—')}),
      round_number: isNum(state.round) ? String(state.round) : '—',
      ct: valueText(state.ct),
      t: valueText(state.t),
      map_mode: valueText(state.map_mode),
      map_phase: capitalize(state.map_phase),
      round_phase: capitalize(state.round_phase),
      round_winner: state.round_winner ? CS2I18N.t('widgets.value.winner', {team: valueText(state.round_winner)}) : '',
      weapon: weaponName(player.weapon),
      ammo_clip: valueText(player.ammo_clip),
      ammo_reserve: '/ ' + valueText(player.ammo_reserve),
      money: cash(player.money),
      nextmoney: cash(economy.on_loss),
      lossbonus: isNum(economy.loss_bonus) ? CS2I18N.t('widgets.value.lossBonus', {amount: cash(economy.loss_bonus)}) : CS2I18N.t("widgets.value.bonusUnavailable"),
      econ_note: economy.source === 'gsi' ? CS2I18N.t("widgets.value.bonusProvidedByGsiExcludingExceptions")
        : economy.source === 'history' ? CS2I18N.t("widgets.value.estimatedFromRoundsStandardRules")
          : CS2I18N.t("widgets.value.insufficientHistoryUnknownBonus"),
      kills: valueText(player.kills),
      assists: valueText(player.assists),
      deaths: valueText(player.deaths),
      kd: isNum(player.kills) && isNum(player.deaths)
        ? (player.kills / Math.max(1, player.deaths)).toFixed(2) : '—',
      mvps: valueText(player.mvps),
      personal_score: valueText(player.score),
      round_kills: valueText(player.round_kills),
      round_hs: valueText(player.round_killhs),
      round_damage: valueText(player.round_totaldmg),
      health: valueText(player.health),
      armor: valueText(player.armor),
      equip_value: cash(player.equip_value),
      helmet: player.helmet === null || player.helmet === undefined ? CS2I18N.t("widgets.value.helmetUnknown")
        : player.helmet ? CS2I18N.t("widgets.value.helmetEquipped") : CS2I18N.t("widgets.value.noHelmet"),
      kit: player.defusekit === null || player.defusekit === undefined ? CS2I18N.t("widgets.value.kitUnknown")
        : player.defusekit ? CS2I18N.t("widgets.value.kitEquipped") : CS2I18N.t("widgets.value.noKit"),
      armor_line: CS2I18N.t('widgets.value.armorLine', {amount: valueText(player.armor)}),
      flash: valueText(player.flashed),
      smoke: valueText(player.smoked),
      fire: valueText(player.burning),
      name: valueText(player.name, CS2I18N.t("widgets.category.player")),
      team: valueText(player.team, CS2I18N.t("widgets.value.team")),
      activity: Object.hasOwn(activities,player.activity) ? CS2I18N.t(activities[player.activity]) : capitalize(player.activity),
      bomb_state: ({
        planted: CS2I18N.t("widgets.value.planted"), defused: CS2I18N.t("widgets.value.defused"), exploded: CS2I18N.t("widgets.value.exploded"),
        dropped: CS2I18N.t("widgets.value.dropped"), planting: CS2I18N.t("widgets.value.planting")
      })[state.bomb_state] || valueText(state.bomb_state, CS2I18N.t("widgets.value.waiting")),
      connection: modeDemo ? CS2I18N.t("app.data.synthetic") : state.online ? CS2I18N.t("widgets.value.liveData")
        : state.gsi_connected ? CS2I18N.t("widgets.value.gsiActiveWaitingForMatch") : CS2I18N.t("widgets.value.offline"),
      lastpacket: state.age_seconds !== null && state.age_seconds !== undefined
        ? CS2I18N.t('widgets.value.lastPacket', {age: state.age_seconds}) : CS2I18N.t("widgets.value.waitingForData"),
      provider: valueText(state.provider?.version)
    };
  }


  function eventText(event) {
    // Only the server's closed inferred-event categories are localized; unknown/free text stays untouched.
    const message = event.message || '';
    if (event.category === 'health') {
      const match = /^(Dégâts|Soins) · ([0-9]+) HP$/.exec(message);
      if (match) return CS2I18N.t(match[1] === 'Dégâts' ? 'widgets.event.damage' : 'widgets.event.healing', {amount: match[2]});
    }
    if (event.category === 'kill') {
      const match = /^Élimination · ([0-9]+) au total$/.exec(message);
      if (match) return CS2I18N.t('widgets.event.kill', {amount: match[1]});
    }
    if (event.category === 'round') {
      if (message === 'Nouvelle manche') return CS2I18N.t('widgets.event.round');
      const match = /^Nouvelle manche · (.+)$/.exec(message);
      if (match) return CS2I18N.t('widgets.event.roundMap', {map: match[1]});
    }
    if (event.category === 'bomb') {
      const keys = {'Bombe plantée': 'planted', 'Bombe désamorcée': 'defused', 'Bombe explosée': 'exploded'};
      if (Object.hasOwn(keys, message)) return CS2I18N.t('widgets.event.' + keys[message]);
    }
    return message;
  }

  window.CS2DisplayFormat = Object.freeze({isNum, percent, weaponName, fields, inventory, eventText});
})();
