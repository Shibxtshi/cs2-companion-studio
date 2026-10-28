/* Display-only projections of received state; protocol field names remain unchanged. */
(() => {
  'use strict';

  const isNum = value => typeof value === 'number' && Number.isFinite(value);
  const valueText = (value, fallback = '—') =>
    value === null || value === undefined || value === '' ? fallback : String(value);
  const locale = () => window.CS2I18N?.locale() === 'FR' ? 'fr-FR' : 'en-US';
  const cash = value => isNum(value) ? value.toLocaleString(locale()) + ' $' : '—';
  const percent = value => isNum(value) ? Math.max(0, Math.min(100, value)) + '%' : '0%';
  const weaponName = value => valueText(value).replace(/^weapon_/, '').replaceAll('_', ' ').toUpperCase();
  const capitalize = value => valueText(value).replace(/^./, character => character.toUpperCase());

  function fields(state) {
    const player = state.player || {};
    const economy = state.economy || {};
    const map = valueText(state.map).replace(/^de_/, '').toUpperCase();
    return {
      map,
      round: 'Round ' + valueText(state.round) + ' · ' + valueText(state.round_phase, state.map_phase || '—'),
      round_number: isNum(state.round) ? String(state.round) : '—',
      ct: valueText(state.ct),
      t: valueText(state.t),
      map_mode: valueText(state.map_mode),
      map_phase: capitalize(state.map_phase),
      round_phase: capitalize(state.round_phase),
      round_winner: state.round_winner ? 'Gagnant : ' + valueText(state.round_winner) : '',
      weapon: weaponName(player.weapon),
      ammo_clip: valueText(player.ammo_clip),
      ammo_reserve: '/ ' + valueText(player.ammo_reserve),
      money: cash(player.money),
      nextmoney: cash(economy.on_loss),
      lossbonus: isNum(economy.loss_bonus) ? 'Bonus de défaite +' + cash(economy.loss_bonus) : 'Bonus indisponible',
      econ_note: economy.source === 'gsi' ? 'Bonus fourni par GSI · hors exceptions'
        : economy.source === 'history' ? 'Estimation à partir des manches · règles standard'
          : 'Historique insuffisant · bonus inconnu',
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
      helmet: player.helmet === null || player.helmet === undefined ? 'Casque —'
        : player.helmet ? '✓ Casque' : 'Sans casque',
      kit: player.defusekit === null || player.defusekit === undefined ? 'Kit —'
        : player.defusekit ? '✓ Kit' : 'Sans kit',
      armor_line: 'Armure : ' + valueText(player.armor),
      flash: valueText(player.flashed),
      smoke: valueText(player.smoked),
      fire: valueText(player.burning),
      name: valueText(player.name, 'Joueur'),
      team: valueText(player.team, 'Équipe —'),
      activity: capitalize(player.activity),
      bomb_state: ({
        planted: 'Plantée', defused: 'Désamorcée', exploded: 'Explosée',
        dropped: 'Au sol', planting: 'Pose en cours'
      })[state.bomb_state] || valueText(state.bomb_state, 'En attente'),
      connection: state.online ? 'Données en direct'
        : state.gsi_connected ? 'GSI actif · match en attente' : 'Hors ligne',
      lastpacket: state.age_seconds !== null && state.age_seconds !== undefined
        ? 'Dernier paquet : ' + state.age_seconds + ' s' : 'En attente de données',
      provider: valueText(state.provider?.version)
    };
  }

  window.CS2DisplayFormat = Object.freeze({isNum, percent, weaponName, fields});
})();
