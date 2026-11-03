"""Maintenance copy must preserve explicit consent and treat parameters as plain data."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys

import pytest

from companion.localization import Translator
from companion.profile_contracts import encode_document, new_server_document

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize('language', ['EN', 'FR'])
def test_plain_parameters_and_unknown_keys(language):
    translator = Translator(language)
    value = 'Émilie "quoted" <tag> $() {code}'
    assert value in translator.text('maintenance.backupPath', path=value)
    assert translator.text('unknown.key') == '[unknown.key]'
    with pytest.raises(ValueError, match='locale_parameters'):
        translator.text('maintenance.backupPath', other='wrong')
    with pytest.raises(ValueError, match='locale_parameters'):
        translator.text('maintenance.backupPath', path='ok', extra='wrong')
    with pytest.raises(ValueError, match='unsupported_language'):
        Translator('UNSUPPORTED')


@pytest.mark.parametrize('language', ['EN', 'FR'])
def test_offline_cli_language_keeps_read_only_inspection_and_stopped_service_guard(tmp_path, language):
    original = encode_document(new_server_document())
    (tmp_path / 'profiles.json').write_bytes(original)
    command = [sys.executable, '-B', 'scripts/recover_profiles.py', '--language', language, '--data-dir', str(tmp_path)]
    result = subprocess.run(command + ['--inspect'], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', env=dict(os.environ, PYTHONIOENCODING='utf-8'), timeout=20)
    assert result.returncode == 0, result.stderr
    assert ('Classification des profils' if language == 'FR' else 'Profile classification') in result.stdout
    assert (tmp_path / 'profiles.json').read_bytes() == original
    result = subprocess.run(command + ['--prepare-activation'], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', env=dict(os.environ, PYTHONIOENCODING='utf-8'), timeout=20)
    assert result.returncode != 0
    assert '--service-stopped' in result.stderr
    assert (tmp_path / 'profiles.json').read_bytes() == original
    assert not (tmp_path / 'profile-reset-backups').exists()


def test_configuration_copy_does_not_change_generated_network_or_credentials_policy(tmp_path, monkeypatch, capsys):
    spec = importlib.util.spec_from_file_location('synthetic_generator', ROOT / 'scripts/generate_config.py')
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    monkeypatch.setattr(generator, 'DOTENV', tmp_path / '.env')
    monkeypatch.setattr(generator, 'GSI', tmp_path / 'cfg/test.cfg')
    monkeypatch.setattr(generator.secrets, 'randbelow', lambda _: 2)
    monkeypatch.setattr(generator.secrets, 'token_urlsafe', lambda _: 'synthetic-localization-token')
    monkeypatch.setattr(sys, 'argv', ['generate_config.py', '--language', 'FR'])
    assert generator.main() == 0
    assert 'Configuration locale créée' in capsys.readouterr().out
    content = (tmp_path / '.env').read_text('utf-8')
    assert 'BIND_HOST=127.0.0.1' in content and 'PORT=8080' in content
    assert 'BOMB_TIMER_ENABLED=false' in content
    original = (tmp_path / '.env').read_bytes()
    assert generator.main() == 1
    assert (tmp_path / '.env').read_bytes() == original


@pytest.mark.parametrize('language', ['EN', 'FR'])
@pytest.mark.parametrize('answer, expected', [('ACTIVATE synthetic-id', True), ('activate synthetic-id', False), ('', False)])
def test_localized_confirmation_preserves_exact_activation_token(language, answer, expected, monkeypatch, capsys):
    spec = importlib.util.spec_from_file_location('synthetic_recovery', ROOT / 'scripts/recover_profiles.py')
    recovery = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(recovery)
    recovery.tr = Translator(language).text
    prompts = []

    def respond(prompt):
        prompts.append(prompt)
        return answer

    monkeypatch.setattr('builtins.input', respond)
    assert recovery.confirm('ACTIVATE synthetic-id') is expected
    assert 'ACTIVATE synthetic-id' in prompts[0]
    assert ('Saisis exactement' if language == 'FR' else 'Type exactly') in prompts[0]
    capsys.readouterr()
