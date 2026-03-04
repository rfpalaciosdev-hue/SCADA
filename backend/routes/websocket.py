import asyncio
from fastapi import APIRouter, WebSocket

from config import r

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("🔌 Cliente conectado al WebSocket")
    pubsub = r.pubsub()
    pubsub.subscribe("live_updates")
    try:
        while True:
            message = pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                await websocket.send_text(message["data"])
            await asyncio.sleep(0.1)
    except Exception as e:
        print(f"❌ WS Disconnected/Error: {e}")
    finally:
        pubsub.unsubscribe("live_updates")
        pubsub.close()
