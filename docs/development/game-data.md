# GSI and displayed game data

CCS uses CS2 Game State Integration only: no memory reading, process injection, spectator service or invented opponent data. [Widget catalog](../user/widgets.md) maps all 29 public kinds to received/derived sources. Field presence depends on the game’s mode, phase, configuration and observed player; automated fixtures are not proof that every server supplies every field.

## Ownership and lifecycle

`server.py` receives token-authenticated bounded `/gsi` JSON, merges partial state and clears round/player/match-scoped observations when their context changes. `gsi_lifecycle.py` contains pure observation/projection helpers. The backend exposes normalized values; `display-format.js`, `widget-renderer.js` and `studio-data.js` render them without persisting game packets in configurations. `dashboard_delivery.py` bounds concurrent delivery and per-peer ordering. There is one process-local game state, not a multi-worker shared service.

GSI reception and valid game-data timestamps are distinct. A provider/identity-only packet can keep GSI reception recent without extending old match values. Current thresholds are 20 seconds for reception/game freshness and a two-second periodic broadcast; these are implementation values, not guaranteed network latency. Map/round/player changes, resets and prolonged gaps invalidate scoped state. Unknown numeric values remain null/unavailable; zero is not substituted. Existing display-only formatting and labels must not change business calculations.

## Economy

`EconomyObserver` scopes a directly received `consecutive_round_losses` value to its team and round. If absent, `history_loss_level` reconstructs only when the complete relevant half is available under standard competitive MR12 assumptions, not overtime/custom half lengths. Incomplete history produces unknown, not an assumed bonus.

`cash_projection` requires valid player money/team, then computes a hypothetical next-loss amount with capped standard bonus/money. Purchases, kill/objective bonuses, survival/timeout exceptions and modified server economies are excluded. Even a reported source for the bonus does not make the projected future money certain. `source` distinguishes gsi/history/unknown; labels and warnings stay in every presentation.

## Bomb and events

The bomb state comes from received bomb/round state. The optional countdown anchors a local estimate; late joins/unknown starts and stale data cannot become an official clock. `BOMB_TIMER_ENABLED` defaults false. Demonstration’s 40/9/4/Stop controls act only on transient synthetic state, not the server setting or published profiles.

The bounded newest-first event journal is inferred from received changes (round, health, kills, bomb), not a global killfeed. Translation matches only known event categories/patterns; free personal text is not translated. Names/titles are text data.

## Demo and validation

Demo uses a public synthetic configuration and clears private cards/state when entered. Studio preview is a separate validated configuration plus transient renderer input; preview does not authenticate or publish independently. Connection labels clearly distinguish demo, server, GSI and current match.

Use separate standalone economy/timer/lifecycle/security processes and relevant integration/browser journeys from [tests](../../tests/README.md). For real CS2, use an authorized training session: compare health/armor, weapon/ammo, money, map/round/score, available stats and bomb states; quit/restart the game and wait beyond freshness plus broadcast to confirm old data is not shown as live. Record missing fields rather than inventing them. Synthetic tests and real-CS2 observations must be reported separately; no anti-cheat or platform approval is implied.
