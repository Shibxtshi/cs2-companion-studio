"""Verify packaged inactive publication code/assets using only isolated container /tmp."""
import hashlib
import json
from pathlib import Path
import subprocess
import textwrap

MODULES = ('draft-schema', 'draft-contract', 'edit-history', 'draft-publications', 'draft-store',
           'draft-session', 'published-profiles', 'profile-publication', 'dashboard-target')


def main():
    expected = {name: hashlib.sha256((Path('static/js') / (name + '.js')).read_bytes()).hexdigest() for name in MODULES}
    code = textwrap.dedent('''
        from pathlib import Path
        from tempfile import TemporaryDirectory
        import hashlib
        from companion.profile_contracts import encode_document, new_server_document
        from companion.profile_publication import PublishedProfileStore
        from companion.profile_protocol import PublishedProfileProtocol
        expected = EXPECTED_HASHES
        for name, digest in expected.items():
            assert hashlib.sha256((Path('static/js') / (name + '.js')).read_bytes()).hexdigest() == digest
        html = Path('static/index.html').read_text()
        assert all(name + '.js' not in html for name in expected)
        assert all('/static/js/' + name + '.js' in html for name in ('dashboard-layout', 'dashboard-grid', 'dashboard-shell'))
        assert Path('static/css/dashboard.css').is_file()
        assert Path('static/css/widget-presentation.css').is_file()
        assert '/static/js/widget-presentation.js' in html
        with TemporaryDirectory(prefix='ccs-publication-', dir='/tmp') as temporary:
            path = Path(temporary) / 'profiles.json'
            document = new_server_document()
            path.write_bytes(encode_document(document))
            store = PublishedProfileStore(path)
            profile = document['profiles'][0]
            operation = {'format': 'ccs-dashboard-operation', 'version': 1,
                'storeId': document['storeId'], 'operationId': 'c' * 32,
                'profileId': profile['id'], 'kind': 'update', 'expectedRevision': 1,
                'profile': {key: profile[key] for key in ('name', 'configuration')}}
            assert store.publish(operation)['result']['revision'] == 2
            assert PublishedProfileStore(path).publish(operation)['replayed']
            assert PublishedProfileProtocol(store).snapshot()['type'] == 'profiles_catalog'
        print('OK: packaged inactive publication, persisted receipt replay and exact frontend assets; no mounted data accessed')
    ''').replace('EXPECTED_HASHES', repr(expected))
    subprocess.run(['docker', 'compose', 'exec', '-T', 'cs2-companion-studio', 'python', '-'],
                   input=code, text=True, check=True, timeout=60)


if __name__ == '__main__':
    main()
