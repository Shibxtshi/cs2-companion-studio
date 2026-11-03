# CCS design foundations and themes

## Approved identity

The maintainer approved Repère, Tactical Blue as the default, Competitive Red, Performance Green and Creator Purple as complementary themes, and Barlow Condensed + Inter on 2026-10-28. This overrides the initial proposal of Competitive Red as the default. The direction is Match Center — Player Edition: a personal second-screen dashboard, with a later streamer evolution, not a broadcast production console.

## Files and ownership

| File | Responsibility |
| --- | --- |
| static/css/tokens.css | Same-origin font faces, semantic colors, spacing, radii, motion and widget hooks |
| static/css/themes.css | Ten complete palettes: backgrounds, navigation, cards, raised surfaces, controls, selection, text and interaction states |
| static/css/styles.css | Existing application layouts and common components using the tokens |
| static/js/theme-preview.js | Allowlisted, in-memory selection for this tab; no storage, HTTP or WebSocket writes |
| static/branding/repere.svg | Compact mark and SVG favicon; the header uses its alpha mask with the active brand color |
| static/branding/ccs-logo.svg | Standalone dark-background lockup, with outlined lettering |
| static/fonts/ | Distributed WOFF2 files, original OFL notices and byte/hash/source provenance |

The shared catalog loader starts the ordered frontend modules under the existing strict CSP. Theme identifiers and names originate in companion/profile_contracts.py and are included in draft-schema.js by scripts/generate_profile_schema.py. CSS owns palette colors; theme-preview.js reads the active background for theme-color. No theme framework or new dependency is used.

## Theme preview boundary

Tactical Blue is the initial fallback. Published profiles select their theme on authentication, profile changes and reconnection. The Studio applies its draft theme locally; Undo/Redo restores earlier choices and only Save and apply publishes them. Preview windows use the same registry and tokens. The temporary theme selector, where available, changes this document only, without storage or transport. Unknown preview values fall back to Tactical Blue; unknown persisted identifiers are rejected by the profile contract rather than silently converted.

The ten identifiers are tactical-blue, competitive-red, performance-green, creator-purple, midnight, arctic-white, neon-pink, crimson, solar-orange and monochrome. The four original palette values are unchanged. Crimson uses burgundy surfaces and a rose-red accent, distinct from Competitive Red's neutral surfaces and brighter red. Midnight uses deep blue-black surfaces and a cool subtle accent; Monochrome uses neutral surfaces, accent and team labels. Critical functional states retain named status tokens and text.

Arctic White defines light surfaces, dark text, readable status palettes and color-scheme:light for native controls. Other themes retain color-scheme:dark. All palettes define the same 16 --ccs-* color tokens: bg, nav, surface, raised, input, border, control-border, text, muted, accent, hover, pressed, on-accent, tint, ink and focus. Light status and shadow overrides live in themes.css, not in components. Studio inputs use control-border rather than a decorative divider; placeholders and primary pointer states consume their existing semantic tokens.

Brand colors and profile colors are separate: individual-widget accents, backgrounds and opacity remain user overrides. Automatic widget surfaces follow the theme. Solid/Glass/Outline surface styles remain independent of Standard/Compact/Minimal presentation and dashboard density. No geometry is rewritten by a theme change.

## Typography and assets

Inter serves UI text and tabular numeric values (400–700), with a fixed optical-size setting for consistent dashboard typography. Barlow Condensed is reserved for branding (700), with 600 available for display headings. The shipped Latin subsets cover EN/FR; other characters fall back to system fonts. Fonts use font-display:swap and load from this server, never a third-party font service. Original OFL notices stay alongside the font files. See [font provenance](../../static/fonts/README.md).

The header is a responsive lockup: a compact Repère mask, live Barlow lettering and the product descriptor. The standalone SVG contains paths rather than external fonts or images. Its default dark-background colors use Tactical Blue. The compact mark also supports monochrome use through a CSS alpha mask. No third-party brand or game artwork is included.

## Interaction and accessibility

Base spacing is 4/8/12/16/24/32 px; control/card/dialog radii are 6/8/10 px. Components retain the current routes and actions. Status meaning stays independent of the chosen brand palette: success, warning, error, information and CT/T keep dedicated tokens and text labels. Estimated and missing values retain their existing explanations.

Text aims for at least 4.5:1 contrast and necessary control/focus indications 3:1. Browser checks sample the actual painted colors, including CSS color-mix. User-selected widget colors or opacity can produce lower contrast; The theme system neither rewrites private choices nor claims conformance for arbitrary custom colors. Disabled states remain distinct; a disabled control is never the only source of essential information.

Keyboard focus has a visible outline. Coarse-pointer controls have 44 px minimum targets; editable mobile fields use 16 px text. Reduced-motion disables decorative transitions and the waiting-state spinner while retaining the status text. Existing responsive layout rules are preserved.

The existing help dialog is themed. Browser-owned select popups, prompt/confirm windows and their appearance remain controlled by the browser/OS; P2 does not replace those flows with a new dialog framework.

## Verification

Keep P1 golden fixtures unchanged. Run the existing live journey, widget characterization and tests/browser/test_themes.py in all three CI browsers. The production theme journey checks ten published themes, local draft/history/preview behavior, profile isolation, reload/restart, EN/FR, seven viewport sizes, keyboard focus and measured contrast samples. The widget gallery covers 29 × 3 presentations across the ten themes; rendering regressions check computed custom surfaces and opacity. It can save synthetic screenshots with --output; never capture a personal PIN or profile.

See [tests/README.md](../../tests/README.md) for commands. Local timing/screenshot evidence is kept outside the repository and reported in the PR. Use the unchanged P1 baseline and the same characterization benchmark for comparisons; do not present automation round trips as pure rendering or infer real CS2/LAN certification.

The dated local results, timing ranges and limitations are recorded in [p2-validation.md](p2-validation.md).

## Adding a palette

1. Add its stable identifier/display name to `THEME_NAMES` in `companion/profile_contracts.py`; preserve existing identifiers.
2. Define the complete semantic palette in `static/css/themes.css`, including native `color-scheme` and readable status/overlay overrides for light themes. Reuse tokens; do not scatter component hex values.
3. Run `python scripts/generate_profile_schema.py`, then `--check`. Never hand-edit generated `draft-schema.js`. Selectors consume generated theme metadata, not new independent lists.
4. Keep copy in the shared JSON catalogs if explanatory labels are needed; validate locales.
5. Test server/browser validation, unknown-value refusal, draft/history, temporary preview, explicit publication/reload/profile isolation and real computed surfaces/contrast. Extend theme/widget journeys and review synthetic desktop/mobile captures. Arbitrary custom colors and sampled ratios do not establish global WCAG conformance.
