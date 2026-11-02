"""Keep the current runtime map and offline recovery boundaries consistent."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]


def test_runtime_map_names_both_compositions_and_the_exclusive_writer():
    architecture = (ROOT / 'docs/development/architecture.md').read_text('utf-8')
    for name in ['profile_runtime.py', 'profile_activation.py', 'application.js', 'studio.js',
                 'profile-sync.js', 'IndexedDB', 'Exactly one store and writer']:
        assert name in architecture
    for description in ['Inactive target', 'without activating them', 'publication remain inactive']:
        assert description not in architecture


def test_current_module_headers_describe_runtime_usage():
    for name in ['companion/profile_contracts.py', 'companion/profile_publication.py',
                 'companion/profile_protocol.py', 'companion/profile_operations.py',
                 'static/js/draft-contract.js', 'static/js/widget-renderer.js']:
        header = (ROOT / name).read_text('utf-8').splitlines()[0].lower()
        assert not any(word in header for word in ['inactive', 'dormant', 'future', 'only by isolated tests'])


def test_offline_recovery_documents_server_lock_and_target_procedure():
    recovery = (ROOT / 'docs/guides/profile-recovery.md').read_text('utf-8')
    assert 'production server lifespan' in recovery
    assert 'service shutdown' in recovery
    assert 'historical storage only' in recovery
    assert 'does not lock out the current server' not in recovery
    for name in ['docs/development/architecture.md', 'docs/guides/profile-recovery.md']:
        path = ROOT / name
        for target in re.findall(r'\]\(([^)#]+)(?:#[^)]*)?\)', path.read_text('utf-8')):
            if not target.startswith(('https:', 'http:')):
                assert (path.parent / target).exists(), (name, target)
