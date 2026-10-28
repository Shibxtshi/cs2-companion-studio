"""Explicit offline recovery with private, verified, non-rotating snapshots."""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import uuid

from companion.profile_contracts import inspect_document
from companion.profile_store import atomic_write, decode_stored_document, default_document, validate_document

BACKUP_DIRECTORY = 'profile-reset-backups'
MAX_SOURCE_BYTES = 16 * 1024 * 1024
FILES = ('profiles.json', 'profiles.json.bak')
BACKUP_ID = re.compile(r'^[a-f0-9]{32}$')
SHA256 = re.compile(r'^[a-f0-9]{64}$')


class RecoveryError(ValueError):
    """A sanitized operational code, without file contents or credentials."""
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _is_link(path):
    return path.is_symlink() or getattr(path, 'is_junction', lambda: False)()


def _directory(directory):
    directory = Path(directory).absolute()
    if '..' in directory.parts or any(part.lower() == 'static' for part in directory.parts):
        raise RecoveryError('unsafe_directory')
    if any(_is_link(parent) for parent in (directory, *directory.parents)):
        raise RecoveryError('linked_directory')
    if not directory.is_dir():
        raise RecoveryError('missing_directory')
    return directory.resolve()


def _read(path, limit=MAX_SOURCE_BYTES):
    path = Path(path)
    if _is_link(path):
        raise RecoveryError('linked_file')
    if not stat.S_ISREG(path.stat().st_mode):
        raise RecoveryError('not_regular_file')
    flags = os.O_RDONLY | getattr(os, 'O_NONBLOCK', 0) | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_BINARY', 0)
    with os.fdopen(os.open(path, flags), 'rb') as file:
        if not stat.S_ISREG(os.fstat(file.fileno()).st_mode):
            raise RecoveryError('not_regular_file')
        raw = file.read(limit + 1)
    if len(raw) > limit:
        raise RecoveryError('source_size_limit')
    return raw


