# Trusted local network

[Français](network.fr.md) · [User guides](README.md)

Local access uses `http://localhost:8080` on the CCS computer. On a different PC, tablet or phone, localhost refers to that device, not the CCS server. LAN access is optional and requires deliberate setup on a trusted private network. **HTTP and WebSocket are unencrypted; the PIN does not encrypt traffic. Never expose CCS directly to the Internet or forward its port on a router.**

During new guided installation, accept LAN only after reading both confirmations. On an existing installation, from its project root with Docker Desktop running:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\installer\install.ps1 -Lan
```

This is an installer operation: it can check/update GSI configuration and recreate the service, not merely display network status. Preserve private installation files first. It sets `BIND_HOST=0.0.0.0` after confirmation; no firewall rule is added. See [installation](installation.md).

1. On the server PC run `ipconfig` in PowerShell (read-only). Identify the IPv4 address of the active private Ethernet/Wi-Fi adapter, not an unrelated VPN/virtual adapter. Do not publish that output.
2. Connect the other device to the same trusted network. Open `http://YOUR-PC-LAN-IP:8080`, replacing the placeholder and using the actual configured port.
3. Enter the private PIN locally on that device. Its drafts belong to that browser/origin and do not copy over from localhost. Published profiles are shared; tab selections remain independent.
4. If connection fails, verify the server health locally, then the Windows firewall profile and a deliberately limited inbound rule for the configured port/private subnet. Docker Desktop/WSL2 networking, Wi-Fi guest isolation, VPNs and access-point policies can block access. Do not disable the firewall as a general fix. No universal second-device success is promised.

To return to local-only binding, run the installer with `-LocalOnly` instead of `-Lan`. These options are mutually exclusive. This changes binding and may recreate the service; existing credentials are reused. Never change public router rules to make CCS reachable. See [security policy](../../SECURITY.md) and [maintenance](maintenance.md).
