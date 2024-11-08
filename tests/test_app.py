import json
import pytest
from fastapi.testclient import TestClient
from fastcall.app import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_websocket_connect():
    room_name = "testroom"
    client_id = "testclient"
    
    # Synchronous connection
    with client.websocket_connect(f"/ws/{room_name}/{client_id}") as websocket:
        # Test if the connection was successful
        assert websocket is not None, "WebSocket connection failed"

@pytest.mark.asyncio
async def test_broadcast_offer():
    room_name = "testroom"
    client_id = "client1"

    # Synchronous connections
    with client.websocket_connect(f"/ws/{room_name}/{client_id}") as websocket1:
        with client.websocket_connect(f"/ws/{room_name}/client2") as websocket2:
            # Send offer message
            offer_message = json.dumps({
                "type": "offer",
                "sdp": "fake_sdp"
            })
            websocket1.send_text(offer_message)

            # Receive message on second websocket connection
            response = websocket2.receive_text()
            received_message = json.loads(response)
            
            # Verify that the message broadcast is correct
            assert received_message["type"] == "offer"
            assert received_message["sdp"] == "fake_sdp"

@pytest.mark.asyncio
async def test_handle_join():
    room_name = "testroom"
    client_id = "client1"

    # Synchronous connections
    with client.websocket_connect(f"/ws/{room_name}/{client_id}") as websocket1:
        with client.websocket_connect(f"/ws/{room_name}/client2") as websocket2:
            # Send join message
            join_message = json.dumps({
                "type": "join",
                "username": "client1"
            })
            websocket1.send_text(join_message)

            # Receive join message on second websocket connection
            response = websocket2.receive_text()
            received_message = json.loads(response)
            
            # Verify the message type and content
            assert received_message["type"] == "join"
            assert received_message["username"] == "client1"

@pytest.mark.asyncio
async def test_handle_candidate():
    room_name = "testroom"
    client_id = "client1"

    # Synchronous connections
    with client.websocket_connect(f"/ws/{room_name}/{client_id}") as websocket1:
        with client.websocket_connect(f"/ws/{room_name}/client2") as websocket2:
            # Send candidate message
            candidate_message = json.dumps({
                "type": "candidate",
                "candidate": "fake_candidate"
            })
            websocket1.send_text(candidate_message)

            # Receive candidate message on second websocket connection
            response = websocket2.receive_text()
            received_message = json.loads(response)
            
            # Verify the message type and content
            assert received_message["type"] == "candidate"
            assert received_message["candidate"] == "fake_candidate"
