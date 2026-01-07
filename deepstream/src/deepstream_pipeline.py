#!/usr/bin/env python3
"""
DeepStream Pipeline Runner - RTSP to Redis
==========================================

This script creates a DeepStream pipeline that:
1. Reads from an RTSP source
2. Runs person detection using PeopleNet
3. Extracts frames and detection metadata
4. Publishes to Redis for VLM processing

Environment variables:
    RTSP_URI: RTSP stream URL (required)
    REDIS_URL: Redis connection URL (default: redis://redis:6379)
    STREAM_ID: Identifier for this stream (default: stream_0)
    SAMPLE_INTERVAL: Frames between Redis publishes (default: 30)
"""
import sys
import os
import json
import time
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# GStreamer/DeepStream imports (available in NGC container)
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GLib

import pyds
import redis
import cv2
import numpy as np

# Configuration from environment
RTSP_URI = os.environ.get('RTSP_URI', 'rtsp://localhost:8554/webcam')
REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379')
STREAM_ID = os.environ.get('STREAM_ID', 'stream_0')
SAMPLE_INTERVAL = int(os.environ.get('SAMPLE_INTERVAL', '30'))

# Shared frame directory
FRAME_DIR = Path('/shared/frames')
FRAME_DIR.mkdir(parents=True, exist_ok=True)

# Global Redis client
redis_client = None

# Frame counter for sampling
frame_counter = 0


def get_redis():
    """Get or create Redis connection."""
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(REDIS_URL)
        redis_client.ping()
        logger.info(f"Connected to Redis at {REDIS_URL}")
    return redis_client


def save_frame(stream_id: str, frame: np.ndarray) -> str:
    """Save frame to shared volume."""
    stream_dir = FRAME_DIR / stream_id
    stream_dir.mkdir(parents=True, exist_ok=True)
    frame_path = stream_dir / "latest.jpg"
    cv2.imwrite(str(frame_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return str(frame_path)


def publish_detection(stream_id: str, frame_path: str, detections: list):
    """Publish detection event to Redis."""
    try:
        r = get_redis()
        message = {
            "type": "detection.received",
            "stream_id": stream_id,
            "frame_path": frame_path,
            "detections": detections,
            "timestamp": time.time()
        }
        r.publish("detections", json.dumps(message))
        logger.debug(f"Published {len(detections)} detections for {stream_id}")
    except Exception as e:
        logger.error(f"Failed to publish: {e}")


def osd_sink_pad_buffer_probe(pad, info, u_data):
    """
    Probe callback on OSD sink pad.
    Extracts metadata from each frame in the batch.
    """
    global frame_counter

    gst_buffer = info.get_buffer()
    if not gst_buffer:
        return Gst.PadProbeReturn.OK

    batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))

    l_frame = batch_meta.frame_meta_list
    while l_frame is not None:
        try:
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
        except StopIteration:
            break

        frame_counter += 1

        # Only process every SAMPLE_INTERVAL frames
        if frame_counter % SAMPLE_INTERVAL != 0:
            try:
                l_frame = l_frame.next
            except StopIteration:
                break
            continue

        # Extract detections
        detections = []
        l_obj = frame_meta.obj_meta_list
        while l_obj is not None:
            try:
                obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
                detections.append({
                    "class_id": obj_meta.class_id,
                    "class_name": obj_meta.obj_label if obj_meta.obj_label else f"class_{obj_meta.class_id}",
                    "confidence": round(obj_meta.confidence, 3),
                    "bbox": [
                        int(obj_meta.rect_params.left),
                        int(obj_meta.rect_params.top),
                        int(obj_meta.rect_params.left + obj_meta.rect_params.width),
                        int(obj_meta.rect_params.top + obj_meta.rect_params.height)
                    ]
                })
                l_obj = l_obj.next
            except StopIteration:
                break

        # Get frame data using nvbufsurface
        n_frame = pyds.get_nvds_buf_surface(hash(gst_buffer), frame_meta.batch_id)

        # Convert to numpy array (RGBA format)
        frame = np.array(n_frame, copy=True, order='C')

        # Convert RGBA to BGR for OpenCV
        frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)

        # Save frame and publish
        frame_path = save_frame(STREAM_ID, frame)
        publish_detection(STREAM_ID, frame_path, detections)

        logger.info(f"Frame {frame_counter}: {len(detections)} detections")

        try:
            l_frame = l_frame.next
        except StopIteration:
            break

    return Gst.PadProbeReturn.OK


def bus_call(bus, message, loop):
    """Handle GStreamer bus messages."""
    t = message.type
    if t == Gst.MessageType.EOS:
        logger.info("End of stream")
        loop.quit()
    elif t == Gst.MessageType.WARNING:
        err, debug = message.parse_warning()
        logger.warning(f"Warning: {err}: {debug}")
    elif t == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        logger.error(f"Error: {err}: {debug}")
        loop.quit()
    elif t == Gst.MessageType.STATE_CHANGED:
        if message.src.get_name() == "pipeline":
            old, new, pending = message.parse_state_changed()
            logger.info(f"Pipeline state: {old.value_nick} -> {new.value_nick}")
    return True


