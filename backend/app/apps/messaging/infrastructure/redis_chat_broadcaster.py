import json
import uuid

import redis.asyncio as aioredis

from app.apps.messaging.domain.entities import Message
from app.apps.messaging.domain.repositories import ChatBroadcaster


def channel_name(job_id: uuid.UUID) -> str:
    """Shared with the WebSocket route, which subscribes to this same
    channel name to receive what this broadcaster publishes."""
    return f"chat:{job_id}"


def _message_to_json(message: Message) -> str:
    return json.dumps(
        {
            "id": str(message.id),
            "job_id": str(message.job_id),
            "sender_id": str(message.sender_id),
            "message_type": message.message_type.value,
            "body": message.body,
            "media_url": message.media_url,
            "duration_seconds": message.duration_seconds,
            "latitude": str(message.latitude) if message.latitude is not None else None,
            "longitude": str(message.longitude) if message.longitude is not None else None,
            "created_at": message.created_at.isoformat() if message.created_at else None,
            "read_at": message.read_at.isoformat() if message.read_at else None,
        }
    )


class RedisChatBroadcaster(ChatBroadcaster):
    def __init__(self, redis_client: aioredis.Redis) -> None:
        self._redis = redis_client

    async def publish(self, job_id: uuid.UUID, message: Message) -> None:
        await self._redis.publish(channel_name(job_id), _message_to_json(message))
