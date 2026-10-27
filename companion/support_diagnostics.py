"""Support-only counters and diagnostic events; raw game state and identities are forbidden."""
import json
import os
import time
from pathlib import Path

ALLOWED_CODES = frozenset({
    'server_start', 'gsi_received', 'gsi_bad_json', 'gsi_bad_token', 'gsi_invalid',
    'gsi_too_large', 'login_success', 'login_failed', 'login_blocked',
    'ws_disconnected', 'profiles_saved', 'profiles_conflict',
    'profiles_rejected', 'profiles_storage_error', 'ws_capacity',
})

class Diagnostics:
    def __init__(self, directory: Path, version: str):
        self.directory = Path(directory)
        self.version = version
        self.profile_count = 0
        self.counts = {key: 0 for key in sorted(ALLOWED_CODES)}
        self.started_at = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        self.directory.mkdir(parents=True, exist_ok=True)
        self.record('server_start')

    def snapshot(self, profile_count=None):
        if profile_count is None:
            profile_count = self.profile_count
        return {'project': 'CS2 Companion Studio', 'version': self.version,
                'started_at_utc': self.started_at, 'generated_at_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'profile_count': profile_count, 'counters': self.counts.copy(),
                'privacy': 'Only event codes, counts and UTC timestamps; no GSI payloads, secrets, player IDs, addresses or profile content.'}

    def record(self, code):
        if code not in ALLOWED_CODES:
            return
        self.counts[code] += 1
        # Count all accepted GSI packets but only persist one of every 20.
        # Avoid disk writes on every game-state update.
        if code == 'gsi_received' and self.counts[code] % 20 != 1:
            return
        try:
            dest = self.directory / 'events.jsonl'
            if dest.exists() and dest.stat().st_size >= 256_000:
                prev = self.directory / 'events.previous.jsonl'
                dest.replace(prev)
            event = {'at_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'code': code}
            with dest.open('a', encoding='utf-8') as file:
                file.write(json.dumps(event, separators=(',', ':')) + '\n')
            self.write_summary()
        except OSError:
            # Diagnostics must never interrupt a running game or profiles operation.
            pass

    def write_summary(self, profile_count=None):
        if profile_count is not None:
            self.profile_count = profile_count
        try:
            p = self.directory / 'support-summary.json'
            tmp = self.directory / '.support-summary.tmp'
            tmp.write_text(json.dumps(self.snapshot(), indent=2), encoding='utf-8')
            os.replace(tmp, p)
        except OSError:
            pass
