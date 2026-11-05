# First use

[Français](first-use.fr.md) · [User guides](README.md)

Complete [installation](installation.md) first. Start Docker Desktop and CCS. If the image was already built, run `docker compose up -d --no-build --pull never` from that installation’s root; this starts the configured service and may create its container. Stop if the image is missing or storage is incompatible. Do not erase files to force startup.

1. Open `http://localhost:8080` (use your configured port). Choose EN, FR, RU, PL, UK, CS or RO.
2. Try **Demonstration**. The values are synthetic and do not verify GSI or expose private profiles. Exit demonstration to connect normally.
3. Enter your private PIN on the connection screen. Never place it in the URL or a report.
4. Open Dashboard and select the desired published profile. A new installation may have no widgets; that is expected.
5. Open **Customization Studio**. Search the library for Health and add it.
6. Select the card. In Properties choose its presentation, X/Y, width and height; desktop drag/resize also snaps to cells. Use numeric controls on narrow screens.
7. Wait for the local draft status. This saves only in this browser, not to the server.
8. Choose **Save and apply**. Wait for confirmation; a network timeout is not success.
9. Return to Dashboard using navigation or the CCS logo. It reads the published layout; reload to verify persistence.
10. For real values, restart CS2 after GSI setup and start a training match. Server connected, GSI active and match active are different states. Missing values remain unavailable.

Help offers an optional quick start that can be closed and reopened. Settings contains appearance previews, connection information and diagnostics. See [Studio](studio.md) for exit/conflict choices and [maintenance](maintenance.md) for troubleshooting.
