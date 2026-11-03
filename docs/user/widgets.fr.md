# Catalogue des 29 widgets

[English](widgets.md) · [Guides utilisateur](README.fr.md)

Chaque ligne décrit une carte, pas une garantie que CS2 fournira tous ses champs. Le mode, la phase, le joueur observé et la fraîcheur peuvent rendre une information indisponible. Zéro est distinct d’une valeur inconnue. Les chemins GSI indiquent la source, pas des données adverses supplémentaires.

| ID public | Nom | Informations | Source GSI ou dérivation |
|---|---|---|---|
| `score` | Score de partie | Carte, manche et scores CT/T | `map.name, map.round, map.team_ct/team_t.score` |
| `map` | Carte | Nom et mode de carte | `map.name, map.mode` |
| `round` | Manche | Numéro, phase et vainqueur reçu | `map.round, round.phase, round.win_team` |
| `score_split` | Score détaillé | Scores CT/T identifiés et contexte de manche | `map.team_ct/team_t.score, map.round` |
| `match_phase` | Phase de partie | Phases de carte et de manche | `map.phase, round.phase` |
| `round_history` | Historique des manches | Victoires de manches reçues ; peuvent manquer | `map.round_wins` |
| `weapon` | Arme | Arme active reçue, chargeur et réserve | `player.weapons (active)` |
| `ammo` | Munitions | Chargeur/réserve, barre et arme | `player.weapons (active ammo fields)` |
| `inventory` | Inventaire | Liste d’armes reçues, non garantie exhaustive | `player.weapons` |
| `grenades` | Grenades | Grenades personnelles reçues | `player.weapons (filtered)` |
| `equip_value` | Valeur équipement | Valeur d’équipement fournie par CS2 | `player.state.equip_value` |
| `gear` | Équipement | Casque, kit et armure | `player.state.helmet, defusekit, armor` |
| `economy` | Économie | Argent et projection sur défaite, bonus/source | `player.state.money + economy derivation` |
| `cash` | Argent | Argent courant reçu | `player.state.money` |
| `forecast` | Prévision | Argent estimé sur défaite et source | `economy derivation` |
| `stats` | Statistiques | Éliminations, assistances et morts | `player.match_stats.kills, assists, deaths` |
| `kd` | K/D | Éliminations / max(1, morts) ; pas une note officielle | `player.match_stats (derived ratio)` |
| `mvp` | MVP | Nombre de MVP reçu | `player.match_stats.mvps` |
| `personal_score` | Score personnel | Points personnels au tableau | `player.match_stats.score` |
| `round_stats` | Statistiques de manche | Éliminations, tirs à la tête et dégâts reçus de la manche | `player.state.round_kills, round_killhs, round_totaldmg` |
| `health` | Santé | HP et jauge de santé | `player.state.health` |
| `armor` | Armure | Valeur et jauge d’armure | `player.state.armor` |
| `effects` | Effets | Intensité flash/fumée/feu reçue, 0–255 | `player.state.flashed, smoked, burning` |
| `player` | Joueur | Nom, équipe et activité reçus | `player.name, team, activity` |
| `bomb` | Bombe | État et chronomètre estimatif facultatif | `bomb.state / round.bomb + local estimate` |
| `bomb_state` | État de bombe | État reçu et contexte de manche | `bomb.state / round.bomb, round.phase` |
| `events` | Événements | Journal local déduit du GSI, pas un killfeed global | `server.add_event from received changes` |
| `connection` | Connexion | État GSI/partie et âge du paquet | `backend online, gsi_connected, age_seconds` |
| `provider` | Fournisseur | Version du fournisseur GSI si reçue | `provider.version` |

## Présentations et disponibilité

- **Standard** affiche les valeurs et contextes complets disponibles. **Compact** densifie les groupes et espacements. **Minimal** garde la lecture essentielle ; les détails secondaires peuvent rester dans un volet accessible.
- Score garde CT/T identifiés. Santé/armure gardent valeur et jauge. Inventaire/grenades peuvent montrer un résumé avec liste complète dans les détails. Statistiques/effets gardent les libellés compréhensibles. Historique/événements peuvent réduire la vue au dernier élément avec liste dans les détails.
- Économie/prévision conservent source, incertitude et mention d’estimation, même en Minimal. Elles utilisent le bonus reçu ou une inférence prudente d’historique selon les règles standard ; exceptions/réinitialisations peuvent empêcher une prévision.
- Bombe conserve état/avertissements ; le chronomètre estimatif est désactivé par défaut, pas un temps officiel. Les commandes 40 s / 9 s / 4 s / Stop sont une simulation temporaire uniquement en démonstration, sans changement du réglage serveur.
- Connexion conserve un texte d’état, jamais seulement une couleur. Les données périmées ne sont pas une partie actuelle. Les listes peuvent défiler ; les minima dépendent du contenu, donc Minimal n’est pas forcément moins haut.

La démonstration présente un ensemble public de cartes synthétiques, pas forcément les 29 cartes simultanément. Les fixtures de test couvrent les 29 types sans promettre que toutes leurs données sont présentes en démo ou en partie. Aucune minimap ennemie, trajectoire, durée officielle ou statistique non reçue n’est inventée. Voir [Studio](studio.fr.md) et [référence technique (anglais)](../development/widget-presentations.md).
