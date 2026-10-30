"""Identity-only GSI packets are not evidence of fresh match data."""
from fastapi.testclient import TestClient
import pytest
from tests.integration.test_profile_publication_ws import target, authenticate


def test_identity_only_signal_does_not_claim_active_match(target):
    server, _adapter = target
    with TestClient(server.app) as client:
        with client.websocket_connect('/ws',headers={'origin':'http://testserver'}) as socket:
            authenticate(socket,server)
            response=client.post('/gsi',json={'auth':{'token':server.GSI_TOKEN},
                'provider':{'name':'Synthetic CS2'},'player':{'name':'Synthetic menu','activity':'menu'}})
            assert response.status_code==200
            snapshot=socket.receive_json()
            assert snapshot['gsi_connected'] is True
            assert snapshot['online'] is False
            assert snapshot['player']['health'] is None


def test_identity_updates_do_not_extend_old_match_lifetime(target,monkeypatch):
    server,_adapter=target
    server.update_from_gsi({'player':{'state':{'health':0,'armor':0}}},100.0)
    assert server.last_game_seen==100.0
    server.update_from_gsi({'player':{'name':'Synthetic identity update','activity':'menu'}},115.0)
    assert server.last_seen==115.0
    assert server.last_game_seen==100.0
    monkeypatch.setattr(server.time,'monotonic',lambda:121.0)
    snapshot=server.summary()
    assert snapshot['gsi_connected'] is True
    assert snapshot['online'] is False
    assert snapshot['player']['health'] is None


@pytest.mark.parametrize('payload', [
    {'map':{'name':'de_synthetic'}}, {'round':{'phase':'freezetime'}},
    {'player':{'state':{'health':0}}}, {'player':{'match_stats':{'kills':0}}},
    {'player':{'weapons':{'weapon_0':{'name':'weapon_knife','state':'active'}}}},
])
def test_partial_game_payload_still_refreshes_match_data(target,payload):
    server,_adapter=target
    server.update_from_gsi(payload,100.0)
    assert server.last_seen==100.0
    assert server.last_game_seen==100.0
