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

## License (draft — not yet effective)

The intended Community No-Resale license would allow free access, use, modifications, free redistribution, and professional/internal use, while prohibiting sale of the software and its modified versions. Monetized use (including coaching) and paid commissioned development are intended to remain permitted; paid setup, hosting and support require further legal drafting. This would be **source-available, not OSI-approved open source**. Legal review and rights-holder confirmation remain mandatory before release.

## Transparency and limitations

AI-assisted implementation and automated tests are not an independent security audit or evidence of anti-cheat approval. See AI_DISCLOSURE.md, SECURITY.md and README.md. Preserve `.env` and `data/` across upgrades; never publish personal files.

## Before publishing

Complete docs/PUBLIC_RELEASE_CHECKLIST.md. In particular, legally finalize and approve the draft license, enable private vulnerability reporting, review the code/assets and fresh screenshots, run all CI checks, and verify archive contents. Do not tag or publish until these are complete.
