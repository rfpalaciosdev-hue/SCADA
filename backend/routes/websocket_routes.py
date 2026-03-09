from fastapi import APIRouter, WebSocket
from repositories.websocket_repository import WebSocketRepository
from services.websocket_service import WebSocketService

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("🔌 Cliente conectado al WebSocket")

    channel = "live_updates"
    pubsub = WebSocketRepository.subscribe(channel)

    try:
        await WebSocketService.stream_redis_channel(websocket, pubsub)
    except Exception as e:
        print(f"❌ WS Disconnected/Error: {e}")
    finally:
        WebSocketRepository.unsubscribe(pubsub, channel)