"""Archive policy covers variants, preserved backups and portable path syntax."""
import importlib.util
import io
from pathlib import Path
import zipfile

import pytest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('archive_policy',ROOT/'scripts/check_public_archive.py')
policy=importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)


def archive_with(name, content=b'synthetic'):
    data=io.BytesIO()
    with zipfile.ZipFile(data,'w') as archive:
        archive.writestr(name,content)
    data.seek(0)
    return data


@pytest.mark.parametrize('name',[
 'release/.companion-write-synthetic.tmp','release/data/profiles.json.bak','release/data/profiles.json.corrupt-synthetic',
 'release/.env.local','release/.env.production','release/.env.example.backup',
 'release/logs/custom.log','release/DATA/arbitrary.json',
 'release/data/.gitkeep','release/data/nested/.gitkeep',
 'release\\data\\profiles.json.bak','release/AGENTS.md','release/docs/LOCAL_AUDIT_FIX_GUIDE.md',
])
def test_private_variants_are_rejected(name):
    with pytest.raises(ValueError,match='Private'):
        policy.check_zip(archive_with(name))


@pytest.mark.parametrize('name',['release/.env.example','release/cs2_cfg/gamestate_integration_companion.cfg.example','release/README.md'])
def test_examples_and_source_are_allowed(name):
    assert policy.check_zip(archive_with(name))


def test_empty_runtime_scaffolding_is_allowed():
    for name in ('release/data/.gitkeep','release/logs/.gitkeep'):
        assert policy.check_zip(archive_with(name,b''))


@pytest.mark.parametrize('name',['../.env','/absolute/file','release/../file','C:/private'])
def test_ambiguous_paths_are_rejected(name):
    with pytest.raises(ValueError,match='Unsafe'):
        policy.check_zip(archive_with(name))
