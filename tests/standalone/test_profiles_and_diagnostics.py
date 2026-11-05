"""Authenticated target publication, independent revisions and sanitized diagnostics."""
import copy
import json
import os
import tempfile
import uuid
from pathlib import Path

os.environ['GSI_TOKEN'] = 'fake-dev-only-gsi-token'
os.environ['DASHBOARD_PIN'] = '1234567890'
from fastapi.testclient import TestClient
from companion.profile_runtime import create_runtime_store
from companion.profile_publication import PublishedProfileStore
from companion.support_diagnostics import Diagnostics
from companion import server as app


def run():
    with tempfile.TemporaryDirectory() as directory:
        app.profile_store = create_runtime_store(Path(directory) / 'data')
        app.diagnostics = Diagnostics(Path(directory) / 'logs', '1.1.0')
        with TestClient(app.app) as client:
            for route in ('/profiles', '/api/profiles', '/data/profiles.json', '/logs/support-summary.json'):
                assert client.get(route).status_code in (404, 405), route
            with client.websocket_connect('/ws', headers={'origin':'http://testserver'}) as first, client.websocket_connect('/ws', headers={'origin':'http://testserver'}) as second:
                for socket in (first, second):
                    socket.send_json({'type':'auth', 'pin':'1234567890'})
                    assert socket.receive_json()['type'] == 'auth_ok'
                    assert socket.receive_json()['type'] == 'profiles_catalog'
                    socket.receive_json()
                document = app.profile_store.data
                profile = document['profiles'][0]
                operation = {'format':'ccs-dashboard-operation', 'version':1, 'storeId':document['storeId'],
                    'operationId':uuid.uuid4().hex, 'profileId':profile['id'], 'kind':'update', 'expectedRevision':1,
                    'profile':{'name':'Synthetic published dashboard', 'configuration':profile['configuration']}}
                first.send_json({'type':'profile_operation', 'operation':operation})
                assert first.receive_json()['type'] == 'profile_operation_ack'
                for socket in (first, second):
                    assert socket.receive_json()['catalog']['profiles'][0]['revision'] == 2
                second.send_json({'type':'profile_operation', 'operation':{**operation, 'operationId':uuid.uuid4().hex}})
                assert second.receive_json()['code'] == 'revision_conflict'
                bad = copy.deepcopy(operation)
                bad.update(operationId=uuid.uuid4().hex, expectedRevision=2)
                bad['profile']['configuration']['layout']['widgets'] = [{'kind':'<script>'}]
                first.send_json({'type':'profile_operation', 'operation':bad})
                assert first.receive_json()['code'] == 'invalid_document'
                first.send_json({'type':'diagnostics_request'})
                report = first.receive_json()
                assert report['type'] == 'diagnostics_data'
                assert 'player' not in report['report'] and 'steam' not in report['report']
                for secret in ['1234567890', 'fake-dev-only-gsi-token']:
                    assert secret not in json.dumps(report)
            restored = PublishedProfileStore(Path(directory) / 'data/profiles.json')
            assert restored.data['profiles'][0]['name'] == 'Synthetic published dashboard'
            logs = ''.join(path.read_text() for path in (Path(directory) / 'logs').glob('*') if path.is_file())
            assert '1234567890' not in logs and 'fake-dev-only-gsi-token' not in logs
            assert 'Synthetic published dashboard' not in logs
    print('OK: target publication, broadcast, revision conflict, validation, persistence and private diagnostics')


if __name__ == '__main__':
    run()
