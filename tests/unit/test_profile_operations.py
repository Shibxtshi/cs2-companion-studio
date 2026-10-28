"""Pure future concurrency/idempotency contracts; no live store is activated."""
import copy

import pytest

from companion.profile_contracts import (ContractError, MAX_REVISION, MAX_TOMBSTONES,
    decode_document, default_configuration, encode_document, new_server_document)
from companion.profile_operations import apply_operation


def operation(store, kind='update', profileId='p-default', revision=1, number=1, name='Updated'):
    result = {'format': 'ccs-dashboard-operation', 'version': 1, 'storeId': store['storeId'],
              'operationId': f'{number:032x}', 'profileId': profileId, 'kind': kind,
              'expectedRevision': 0 if kind == 'create' else revision}
    if kind != 'delete':
        result['profile'] = {'name': name, 'configuration': default_configuration()}
    return result


def test_different_profiles_do_not_conflict():
    store = new_server_document()
    store, _ = apply_operation(store, operation(store, 'create', 'second'))
    before = copy.deepcopy(store)
    first, _ = apply_operation(store, operation(store, number=2))
    both, result = apply_operation(first, operation(before, profileId='second', number=3))
    assert [profile['revision'] for profile in both['profiles']] == [2, 2]
    assert before['profiles'][0]['revision'] == 1
    assert result['result']['catalogRevision'] == 4


def test_same_profile_conflict_never_mutates_the_document():
    store = new_server_document()
    changed, _ = apply_operation(store, operation(store))
    before = copy.deepcopy(changed)
    with pytest.raises(ContractError, match='revision_conflict'):
        apply_operation(changed, operation(store, number=2))
    assert changed == before
    assert store['profiles'][0]['revision'] == 1


def test_lost_reply_retry_is_idempotent_even_after_reload():
    store = new_server_document()
    command = operation(store)
    changed, first = apply_operation(store, command)
    restarted = decode_document(encode_document(changed))
    repeated, second = apply_operation(restarted, command)
    assert repeated == changed
    assert first['result'] == second['result']
    assert second['replayed'] and not first['replayed']
    command['profile']['name'] = 'Different request'
    with pytest.raises(ContractError, match='operation_id_reused'):
        apply_operation(restarted, command)


def test_deleted_profile_cannot_be_overwritten_or_reused():
    store = new_server_document()
    store, _ = apply_operation(store, operation(store, 'create', 'second'))
    editing = operation(store, profileId='second', number=3)
    delete = operation(store, 'delete', 'second', number=2)
    deleted, receipt = apply_operation(store, delete)
    assert deleted['tombstones'] == [{'id': 'second', 'revision': 2}]
    assert apply_operation(deleted, delete)[1]['replayed']
    for command in (editing, operation(store, 'create', 'second', number=4)):
        with pytest.raises(ContractError, match='profile_deleted'):
            apply_operation(deleted, command)
    assert receipt['result']['kind'] == 'delete'


@pytest.mark.parametrize('case,code', [('last', 'last_profile'), ('exists', 'profile_exists'),
                                     ('missing', 'profile_missing'), ('store', 'store_changed'),
                                     ('invalid', 'invalid_document'), ('overflow', 'revision_limit')])
def test_refused_operations_leave_inputs_intact(case, code):
    store = new_server_document()
    command = operation(store)
    if case == 'last':
        command = operation(store, 'delete')
    elif case == 'exists':
        command = operation(store, 'create')
    elif case == 'missing':
        command['profileId'] = 'missing'
    elif case == 'store':
        command['storeId'] = '0' * 32
    elif case == 'invalid':
        command['profile']['configuration']['theme'] = 'unsafe'
    else:
        store['catalogRevision'] = store['profiles'][0]['revision'] = MAX_REVISION
        command['expectedRevision'] = MAX_REVISION
    before = copy.deepcopy(store)
    with pytest.raises(ContractError, match=code):
        apply_operation(store, command)
    assert store == before


def test_receipt_expiry_cannot_repeat_an_old_update():
    store = new_server_document()
    original = operation(store)
    for index in range(70):
        store, _ = apply_operation(store, operation(store, revision=index + 1, number=index + 1))
    assert len(store['receipts']) == 64
    with pytest.raises(ContractError, match='revision_conflict'):
        apply_operation(store, original)


def test_tombstone_capacity_is_explicit_not_silently_pruned():
    store = new_server_document()
    store, _ = apply_operation(store, operation(store, 'create', 'second'))
    store['catalogRevision'] = 4096
    store['tombstones'] = [{'id': 'deleted-' + str(index), 'revision': 2} for index in range(MAX_TOMBSTONES)]
    before = copy.deepcopy(store)
    with pytest.raises(ContractError, match='tombstone_limit'):
        apply_operation(store, operation(store, 'delete', 'second', number=2))
    assert store == before
