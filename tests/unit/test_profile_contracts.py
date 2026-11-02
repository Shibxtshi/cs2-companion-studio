"""Strict future contracts, using synthetic configurations only."""
import copy
import json

import pytest

from companion import profile_contracts as contracts
from companion.profile_store import default_document
from tests.historical_profiles import HistoricalProfileFixture


def widget(**changes):
    return {'id': 'widget-a', 'kind': 'health', 'x': 0, 'y': 0, 'width': 6, 'height': 2,
            'variant': 'standard', 'style': 'solid', 'title': '', 'color': '',
            'background': '', 'opacity': 100, **changes}


def target():
    store = contracts.new_server_document()
    store['profiles'][0]['configuration']['layout']['widgets'] = [widget()]
    return store


def locate(document, path):
    value = document
    for part in path:
        value = value[part]
    return value


PROFILE = ('profiles', 0)
CONFIG = (*PROFILE, 'configuration')
LAYOUT = (*CONFIG, 'layout')
WIDGET = (*LAYOUT, 'widgets', 0)


def test_default_contract_and_separate_envelopes():
    store = target()
    assert contracts.validate_contract(store, 'server') == store
    profile = store['profiles'][0]
    payload = {key: profile[key] for key in ('name', 'configuration')}
    exported = {'format': 'ccs-dashboard-export', 'version': 1, **payload}
    draft = {'format': 'ccs-dashboard-draft', 'version': 1, **payload,
             'storeId': store['storeId'], 'profileId': profile['id'], 'draftId': 'a' * 32,
             'baseRevision': profile['revision'], 'localRevision': 2, 'updatedAt': 1700000000000}
    assert contracts.validate_contract(exported, 'export') == exported
    assert contracts.validate_contract(draft, 'draft') == draft
    assert profile['configuration']['layout']['columns'] == 24
    assert profile['configuration']['theme'] == 'tactical-blue'
    assert profile['configuration']['navigation']['mode'] == 'compact'
    assert 'activeProfile' not in store
    for kind, value in (('server', exported), ('export', store), ('draft', exported)):
        with pytest.raises(contracts.ContractError):
            contracts.validate_contract(value, kind)


@pytest.mark.parametrize('path', [(), PROFILE, CONFIG, (*CONFIG, 'appearance'),
                                (*CONFIG, 'navigation'), (*CONFIG, 'fullscreen'), LAYOUT, WIDGET])
def test_unknown_fields_are_not_silently_discarded(path):
    store = target()
    locate(store, path)['PIN_PRIVATE_SENTINEL'] = 'never-echo-this-value'
    with pytest.raises(contracts.ContractError) as error:
        contracts.validate_contract(store, 'server')
    assert str(error.value) == 'invalid_document'
    assert 'SENTINEL' not in str(error.value)
    assert 'never-echo' not in str(error.value)


@pytest.mark.parametrize('path,key', [((), 'format'), ((), 'version'), ((), 'storeId'),
    ((), 'catalogRevision'), (PROFILE, 'id'), (PROFILE, 'revision'), (PROFILE, 'name'),
    (CONFIG, 'theme'), (CONFIG, 'appearance'), (CONFIG, 'navigation'), (CONFIG, 'fullscreen'),
    (LAYOUT, 'columns'), (LAYOUT, 'widgets'), (WIDGET, 'x'), (WIDGET, 'height'), (WIDGET, 'variant')])
def test_required_fields(path, key):
    store = target()
    del locate(store, path)[key]
    with pytest.raises(contracts.ContractError):
        contracts.validate_contract(store, 'server')


@pytest.mark.parametrize('path,key,value', [
    ((), 'version', True), ((), 'version', 0), ((), 'version', 2),
    ((), 'catalogRevision', True), ((), 'catalogRevision', 2 ** 53),
    (PROFILE, 'revision', 0), (PROFILE, 'revision', 1.0), (PROFILE, 'name', '  '),
    (PROFILE, 'name', 'bad\nname'), (PROFILE, 'name', 'a' * 33),
    (CONFIG, 'theme', 'unknown'), ((*CONFIG, 'navigation'), 'mode', 'broadcast'),
    ((*CONFIG, 'navigation'), 'floatingButton', 1),
    ((*CONFIG, 'fullscreen'), 'showConnectionStatus', 'true'),
    (LAYOUT, 'columns', 0), (LAYOUT, 'columns', 65), (LAYOUT, 'columns', 24.0),
    (WIDGET, 'x', -1), (WIDGET, 'x', 24), (WIDGET, 'x', True), (WIDGET, 'x', .5),
    (WIDGET, 'width', 0), (WIDGET, 'width', 25), (WIDGET, 'height', 0),
    (WIDGET, 'y', -1), (WIDGET, 'y', 4096), (WIDGET, 'height', 4097),
    (WIDGET, 'variant', 'glass'), (WIDGET, 'style', 'minimal'),
    (WIDGET, 'kind', '__proto__'), (WIDGET, 'opacity', 61), (WIDGET, 'opacity', 100.0),
    (WIDGET, 'color', 'red'), (WIDGET, 'background', 'url(secret)'),
    (WIDGET, 'title', '\n'), (WIDGET, 'id', '../unsafe'),
])
def test_invalid_values(path, key, value):
    store = target()
    locate(store, path)[key] = value
    with pytest.raises(contracts.ContractError):
        contracts.validate_contract(store, 'server')


