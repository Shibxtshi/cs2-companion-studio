# CCS design foundations — P2

## Approved identity

The maintainer approved Repère, Tactical Blue as the default, Competitive Red, Performance Green and Creator Purple as complementary themes, and Barlow Condensed + Inter on 2026-10-28. This overrides the initial proposal of Competitive Red as the default. The direction is Match Center — Player Edition: a personal second-screen dashboard, with a later streamer evolution, not a broadcast production console.

## Files and ownership

| File | Responsibility |
| --- | --- |
| static/css/tokens.css | Same-origin font faces, semantic colors, spacing, radii, motion and widget hooks |
| static/css/themes.css | Four complete palettes: backgrounds, navigation, cards, raised surfaces, controls, selection, text and interaction states |
| static/css/styles.css | Existing application layouts and common components using the tokens |
| static/js/theme-preview.js | Allowlisted, in-memory selection for this tab; no storage, HTTP or WebSocket writes |
| static/branding/repere.svg | Compact mark and SVG favicon; the header uses its alpha mask with the active brand color |
| static/branding/ccs-logo.svg | Standalone dark-background lockup, with outlined lettering |
| static/fonts/ | Distributed WOFF2 files, original OFL notices and byte/hash/source provenance |

The existing deferred scripts, strict CSP and frontend modules from P1 remain in use. There is no framework, build tool, runtime package or backend change. Asset-preparation tools used locally are not application dependencies.

## Theme preview boundary

Tactical Blue is applied on every page load. The header selector is visibly marked as a preview that is not saved and affects only this tab. Open tabs do not change one another. Reloading returns to Tactical Blue. It does not modify the server profile document, active profile, revision, import/export format or autosave policy. Theme persistence belongs to the later profile contract.

Brand colors and profile colors are separate: controls and branding follow the preview; existing profile and individual-widget accents/backgrounds remain user overrides. Automatic widget surfaces follow the theme. Existing solid/glass/outline choices and opacity remain functional; the global design adds no glass effects, gradients or decorative animation. Standard/Compact/Minimal widget variants are not implemented here.

## Typography and assets

Inter serves UI text and tabular numeric values (400–700). Barlow Condensed is reserved for branding (700), with 600 available for display headings. The shipped Latin subsets cover EN/FR; other characters fall back to system fonts. Fonts use font-display:swap and load from this server, never a third-party font service. Original OFL notices stay alongside the font files. See [font provenance](../../static/fonts/README.md).

The header is a responsive lockup: a compact Repère mask, live Barlow lettering and the product descriptor. The standalone SVG contains paths rather than external fonts or images. Its default dark-background colors use Tactical Blue. The compact mark also supports monochrome use through a CSS alpha mask. No third-party brand or game artwork is included.

## Interaction and accessibility

Base spacing is 4/8/12/16/24/32 px; control/card/dialog radii are 6/8/10 px. Components retain the current routes and actions. Status meaning stays independent of the chosen brand palette: success, warning, error, information and CT/T keep dedicated tokens and text labels. Estimated and missing values retain their existing explanations.

Text aims for at least 4.5:1 contrast and necessary control/focus indications 3:1. Browser checks sample the actual painted colors, including CSS color-mix. User-selected widget colors or opacity can produce lower contrast; P2 neither rewrites private choices nor claims conformance for arbitrary custom colors. Disabled states remain distinct; a disabled control is never the only source of essential information.

Keyboard focus has a visible outline. Coarse-pointer controls have 44 px minimum targets; editable mobile fields use 16 px text. Reduced-motion disables decorative transitions and the waiting-state spinner while retaining the status text. Existing responsive layout rules are preserved.

The existing help dialog is themed. Browser-owned select popups, prompt/confirm windows and their appearance remain controlled by the browser/OS; P2 does not replace those flows with a new dialog framework.

## Verification

Keep P1 golden fixtures unchanged. Run the existing live journey, widget characterization and tests/browser/test_themes.py in all three CI browsers. The theme journey checks 29-widget output parity, four viewport widths, EN/FR, keyboard focus, contrast, same-origin resources and absence of profile/storage writes. It can save synthetic screenshots with --output; never capture a personal PIN or profile.

See [tests/README.md](../../tests/README.md) for commands. Local timing/screenshot evidence is kept outside the repository and reported in the PR. Use the unchanged P1 baseline and the same characterization benchmark for comparisons; do not present automation round trips as pure rendering or infer real CS2/LAN certification.
