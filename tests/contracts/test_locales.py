"""Strict shared-catalog data, completeness, references and packaging contracts."""
import importlib.util
import json
from pathlib import Path
import shutil

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('locale_checks', ROOT / 'scripts/check_locales.py')
checks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checks)


def test_real_catalogs_and_references_are_valid():
    result = checks.check()
    assert result['languages'] == ['EN', 'FR', 'RU', 'PL', 'UK', 'CS', 'RO']
    assert result['keys'] > 500


@pytest.mark.parametrize('language', ['EN', 'FR', 'RU', 'PL', 'UK', 'CS', 'RO'])
def test_offline_tools_use_the_same_complete_catalog(language):
    from companion.localization import Translator

    translator = Translator(language)
    assert translator.catalog.keys() == translator.reference.keys()
    personal = 'Private name {unchanged} <tag>'
    assert personal in translator.text('studio.addWidget', widget=personal)
    assert translator.text('studio.publish') == translator.catalog['studio.publish']


@pytest.mark.parametrize('content', [b'{broken', b'{"key":"one","key":"two"}', b'{"key":"one","Key":"two"}', b'\xff', b'\xef\xbb\xbf{}'])
def test_invalid_json_duplicate_keys_and_encoding_are_rejected(tmp_path, content):
    path = tmp_path / 'bad.json'
    path.write_bytes(content)
    with pytest.raises(checks.LocaleError):
        checks.read_json(path)


@pytest.mark.parametrize('catalog', [
    {}, {'message.key': ''}, {'message.key': None}, {'message.key': 'Bad {other}'},
    {'message.key': 'Bad {amount'}, {'message.key': 'Valid {amount}', 'extra.key': 'Extra'},
])
def test_incomplete_empty_extra_and_parameter_errors_are_rejected(catalog):
    with pytest.raises(checks.LocaleError):
        checks.validate_catalog({'message.key': 'Value {amount}'}, catalog)


def test_third_complete_locale_requires_only_data(tmp_path):
    folder = tmp_path / 'locales'
    shutil.copytree(ROOT / 'static/locales', folder)
    registry = checks.read_json(folder / 'languages.json')
    registry['languages'].append({'code': 'ZZ', 'name': 'Synthetic', 'file': 'zz.json', 'confirmYes': 'Y'})
    (folder / 'languages.json').write_text(json.dumps(registry), encoding='utf-8')
    (folder / 'zz.json').write_bytes((folder / 'en.json').read_bytes())
    assert 'ZZ' in checks.load_catalogs(folder)[1]
    (folder / 'zz.json').write_text('{}', encoding='utf-8')
    with pytest.raises(checks.LocaleError):
        checks.load_catalogs(folder)


def test_unsupported_registry_and_unknown_references_are_rejected(tmp_path):
    root = tmp_path / 'source'
    (root / 'static/js').mkdir(parents=True)
    (root / 'static/js/test.js').write_text("CS2I18N.t('not.a.real.key')", encoding='utf-8')
    with pytest.raises(checks.LocaleError, match='unknown_message'):
        checks.references(root, {'app.title': 'CCS'})
    folder = tmp_path / 'locales'
    shutil.copytree(ROOT / 'static/locales', folder)
    registry = checks.read_json(folder / 'languages.json')
    registry['languages'][1]['file'] = '../private.json'
    (folder / 'languages.json').write_text(json.dumps(registry), encoding='utf-8')
    with pytest.raises(checks.LocaleError, match='language_file'):
        checks.load_catalogs(folder)


def test_runtime_translates_explicit_messages_only():
    source = (ROOT / 'static/js/i18n.js').read_text('utf-8')
    assert 'seenText' not in source
    assert 'textContent = next' in source and 'innerHTML' not in source
    assert 'cs2-companion-language' in source
    for path in ['static/index.html', 'static/preview.html']:
        html = (ROOT / path).read_text('utf-8')
        assert 'data-ccs-src=' in html and '/static/js/i18n.js' in html
        assert 'sauvegarde automatique' not in html
    assert 'COPY static ./static' in (ROOT / 'Dockerfile').read_text('utf-8')
    installer = (ROOT / 'installer/i18n.ps1').read_text('utf-8-sig')
    assert "'static/locales'" in installer
    assert '-Encoding UTF8' in installer and 'ConvertFrom-Json' in installer
    assert '$script:Strings' not in installer


def test_obsolete_keys_do_not_silently_remain_in_catalogs(tmp_path):
    folder = tmp_path / 'static/locales'
    folder.mkdir(parents=True)
    registry = {'reference': 'EN', 'languages': [{'code': 'EN', 'name': 'English', 'file': 'en.json', 'confirmYes': 'Y'}]}
    (folder / 'languages.json').write_text(json.dumps(registry), encoding='utf-8')
    (folder / 'en.json').write_text(json.dumps({'app.title': 'Title', 'app.retired': 'Unused'}), encoding='utf-8')
    scripts = tmp_path / 'static/js'
    scripts.mkdir()
    (scripts / 'app.js').write_text("CS2I18N.t('app.title')", encoding='utf-8')
    with pytest.raises(checks.LocaleError, match='obsolete_or_unreferenced'):
        checks.check(tmp_path)
