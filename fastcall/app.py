import json
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from typing import Dict, List, Optional

app = FastAPI()

app.mount("/static", StaticFiles(directory="fastcall/static"), name="static")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.rooms: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_name: str):
        await websocket.accept()
        if room_name not in self.rooms:
            self.rooms[room_name] = []
        self.rooms[room_name].append(websocket)
        logger.info(f"Client {websocket.client} connected to room {room_name}")

    def disconnect(self, websocket: WebSocket, room_name: str):
        self.rooms[room_name].remove(websocket)
        if not self.rooms[room_name]:  # Remove room if empty
            del self.rooms[room_name]
        logger.info(f"Client {websocket.client} disconnected from room {room_name}")

    async def broadcast(
        self, room_name: str, message: dict, sender: Optional[WebSocket] = None
    ):
        for connection in self.rooms.get(room_name, []):
            if connection != sender:
                await connection.send_text(json.dumps(message))


manager = ConnectionManager()


@app.websocket("/ws/{room_name}/{client_id}")
async def websocket_endpoint(websocket: WebSocket, room_name: str, client_id: str):
    await manager.connect(websocket, room_name)
    try:
        while True:
            # Receive JSON data from a client
            data = await websocket.receive_text()
            message = json.loads(data)
            message_type = message.get("type")
            # logger.info(f"Received message in room {room_name} from {client_id}: {message}")

            # Handle the message based on its type
            if message_type == "join":
                await handle_join(room_name, message, websocket)
            elif message_type == "offer":
                await handle_offer(room_name, message, websocket)
            elif message_type == "answer":
                await handle_answer(room_name, message, websocket)
            elif message_type == "candidate":
                await handle_candidate(room_name, message, websocket)
            elif message_type == "chat":
                await handle_chat_message(room_name, message, websocket)
            else:
                logger.warning(f"Unknown message type received: {message_type}")

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_name)
        logger.info(f"WebSocket connection closed for {client_id} in room {room_name}")
    except Exception as e:
        logger.error(f"Error with client {client_id} in room {room_name}: {e}")
        await websocket.close()


async def handle_join(room_name: str, join_data: dict, websocket: WebSocket):
    logger.info(f"{websocket.client} sent join message: ")
    await manager.broadcast(room_name, join_data, sender=websocket)


async def handle_offer(room_name: str, offer_data: dict, websocket: WebSocket):
    logger.info(f"{websocket.client} sent offer data: ")
    await manager.broadcast(room_name, offer_data, sender=websocket)


async def handle_answer(room_name: str, answer_data: dict, websocket: WebSocket):
    logger.info(f"{websocket.client} sent answer data: ")
    await manager.broadcast(room_name, answer_data, sender=websocket)


async def handle_candidate(room_name: str, candidate_data: dict, websocket: WebSocket):
    logger.info(f"{websocket.client} sent ICE candidate:")
    await manager.broadcast(room_name, candidate_data, sender=websocket)


async def handle_chat_message(room_name: str, chat_data: dict, websocket: WebSocket):
    logger.info(f"{websocket.client} sent chat message: ")
    await manager.broadcast(room_name, chat_data, sender=websocket)
