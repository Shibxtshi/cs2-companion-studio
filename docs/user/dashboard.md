# Dashboard

[Français](dashboard.fr.md) · [User guides](README.md)

Dashboard is a viewing surface. It reads the **published** profile, not the Studio draft. Choose a profile from the selector: each tab keeps its own selection, while published configurations are shared with authenticated devices. Publishing another profile does not force your tab to select it. If your selected profile is deleted, the tab chooses a remaining profile; an open draft is retained for explicit recovery.

A new Dashboard can be empty. Add widgets in [Studio](studio.md), then explicitly publish. Theme, navigation and fullscreen preferences belong to the profile. Settings appearance controls, where offered, are temporary previews; save lasting preferences through Studio. Widget colors override automatic theme values.

Full navigation shows labels; compact shows essential icons; hidden navigation maximizes widget space. Recover controls using the edge button, the optional floating button, or Alt+M outside input fields when the browser allows it. The edge button remains available even if the floating button is disabled. The CCS logo returns to Dashboard without reloading; leaving Studio follows its guarded exit choices.

Fullscreen uses the browser API with an immersive fallback. The profile selects widgets only or widgets plus connection status. Use Escape or the visible exit/recovery controls to leave; fullscreen never rewrites layout.

Positions are stored in grid units. At smaller available widths CCS computes a deterministic reflow, then restores the desktop projection when space returns. Collisions/content minima can move or enlarge cards visually, without saving new coordinates. Long lists/details remain accessible by keyboard or touch.

## Read the connection state

| State | Meaning |
|---|---|
| Server available | HTTP health responded; not proof of authentication or CS2 |
| WebSocket connected | Authenticated live connection to CCS |
| GSI active, waiting for match | Recent CS2 packets, insufficient current match data |
| Match active | Recent valid match data is available |
| Offline/stale | Required current data is missing; old values must not be treated as live |
| Demonstration | Synthetic values, not a real connection |

Zero is a known value; an em dash/unavailable label is not zero. Forecasts and bomb timing retain estimate warnings. Use Settings → diagnostics for server/WebSocket/GSI status and packet age where available. Help and onboarding can be reopened. See [widgets](widgets.md) and [troubleshooting](maintenance.md).
