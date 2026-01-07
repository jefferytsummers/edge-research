"""
EventBus - Async event bus with Redis pub/sub integration.

Provides both intra-container async events and inter-container Redis messaging.
"""
import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from collections import defaultdict

import redis.asyncio as redis

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Event data structure."""
    type: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    stream_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "stream_id": self.stream_id
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Event":
        return cls(
            type=d["type"],
            data=d["data"],
            timestamp=datetime.fromisoformat(d["timestamp"]),
            stream_id=d.get("stream_id")
        )


class EventBus:
    """
    Async event bus with Redis pub/sub integration.

    Supports:
    - Local async event handlers
    - Redis pub/sub for inter-container messaging
    - Thread-safe emit for sync contexts
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self._handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._redis: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._queue: asyncio.Queue = asyncio.Queue()
        self.is_connected = False

    async def connect(self):
        """Connect to Redis."""
        try:
            self._redis = redis.from_url(self.redis_url)
            await self._redis.ping()
            self._pubsub = self._redis.pubsub()
            self._loop = asyncio.get_event_loop()
            self.is_connected = True
            logger.info(f"Connected to Redis at {self.redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.is_connected = False

    async def disconnect(self):
        """Disconnect from Redis."""
        if self._pubsub:
            await self._pubsub.close()
        if self._redis:
            await self._redis.close()
        self.is_connected = False
        logger.info("Disconnected from Redis")

    def on(self, event_type: str, handler: Callable):
        """Register an event handler."""
        self._handlers[event_type].append(handler)
        logger.debug(f"Registered handler for {event_type}")

    def off(self, event_type: str, handler: Callable):
        """Unregister an event handler."""
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)

    async def emit(self, event: Event):
        """Emit an event to local handlers."""
        handlers = self._handlers.get(event.type, [])
        handlers += self._handlers.get("*", [])  # Wildcard handlers

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Handler error for {event.type}: {e}")

    def emit_sync(self, event: Event):
        """Thread-safe emit for sync contexts (e.g., DeepStream callbacks)."""
        if self._loop:
            self._loop.call_soon_threadsafe(
                lambda: asyncio.create_task(self.emit(event))
            )

    async def publish(self, channel: str, event: Event):
        """Publish event to Redis channel."""
        if self._redis and self.is_connected:
            try:
                await self._redis.publish(channel, json.dumps(event.to_dict()))
                logger.debug(f"Published to {channel}: {event.type}")
            except Exception as e:
                logger.error(f"Failed to publish to {channel}: {e}")

    async def subscribe_redis(self, channels: List[str]):
        """Subscribe to Redis channels and emit events locally."""
        if not self._pubsub:
            logger.error("PubSub not initialized")
            return

        await self._pubsub.subscribe(*channels)
        logger.info(f"Subscribed to Redis channels: {channels}")

        try:
            async for message in self._pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        event = Event.from_dict(data)
                        await self.emit(event)
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON from Redis: {message['data']}")
                    except Exception as e:
                        logger.error(f"Error processing Redis message: {e}")
        except asyncio.CancelledError:
            logger.info("Redis subscriber cancelled")
        except Exception as e:
            logger.error(f"Redis subscriber error: {e}")
