"""
VLM Subscriber - Redis subscriber for VLM container.

Subscribes to detection events, runs VLM inference, publishes summaries.
"""
import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

import redis.asyncio as redis

from .protocol_evaluator import ProtocolConfig, ProtocolEvaluator, StreamStatus

logger = logging.getLogger(__name__)


class MultiStreamVLMSampler:
    """
    Round-robin VLM sampling across multiple streams.

    With N streams and ~500ms VLM latency, ensures fair sampling.
    """

    def __init__(
        self,
        streams: List[str],
        interval_per_stream: float = 10.0
    ):
        self.streams = streams
        self.interval = interval_per_stream  # seconds between VLM calls per stream
        self.current_index = 0
        self._last_sample: Dict[str, float] = {}

    def add_stream(self, stream_id: str):
        """Add a new stream to the rotation."""
        if stream_id not in self.streams:
            self.streams.append(stream_id)

    def remove_stream(self, stream_id: str):
        """Remove a stream from the rotation."""
        if stream_id in self.streams:
            self.streams.remove(stream_id)
            self._last_sample.pop(stream_id, None)

    def should_sample(self, stream_id: str) -> bool:
        """Check if stream should be sampled now."""
        now = time.time()
        last = self._last_sample.get(stream_id, 0)
        return (now - last) >= self.interval

    def mark_sampled(self, stream_id: str):
        """Mark stream as recently sampled."""
        self._last_sample[stream_id] = time.time()

    def next_stream(self) -> Optional[str]:
        """Get next stream to sample (round-robin)."""
        if not self.streams:
            return None

        # Find next stream that's ready for sampling
        for _ in range(len(self.streams)):
            stream_id = self.streams[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.streams)

            if self.should_sample(stream_id):
                return stream_id

        return None


class VLMSubscriber:
    """
    Main VLM service that subscribes to Redis and processes frames.
    """

    def __init__(
        self,
        redis_url: str,
        protocols: ProtocolConfig,
        frame_dir: str = "/shared/frames"
    ):
        self.redis_url = redis_url
        self.frame_dir = Path(frame_dir)
        self._redis: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None

        # VLM model (loaded on start)
        self._vlm = None

        # Protocol evaluator
        self.evaluator = ProtocolEvaluator(protocols, vlm_client=None)

        # Multi-stream sampler
        self.sampler = MultiStreamVLMSampler([], interval_per_stream=10.0)

        # Pending frames waiting for VLM
        self._pending_frames: Dict[str, Dict] = {}

    async def connect(self):
        """Connect to Redis."""
        self._redis = redis.from_url(self.redis_url)
        await self._redis.ping()
        self._pubsub = self._redis.pubsub()
        logger.info(f"VLM subscriber connected to Redis")

    async def disconnect(self):
        """Disconnect from Redis."""
        if self._pubsub:
            await self._pubsub.close()
        if self._redis:
            await self._redis.close()

    async def load_vlm(self):
        """Load VLM model."""
        # TODO: Load NanoLLM/VILA model
        # from nano_llm import NanoLLM
        # self._vlm = NanoLLM.from_pretrained("Efficient-Large-Model/VILA1.5-7b")
        logger.info("VLM model loaded (placeholder)")

    def _read_frame(self, stream_id: str) -> Optional[bytes]:
        """Read latest frame from shared volume."""
        frame_path = self.frame_dir / stream_id / "latest.jpg"
        try:
            if frame_path.exists():
                return frame_path.read_bytes()
        except Exception as e:
            logger.warning(f"Failed to read frame for {stream_id}: {e}")
        return None

    async def _describe_frame(self, frame_bytes: bytes) -> str:
        """Generate description using VLM."""
        # TODO: Implement VLM inference
        # if self._vlm:
        #     return await self._vlm.describe(frame_bytes)
        return "Person sitting calmly in room"  # Placeholder

    async def _process_detection(self, data: Dict):
        """Process incoming detection event."""
        stream_id = data.get("stream_id")
        detections = data.get("detections", [])
        frame_path = data.get("frame_path")

        if not stream_id:
            return

        # Add stream to sampler if new
        self.sampler.add_stream(stream_id)

        # Store pending frame data
        self._pending_frames[stream_id] = {
            "detections": detections,
            "frame_path": frame_path,
            "timestamp": data.get("timestamp", time.time())
        }

    async def _run_vlm_inference(self):
        """Run VLM inference on next ready stream."""
        stream_id = self.sampler.next_stream()
        if not stream_id or stream_id not in self._pending_frames:
            return

        pending = self._pending_frames[stream_id]
        detections = pending["detections"]

        # Read frame
        frame_bytes = self._read_frame(stream_id)
        if not frame_bytes:
            return

        # Generate description
        description = await self._describe_frame(frame_bytes)

        # Evaluate against protocols
        status = await self.evaluator.evaluate(
            stream_id=stream_id,
            description=description,
            detections=detections
        )

        # Publish summary if status changed
        if status:
            await self._publish_summary(status)

        # Mark as sampled
        self.sampler.mark_sampled(stream_id)

    async def _publish_summary(self, status: StreamStatus):
        """Publish status summary to Redis."""
        if self._redis:
            message = {
                "type": "summary.received",
                "stream_id": status.stream_id,
                "data": {
                    "severity": status.severity,
                    "icon": status.icon,
                    "description": status.description,
                    "confidence": status.confidence
                },
                "timestamp": time.time()
            }
            await self._redis.publish("summaries", json.dumps(message))
            logger.info(f"Published summary for {status.stream_id}: {status.severity}")

    async def run(self):
        """Main run loop."""
        await self.connect()
        await self.load_vlm()

        # Subscribe to detections channel
        await self._pubsub.subscribe("detections")
        logger.info("Subscribed to detections channel")

        # Create inference task
        inference_task = asyncio.create_task(self._inference_loop())

        try:
            async for message in self._pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        await self._process_detection(data)
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON: {message['data']}")
        except asyncio.CancelledError:
            inference_task.cancel()
            await self.disconnect()
        except Exception as e:
            logger.error(f"Subscriber error: {e}")
            inference_task.cancel()
            await self.disconnect()

    async def _inference_loop(self):
        """Background loop for VLM inference."""
        while True:
            try:
                await self._run_vlm_inference()
                await asyncio.sleep(0.5)  # ~500ms VLM inference time
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Inference error: {e}")
                await asyncio.sleep(1.0)


async def main():
    """Entry point for VLM service."""
    logging.basicConfig(level=logging.INFO)

    # Load protocols from config or use defaults
    protocols = ProtocolConfig(
        green_rules="Reading, watching TV, sleeping normally in bed, eating meals, sitting calmly",
        yellow_rules="Out of camera view, crouching in corners, minor injuries, pacing erratically",
        red_rules="Unconscious on ground, severe injury, room is empty, self-harm behavior"
    )

    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
    subscriber = VLMSubscriber(redis_url, protocols)

    await subscriber.run()


if __name__ == "__main__":
    asyncio.run(main())
