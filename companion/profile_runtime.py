"""One target runtime; create defaults only in a genuinely empty private directory."""
from contextlib import contextmanager
import os
from pathlib import Path
import uuid

from companion.profile_contracts import decode_document, encode_document, new_server_document, validate_contract
from companion.profile_publication import PublishedProfileStore
from companion.profile_protocol import PublishedProfileProtocol
from companion.profile_recovery import RecoveryError, _is_link, _read, _sync_directory, recovery_lock
from companion.profile_store import atomic_write


def _create_runtime_store(directory):
    directory = Path(directory).absolute()
    if any(_is_link(item) for item in (directory, *directory.parents)) or 'static' in [part.lower() for part in directory.parts]:
        raise RecoveryError('unsafe_directory')
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    with recovery_lock(directory):
        if any(directory.glob('.profiles-restore-*.pending')):
            raise RecoveryError('restore_interrupted_keep_service_stopped')
        path = directory / 'profiles.json'
        if not path.exists():
            allowed = {'.gitkeep', '.profiles-recovery.lock'}
            marker = directory / '.gitkeep'
            if marker.exists() or _is_link(marker):
                if _is_link(marker) or not marker.is_file() or marker.stat().st_size:
                    raise RecoveryError('invalid_empty_directory_marker')
            if any(item.name not in allowed for item in directory.iterdir()):
                raise RecoveryError('missing_profiles_recovery_required')
            # Publish fully written bytes without replacing a concurrently created file.
            staging = directory / ('.profiles-initialize-' + uuid.uuid4().hex)
            atomic_write(staging, encode_document(new_server_document()))
            try:
                if any(item.name not in allowed | {staging.name} for item in directory.iterdir()):
                    raise RecoveryError('source_changed_before_initialization')
                try:
                    os.link(staging, path)
                except FileExistsError:
                    raise RecoveryError('source_changed_before_initialization') from None
                except OSError:
                    raise RecoveryError('atomic_initialization_unavailable') from None
                _sync_directory(directory)
            finally:
                staging.unlink()
        loaded = decode_document(_read(path))
        if isinstance(loaded, dict) and 'format' not in loaded:
            raise RecoveryError('historical_profiles_require_offline_activation')
        validate_contract(loaded, 'server')
        return PublishedProfileProtocol(PublishedProfileStore(path))


def create_runtime_store(directory):
    try:
        return _create_runtime_store(directory)
    except (ValueError, OSError, UnicodeError) as error:
        reason = error.code if isinstance(error, RecoveryError) else 'invalid_or_unreadable_document'
        raise RuntimeError(f'Profile storage refused ({reason}). ' + 'Invalid, historical, incompatible or busy profile storage. Preserve all files; stop the service and use scripts/recover_profiles.py --inspect. Historical profiles require explicitly confirmed offline activation or their compatible archived application. No existing document was reset or converted.') from None


@contextmanager
def runtime_lease(store):
    """An active ASGI service excludes offline recovery in the same filesystem environment."""
    path = store.store.path
    with recovery_lock(path.parent):
        if any(path.parent.glob('.profiles-restore-*.pending')):
            raise RecoveryError('restore_interrupted_keep_service_stopped')
        if validate_contract(decode_document(_read(path)), 'server') != store.data:
            raise RecoveryError('source_changed_before_start')
        yield
