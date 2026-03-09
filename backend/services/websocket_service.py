import asyncio


class WebSocketService:
    """
    Lógica de transmisión en tiempo real.
    """

    @staticmethod
    async def stream_redis_channel(websocket, pubsub):
        try:
            while True:
                message = pubsub.get_message(ignore_subscribe_messages=True)
                if message:
                    await websocket.send_text(message["data"])
                await asyncio.sleep(0.1)
        except Exception:
            raise