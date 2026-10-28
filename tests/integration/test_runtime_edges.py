"""Malformed inputs and atomic admission must be controlled, not crash handlers."""
import asyncio
import ast
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest
from companion.profile_store import validate_document
from companion.security import credential_matches, decode_message

ROOT=Path(__file__).resolve().parents[2]


@pytest.fixture
def runtime_server(monkeypatch, tmp_path):
    monkeypatch.setenv('GSI_TOKEN', 'synthetic-edge-token')
    monkeypatch.setenv('DASHBOARD_PIN', 'synthetic-edge-pin')
    monkeypatch.setenv('PROFILE_DATA_DIR', str(tmp_path / 'data'))
    monkeypatch.setenv('DIAGNOSTICS_DIR', str(tmp_path / 'logs'))
    from companion import server
    from companion.profile_store import ProfileStore
    from companion.support_diagnostics import Diagnostics
    from companion.security import LoginLimiter
    monkeypatch.setattr(server, 'GSI_TOKEN', 'synthetic-edge-token')
    monkeypatch.setattr(server, 'DASHBOARD_PIN', 'synthetic-edge-pin')
    monkeypatch.setattr(server, 'profile_store', ProfileStore(tmp_path / 'data' / 'profiles.json'))
    monkeypatch.setattr(server, 'diagnostics', Diagnostics(tmp_path / 'logs', '1.0.0'))
    monkeypatch.setattr(server, 'limiter', LoginLimiter())
    return server


@pytest.mark.parametrize('value',[[],{},None,42])
def test_invalid_widget_kind_is_validation_error(value):
    document={'activeProfile':'p','profiles':[{'id':'p','widgets':[{'id':'w','kind':value,'span':12}]}]}
    with pytest.raises(ValueError,match='widget_type'):
        validate_document(document)


def test_unicode_credentials_are_rejected_without_comparison_exception():
    assert not credential_matches('é','synthetic-pin')
    assert not credential_matches('x'*257,'synthetic-pin')
    assert credential_matches('synthetic-pin','synthetic-pin')


def test_invalid_configuration_does_not_create_runtime_files(tmp_path):
    env=dict(os.environ,GSI_TOKEN='bad',DASHBOARD_PIN='synthetic-pin',
             PROFILE_DATA_DIR=str(tmp_path/'data'),DIAGNOSTICS_DIR=str(tmp_path/'logs'),PYTHONPATH=str(ROOT))
    result=subprocess.run([sys.executable,'-B','-c','import companion.server'],cwd=tmp_path,env=env,capture_output=True,text=True)
    assert result.returncode != 0
    assert 'Configure ASCII' in result.stderr
    assert not (tmp_path/'data').exists()
    assert not (tmp_path/'logs').exists()


def test_phase_contract_is_shared_with_browser(runtime_server):
    app=runtime_server
    previous=copy.deepcopy(app.state)
    lastGame,lastSeen=app.last_game_seen,app.last_seen
    try:
        app.state={'map':{'phase':'live'},'player':{},'round':{},'provider':{}}
        app.last_game_seen=app.last_seen=time.monotonic()
        assert app.summary()['map_phase']=='live'
        assert 'mapPhase' not in app.summary()
    finally:
        app.state=previous
        app.last_game_seen,app.last_seen=lastGame,lastSeen


def test_simultaneous_authentication_respects_capacity(runtime_server):
    # Execute the actual handler against deterministic in-memory transport peers.
    server=runtime_server
    class Disconnected(Exception):
        pass

    async def scenario():
        gate=asyncio.Event()
        accepted=0
        admitted=[]
        peers=set()
        sockets=[]
        class Socket:
            headers={'origin':'http://testserver','host':'testserver'}
            url=SimpleNamespace(scheme='ws')
            client=SimpleNamespace(host='synthetic')
            def __init__(self):
                self.first=True
                self.closed=None
                sockets.append(self)
            async def accept(self):
                nonlocal accepted
                accepted+=1
                if accepted==17: gate.set()
            async def receive_text(self):
                if self.first:
                    self.first=False
                    await gate.wait()
                    return json.dumps({'type':'auth','pin':'synthetic-pin'})
                await asyncio.Event().wait()
            async def receive(self):
                return {'type': 'websocket.receive', 'text': await self.receive_text()}
            async def send_json(self,message):
                if message.get('type')=='auth_ok':
                    await asyncio.sleep(0)
            async def send_text(self,message):
                admitted.append(len(peers))
            async def close(self,code):
                self.closed=code
        namespace=dict(vars(server),WebSocket=Socket,WebSocketDisconnect=Disconnected,
          same_origin=lambda *a,**k:True,
          limiter=SimpleNamespace(allowed=lambda *a:True,success=lambda *a:None,fail=lambda *a:None),
          diagnostics=SimpleNamespace(record=lambda *a:None),
          profile_store=SimpleNamespace(snapshot=lambda:{}),summary=lambda:{},
          connected=peers,pending_logins=0,reserved_logins=0,MAX_WS_CLIENTS=16,MAX_PENDING_LOGINS=32,
          DASHBOARD_PIN='synthetic-pin')
        node=next(n for n in ast.parse((ROOT/'companion/server.py').read_text('utf-8')).body
                  if isinstance(n,ast.AsyncFunctionDef) and n.name=='ws')
        node.decorator_list=[]
        exec(compile(ast.Module(body=[node],type_ignores=[]),'capacity_handler','exec'),namespace)
        tasks=[asyncio.create_task(namespace['ws'](Socket())) for _ in range(17)]
        for _ in range(30):
            await asyncio.sleep(0)
        assert len(peers)==16
        assert max(admitted)==16
        assert sum(s.closed==1013 for s in sockets)==1
        for task in tasks: task.cancel()
        await asyncio.gather(*tasks,return_exceptions=True)
        assert namespace['pending_logins']==namespace['reserved_logins']==0
    asyncio.run(scenario())


