#!/usr/bin/env python3
"""Generate distinct local secrets and the CS2 GSI file, without overwriting users."""
import argparse
from pathlib import Path
import secrets
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
DOTENV = ROOT / '.env'
GSI = ROOT / 'cs2_cfg' / 'gamestate_integration_companion.cfg'

sys.path.insert(0, str(ROOT))
from companion.localization import Translator


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--language', default='EN', choices=list(Translator().languages))
    args = parser.parse_args()
    tr = Translator(args.language).text
    if DOTENV.exists() or GSI.exists():
        print(tr('configuration.existing'))
        print(tr('configuration.regenerate'))
        return 1
    pin = ''.join(str(secrets.randbelow(10)) for _ in range(10))
    token = secrets.token_urlsafe(36)
    content = (
        '# Local private configuration: never publish to GitHub.\n'
        'GSI_TOKEN=' + token + '\n'
        'DASHBOARD_PIN=' + pin + '\n'
        'BOMB_TIMER_ENABLED=false\n'
        'BOMB_DURATION_SECONDS=40\n'
        '# Localhost by default. For other devices on the local network, use BIND_HOST=0.0.0.0 on a trusted LAN with firewall rules.\n'
        'BIND_HOST=127.0.0.1\n'
        'PORT=8080\n'
    )
    cfg = (
        '"CS2 Companion Studio"\n{\n'
        '    "uri" "http://127.0.0.1:8080/gsi"\n'
        '    "timeout" "5.0"\n    "buffer" "0.1"\n'
        '    "throttle" "0.2"\n    "heartbeat" "10.0"\n'
        '    "auth"\n    {\n        "token" "' + token + '"\n    }\n'
        '    "data"\n    {\n'
        '        "provider" "1"\n        "map" "1"\n        "map_round_wins" "1"\n'
        '        "round" "1"\n        "player_id" "1"\n'
        '        "player_state" "1"\n        "player_weapons" "1"\n'
        '        "player_match_stats" "1"\n    }\n}\n'
    )
    GSI.parent.mkdir(exist_ok=True, parents=True)
    # Exclusive create prevents overwriting existing credentials.
    with DOTENV.open('x', encoding='utf-8') as f:
        f.write(content)
    try:
        with GSI.open('x', encoding='utf-8') as f:
            f.write(cfg)
    except Exception:
        DOTENV.unlink(missing_ok=True)
        raise
    if os.name != 'nt':
        DOTENV.chmod(0o600)
        GSI.chmod(0o600)
    print(tr('configuration.created', pin=pin))
    print(tr('configuration.path', path=str(GSI)))
    print(tr('configuration.privacy'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
