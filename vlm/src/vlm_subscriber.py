"""
VLM Subscriber - Redis subscriber for VLM container.

Subscribes to detection events, runs VLM inference, publishes summaries.
Uses NanoLLM/VILA for vision-language understanding.
"""
import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

import redis.asyncio as redis
from PIL import Image

from .protocol_evaluator import ProtocolConfig, ProtocolEvaluator, StreamStatus

logger = logging.getLogger(__name__)

# Configuration
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
VLM_MODEL = os.environ.get('VLM_MODEL', 'Efficient-Large-Model/VILA1.5-3b')
FRAME_DIR = Path(os.environ.get('FRAME_DIR', '/shared/frames'))


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


class NanoLLMWrapper:
    """
    Wrapper for NanoLLM/VILA model.

    Handles model loading and inference.
    """

    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = None
        self._loaded = False

    def load(self):
        """Load the VLM model."""
        try:
            from nano_llm import NanoLLM
            logger.info(f"Loading VLM model: {self.model_name}")
            self._model = NanoLLM.from_pretrained(
                self.model_name,
                quantization='q4f16_ft'  # Quantized for Jetson
            )
            self._loaded = True
            logger.info("VLM model loaded successfully")
        except ImportError:
            logger.warning("nano_llm not available - using mock mode")
            self._loaded = False
        except Exception as e:
            logger.error(f"Failed to load VLM model: {e}")
            self._loaded = False

    def describe(self, image_path: str, prompt: str = None) -> str:
        """
        Generate description for an image.

        Args:
            image_path: Path to the image file
            prompt: Optional prompt for the model

        Returns:
            Text description of the image
        """
        if not self._loaded or self._model is None:
            # Mock response for testing
            return "Person sitting calmly in room. No immediate concerns detected."

        try:
            # Load image
            image = Image.open(image_path)

            # Default prompt for scene description
            if prompt is None:
                prompt = (
                    "Describe what you see in this image. "
                    "Focus on: people present, their activities, posture, "
                    "and any safety concerns. Be concise."
                )

            # Run inference
            response = self._model.generate(
                prompt,
                image=image,
                max_new_tokens=100
            )

            return response
        except Exception as e:
            logger.error(f"VLM inference failed: {e}")
            return "Unable to analyze image"

    def classify(self, image_path: str, protocols: ProtocolConfig) -> str:
        """
        Classify scene against protocols.

        Args:
            image_path: Path to the image file
            protocols: User-defined behavioral protocols

        Returns:
            Classification string: "SEVERITY|ICON|MESSAGE"
        """
        if not self._loaded or self._model is None:
            # Mock response for testing
            return "GREEN|calm|Person sitting calmly, no concerns"

        try:
            image = Image.open(image_path)

            prompt = f"""Analyze this image and classify the situation.

User's protocols:
- GREEN (safe): {protocols.green_rules}
- YELLOW (attention): {protocols.yellow_rules}
- RED (critical): {protocols.red_rules}

Respond with EXACTLY this format (one line):
SEVERITY|ICON|MESSAGE

Where:
- SEVERITY is one of: GREEN, YELLOW, RED
- ICON is one word: reading, tv, sleeping, eating, calm, exercise, unclear, injury, distress, pacing, emergency, missing, danger, unconscious
- MESSAGE is a brief one-sentence status

Example: GREEN|reading|Resident reading in rocking chair."""

            response = self._model.generate(
                prompt,
                image=image,
                max_new_tokens=50
            )

            # Parse and validate response
            response = response.strip().split('\n')[0]  # Take first line
            parts = response.split('|')
            if len(parts) >= 3:
                return response

            # Fallback if parsing fails
            return "YELLOW|unclear|Unable to determine status clearly"

        except Exception as e:
            logger.error(f"VLM classification failed: {e}")
            return "YELLOW|unclear|Error analyzing image"


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

        # VLM model
        self._vlm = NanoLLMWrapper(VLM_MODEL)

        # Protocol evaluator
        self.evaluator = ProtocolEvaluator(protocols, vlm_client=self._vlm)

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

    def load_vlm(self):
        """Load VLM model (synchronous, done at startup)."""
        self._vlm.load()

    def _read_frame_path(self, stream_id: str) -> Optional[str]:
        """Get path to latest frame for stream."""
        frame_path = self.frame_dir / stream_id / "latest.jpg"
        if frame_path.exists():
            return str(frame_path)
        return None

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
        frame_path = pending.get("frame_path") or self._read_frame_path(stream_id)

        if not frame_path or not Path(frame_path).exists():
            logger.warning(f"No frame available for {stream_id}")
            return

        # Classify using VLM
        classification = self._vlm.classify(frame_path, self.evaluator.protocols)

        # Parse response
        status = self.evaluator._parse_response(stream_id, classification)

        # Apply state machine debouncing
        sm = self.evaluator._get_state_machine(stream_id)
        if sm.update(status.severity):
            await self._publish_summary(status)
        else:
            # Still publish status update even if severity unchanged
            # (description may have changed)
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
            logger.info(f"Published summary for {status.stream_id}: {status.severity} - {status.description}")

    async def run(self):
        """Main run loop."""
        await self.connect()

        # Load VLM model (blocking, done once at startup)
        logger.info("Loading VLM model...")
        self.load_vlm()
        logger.info("VLM model ready")

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
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Load protocols from config or use defaults
    protocols = ProtocolConfig(
        green_rules="Reading, watching TV, sleeping normally in bed, eating meals, sitting calmly",
        yellow_rules="Out of camera view, crouching in corners, minor injuries, pacing erratically",
        red_rules="Unconscious on ground, severe injury, room is empty, self-harm behavior"
    )

    subscriber = VLMSubscriber(REDIS_URL, protocols, str(FRAME_DIR))

    logger.info("Starting VLM subscriber service")
    logger.info(f"Redis URL: {REDIS_URL}")
    logger.info(f"VLM Model: {VLM_MODEL}")
    logger.info(f"Frame directory: {FRAME_DIR}")

    await subscriber.run()


if __name__ == "__main__":
    asyncio.run(main())
