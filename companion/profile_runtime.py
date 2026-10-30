"""Select one validated storage generation; never convert existing files at startup."""
from contextlib import contextmanager
from pathlib import Path

from companion.profile_contracts import decode_document, validate_contract
from companion.profile_publication import PublishedProfileStore
from companion.profile_protocol import PublishedProfileProtocol
from companion.profile_recovery import RecoveryError, _is_link, _read, recovery_lock
from companion.profile_store import ProfileStore, decode_stored_document


def is_target_store(store):
    return isinstance(store, PublishedProfileProtocol)


def _create_runtime_store(directory):
    directory = Path(directory).absolute()
    if any(_is_link(item) for item in (directory, *directory.parents)) or 'static' in [part.lower() for part in directory.parts]:
        raise RecoveryError('unsafe_directory')
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    with recovery_lock(directory):
        if any(directory.glob('.profiles-restore-*.pending')):
            raise RecoveryError('restore_interrupted_keep_service_stopped')
        path = directory / 'profiles.json'
        if path.exists():
            loaded = decode_document(_read(path))
            if isinstance(loaded, dict) and loaded.get('format') == 'ccs-dashboard-store':
                validate_contract(loaded, 'server')
                return PublishedProfileProtocol(PublishedProfileStore(path))
            # The historical validator rejects explicit unsupported version markers.
            return ProfileStore(path)
        if any(item.name not in ['.gitkeep', '.profiles-recovery.lock'] for item in directory.iterdir()):
            raise RecoveryError('missing_profiles_recovery_required')
        # Retain the existing cold-start behavior; target initialization is an explicit offline action.
        return ProfileStore(path)


def create_runtime_store(directory):
    try:
        return _create_runtime_store(directory)
    except (ValueError, OSError, UnicodeError):
        raise RuntimeError('Invalid, incompatible or busy profile storage. Preserve all files; stop the service and use scripts/recover_profiles.py --inspect. No reset was performed.') from None


@contextmanager
def runtime_lease(store):
    """An active ASGI service excludes offline recovery in the same filesystem environment."""
    target = is_target_store(store)
    path = store.store.path if target else store.path
    with recovery_lock(path.parent):
        if any(path.parent.glob('.profiles-restore-*.pending')):
            raise RecoveryError('restore_interrupted_keep_service_stopped')
        raw = _read(path)
        if target:
            if validate_contract(decode_document(raw), 'server') != store.data:
                raise RecoveryError('source_changed_before_start')
        else:
            data, revision = decode_stored_document(raw)
            if data != store.data or revision != store.revision:
                raise RecoveryError('source_changed_before_start')
        yield
