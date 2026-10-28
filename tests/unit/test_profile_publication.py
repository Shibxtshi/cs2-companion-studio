"""Atomic target publication uses only explicitly provisioned temporary files."""
import copy
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import uuid

import pytest
from companion import profile_publication as publication
from companion.profile_contracts import ContractError, encode_document, new_server_document, validate_contract
from companion.profile_operations import apply_operation


def operation(document, kind='update', profileId='p-default', expected=1):
    result = {'format': 'ccs-dashboard-operation', 'version': 1, 'storeId': document['storeId'],
              'operationId': uuid.uuid4().hex, 'kind': kind, 'profileId': profileId, 'expectedRevision': expected}
    if kind != 'delete':
        profile = document['profiles'][0]
        result['profile'] = {'name': 'Published synthetic', 'configuration': copy.deepcopy(profile['configuration'])}
    return result


@pytest.fixture
def store(tmp_path):
    document = new_server_document()
    second = operation(document, 'create', 'p-second', 0)
    document, _ = apply_operation(document, second)
    path = tmp_path / 'profiles.json'
    path.write_bytes(encode_document(document))
    return publication.PublishedProfileStore(path)


def test_no_implicit_initialization_or_conversion(tmp_path):
    path = tmp_path / 'profiles.json'
    with pytest.raises(FileNotFoundError):
        publication.PublishedProfileStore(path)
    assert not path.exists()
    path.write_text('{"profiles": [], "activeProfile": "old"}')
    before = path.read_bytes()
    with pytest.raises(ValueError):
        publication.PublishedProfileStore(path)
    assert path.read_bytes() == before


def test_create_update_delete_receipts_and_restart(store):
    before = store.data
    created = operation(before, 'create', 'p-created', 0)
    first = store.publish(created)
    assert first['result']['revision'] == 1
    assert first['result']['kind'] == 'create'
    changed = operation(store.data, profileId='p-created')
    receipt = store.publish(changed)
    assert receipt['result']['revision'] == 2
    loaded = publication.PublishedProfileStore(store.path)
    persisted = loaded.path.read_bytes()
    assert loaded.publish(changed) == {**receipt, 'replayed': True}
    assert loaded.path.read_bytes() == persisted
    deleted = operation(loaded.data, 'delete', 'p-created', 2)
    assert loaded.publish(deleted)['result']['revision'] == 3
    assert any(item['id'] == 'p-created' for item in loaded.data['tombstones'])
    with pytest.raises(ContractError, match='profile_deleted'):
        loaded.publish(operation(loaded.data, 'create', 'p-created', 0))
    validate_contract(json.loads(loaded.path.with_suffix('.json.bak').read_bytes()), 'server')


def test_per_profile_revision_concurrency(store):
    commands = [operation(store.data, profileId=profileId) for profileId in ('p-default', 'p-second')]
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(store.publish, commands))
    assert all(result['result']['revision'] == 2 for result in results)
    assert [profile['revision'] for profile in store.data['profiles']] == [2, 2]
    same = [operation(store.data, expected=2) for _ in range(2)]
    def attempt(command):
        try:
            return store.publish(command)
        except ContractError as error:
            return error.code
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(attempt, same))
    assert results.count('revision_conflict') == 1
    assert store.data['profiles'][0]['revision'] == 3


@pytest.mark.parametrize('stage', ['backup', 'main'])
def test_disk_failure_changes_neither_main_nor_memory(store, monkeypatch, stage):
    before = store.data
    raw = store.path.read_bytes()
    write = publication.atomic_write
    def fail(path, content):
        if (path.suffix == '.bak') == (stage == 'backup'):
            raise OSError('synthetic disk failure')
        write(path, content)
    monkeypatch.setattr(publication, 'atomic_write', fail)
    with pytest.raises(OSError):
        store.publish(operation(before))
    assert store.data == before
    assert store.path.read_bytes() == raw
    assert publication.PublishedProfileStore(store.path).data == before