@pytest.mark.parametrize('kind', sorted(contracts.PROFILE_KINDS))
def test_all_widget_kinds_and_repeated_instances(kind):
    store = target()
    store['profiles'][0]['configuration']['layout']['widgets'] = [
        widget(id='first', kind=kind), widget(id='second', kind=kind, variant='minimal', style='glass')]
    assert len(contracts.validate_contract(store, 'server')['profiles'][0]['configuration']['layout']['widgets']) == 2


def test_grid_bounds_without_collision_or_mobile_policy():
    store = target()
    layout = store['profiles'][0]['configuration']['layout']
    layout['widgets'] = [widget(id='first', x=18, width=6, y=4094, height=2),
                         widget(id='second', x=18, width=6, y=4094, height=2)]
    assert contracts.validate_contract(store, 'server')
    layout['widgets'][0]['height'] = 3
    with pytest.raises(contracts.ContractError):
        contracts.validate_contract(store, 'server')


@pytest.mark.parametrize('duplicate', ['profile', 'widget', 'tombstone', 'receipt'])
def test_duplicate_ids(duplicate):
    store = target()
    if duplicate == 'profile':
        store['profiles'].append(copy.deepcopy(store['profiles'][0]))
    elif duplicate == 'widget':
        widgets = store['profiles'][0]['configuration']['layout']['widgets']
        widgets.append(copy.deepcopy(widgets[0]))
    elif duplicate == 'tombstone':
        store['tombstones'] = [{'id': 'p-default', 'revision': 1}]
    else:
        receipt = {'operationId': '1' * 32, 'requestDigest': 'a' * 64,
                   'result': {'kind': 'update', 'profileId': 'p-default', 'revision': 1, 'catalogRevision': 1}}
        store['receipts'] = [receipt, copy.deepcopy(receipt)]
    with pytest.raises(contracts.ContractError):
        contracts.validate_contract(store, 'server')


def test_count_and_byte_limits():
    store = target()
    prototype = store['profiles'][0]
    store['profiles'] = [{**copy.deepcopy(prototype), 'id': 'profile-' + str(index)} for index in range(12)]
    for profile in store['profiles']:
        profile['configuration']['layout']['widgets'] = [widget(id='w-' + str(index)) for index in range(60)]
    assert contracts.validate_contract(store, 'server')
    store['profiles'].append({**copy.deepcopy(prototype), 'id': 'too-many'})
    with pytest.raises(contracts.ContractError):
        contracts.validate_contract(store, 'server')
    store = target()
    store['profiles'][0]['configuration']['layout']['widgets'] = [widget(id='w-' + str(index)) for index in range(61)]
    with pytest.raises(contracts.ContractError):
        contracts.validate_contract(store, 'server')
    with pytest.raises(contracts.ContractError, match='size_limit'):
        contracts.validate_contract({'extra': 'x' * contracts.MAX_STORE_BYTES}, 'server')


@pytest.mark.parametrize('raw', [b'{', b'\xff', b'{"x":1,"x":2}', b'{"x":NaN}',
                               b'{"x":1e999}', b'[' * 10000 + b'0' + b']' * 10000])
def test_malformed_json_is_controlled(raw):
    assert contracts.inspect_document(raw)['status'] == 'corrupt'
    with pytest.raises(contracts.ContractError):
        contracts.decode_document(raw)


def test_cyclic_and_deep_python_input_is_bounded():
    value = {}
    value['self'] = value
    with pytest.raises(contracts.ContractError, match='complexity_limit'):
        contracts.validate_contract(value, 'server')


def test_format_classification_and_current_store_refusal(tmp_path):
    store = target()
    assert contracts.inspect_document(contracts.encode_document(store)) == {'status': 'recognized', 'kind': 'server'}
    store['version'] = 2
    assert contracts.inspect_document(contracts.encode_document(store))['status'] == 'future'
    store['version'] = True
    assert contracts.inspect_document(contracts.encode_document(store))['status'] == 'invalid'
    assert contracts.inspect_document(b'{"format":"unknown","version":1}')['status'] == 'unsupported'
    legacy = {**default_document(), 'revision': 1}
    assert contracts.inspect_document(json.dumps(legacy).encode()) == {'status': 'legacy', 'kind': 'server'}
    path = tmp_path / 'profiles.json'
    path.write_bytes(contracts.encode_document(target()))
    before = path.read_bytes()
    with pytest.raises(RuntimeError, match='recover_profiles'):
        HistoricalProfileFixture(path)
    assert path.read_bytes() == before
    assert not path.with_suffix('.json.bak').exists()


def test_schemas_are_derived_from_the_authoritative_models():
    for kind in ('server', 'export', 'draft', 'operation'):
        schema = contracts.contract_schema(kind)
        assert schema
        assert all(model.get('additionalProperties') is False for model in schema.get('$defs', {}).values()
                   if model.get('type') == 'object')
    assert set(contracts.contract_schema('server')['$defs']['Widget']['properties']['kind']['enum']) == contracts.PROFILE_KINDS


def test_legacy_exports_and_resource_limit_classification():
    profile = default_document()['profiles'][0]
    exported = {'format': 'cs2-companion-layout', 'version': 2, 'profile': profile}
    assert contracts.inspect_document(json.dumps(exported).encode()) == {'status': 'legacy', 'kind': 'export'}
    del exported['profile']
    assert contracts.inspect_document(json.dumps(exported).encode())['status'] == 'invalid'
    exported['version'] = 3
    assert contracts.inspect_document(json.dumps(exported).encode())['status'] == 'future'
    assert contracts.inspect_document(b' ' * (contracts.MAX_STORE_BYTES + 1))['status'] == 'invalid'
