# The 29 widgets

[Français](widgets.fr.md) · [User guides](README.md)

Each row describes a card, not a guarantee that CS2 provides every field. Mode, phase, observed player and freshness can make information unavailable. Zero differs from unknown. GSI paths identify sources, not additional opponent data.

| Public ID | Name | Information | GSI source or derivation |
|---|---|---|---|
| `score` | Match score | Map, round and CT/T scores | `map.name, map.round, map.team_ct/team_t.score` |
| `map` | Map | Map name and mode | `map.name, map.mode` |
| `round` | Round | Round number, phase and reported winner | `map.round, round.phase, round.win_team` |
| `score_split` | Detailed score | Labeled CT/T scores and round context | `map.team_ct/team_t.score, map.round` |
| `match_phase` | Match phase | Map and round phases | `map.phase, round.phase` |
| `round_history` | Round history | Received round wins; can be absent | `map.round_wins` |
| `weapon` | Weapon | Active received weapon, clip and reserve | `player.weapons (active)` |
| `ammo` | Ammunition | Clip/reserve, ammo bar and weapon | `player.weapons (active ammo fields)` |
| `inventory` | Inventory | Received weapon list, not guaranteed complete | `player.weapons` |
| `grenades` | Grenades | Personal received grenade items | `player.weapons (filtered)` |
| `equip_value` | Equipment value | Equipment value reported by CS2 | `player.state.equip_value` |
| `gear` | Gear | Helmet, defuse kit and armor | `player.state.helmet, defusekit, armor` |
| `economy` | Economy | Money plus loss projection, bonus/source caveats | `player.state.money + economy derivation` |
| `cash` | Cash | Current received money | `player.state.money` |
| `forecast` | Forecast | Estimated next money on loss with source caveat | `economy derivation` |
| `stats` | Statistics | Kills, assists and deaths | `player.match_stats.kills, assists, deaths` |
| `kd` | K/D | Kills divided by max(1, deaths); not an official rating | `player.match_stats (derived ratio)` |
| `mvp` | MVP | Received MVP count | `player.match_stats.mvps` |
| `personal_score` | Personal score | Personal scoreboard points | `player.match_stats.score` |
| `round_stats` | Round statistics | Round kills, headshot kills and reported damage | `player.state.round_kills, round_killhs, round_totaldmg` |
| `health` | Health | HP and health meter | `player.state.health` |
| `armor` | Armor | Armor value and meter | `player.state.armor` |
| `effects` | Effects | Reported flash/smoke/fire intensity, 0–255 | `player.state.flashed, smoked, burning` |
| `player` | Player | Received name, team and activity | `player.name, team, activity` |
| `bomb` | Bomb | Bomb state and optional estimated countdown | `bomb.state / round.bomb + local estimate` |
| `bomb_state` | Bomb state | Reported state with round context | `bomb.state / round.bomb, round.phase` |
| `events` | Events | Local inferred GSI journal, not global killfeed | `server.add_event from received changes` |
| `connection` | Connection | GSI/match status and packet age | `backend online, gsi_connected, age_seconds` |
| `provider` | Provider | GSI provider version when received | `provider.version` |

## Presentations and availability

- **Standard** shows the available full readings/context. **Compact** densifies groups and spacing. **Minimal** retains the essential reading; secondary information may remain in accessible details.
- Score keeps CT/T labels. Health/armor retain value and meter. Inventory/grenades can show a summary with a full disclosure list. Statistics/effects keep meaningful labels. History/events can show the latest item with the full list in details.
- Economy/forecast preserve source, uncertainty and estimate qualifications even in Minimal. They use a received bonus or conservative observed-round inference under standard rules; exceptions/resets can prevent a forecast.
- Bomb retains state/warnings; estimated timing is disabled by default, not an official clock. The 40 s / 9 s / 4 s / Stop controls are temporary demo simulations only, without changing the server setting.
- Connection retains textual status, not only color. Stale values are not current match data. Lists may scroll; minima depend on content, so Minimal is not always shorter.

Demonstration shows a public set of synthetic cards, not necessarily all 29 simultaneously. Test fixtures cover all kinds without promising every field exists in demo or a real match. No enemy minimap, trajectory, official clock or unreceived statistic is invented. See [Studio](studio.md) and [technical reference](../development/widget-presentations.md).