def _digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _sync_directory(directory):
    if os.name != 'nt':
        fd = os.open(directory, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def _exclusive(path, content):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_BINARY', 0), 0o600)
    with os.fdopen(fd, 'wb') as file:
        file.write(content)
        file.flush()
        os.fsync(file.fileno())


@contextmanager
def recovery_lock(directory):
    """Serialize recovery tools; this does not prove that the server is stopped."""
    directory = _directory(directory)
    path = directory / '.profiles-recovery.lock'
    if _is_link(path):
        raise RecoveryError('linked_file')
    fd = os.open(path, os.O_RDWR | os.O_CREAT | getattr(os, 'O_NOFOLLOW', 0)
                 | getattr(os, 'O_BINARY', 0), 0o600)
    acquired = False
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise RecoveryError('not_regular_file')
        if os.fstat(fd).st_size == 0:
            os.write(fd, b'\0')
        os.lseek(fd, 0, os.SEEK_SET)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
        except OSError:
            raise RecoveryError('recovery_busy') from None
        yield directory
    finally:
        if acquired:
            if os.name == 'nt':
                import msvcrt
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _bundle(directory, backupId):
    if not isinstance(backupId, str) or not BACKUP_ID.fullmatch(backupId):
        raise RecoveryError('backup_id')
    parent = directory / BACKUP_DIRECTORY
    bundle = parent / backupId
    if _is_link(parent) or _is_link(bundle) or not bundle.is_dir():
        raise RecoveryError('invalid_backup_directory')
    return bundle


def _verify(directory, backupId):
    bundle = _bundle(directory, backupId)
    from companion.profile_contracts import decode_document
    try:
        manifest = decode_document(_read(bundle / 'manifest.json', 64000), 64000)
    except ValueError:
        raise RecoveryError('backup_manifest') from None
    if (not isinstance(manifest, dict) or set(manifest) != {'format', 'version', 'files'}
            or manifest['format'] != 'ccs-profile-reset-backup'
            or type(manifest['version']) is not int or manifest['version'] != 1
            or not isinstance(manifest['files'], dict)
            or 'profiles.json' not in manifest['files']
            or not set(manifest['files']).issubset(FILES)):
        raise RecoveryError('backup_manifest')
    if any(path.name not in {*FILES, 'manifest.json', 'reset-intent.json'} for path in bundle.iterdir()):
        raise RecoveryError('backup_manifest')
    for name, entry in manifest['files'].items():
        if (not isinstance(entry, dict) or set(entry) != {'sha256', 'size'}
                or type(entry['size']) is not int or not 0 <= entry['size'] <= MAX_SOURCE_BYTES
                or not isinstance(entry['sha256'], str) or not SHA256.fullmatch(entry['sha256'])):
            raise RecoveryError('backup_manifest')
        raw = _read(bundle / name)
        if len(raw) != entry['size'] or _digest(raw) != entry['sha256']:
            raise RecoveryError('backup_integrity')
    return bundle, manifest


def _matches_source(directory, manifest):
    for name in FILES:
        path = directory / name
        entry = manifest['files'].get(name)
        if entry is None:
            if path.exists() or _is_link(path):
                raise RecoveryError('source_changed')
        elif not path.exists() or _digest(_read(path)) != entry['sha256']:
            raise RecoveryError('source_changed')


def _prepare(directory):
    parent = directory / BACKUP_DIRECTORY
    if _is_link(parent):
        raise RecoveryError('linked_directory')
    parent.mkdir(mode=0o700, exist_ok=True)
    backupId = uuid.uuid4().hex
    bundle = parent / backupId
    bundle.mkdir(mode=0o700)  # Exclusive: a previous snapshot is never overwritten.
    manifest = {'format': 'ccs-profile-reset-backup', 'version': 1, 'files': {}}
    for name in FILES:
        path = directory / name
        if name != 'profiles.json' and not path.exists() and not _is_link(path):
            continue
        raw = _read(path)
        _exclusive(bundle / name, raw)
        manifest['files'][name] = {'size': len(raw), 'sha256': _digest(raw)}
    _exclusive(bundle / 'manifest.json', json.dumps(manifest, sort_keys=True).encode())
    _sync_directory(bundle)
    _sync_directory(parent)
    _sync_directory(directory)
    _verify(directory, backupId)
    _matches_source(directory, manifest)
    return backupId


def prepare_reset(directory):
    with recovery_lock(directory) as directory:
        return _prepare(directory)


def verify_backup(directory, backupId):
    directory = _directory(directory)
    _, manifest = _verify(directory, backupId)
    return manifest


def _install(path, target, original, validator=None):
    try:
        atomic_write(path, target)
        _sync_directory(path.parent)
        installed = _read(path)
        if installed != target:
            raise RecoveryError('verification_failed')
        if validator:
            validator(installed)
    except (OSError, ValueError, UnicodeError):
        if original is not None:
            try:
                if _read(path) != original:
                    atomic_write(path, original)
                    _sync_directory(path.parent)
                    if _read(path) != original:
                        raise RecoveryError('rollback_required')
            except (OSError, ValueError):
                raise RecoveryError('rollback_required') from None
        raise RecoveryError('write_failed') from None


def reset_profiles(directory, backupId, confirm):
    """Reset only to the CURRENT schema, after a verified snapshot and explicit consent."""
    with recovery_lock(directory) as directory:
        bundle, manifest = _verify(directory, backupId)
        _matches_source(directory, manifest)
        if not confirm('RESET ' + backupId):
            return False
        # Consent may take time: reject changes made while the operator was deciding.
        _verify(directory, backupId)
        _matches_source(directory, manifest)
        target = json.dumps({**validate_document(default_document()), 'revision': 1},
                            ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        decode_stored_document(target)
        intent = {'format': 'ccs-profile-reset-intent', 'version': 1, 'targetSha256': _digest(target)}
        intentBytes = json.dumps(intent, sort_keys=True).encode()
        intentPath = bundle / 'reset-intent.json'
        if intentPath.exists():
            if _read(intentPath, 64000) != intentBytes:
                raise RecoveryError('reset_intent')
        else:
            _exclusive(intentPath, intentBytes)
            _sync_directory(bundle)
        _install(directory / 'profiles.json', target, _read(bundle / 'profiles.json'), decode_stored_document)
        return True


def reset_state(directory, backupId):
    directory = _directory(directory)
    bundle, manifest = _verify(directory, backupId)
    current = directory / 'profiles.json'
    if not current.exists():
        return 'missing'
    digest = _digest(_read(current))
    intentPath = bundle / 'reset-intent.json'
    if intentPath.exists():
        from companion.profile_contracts import decode_document
        intent = decode_document(_read(intentPath, 64000), 64000)
        if (not isinstance(intent, dict) or set(intent) != {'format', 'version', 'targetSha256'}
                or intent['format'] != 'ccs-profile-reset-intent'
                or type(intent['version']) is not int or intent['version'] != 1
                or not isinstance(intent['targetSha256'], str) or not SHA256.fullmatch(intent['targetSha256'])):
            raise RecoveryError('reset_intent')
        if digest == intent['targetSha256']:
            decode_stored_document(_read(current))
            return 'applied'
    return 'prepared' if digest == manifest['files']['profiles.json']['sha256'] else 'changed'


def restore_reset(directory, backupId, confirm):
    """Restore exact old bytes, even incompatible bytes; preserve the current file first."""
    with recovery_lock(directory) as directory:
        bundle, _ = _verify(directory, backupId)
        target = _read(bundle / 'profiles.json')
        current = directory / 'profiles.json'
        safetyId = _prepare(directory) if current.exists() else None
        safety = _verify(directory, safetyId)[1] if safetyId else None
        if not confirm('RESTORE ' + backupId):
            return False, safetyId
        _verify(directory, backupId)
        if safety:
            _matches_source(directory, safety)
            original = _read(directory / BACKUP_DIRECTORY / safetyId / 'profiles.json')
        else:
            if current.exists() or _is_link(current):
                raise RecoveryError('source_changed')
            original = None
        _install(current, target, original)
        return True, safetyId


def restore_legacy(directory):
    """Keep the existing validated .bak restore entry point and corrupt-file preservation."""
    with recovery_lock(directory) as directory:
        backup = _read(directory / 'profiles.json.bak')
        decode_stored_document(backup)
        current = directory / 'profiles.json'
        original = _read(current) if current.exists() else None
        if original is not None:
            preserved = directory / ('profiles.json.corrupt-' + uuid.uuid4().hex)
            _exclusive(preserved, original)
            if _read(preserved) != original:
                raise RecoveryError('backup_integrity')
            _sync_directory(directory)
        _install(current, backup, original, decode_stored_document)


def inspect_current(directory):
    directory = _directory(directory)
    current = directory / 'profiles.json'
    return inspect_document(_read(current)) if current.exists() else {'status': 'missing', 'kind': None}