def test_crash_after_replace_is_reconciled_from_persisted_receipt(store, monkeypatch):
    command = operation(store.data)
    write = publication.atomic_write
    def crash(path, content):
        write(path, content)
        if path == store.path:
            raise KeyboardInterrupt('synthetic process death')
    with monkeypatch.context() as patch:
        patch.setattr(publication, 'atomic_write', crash)
        with pytest.raises(KeyboardInterrupt):
            store.publish(command)
    restarted = publication.PublishedProfileStore(store.path)
    assert restarted.publish(command)['replayed']
    assert restarted.data['profiles'][0]['revision'] == 2


def test_invalid_stale_generation_and_reused_operation_preserve_state(store):
    command = operation(store.data)
    store.publish(command)
    before, raw = store.data, store.path.read_bytes()
    cases = [(copy.deepcopy(command), 'operation_id_reused'),
             (operation(before), 'revision_conflict'),
             (operation(before, 'delete', 'p-missing'), 'profile_missing')]
    cases[0][0]['profile']['name'] = 'Different payload'
    wrongGeneration = operation(before, expected=2)
    wrongGeneration['storeId'] = '0' * 32
    cases.append((wrongGeneration, 'store_changed'))
    invalid = operation(before, expected=2)
    invalid['profile']['configuration']['layout']['columns'] = -1
    cases.append((invalid, 'invalid_document'))
    for candidate, code in cases:
        with pytest.raises(ContractError, match=code):
            store.publish(candidate)
        assert store.data == before
        assert store.path.read_bytes() == raw


def test_evicted_receipt_never_reapplies_old_command(store):
    first = operation(store.data)
    store.publish(first)
    for revision in range(2, 67):
        store.publish(operation(store.data, expected=revision))
    before = store.data
    assert len(before['receipts']) == 64
    with pytest.raises(ContractError, match='revision_conflict'):
        publication.PublishedProfileStore(store.path).publish(first)
    assert store.data == before


def test_context_is_public_stable_and_generation_scoped(store):
    catalog = store.catalog()
    assert catalog['accessId'] == publication.access_id(catalog['storeId'])
    assert publication.PublishedProfileStore(store.path).catalog()['accessId'] == catalog['accessId']
    other = new_server_document()
    assert publication.access_id(other['storeId']) != catalog['accessId']
    catalog['profiles'][0]['name'] = 'External mutation'
    assert store.data['profiles'][0]['name'] != 'External mutation'


def test_target_backup_can_be_preserved_and_restored_offline(store):
    from companion.profile_recovery import prepare_reset, restore_reset
    old = store.path.read_bytes()
    backupId = prepare_reset(store.path.parent)
    store.publish(operation(store.data))
    restored, safetyId = restore_reset(store.path.parent, backupId, lambda _: True)
    assert restored and safetyId
    assert store.path.read_bytes() == old
    assert publication.PublishedProfileStore(store.path).data['profiles'][0]['revision'] == 1


def test_profile_limits_and_last_profile_remain_enforced(store):
    for index in range(10):
        store.publish(operation(store.data, 'create', 'p-extra-' + str(index), 0))
    before = store.data
    with pytest.raises(ContractError, match='profile_limit'):
        store.publish(operation(before, 'create', 'p-too-many', 0))
    assert store.data == before
    for profile in list(store.data['profiles'])[1:]:
        store.publish(operation(store.data, 'delete', profile['id'], profile['revision']))
    with pytest.raises(ContractError, match='last_profile'):
        store.publish(operation(store.data, 'delete'))


def test_readers_only_observe_complete_committed_documents(store):
    def writer():
        for _ in range(10):
            current = store.data
            store.publish(operation(current, expected=current['profiles'][0]['revision']))
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(writer)
        for _ in range(50):
            validate_contract(store.data, 'server')
            from companion.profile_wire import ProfileCatalog
            ProfileCatalog.model_validate(store.catalog())
        future.result()


def test_explicit_generation_renewal_invalidates_even_matching_old_revisions(store):
    command = operation(store.data)
    renewed = publication.renewed_generation(store.data)
    assert renewed['profiles'] == store.data['profiles']
    assert renewed['receipts'] == []
    store.path.write_bytes(encode_document(renewed))
    with pytest.raises(ContractError, match='store_changed'):
        publication.PublishedProfileStore(store.path).publish(command)
