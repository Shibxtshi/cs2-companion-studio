# Ten themes

[Français](themes.fr.md) · [User guides](README.md)

| ID | Name | Palette |
|---|---|---|
| `tactical-blue` | Tactical Blue | Graphite and blue; default |
| `competitive-red` | Competitive Red | Neutral graphite, bright red |
| `performance-green` | Performance Green | Dark surfaces, green |
| `creator-purple` | Creator Purple | Dark surfaces, purple |
| `midnight` | Midnight | Deep cool blue-black |
| `arctic-white` | Arctic White | Light surfaces and dark text |
| `neon-pink` | Neon Pink | Dark surfaces, vivid pink |
| `crimson` | Crimson | Burgundy surfaces, rose-red |
| `solar-orange` | Solar Orange | Dark surfaces, warm orange |
| `monochrome` | Monochrome | Neutral black/white/gray |

In Studio, open profile properties, choose a theme and inspect preview. Undo/Redo can restore the previous choice. Only **Save and apply** publishes that profile’s theme. Reload/reconnection reapplies the published theme; other profiles stay unchanged. A temporary selector offered in Settings affects this display only, without publication.

Arctic White is a true light theme: panels, text, fields, native menus and messages use light palettes and `color-scheme: light`. The other nine use dark mode. Crimson has burgundy surfaces distinct from Competitive Red’s vivid red on graphite. Midnight has subtle cool hues; Monochrome stays neutral, while critical states retain functional text/colors.

Individual widget accents/backgrounds/opacity override automatic theme colors. A theme cannot fix an unreadable custom choice; particularly check transparent surfaces on Arctic White. Solid/Glass/Outline surface, Standard/Compact/Minimal presentation and global density remain independent. Selected-component contrast measurements are not global WCAG certification. See [design reference](../development/design-system.md).
