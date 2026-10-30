"""Explicit offline target activation; immutable verified snapshots precede every replacement."""
from pathlib import Path
import re
import uuid

from companion.profile_contracts import decode_document, encode_document, validate_contract
from companion.profile_recovery import (
    RecoveryError, BACKUP_ID, _directory, _read, _digest, _exclusive,
    _sync_directory, _prepare, _verify, _matches_source, _install, recovery_lock,
)
from companion.profile_store import decode_stored_document, atomic_write

APPLICATION_REVISION = re.compile(r'^[a-f0-9]{40}$')


def target_document():
    """Fresh target defaults; never interpret historical geometry as X/Y."""
    return validate_contract({'format': 'ccs-dashboard-store', 'version': 1,
        'storeId': uuid.uuid4().hex, 'catalogRevision': 1, 'profiles': [{
            'id': uuid.uuid4().hex, 'name': 'My dashboard', 'revision': 1,
            'configuration': {'theme': 'tactical-blue',
                'appearance': {'accent': '', 'background': '', 'density': 'normal'},
                'navigation': {'mode': 'compact', 'floatingButton': True},
                'fullscreen': {'showConnectionStatus': True},
                'layout': {'columns': 24, 'widgets': []}}}], 'tombstones': [], 'receipts': []}, 'server')


def _paths(directory, backupId):
    if not isinstance(backupId, str) or not BACKUP_ID.fullmatch(backupId):
        raise RecoveryError('backup_id')
    prefix = directory / ('.profiles-activation-' + backupId)
    return Path(str(prefix) + '.json'), Path(str(prefix) + '.candidate')


def _load(directory, backupId):
    bundle, manifest = _verify(directory, backupId)
    metaPath, candidatePath = _paths(directory, backupId)
    meta = decode_document(_read(metaPath, 64000), 64000)
    fields = {'format', 'version', 'backupId', 'applicationRevision', 'targetSha256', 'storeId'}
    if (not isinstance(meta, dict) or set(meta) != fields or meta['format'] != 'ccs-profile-activation'
            or type(meta['version']) is not int or meta['version'] not in (1, 2) or meta['backupId'] != backupId
            or not isinstance(meta['applicationRevision'], str) or not APPLICATION_REVISION.fullmatch(meta['applicationRevision'])):
        raise RecoveryError('activation_manifest')
    candidate = _read(candidatePath)
    target = validate_contract(decode_document(candidate), 'server')
    if _digest(candidate) != meta['targetSha256'] or target['storeId'] != meta['storeId']:
        raise RecoveryError('activation_integrity')
    decode_stored_document(_read(bundle / 'profiles.json'))
    return bundle, manifest, meta, candidate


def prepare_activation(directory, applicationRevision):
    if not isinstance(applicationRevision, str) or not APPLICATION_REVISION.fullmatch(applicationRevision):
        raise RecoveryError('application_revision')
    with recovery_lock(directory) as directory:
        if any(directory.glob('.profiles-restore-*.pending')):
            raise RecoveryError('restore_interrupted_keep_service_stopped')
        decode_stored_document(_read(directory / 'profiles.json'))
        if (directory / 'profiles.json.bak').exists():
            decode_stored_document(_read(directory / 'profiles.json.bak'))
        backupId = _prepare(directory)
        _, manifest = _verify(directory, backupId)
        candidate = encode_document(target_document())
        metaPath, candidatePath = _paths(directory, backupId)
        _exclusive(candidatePath, candidate)
        target = decode_document(candidate)
        meta = {'format': 'ccs-profile-activation', 'version': 2, 'backupId': backupId,
                'applicationRevision': applicationRevision, 'targetSha256': _digest(candidate), 'storeId': target['storeId']}
        _exclusive(metaPath, encode_document(meta))
        _sync_directory(directory)
        _load(directory, backupId)
        _matches_source(directory, manifest)
        return backupId


def activation_state(directory, backupId):
    directory = _directory(directory)
    _, manifest, meta, _ = _load(directory, backupId)
    if (directory / ('.profiles-restore-' + backupId + '.pending')).exists():
        return 'restore_interrupted'
    path = directory / 'profiles.json'
    if not path.exists():
        return 'missing'
    raw = _read(path)
    if _digest(raw) == meta['targetSha256']:
        return 'activated'
    if _digest(raw) == manifest['files']['profiles.json']['sha256']:
        try:
            _matches_source(directory, manifest)
            return 'prepared_or_restored'
        except RecoveryError:
            return 'changed'
    try:
        current = validate_contract(decode_document(raw), 'server')
        if current['storeId'] == meta['storeId']:
            return 'published'
    except ValueError:
        pass
    return 'changed'