@pytest.mark.parametrize('raw', ['NaN', 'Infinity', '1e400', '[' * 40 + '0' + ']' * 40])
def test_json_complexity_and_non_finite_numbers_are_rejected(raw):
    with pytest.raises(ValueError):
        decode_message(raw)


def test_boundary_inputs_return_controlled_errors(runtime_server):
    from fastapi.testclient import TestClient
    server=runtime_server
    with TestClient(server.app) as client:
        assert client.post('/gsi', json={'auth':{'token':'é'}}).status_code==401
        assert client.post('/gsi', content='['*1100+'0'+']'*1100).status_code==400
        with client.websocket_connect('/ws', headers={'origin':'http://testserver'}) as ws:
            ws.send_json({'type':'auth','pin':'é'*8})
            assert ws.receive_json()['type']=='auth_error'
        with client.websocket_connect('/ws', headers={'origin':'http://testserver'}) as ws:
            ws.send_json({'type':'auth','pin':server.DASHBOARD_PIN})
            assert ws.receive_json()['type']=='auth_ok'
            snapshot=ws.receive_json()
            ws.receive_json()
            document={key:copy.deepcopy(snapshot[key]) for key in ('profiles','activeProfile')}
            document['profiles'][0]['widgets'][0]['kind']=[]
            ws.send_json({'type':'profiles_save','revision':snapshot['revision'],'document':document})
            assert ws.receive_json()=={'type':'profiles_error','code':'invalid'}
            ws.send_json({'type':'diagnostics_request'})
            assert ws.receive_json()['type']=='diagnostics_data'

@pytest.mark.parametrize('authenticated', [False, True])
def test_binary_websocket_frames_close_cleanly(runtime_server, authenticated):
    from fastapi.testclient import TestClient
    from starlette.websockets import WebSocketDisconnect
    server = runtime_server
    with TestClient(server.app) as client:
        with client.websocket_connect('/ws', headers={'origin': 'http://testserver'}) as socket:
            if authenticated:
                socket.send_json({'type': 'auth', 'pin': server.DASHBOARD_PIN})
                assert socket.receive_json()['type'] == 'auth_ok'
                socket.receive_json()
                socket.receive_json()
            socket.send_bytes(b'synthetic binary frame')
            with pytest.raises(WebSocketDisconnect) as closed:
                socket.receive_text()
            assert closed.value.code == 1003
    assert server.pending_logins == server.reserved_logins == 0
    assert not server.connected


@pytest.mark.parametrize('marker', ['format', 'version', 'schemaVersion'])
def test_target_markers_cannot_be_silently_saved_by_current_websocket(runtime_server, marker):
    from fastapi.testclient import TestClient
    server = runtime_server
    original = server.profile_store.path.read_bytes()
    revision = server.profile_store.revision
    with TestClient(server.app) as client:
        with client.websocket_connect('/ws', headers={'origin': 'http://testserver'}) as socket:
            socket.send_json({'type': 'auth', 'pin': server.DASHBOARD_PIN})
            assert socket.receive_json()['type'] == 'auth_ok'
            snapshot = socket.receive_json()
            socket.receive_json()
            document = {key: copy.deepcopy(snapshot[key]) for key in ('profiles', 'activeProfile')}
            document[marker] = 'ccs-dashboard-store' if marker == 'format' else 1
            socket.send_json({'type': 'profiles_save', 'revision': revision, 'document': document})
            assert socket.receive_json() == {'type': 'profiles_error', 'code': 'invalid'}
            socket.send_json({'type': 'diagnostics_request'})
            assert socket.receive_json()['type'] == 'diagnostics_data'
    assert server.profile_store.path.read_bytes() == original
    assert server.profile_store.revision == revision
