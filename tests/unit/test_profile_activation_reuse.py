"""An activation intent must never resurrect an already used storage generation."""
import pytest
import json

from companion import profile_activation as activation
from companion.profile_recovery import RecoveryError
from companion.profile_publication import PublishedProfileStore
from companion.profile_contracts import ContractError
from tests.unit.test_profile_activation import historical, REVISION
from tests.unit.test_profile_publication import operation


def test_rollback_does_not_make_the_same_activation_intent_reusable(historical):
    directory,original=historical
    backupId=activation.prepare_activation(directory,REVISION)
    activation.activate_profiles(directory,backupId,lambda _:True)
    store=PublishedProfileStore(directory/'profiles.json')
    stale=operation(store.data,profileId=store.data['profiles'][0]['id'])
    store.publish(stale)
    assert activation.restore_activation(directory,backupId,lambda _:True)[0]
    with pytest.raises(RecoveryError,match='activation_already_attempted'):
        activation.activate_profiles(directory,backupId,lambda _:True)
    assert (directory/'profiles.json').read_bytes()==original
    freshId=activation.prepare_activation(directory,REVISION)
    assert freshId!=backupId
    assert activation.activate_profiles(directory,freshId,lambda _:True)
    fresh=PublishedProfileStore(directory/'profiles.json')
    assert fresh.data['storeId']!=stale['storeId']
    before=fresh.path.read_bytes()
    with pytest.raises(ContractError,match='store_changed'):
        fresh.publish(stale)
    assert fresh.path.read_bytes()==before


def test_failed_install_also_consumes_the_attempt(historical,monkeypatch):
    directory,original=historical
    backupId=activation.prepare_activation(directory,REVISION)
    def fail(*args):
        raise OSError('Synthetic interrupted install')
    monkeypatch.setattr(activation,'_install',fail)
    with pytest.raises(OSError):
        activation.activate_profiles(directory,backupId,lambda _:True)
    with pytest.raises(RecoveryError,match='activation_already_attempted'):
        activation.activate_profiles(directory,backupId,lambda _:True)
    assert (directory/'profiles.json').read_bytes()==original


def test_old_preparations_remain_restorable_but_cannot_activate(historical):
    directory,original=historical
    backupId=activation.prepare_activation(directory,REVISION)
    activation.activate_profiles(directory,backupId,lambda _:True)
    path=directory/('.profiles-activation-'+backupId+'.json')
    meta=json.loads(path.read_bytes())
    meta['version']=1
    path.write_text(json.dumps(meta),encoding='utf-8')
    assert activation.restore_activation(directory,backupId,lambda _:True)[0]
    assert (directory/'profiles.json').read_bytes()==original
    with pytest.raises(RecoveryError,match='activation_prepare_again'):
        activation.activate_profiles(directory,backupId,lambda _:True)


def test_pending_restore_blocks_other_mutating_recovery_paths(historical):
    directory,original=historical
    backupId=activation.prepare_activation(directory,REVISION)
    pending=directory/('.profiles-restore-'+'f'*32+'.pending')
    pending.write_text('{}',encoding='utf-8')
    with pytest.raises(RecoveryError,match='restore_interrupted'):
        activation.prepare_activation(directory,REVISION)
    with pytest.raises(RecoveryError,match='restore_interrupted'):
        activation.activate_profiles(directory,backupId,lambda _:True)
    with pytest.raises(RecoveryError,match='restore_interrupted'):
        activation.restore_target_backup(directory,lambda _:True)
    with pytest.raises(RecoveryError,match='another_restore_interrupted'):
        activation.restore_activation(directory,backupId,lambda _:True)
    assert (directory/'profiles.json').read_bytes()==original
