# Widget presentations — P7

> P9.5 update: these phase boundaries describe their original delivery. The integrated production composition and the explicit, separately authorized transition are documented in [Production activation](production-activation.md). Valid historical installations remain usable until offline confirmation.


The maintainer approved the representative score, health, weapon, inventory, economy, stats, round_history, bomb and connection direction before catalog-wide implementation. Identity, themes and fonts remain P2; no P8 Studio or target-store activation is introduced.

## Ownership and active boundary

| Module | Responsibility |
| --- | --- |
| widgets.js | Unchanged 29 public kinds, labels and canonical shipped value markup |
| display-format.js | Shared values, locale formatting, existing inventory classification and demo connection text |
| widget-presentation.js | One structural decorator per family, presentation minima, density and source/status metadata |
| widget-renderer.js | Cached value bindings, bars, lists, countdown and explicit presentation/geometry hooks |
| widget-presentation.css | Standard, Compact, Minimal and semantic source/status presentation |
| dashboard-layout.js / dashboard-grid.js | P6 projection plus variant minima and measured intrinsic content height |

The active legacy dashboard uses Standard. No variant field is added to legacy profiles, autosave or v2 export/import. The isolated authenticated P3/P6 host reads standard/compact/minimal from the existing target contract. Surface solid/glass/outline remains independent, as do custom title, accent, background and opacity. No persistent preview selector, conversion, second writer or new schema exists.

## Shared structure and family differences

All variants reuse the original data-v/data-list/data-p nodes. Numeric/business calculations are not implemented separately per variant. Moving secondary nodes into native details preserves them for keyboard/touch access and never mutates profile objects.

| Family | Standard / Compact | Minimal |
| --- | --- | --- |
| Score and detailed score | Labeled CT/T groups and context; denser grouping in Compact | Scores remain labeled; secondary match context available in details |
| Single readings (map, money, K/D, MVP, personal score, provider) | Value plus caption; inline grouping in Compact | Header/value alignment, with redundant static captions retained for assistive access |
| Health and armor | Value/unit plus progress; inline meter in Compact | Value/unit and narrow meter; unknown has no numeric meter value |
| Weapon and ammunition | Weapon/clip/reserve, different block grouping | Essential reading retained; secondary weapon context available when applicable |
| Inventory and grenades | Received-item summary plus full list; dense chips in Compact | Active weapon or received grenade count, with full list in details |
| Economy and forecast | Current/projected values with explicit estimate/source | Projection remains identified as an estimate and source text remains visible; bonus details may collapse |
| Statistics and effects | Three labeled readings; inline grouping in Compact | Short unambiguous labels; effects retain the reported 0–255 scope |
| Player, round and bomb state | Primary state plus relevant context | Identity/state remains visible; secondary context can use details |
| Round history and events | Available received history/journal; Compact avoids redundant framing | Latest received item plus full list in details; source/availability caveat remains visible |
| Bomb and connection | Explicit state, estimate/age and warnings | No ambiguous colored dot or unqualified timer; essential warnings remain visible |

No exception omits a kind or variant: all 29 × 3 combinations are represented. Minimal does not imply a smaller DOM: preserving accessible detail content intentionally retains the same value nodes. Economy, forecast, effects and bomb have larger minima because their qualifications must fit.

## Data meaning and localization

Missing values remain distinct from zero. Demonstration is labeled synthetic; the connection value does not claim live data in demo. Waiting-for-match, offline, unavailable and stale states are textual, not color-only. Staleness follows the backend connection/age state rather than inventing another timeout.

Inventory counts describe items received, not a guaranteed complete inventory. The event preview uses the first item because companion.server.add_event inserts newest first. It is a local journal inferred from received GSI, not a global killfeed. No source of game data or business calculation is added.

Known activity enum playing is localized as En jeu in French, not by translating player names. Personal names and custom titles retain translate=no. Received round winner codes ct_win/t_win are shown as CT/T; unknown codes remain unchanged. This is display-only.

The bomb estimate remains disabled by default. The compact/minimal views preserve its estimate label, warnings and demo controls (native disclosure). They do not supply an official timer or competitive-platform approval.

## Geometry and accessibility

P6's 32-pixel rows/8-pixel gaps, collision order, responsive policy and bounded fallback remain. minimum(kind,variant) is a defensive presentation table, not a profile write. The renderer measures natural card height at the projected width, then P6 rounds it to rows and resolves collisions again. Long titles, warnings, demo notes and open details can grow the calculated footprint. Returning to desktop still uses saved geometry.

Geometry requests occur on variant/details changes, relevant wrapping text/status/list changes and container-width changes. Tabular numeric changes of equal length do not request a grid pass. Calls coalesce into animation frames. GSI values update existing nodes; identical list signatures preserve item nodes and focus/scroll state. Native scrolling lists enter the tab order only when overflowing. Renderers expose dispose to remove observers, listeners and pending accessibility frames.

User color overrides are preserved, so arbitrary private colors cannot be guaranteed to meet contrast targets. Default palettes retain semantic CT/T, warning/error/success tokens and focus indicators. Reduced motion disables decorative transitions.

## Verification and references

Run the existing checks in tests/README.md, plus node tests/js/test_widget_presentation.js and python tests/browser/test_widget_preview.py --browser chromium (also firefox/webkit). The gallery harness is synthetic and not a production route. --output PATH creates private local screenshots, a standalone HTML gallery with synthetic state/theme/width controls, DOM metrics and font notices. Keep artifacts outside the source tree.

P1 fixture files are not regenerated. Characterization compares the same values, bars, lists and estimates, normalizing only reviewed node order, round winner labels and French playing localization. P6's earlier demo-board correction remains. Separate tests compare all variants over complete/partial/missing/zero/estimated/stale/waiting/long/demo data, customization, language and theme changes. Target tests cover 87 variant/kind combinations at all seven required resolutions, with clipping checks and no storage writes from reflow/details.

Native IndexedDB, publication, PIN/Origin, GSI/WS, reconnect, historical autosave/import/export, PowerShell, Windows/Linux and Docker gates remain. Performance comparisons must use foreground pages, matching fixtures and sequential runs; background-tab throttling is not rendering cost.

## Remaining transition

Standard is active, but target variant selection/persistence remains the P3/P5/P6 isolated path. P8 still needs actual editing/selection UI, draft lifecycle and explicit publication flows before a warned, backed-up, confirmed replacement of legacy storage. P7 does not activate that transition, implement OBS, or change licensing/publication.