def create_pipeline():
    """Create the DeepStream pipeline."""
    logger.info(f"Creating pipeline for {RTSP_URI}")

    Gst.init(None)

    # Create pipeline
    pipeline = Gst.Pipeline.new("pipeline")
    if not pipeline:
        raise RuntimeError("Failed to create pipeline")

    # Source - RTSP
    source = Gst.ElementFactory.make("rtspsrc", "source")
    source.set_property("location", RTSP_URI)
    source.set_property("latency", 100)
    source.set_property("drop-on-latency", True)

    # RTP depayloader
    depay = Gst.ElementFactory.make("rtph264depay", "depay")

    # H264 parser
    parse = Gst.ElementFactory.make("h264parse", "parse")

    # NVDEC decoder
    decoder = Gst.ElementFactory.make("nvv4l2decoder", "decoder")

    # Stream muxer
    streammux = Gst.ElementFactory.make("nvstreammux", "streammux")
    streammux.set_property("width", 1280)
    streammux.set_property("height", 720)
    streammux.set_property("batch-size", 1)
    streammux.set_property("batched-push-timeout", 40000)
    streammux.set_property("live-source", True)

    # Primary inference (nvinfer)
    pgie = Gst.ElementFactory.make("nvinfer", "pgie")
    pgie.set_property("config-file-path", "/app/config/nvinfer_config.txt")

    # Converter for OSD
    nvvidconv = Gst.ElementFactory.make("nvvideoconvert", "nvvidconv")

    # OSD (on-screen display)
    nvosd = Gst.ElementFactory.make("nvdsosd", "nvosd")

    # Another converter for output
    nvvidconv2 = Gst.ElementFactory.make("nvvideoconvert", "nvvidconv2")

    # Fake sink (we only need metadata)
    sink = Gst.ElementFactory.make("fakesink", "sink")
    sink.set_property("sync", False)
    sink.set_property("async", False)

    # Add elements to pipeline
    elements = [source, depay, parse, decoder, streammux, pgie, nvvidconv, nvosd, nvvidconv2, sink]
    for elem in elements:
        if not elem:
            raise RuntimeError(f"Failed to create element: {elem}")
        pipeline.add(elem)

    # Link static elements
    # Note: rtspsrc uses dynamic pads, handled via callback
    depay.link(parse)
    parse.link(decoder)

    # Link decoder to streammux sink pad
    sinkpad = streammux.get_request_pad("sink_0")
    srcpad = decoder.get_static_pad("src")
    srcpad.link(sinkpad)

    # Link rest of pipeline
    streammux.link(pgie)
    pgie.link(nvvidconv)
    nvvidconv.link(nvosd)
    nvosd.link(nvvidconv2)
    nvvidconv2.link(sink)

    # Handle rtspsrc dynamic pads
    def on_pad_added(src, new_pad, depay):
        caps = new_pad.get_current_caps()
        struct = caps.get_structure(0)
        if struct.get_name().startswith("application/x-rtp"):
            sink_pad = depay.get_static_pad("sink")
            if not sink_pad.is_linked():
                new_pad.link(sink_pad)
                logger.info("RTSP source linked")

    source.connect("pad-added", on_pad_added, depay)

    # Add probe to OSD sink pad
    osdsinkpad = nvosd.get_static_pad("sink")
    if osdsinkpad:
        osdsinkpad.add_probe(Gst.PadProbeType.BUFFER, osd_sink_pad_buffer_probe, 0)
    else:
        logger.warning("Could not get OSD sink pad for probe")

    return pipeline


def main():
    """Main entry point."""
    logger.info("Starting DeepStream pipeline")
    logger.info(f"RTSP URI: {RTSP_URI}")
    logger.info(f"Stream ID: {STREAM_ID}")
    logger.info(f"Sample interval: {SAMPLE_INTERVAL} frames")

    # Test Redis connection
    try:
        get_redis()
    except Exception as e:
        logger.error(f"Cannot connect to Redis: {e}")
        sys.exit(1)

    # Create pipeline
    pipeline = create_pipeline()

    # Create event loop
    loop = GLib.MainLoop()

    # Add bus watch
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", bus_call, loop)

    # Start pipeline
    logger.info("Starting pipeline...")
    ret = pipeline.set_state(Gst.State.PLAYING)
    if ret == Gst.StateChangeReturn.FAILURE:
        logger.error("Failed to set pipeline to PLAYING")
        sys.exit(1)

    try:
        loop.run()
    except KeyboardInterrupt:
        logger.info("Interrupted")
    finally:
        pipeline.set_state(Gst.State.NULL)
        logger.info("Pipeline stopped")


if __name__ == "__main__":
    main()
