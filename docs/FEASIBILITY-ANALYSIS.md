# Feasibility Analysis: Event-Driven Architecture

## Research Summary

After reviewing NVIDIA's documentation, sample applications, and architecture patterns, here's what we found about implementing an event-driven approach.

---

## Key Findings

### 1. DeepStream Probe Callbacks Are Synchronous

From [DeepStream Python docs](https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_Python_Sample_Apps.html):

> "Probe callbacks are synchronous and hold the buffer from traversing the pipeline until user returns. Loops inside probe callbacks could be costly in Python."

**Implication:** We cannot do async work directly in DeepStream probes. We need a bridging mechanism.

### 2. NanoLLM Has Its Own Plugin Architecture

From [NanoLLM Plugins docs](https://dusty-nv.github.io/NanoLLM/plugins.html):

> "Plugins receive input into a processing queue, process it, and output results across output channels. By default plugins are threaded and run off their own queue."

**Key insight:** NanoLLM already implements an event-like pattern with:
- **Threaded queues** for async processing
- **Output channels** (Delta, Partial, Final, etc.)
- **Plugin chaining** for pipeline composition

### 3. NanoLLM Uses jetson-utils, NOT DeepStream

NanoLLM's `VideoSource` plugin uses `jetson-utils` for video input, which is a **different** video pipeline than DeepStream.

```
DeepStream:     GStreamer → nvdec → nvinfer → nvmsgbroker
NanoLLM:        jetson-utils → VideoSource → Plugin chain
```

### 4. Jetson Platform Services Uses Microservice Architecture

From [JPS docs](https://docs.nvidia.com/jetson/jps/):

> "Services run as containers, deployed as a bundle using docker-compose. VLM output is sent over WebSocket to integrate with other services."

JPS runs DeepStream and VLM as **separate containers** communicating via REST/WebSocket.

---

## Architecture Options

### Option A: NanoLLM-Native (Recommended for MVP)

Use NanoLLM's existing plugin architecture as our foundation.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         NanoLLM Plugin Pipeline                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  VideoSource ───► [Custom Detector Plugin] ───► [VLM Plugin]            │
│       │                    │                         │                   │
│       │                    │                         │                   │
│       ▼                    ▼                         ▼                   │
│  frame output         detection output          summary output           │
│       │                    │                         │                   │
│       └────────────────────┴─────────────────────────┘                   │
│                            │                                             │
│                            ▼                                             │
│                    [Event Adapter Plugin]                                │
│                            │                                             │
│                            ▼                                             │
│                      Our EventBus                                        │
│                            │                                             │
│              ┌─────────────┼─────────────┐                              │
│              ▼             ▼             ▼                              │
│          FastAPI      AlertChecker    Memory                            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Pros:**
- NanoLLM already handles video → VLM pipeline
- Plugin threading model aligns with our needs
- Built-in RTSP/camera support via jetson-utils
- Optimized for Jetson

**Cons:**
- Need to add YOLO detection as custom plugin
- Less flexible than pure DeepStream for multi-stream

**Feasibility: HIGH**

### Option B: DeepStream + Bridge Pattern

Use DeepStream for video/detection, bridge to async Python for VLM.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    DeepStream Pipeline                           │    │
│  │  RTSP → nvdec → nvinfer(YOLO) → probe → nvmsgbroker             │    │
│  └──────────────────────────────────┬──────────────────────────────┘    │
│                                     │                                    │
│                              (sync callback)                             │
│                                     │                                    │
│                                     ▼                                    │
│                          ┌──────────────────┐                           │
│                          │  Thread-safe     │                           │
│                          │  Queue           │                           │
│                          └────────┬─────────┘                           │
│                                   │                                      │
│                            (async consumer)                              │
│                                   │                                      │
│                                   ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                       Async Event Bus                            │    │
│  │                                                                  │    │
│  │   frame.new → Sampler → VLM → summary.new                       │    │
│  │   detection.complete → AlertChecker → alert.triggered           │    │
│  │   query.received → Agent → response.ready                       │    │
│  │                                                                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**Pros:**
- DeepStream optimized for multi-stream video
- nvmsgbroker can directly publish to Kafka/Redis
- More control over detection pipeline

**Cons:**
- GLib main loop ↔ asyncio integration complexity
- Two different threading models to manage
- More moving parts

**Feasibility: MEDIUM** (more integration work)

### Option C: Microservice Architecture (JPS-style)

Separate containers for DeepStream and VLM, communicate via messaging.

```
┌─────────────────────┐     ┌─────────────────────┐
│  DeepStream         │     │  VLM Service        │
│  Container          │     │  Container          │
│                     │     │                     │
│  RTSP → Detection   │     │  NanoLLM + VILA     │
│         │           │     │         ▲           │
│         ▼           │     │         │           │
│    nvmsgbroker ─────┼─────┼────► REST API       │
│                     │     │         │           │
└─────────────────────┘     │         ▼           │
                            │    Summaries        │
                            └─────────────────────┘
           │                          │
           ▼                          ▼
    ┌─────────────────────────────────────────────┐
    │              Redis Pub/Sub                   │
    │                                              │
    │  Channels: detections, summaries, alerts    │
    └─────────────────────────────────────────────┘
           │                          │
           ▼                          ▼
    ┌─────────────────────────────────────────────┐
    │           Application Service               │
    │                                              │
    │  FastAPI + WebSocket + Agent                │
    └─────────────────────────────────────────────┘
```

**Pros:**
- True microservice isolation
- Proven by JPS reference architecture
- Easy to scale/replace components

**Cons:**
- More containers = more resource overhead
- Network latency between services
- More complex deployment

**Feasibility: HIGH** (but heavier weight for MVP)

---

## Recommended Approach: Hybrid (A + elements of B)

For MVP, we recommend **adapting our EventBus to work with NanoLLM's plugin model**:

### Core Architecture

```python
# Our EventBus wraps NanoLLM's plugin output system

class EventBusPlugin(Plugin):
    """Bridge between NanoLLM plugins and our EventBus."""

    def __init__(self, event_bus: EventBus):
        super().__init__(outputs=['events'])
        self.bus = event_bus

    def process(self, input, **kwargs):
        """Convert plugin outputs to EventBus events."""
        if isinstance(input, Detection):
            self.bus.emit_sync(Event("detection.complete", input))
        elif isinstance(input, str):  # VLM output
            self.bus.emit_sync(Event("summary.new", {"text": input}))

        # Also forward through plugin system
        self.output(input)
```

### Video Pipeline Using NanoLLM

```python
from nano_llm import NanoLLM, ChatHistory
from nano_llm.plugins import VideoSource, VideoOutput

# Video input via jetson-utils (supports RTSP, USB, files)
video = VideoSource(video_source)

# Detection as custom plugin
detector = YOLODetector(model="yolov8s", precision="int8")

# VLM via NanoLLM
vlm = NanoLLM.from_pretrained("Efficient-Large-Model/VILA1.5-7b")

# Our bridge to EventBus
bridge = EventBusPlugin(event_bus)

# Connect pipeline
video.add(detector)
detector.add(vlm)
detector.add(bridge)  # Detections to EventBus
vlm.add(bridge)       # Summaries to EventBus
```

### What Changes in AGILE Plan

| Original | Updated |
|----------|---------|
| Epic 2: Event Bus | Keep, but add NanoLLM plugin adapter |
| Epic 3: DeepStream pipeline | Change to NanoLLM VideoSource |
| Epic 4: nvinfer detection | Custom NanoLLM plugin with TensorRT |
| Epic 5: VLM integration | Use NanoLLM native, already done |

---

## Technical Concerns & Mitigations

### Concern 1: Sync → Async Bridging

**Issue:** NanoLLM plugins are threaded, our EventBus is async.

**Mitigation:**
```python
def emit_sync(self, event: Event):
    """Thread-safe emit for sync contexts."""
    self._loop.call_soon_threadsafe(
        lambda: asyncio.create_task(self._queue.put(event))
    )
```

### Concern 2: Detection Performance

**Issue:** NanoLLM doesn't include detection out-of-box.

**Mitigation:** Create a detection plugin using TensorRT directly:
```python
class YOLODetectorPlugin(Plugin):
    def __init__(self, model_path, precision="int8"):
        super().__init__(outputs=['detections'])
        self.engine = TensorRTEngine(model_path, precision)

    def process(self, frame, **kwargs):
        detections = self.engine.detect(frame)
        self.output(detections)
```

### Concern 3: Multi-Stream Support

**Issue:** NanoLLM VideoSource is single-stream focused.

**Mitigation:** For MVP, single stream is fine. For multi-stream (V2), could:
- Run multiple VideoSource instances
- Or switch to DeepStream for video decode only

### Concern 4: Video Frame Rate vs VLM Rate

**Issue:** VLM is slow (~500ms), video is fast (30fps).

**Mitigation:** Already in plan - Sampler plugin decimates frames:
```python
class SamplerPlugin(Plugin):
    def __init__(self, interval_ms=10000):
        self.interval = interval_ms
        self.last_sample = 0

    def process(self, frame, **kwargs):
        now = time.time() * 1000
        if now - self.last_sample >= self.interval:
            self.last_sample = now
            self.output(frame)  # Only emit periodically
```

---

## Verdict: FEASIBLE with Modifications

The event-driven approach **is feasible**, but we should:

1. **Use NanoLLM's plugin architecture** as the foundation (not pure DeepStream)
2. **Create an EventBus adapter plugin** that bridges to our async EventBus
3. **Add detection as a custom NanoLLM plugin** using TensorRT
4. **Keep the EventBus for application-level events** (alerts, queries, responses)

### Updated Component Mapping

| Component | Original Plan | Updated Plan |
|-----------|---------------|--------------|
| Video Input | DeepStream | NanoLLM VideoSource (jetson-utils) |
| Detection | DeepStream nvinfer | Custom TensorRT Plugin |
| VLM | NanoLLM (standalone) | NanoLLM Plugin |
| Pipeline Orchestration | Our EventBus | NanoLLM Plugin Chain |
| App-Level Events | Our EventBus | Our EventBus (via adapter) |
| API/WebSocket | FastAPI async | FastAPI async |

---

## References

- [DeepStream Python Apps](https://github.com/NVIDIA-AI-IOT/deepstream_python_apps)
- [NanoLLM Plugins](https://dusty-nv.github.io/NanoLLM/plugins.html)
- [NanoLLM Agents](https://dusty-nv.github.io/NanoLLM/agents.html)
- [Jetson Platform Services](https://docs.nvidia.com/jetson/jps/)
- [jetson-utils VideoSource](https://github.com/dusty-nv/jetson-utils)

---

*Feasibility Analysis - January 2026*
