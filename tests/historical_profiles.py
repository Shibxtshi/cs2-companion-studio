"""Synthetic historical files for offline recovery tests, never a production writer."""
import json
from pathlib import Path
from companion.profile_store import read_document, default_document, validate_document, atomic_write, MAX_STORE_BYTES


class HistoricalProfileFixture:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.data = {'profiles': [], 'activeProfile': ''}
        self.revision = 0
        if self.path.exists():
            try:
                self.data, self.revision = read_document(self.path)
            except (ValueError, UnicodeError):
                raise RuntimeError('Invalid or incompatible profile storage. Preserve the file; stop the service and use scripts/recover_profiles.py --inspect or --restore with a validated backup.') from None
        else:
            self.put(default_document(), 0)

    def snapshot(self, source=None):
        # Deep copy to avoid shared mutable reference leaks.
        return {'type': 'profiles_state', 'revision': self.revision,
                'source': source, **json.loads(json.dumps(self.data, ensure_ascii=False))}

    def put(self, document, revision):
        if type(revision) is not int or revision != self.revision:
            return False
        cleaned = validate_document(document)
        nextRev = self.revision + 1
        packed = json.dumps({**cleaned, 'revision': nextRev}, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        if len(packed) > MAX_STORE_BYTES:
            raise ValueError('too_large')
        # Keep the last accepted document before replacing the current file.
        # Failed writes leave the in-memory revision and existing main file intact.
        previous = {**self.data, 'revision': self.revision} if self.data['profiles'] else {**cleaned, 'revision': nextRev}
        backup = json.dumps(previous, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        atomic_write(self.path.with_suffix(self.path.suffix + '.bak'), backup)
        atomic_write(self.path, packed)
        self.data = cleaned
        self.revision = nextRev
        return True
