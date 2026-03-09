from core.config import r


class WebSocketRepository:
    """
    Maneja la suscripción a canales Redis (Pub/Sub).
    """

    @staticmethod
    def subscribe(channel: str):
        pubsub = r.pubsub()
        pubsub.subscribe(channel)
        return pubsub

    @staticmethod
    def unsubscribe(pubsub, channel: str):
        pubsub.unsubscribe(channel)
        pubsub.close()