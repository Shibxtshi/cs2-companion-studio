# CS2 Companion Studio v1.0.0 — Release Notes (draft)

This is a personal CS2 Game State Integration dashboard developed with substantial assistance from ChatGPT by OpenAI. Neither Valve, FACEIT, nor OpenAI endorses or maintains this project.

## Highlights

- Target-only X/Y Dashboard and three-panel Studio; 29 widget types with Standard/Compact/Minimal, separate surfaces and ten themes.
- Persistent local drafts, bounded session undo/redo, explicit publication and per-tab profile selection.
- Reviewed `ccs-dashboard-export` v1 import/export; no automatic historical conversion.
- EN/FR interface; responsive dashboards on PC and phone.
- Server-side profiles synchronized across devices after PIN authentication.
- Guided Windows installer and Docker deployment.
- Private demo mode and sanitized support diagnostics.
- Estimated bomb countdown is disabled by default; not approved for FACEIT use.

## Requirements

Windows, Docker Desktop and CS2 installed via Steam for guided setup. LAN access is optional and uses unencrypted HTTP/WebSocket; keep it on trusted networks and never expose port 8080 to the Internet.

## License and integration status

The [Community No-Resale License v1.0](../../LICENSE) allows personal, professional and internal use, modifications and free redistribution under its conditions; it prohibits software resale, paid Pro editions and subscriptions selling CCS functionality. Genuine commissioned development, optional installation/configuration/support/maintenance and qualifying managed infrastructure services are permitted under sections 6–8. Source delivery, privacy and attribution obligations remain. CCS is **source-available, not OSI-approved open source**; third-party licenses are independent. The [French translation](../legal/LICENSE.fr.md) is informative; English is authoritative. See [licensing and integration status](../legal/licensing.md). The integration requires an expressly authorized merge, not this draft announcement; no lawyer approval is claimed.

## Transparency and limitations

AI-assisted implementation and automated tests are not an independent security audit or evidence of anti-cheat approval. See AI_DISCLOSURE.md, SECURITY.md and README.md. Preserve `.env`, `data/`, installation/GSI backups and a compatible application artifact during a documented target update; never publish personal files. Historical storage requires separate offline recovery, not automatic conversion.

## Before publishing

Complete [the release checklist](checklist.md). Confirm expressly authorized license adoption and rights/notices, enable private vulnerability reporting, review the code/assets and fresh screenshots, run the required checks, and verify the exact final source ZIP. The selected distribution includes the Windows installer, Dockerfile and Compose, not a prebuilt Docker image. Do not tag or publish until the separate publication decision and remaining gates are complete.
