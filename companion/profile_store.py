"""Validated, authenticated, persisted profile state. Never served as static files."""
import json
import os
import re
import tempfile
from pathlib import Path

from companion.security import decode_message

PROFILE_KINDS = frozenset('score map round score_split match_phase round_history weapon ammo inventory grenades equip_value gear economy cash forecast stats kd mvp personal_score round_stats health armor effects player bomb bomb_state events connection provider'.split())
# Keep this list in sync with static/js/widgets.js's widget catalog.
COLORS = re.compile(r'^#[0-9a-fA-F]{6}$')
IDS = re.compile(r'^[a-zA-Z0-9_-]{1,64}$')
DEFAULT_COLOR = '#f3ac52'
MAX_PROFILES = 12
MAX_WIDGETS = 60
MAX_STORE_BYTES = 200_000


def _color(val, default=''):
    return val if isinstance(val, str) and COLORS.fullmatch(val) else default


def _name(val, length=32):
    if not isinstance(val, str):
        return ''
    return ''.join(c for c in val if c.isprintable()).strip()[:length]


def _id(val):
    return val if isinstance(val, str) and IDS.fullmatch(val) else None


def validate_document(obj):
    if isinstance(obj, dict) and any(key in obj for key in ('format', 'version', 'schemaVersion')):
        raise ValueError('unsupported_format')
    if not isinstance(obj, dict) or not isinstance(obj.get('profiles'), list):
        raise ValueError('format')
    source = obj['profiles']
    if not 1 <= len(source) <= MAX_PROFILES:
        raise ValueError('profile_count')
    profiles, ids = [], set()
    for raw in source:
        if not isinstance(raw, dict):
            raise ValueError('profile')
        pid = _id(raw.get('id'))
        if not pid or pid in ids:
            raise ValueError('profile_id')
        ids.add(pid)
        widgetsRaw = raw.get('widgets')
        if not isinstance(widgetsRaw, list) or len(widgetsRaw) > MAX_WIDGETS:
            raise ValueError('widgets_count')
        widgets, wids = [], set()
        for item in widgetsRaw:
            if (not isinstance(item, dict) or not isinstance(item.get('kind'), str)
                    or item['kind'] not in PROFILE_KINDS):
                raise ValueError('widget_type')
            wid = _id(item.get('id'))
            if not wid or wid in wids:
                raise ValueError('widget_id')
            wids.add(wid)
            width = item.get('span')
            if type(width) is not int or width not in (3, 4, 6, 8, 12):
                raise ValueError('widget_width')
            opacity = item.get('opacity', 100)
            if type(opacity) is not int or opacity not in range(60, 101, 5):
                raise ValueError('widget_opacity')
            style = item.get('style', 'solid')
            if style not in ('solid', 'glass', 'outline'):
                raise ValueError('widget_style')
            widgets.append({'id': wid, 'kind': item['kind'], 'span': width,
                            'title': _name(item.get('title'), 36),
                            'color': _color(item.get('color')),
                            'background': _color(item.get('background')),
                            'opacity': opacity, 'style': style})
        profiles.append({'id': pid, 'name': _name(raw.get('name')) or 'Dashboard',
                         'accent': _color(raw.get('accent'), DEFAULT_COLOR),
                         'density': 'compact' if raw.get('density') == 'compact' else 'normal',
                         'widgets': widgets})
    active = _id(obj.get('activeProfile'))
    if active not in ids:
        raise ValueError('active_profile')
    return {'profiles': profiles, 'activeProfile': active}


def atomic_write(path: Path, content: bytes):
    """Replace one private file atomically; leave the previous file on failure."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, filename = tempfile.mkstemp(prefix='.profiles-', suffix='.tmp', dir=str(path.parent))
    try:
        if os.name != 'nt':
            os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'wb') as file:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        os.replace(filename, path)
    finally:
        if os.path.exists(filename):
            os.unlink(filename)


def default_document():
    """Return fresh current-format defaults without touching disk."""
    return {'activeProfile': 'p-default', 'profiles': [{'id': 'p-default',
        'name': 'My dashboard', 'accent': DEFAULT_COLOR, 'density': 'normal',
        'widgets': [{'id': 'w-default-' + str(index), 'kind': kind, 'span': span,
                     'title': '', 'color': '', 'background': '', 'opacity': 100, 'style': 'solid'}
                    for index, (kind, span) in enumerate([
                        ('score', 12), ('weapon', 4), ('economy', 8), ('stats', 12), ('bomb', 12)])]}]}


def decode_stored_document(raw):
    """Validate bounded current-format bytes, retaining no untrusted fields."""
    if len(raw) > MAX_STORE_BYTES:
        raise ValueError('Profile storage exceeds size limit')
    loaded = decode_message(raw)
    cleaned = validate_document(loaded)
    revision = loaded.get('revision', 0)
    if type(revision) is not int or revision < 0:
        raise ValueError('Invalid profile revision')
    return cleaned, revision


def read_document(path: Path):
    # Bound allocation before parsing a corrupt or unexpectedly large local file.
    with Path(path).open('rb') as file:
        raw = file.read(MAX_STORE_BYTES + 1)
    return decode_stored_document(raw)


class ProfileStore:
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
