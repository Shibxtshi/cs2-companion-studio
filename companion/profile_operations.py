"""Pure future publication transitions. No runtime store, route or disk writes."""
from __future__ import annotations

import copy
import hashlib

from companion.profile_contracts import (
    ContractError, MAX_PROFILES, MAX_RECEIPTS, MAX_REVISION, MAX_TOMBSTONES,
    encode_document, validate_contract,
)


def apply_operation(document, command):
    """Validate a complete target state; P5 must persist before acknowledging it."""
    current = validate_contract(document, 'server')
    operation = validate_contract(command, 'operation')
    if operation['storeId'] != current['storeId']:
        raise ContractError('store_changed')
    digest = hashlib.sha256(encode_document(operation)).hexdigest()
    for receipt in current['receipts']:
        if receipt['operationId'] == operation['operationId']:
            if receipt['requestDigest'] != digest:
                raise ContractError('operation_id_reused')
            return copy.deepcopy(current), {**copy.deepcopy(receipt), 'replayed': True}

    profileId = operation['profileId']
    found = next((profile for profile in current['profiles'] if profile['id'] == profileId), None)
    if any(item['id'] == profileId for item in current['tombstones']):
        raise ContractError('profile_deleted')
    kind = operation['kind']
    if kind == 'create':
        if found is not None:
            raise ContractError('profile_exists')
        if len(current['profiles']) >= MAX_PROFILES:
            raise ContractError('profile_limit')
        revision = 1
    else:
        if found is None:
            raise ContractError('profile_missing')
        if found['revision'] != operation['expectedRevision']:
            raise ContractError('revision_conflict')
        if found['revision'] >= MAX_REVISION:
            raise ContractError('revision_limit')
        revision = found['revision'] + 1
        if kind == 'delete':
            if len(current['profiles']) <= 1:
                raise ContractError('last_profile')
            if len(current['tombstones']) >= MAX_TOMBSTONES:
                raise ContractError('tombstone_limit')
    if current['catalogRevision'] >= MAX_REVISION:
        raise ContractError('revision_limit')

    result = copy.deepcopy(current)
    result['catalogRevision'] += 1
    if kind == 'create':
        result['profiles'].append({'id': profileId, 'revision': revision, **operation['profile']})
    elif kind == 'update':
        result['profiles'] = [({'id': profileId, 'revision': revision, **operation['profile']}
                               if profile['id'] == profileId else profile)
                              for profile in result['profiles']]
    else:
        result['profiles'] = [profile for profile in result['profiles'] if profile['id'] != profileId]
        result['tombstones'].append({'id': profileId, 'revision': revision})
    receipt = {'operationId': operation['operationId'], 'requestDigest': digest,
               'result': {'kind': kind, 'profileId': profileId, 'revision': revision,
                          'catalogRevision': result['catalogRevision']}}
    result['receipts'] = (result['receipts'] + [receipt])[-MAX_RECEIPTS:]
    return validate_contract(result, 'server'), {**copy.deepcopy(receipt), 'replayed': False}
