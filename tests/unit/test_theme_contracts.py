"""All published theme choices use the unchanged v1 contracts and recovery path."""
import copy
import uuid

import pytest

from companion.profile_contracts import THEMES, ContractError, encode_document, new_server_document, validate_contract
from companion.profile_publication import PublishedProfileStore
from companion.profile_activation import restore_target_backup


@pytest.mark.parametrize('theme', THEMES)
def test_theme_envelopes_publication_restart_and_recovery(tmp_path, theme):
    original = new_server_document()
    path = tmp_path / 'profiles.json'
    path.write_bytes(encode_document(original))
    content = {key: copy.deepcopy(original['profiles'][0][key]) for key in ('name', 'configuration')}
    content['configuration']['theme'] = theme
    exported = {'format': 'ccs-dashboard-export', 'version': 1, **content}
    draft = {'format': 'ccs-dashboard-draft', 'version': 1, **content,
             'storeId': original['storeId'], 'profileId': 'p-default', 'draftId': 'a' * 32,
             'baseRevision': 1, 'localRevision': 2, 'updatedAt': 1700000000000}
    assert validate_contract(exported, 'export') == exported
    assert validate_contract(draft, 'draft') == draft
    store = PublishedProfileStore(path)
    for revision in (1, 2):
        operation = {'format': 'ccs-dashboard-operation', 'version': 1,
                     'storeId': original['storeId'], 'operationId': uuid.uuid4().hex,
                     'profileId': 'p-default', 'kind': 'update', 'expectedRevision': revision, 'profile': content}
        assert store.publish(operation)['result']['revision'] == revision + 1
    reloaded = PublishedProfileStore(path).data
    assert reloaded['profiles'][0]['configuration']['theme'] == theme
    assert reloaded['format'] == 'ccs-dashboard-store' and reloaded['version'] == 1
    assert reloaded['storeId'] == original['storeId']
    restored, _snapshot = restore_target_backup(tmp_path, lambda expected: expected.startswith('RESTORE TARGET '))
    assert restored
    recovered = PublishedProfileStore(path).data
    assert recovered['profiles'][0]['configuration']['theme'] == theme
    assert recovered['storeId'] != original['storeId']


def test_unknown_theme_does_not_change_published_bytes(tmp_path):
    original = new_server_document()
    path = tmp_path / 'profiles.json'
    raw = encode_document(original)
    path.write_bytes(raw)
    store = PublishedProfileStore(path)
    content = {key: copy.deepcopy(original['profiles'][0][key]) for key in ('name', 'configuration')}
    content['configuration']['theme'] = 'unknown-theme'
    with pytest.raises(ContractError, match='invalid_document'):
        store.publish({'format': 'ccs-dashboard-operation', 'version': 1, 'storeId': original['storeId'],
                       'operationId': 'b' * 32, 'profileId': 'p-default', 'kind': 'update',
                       'expectedRevision': 1, 'profile': content})
    assert store.data == original
    assert path.read_bytes() == raw
