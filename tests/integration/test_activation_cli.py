"""Exercise operator confirmations and locks through the shipped CLI on temporary data."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest
from companion.profile_runtime import create_runtime_store, runtime_lease
from companion.profile_recovery import verify_backup
from tests.unit.test_profile_activation import historical, REVISION

ROOT=Path(__file__).resolve().parents[2]


def cli(directory,*arguments,inputText=''):
    return subprocess.run([sys.executable,'scripts/recover_profiles.py','--data-dir',str(directory),
        *arguments,'--service-stopped'],input=inputText,text=True,encoding='utf-8',errors='replace',
        capture_output=True,cwd=ROOT,env=dict(os.environ,PYTHONUTF8='1'),timeout=20)


def prepare(directory):
    result=cli(directory,'--prepare-activation','--application-revision',REVISION)
    assert result.returncode==0,result.stderr
    return re.search(r'Activation candidate ID: ([a-f0-9]{32})',result.stdout).group(1)


def test_cli_requires_exact_confirmation_and_retains_verified_original(historical):
    directory,original=historical
    backupId=prepare(directory)
    verify_backup(directory,backupId)
    cancelled=cli(directory,'--activate',backupId,inputText='ACTIVATE WRONG\n')
    assert cancelled.returncode==0 and 'Cancelled' in cancelled.stdout
    assert (directory/'profiles.json').read_bytes()==original
    assert not (directory/('.profiles-activation-'+backupId+'.attempted')).exists()
    confirmed=cli(directory,'--activate',backupId,inputText='ACTIVATE '+backupId+'\n')
    assert confirmed.returncode==0,confirmed.stderr
    assert json.loads((directory/'profiles.json').read_bytes())['format']=='ccs-dashboard-store'
    restored=cli(directory,'--restore-activation',backupId,inputText='RESTORE ACTIVATION '+backupId+'\n')
    assert restored.returncode==0,restored.stderr
    assert (directory/'profiles.json').read_bytes()==original
    refused=cli(directory,'--activate',backupId,inputText='ACTIVATE '+backupId+'\n')
    assert refused.returncode==1 and 'activation_already_attempted' in refused.stderr
    assert 'NEW activation ID' in refused.stdout
    assert (directory/'profiles.json').read_bytes()==original


def test_cli_cannot_bypass_running_runtime_lock_with_acknowledgement(historical):
    directory,original=historical
    store=create_runtime_store(directory)
    with runtime_lease(store):
        result=cli(directory,'--prepare-activation','--application-revision',REVISION)
    assert result.returncode==1 and 'recovery_busy' in result.stderr
    assert (directory/'profiles.json').read_bytes()==original


@pytest.mark.parametrize('action',['--restore','--reset','--restore-reset','--activate'])
def test_cli_refuses_other_writers_during_interrupted_restore(historical,action):
    directory,original=historical
    backupId=prepare(directory)
    (directory/('.profiles-restore-'+backupId+'.pending')).write_text('{}',encoding='utf-8')
    arguments=[action] if action=='--restore' else [action,backupId]
    result=cli(directory,*arguments,inputText='YES\n')
    assert result.returncode==1 and 'restore_interrupted_keep_service_stopped' in result.stderr
    assert (directory/'profiles.json').read_bytes()==original