def activate_profiles(directory, backupId, confirm):
    with recovery_lock(directory) as directory:
        if any(directory.glob('.profiles-restore-*.pending')):
            raise RecoveryError('restore_interrupted_keep_service_stopped')
        bundle, manifest, meta, candidate = _load(directory, backupId)
        if meta['version'] != 2:
            raise RecoveryError('activation_prepare_again')
        attempted = directory / ('.profiles-activation-' + backupId + '.attempted')
        if attempted.exists():
            raise RecoveryError('activation_already_attempted')
        _matches_source(directory, manifest)
        if not confirm('ACTIVATE ' + backupId):
            return False
        _load(directory, backupId)
        _matches_source(directory, manifest)
        # Consume before installation: a failed/interrupted attempt requires a fresh generation too.
        _exclusive(attempted, encode_document({'backupId': backupId, 'storeId': meta['storeId']}))
        _sync_directory(directory)
        _install(directory / 'profiles.json', candidate, _read(bundle / 'profiles.json'),
                 lambda raw: validate_contract(decode_document(raw), 'server'))
        return True


def restore_activation(directory, backupId, confirm):
    with recovery_lock(directory) as directory:
        if any(path.name != '.profiles-restore-' + backupId + '.pending'
               for path in directory.glob('.profiles-restore-*.pending')):
            raise RecoveryError('another_restore_interrupted')
        bundle, manifest, meta, _ = _load(directory, backupId)
        current = directory / 'profiles.json'
        safetyId = _prepare(directory) if current.exists() else None
        safety = _verify(directory, safetyId)[1] if safetyId else None
        state = activation_state(directory, backupId)
        phrase = ('RESTORE AFTER PUBLICATION ' if state == 'published' else 'RESTORE ACTIVATION ') + backupId
        if not confirm(phrase):
            return False, safetyId, meta['applicationRevision']
        _load(directory, backupId)
        if safety:
            _matches_source(directory, safety)
        elif current.exists():
            raise RecoveryError('source_changed')
        marker = directory / ('.profiles-restore-' + backupId + '.pending')
        if not marker.exists():
            _exclusive(marker, encode_document({'backupId': backupId, 'safetyId': safetyId}))
        _sync_directory(directory)
        # The two filenames are not a filesystem transaction. A retained marker blocks startup on interruption.
        for name in ['profiles.json', 'profiles.json.bak']:
            path = directory / name
            if name in manifest['files']:
                atomic_write(path, _read(bundle / name))
            elif path.exists():
                path.unlink()
            _sync_directory(directory)
        _matches_source(directory, manifest)
        marker.unlink()
        _sync_directory(directory)
        return True, safetyId, meta['applicationRevision']


def initialize_target(directory, confirm):
    """Explicit new-install creation only; an existing file or recovery artifact forbids initialization."""
    with recovery_lock(directory) as directory:
        allowed = {'.gitkeep', '.profiles-recovery.lock'}
        if any(item.name not in allowed for item in directory.iterdir()):
            raise RecoveryError('initialization_requires_empty_directory')
        if not confirm('INITIALIZE TARGET'):
            return False
        if any(item.name not in allowed for item in directory.iterdir()):
            raise RecoveryError('source_changed')
        packed = encode_document(target_document())
        _exclusive(directory / 'profiles.json', packed)
        _sync_directory(directory)
        validate_contract(decode_document(_read(directory / 'profiles.json')), 'server')
        return True


def restore_target_backup(directory, confirm):
    """Restore validated target backup data into a new generation, never replaying old intents."""
    with recovery_lock(directory) as directory:
        if any(directory.glob('.profiles-restore-*.pending')):
            raise RecoveryError('restore_interrupted_keep_service_stopped')
        target = validate_contract(decode_document(_read(directory / 'profiles.json.bak')), 'server')
        if not (directory / 'profiles.json').is_file():
            raise RecoveryError('missing_source_preserve_recovery_required')
        safetyId = _prepare(directory)
        _, manifest = _verify(directory, safetyId)
        if not confirm('RESTORE TARGET ' + safetyId):
            return False, safetyId
        _matches_source(directory, manifest)
        target['storeId'] = uuid.uuid4().hex
        target['receipts'] = []
        candidate = encode_document(validate_contract(target, 'server'))
        _install(directory / 'profiles.json', candidate, _read(directory / 'profiles.json'),
                 lambda raw: validate_contract(decode_document(raw), 'server'))
        return True, safetyId
