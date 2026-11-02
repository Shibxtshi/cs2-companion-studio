"""Profile recovery and disk failure regressions using only synthetic data."""
import copy
import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest

from companion.profile_store import read_document
from tests.historical_profiles import HistoricalProfileFixture

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('recover_profiles', ROOT / 'scripts/recover_profiles.py')
recovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recovery)


def test_backup_and_explicit_recovery_preserve_invalid_file(tmp_path):
    store = HistoricalProfileFixture(tmp_path / 'profiles.json')
    original = store.snapshot()
    document = {key: copy.deepcopy(original[key]) for key in ('profiles', 'activeProfile')}
    document['profiles'][0]['name'] = 'Changed'
    assert store.put(document, store.revision)
    assert read_document(tmp_path / 'profiles.json.bak')[0]['profiles'][0]['name'] == 'My dashboard'
    store.path.write_bytes(b'broken json')
    with pytest.raises(RuntimeError, match='recover_profiles'):
        HistoricalProfileFixture(store.path)
    recovery.restore(tmp_path)
    assert HistoricalProfileFixture(store.path).data['profiles'][0]['name'] == 'My dashboard'
    preserved = list(tmp_path.glob('profiles.json.corrupt-*'))
    assert len(preserved) == 1
    assert preserved[0].read_bytes() == b'broken json'


def test_invalid_backup_does_not_touch_current(tmp_path):
    store = HistoricalProfileFixture(tmp_path / 'profiles.json')
    before = store.path.read_bytes()
    (tmp_path / 'profiles.json.bak').write_bytes(b'invalid')
    with pytest.raises(ValueError):
        recovery.restore(tmp_path)
    assert store.path.read_bytes() == before
    assert not list(tmp_path.glob('profiles.json.corrupt-*'))


def test_failed_replace_keeps_current_revision_and_file(tmp_path):
    store = HistoricalProfileFixture(tmp_path / 'profiles.json')
    before = store.path.read_bytes()
    revision = store.revision
    document = {key: copy.deepcopy(store.data[key]) for key in ('profiles', 'activeProfile')}
    document['profiles'][0]['name'] = 'Unsaved'
    from companion import profile_store
    realReplace = profile_store.os.replace

    def replace(source, destination):
        if Path(destination) == store.path:
            raise OSError('synthetic disk failure')
        return realReplace(source, destination)

    with patch('companion.profile_store.os.replace', side_effect=replace):
        with pytest.raises(OSError):
            store.put(document, revision)
    assert store.path.read_bytes() == before
    assert store.revision == revision
    assert store.data['profiles'][0]['name'] == 'My dashboard'
    assert not list(tmp_path.glob('.profiles-*.tmp'))

@pytest.mark.parametrize('raw', [
    '[' * 10000 + '0' + ']' * 10000,
    '{"profiles":[],"extra":NaN}',
    '{"profiles":[],"extra":1e400}',
], ids=['deep', 'nan', 'overflow'])
def test_corrupt_storage_has_controlled_recovery_error(tmp_path, raw):
    path = tmp_path / 'profiles.json'
    import json
    store = HistoricalProfileFixture(path)
    raw = json.dumps(store.snapshot())[:-1] + ', "extra":' + raw + '}'
    path.write_text(raw, encoding='utf-8')
    with pytest.raises(RuntimeError, match='recover_profiles'):
        HistoricalProfileFixture(path)
    assert path.read_text(encoding='utf-8') == raw


def test_deep_backup_is_rejected_without_touching_current(tmp_path):
    store = HistoricalProfileFixture(tmp_path / 'profiles.json')
    before = store.path.read_bytes()
    (tmp_path / 'profiles.json.bak').write_text('[' * 10000 + '0' + ']' * 10000)
    with pytest.raises(ValueError):
        recovery.restore(tmp_path)
    assert store.path.read_bytes() == before
    assert not list(tmp_path.glob('profiles.json.corrupt-*'))
