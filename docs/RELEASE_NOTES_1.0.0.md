# CS2 Companion Studio v1.0.0 — Release Notes (draft)

This is a personal CS2 Game State Integration dashboard developed with substantial assistance from ChatGPT by OpenAI. Neither Valve, FACEIT, nor OpenAI endorses or maintains this project.

## Highlights

- 29 customizable widgets for game state, economy estimates, weapons and personal statistics.
- EN/FR interface; responsive dashboards on PC and phone.
- Server-side profiles synchronized across devices after PIN authentication.
- Guided Windows installer and Docker deployment.
- Private demo mode and sanitized support diagnostics.
- Estimated bomb countdown is disabled by default; not approved for FACEIT use.

## Requirements

Windows, Docker Desktop and CS2 installed via Steam for guided setup. LAN access is optional and uses unencrypted HTTP/WebSocket; keep it on trusted networks and never expose port 8080 to the Internet.

## Transparency and limitations

AI-assisted implementation and automated tests are not an independent security audit or evidence of anti-cheat approval. See AI_DISCLOSURE.md, SECURITY.md and README.md. Preserve `.env` and `data/` across upgrades; never publish personal files.

## Before publishing

Complete docs/PUBLIC_RELEASE_CHECKLIST.md. In particular, confirm copyright holder in LICENSE, enable private vulnerability reporting, review the code/assets and fresh screenshots, run all CI checks, and verify archive contents. Do not tag or publish until these are complete.
