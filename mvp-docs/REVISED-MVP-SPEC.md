# Revised MVP Spec: Real-Time Video Intelligence

## Overview

A focused edge AI application that provides real-time video understanding with natural language interaction. Users connect a video source, see live inference results, and ask questions in plain English.

**One-liner:** "Ask questions about what's happening in your video feed."

---

## Core Concept

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   Video Source ──► Real-Time Inference ──► Live Understanding              │
│        │                   │                        │                       │
│        │                   ▼                        ▼                       │
│        │            ┌─────────────┐         ┌─────────────┐                │
│        │            │ Detection   │         │ VLM Summary │                │
│        │            │ (YOLOv8)    │         │ (VILA)      │                │
│        │            └─────────────┘         └─────────────┘                │
│        │                   │                        │                       │
│        │                   └────────────┬───────────┘                       │
│        │                                │                                   │
│        ▼                                ▼                                   │
│   ┌─────────┐                    ┌─────────────┐                           │
│   │ Display │◄───────────────────│ Agent Tools │◄──── "How many people?"   │
│   └─────────┘                    └─────────────┘                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## What This Is

- **Real-time video understanding** running on Jetson
- **Natural language queries** about live or recent footage
- **Tool-based agent** that can detect, describe, count, and alert
- **Single video source** focus (camera or stream)
- **Edge-native** - no cloud dependency

## What This Is NOT

- Video library/archive management
- Batch processing of uploaded files
- Multi-camera orchestration platform
- General-purpose AI playground
- Cloud-connected analytics service

---

## Target User

**Primary:** Developer or technical operator who wants to add AI understanding to a video feed.

**Use cases:**
- "What's happening on this camera right now?"
- "Count how many people walked by in the last minute"
- "Alert me when a vehicle enters the frame"
- "Is anyone in the restricted area?"

---

## MVP Scope

### Included

| Feature | Description |
|---------|-------------|
| Video input | RTSP stream or USB camera |
| Live view | Real-time display with detection overlays |
| Continuous inference | Detection + periodic VLM summaries |
| Natural language Q&A | Ask questions, get answers |
| Tool-based agent | Structured tools for specific capabilities |
| Recent memory | Query about last N seconds/minutes |
| Simple alerts | Watch for conditions, notify when met |

### Excluded (V2+)

| Feature | Reason to Defer |
|---------|-----------------|
| Multiple cameras | Adds complexity, single source is MVP |
| Video recording | Focus on real-time, not storage |
| User authentication | Single-user edge device |
| Cloud sync | Edge-first, cloud later |
| Custom model upload | Use provided models first |
| Historical search | Real-time focus, not archive |

---

## User Experience

### Single Screen Interface

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Edge Vision                                    ● Live    rtsp://camera:554 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────┐           │
│  │                                                              │           │
│  │                                                              │           │
│  │                    [ Live Video Feed ]                       │           │
│  │                                                              │           │
│  │              ┌─────────┐                                     │           │
│  │              │ person  │  Detection boxes overlaid           │           │
│  │              │  0.94   │                                     │           │
│  │              └─────────┘                                     │           │
│  │                                                              │           │
│  └──────────────────────────────────────────────────────────────┘           │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────┐           │
│  │ 📍 Now: One person walking across the frame from left to     │           │
│  │ right, appears to be carrying a bag. Empty parking lot in    │           │
│  │ background with two parked vehicles.                         │           │
│  └──────────────────────────────────────────────────────────────┘           │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Ask: "Is anyone wearing safety equipment?"                      [▶]  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────┐           │
│  │ 🤖 Looking at the current frame... No, the person visible    │           │
│  │ is not wearing any safety equipment such as hard hats,       │           │
│  │ vests, or protective gear.                                   │           │
│  └──────────────────────────────────────────────────────────────┘           │
│                                                                              │
│  Active Alerts: [Person in frame → notify]                      [+ Alert]   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Core Interactions

| Action | How |
|--------|-----|
| Connect source | Enter RTSP URL or select USB camera |
| View live feed | Always visible with detection overlays |
| Read summary | Auto-updating natural language description |
| Ask question | Type in natural language, get response |
| Set alert | Define condition to watch for |

---

## Agent & Tools

### Agent Design

Simple ReAct-style agent with focused tool set. No complex reasoning chains - direct tool execution for most queries.

```python
class LiveVideoAgent:
    """Agent for real-time video understanding."""

    def __init__(self, vlm, detector, memory):
        self.vlm = vlm
        self.detector = detector
        self.memory = memory  # Recent frames/summaries

    def query(self, user_input: str) -> str:
        """Process natural language query."""
        # 1. Classify intent
        intent = self.classify_intent(user_input)

        # 2. Execute appropriate tool
        if intent == "describe":
            return self.tools.describe_now()
        elif intent == "detect":
            return self.tools.detect_objects(user_input)
        elif intent == "count":
            return self.tools.count_objects(user_input)
        elif intent == "check":
            return self.tools.check_condition(user_input)
        elif intent == "recent":
            return self.tools.recent_summary(user_input)
        elif intent == "alert":
            return self.tools.set_alert(user_input)
        else:
            return self.tools.general_query(user_input)
```

### Tool Definitions

| Tool | Input | Output | Example Query |
|------|-------|--------|---------------|
| `describe_now` | None | Natural language description | "What's happening?" |
| `detect_objects` | Optional: class filter | List of detections | "What objects are visible?" |
| `count_objects` | Object class | Integer count | "How many people?" |
| `check_condition` | Condition description | Boolean + explanation | "Is there a forklift?" |
| `recent_summary` | Time window | Summary of period | "What happened in the last minute?" |
| `set_alert` | Condition description | Confirmation | "Alert me when someone enters" |
| `clear_alert` | Alert ID or "all" | Confirmation | "Stop all alerts" |

### Tool Implementations

```python
class LiveVideoTools:
    """Tool implementations for live video agent."""

    def describe_now(self) -> str:
        """Get VLM description of current frame."""
        frame = self.get_current_frame()
        return self.vlm.describe(
            frame,
            prompt="Describe what is happening in this scene. "
                   "Be specific about people, objects, and actions."
        )

    def detect_objects(self, filter_class: str = None) -> str:
        """Run detection on current frame."""
        frame = self.get_current_frame()
        detections = self.detector.detect(frame)

        if filter_class:
            detections = [d for d in detections if filter_class in d.class_name]

        if not detections:
            return f"No {filter_class or 'objects'} detected in current frame."

        return self.format_detections(detections)

    def count_objects(self, object_class: str) -> str:
        """Count specific object type."""
        frame = self.get_current_frame()
        detections = self.detector.detect(frame)
        count = sum(1 for d in detections if object_class.lower() in d.class_name.lower())
        return f"I can see {count} {object_class}(s) in the current frame."

    def check_condition(self, condition: str) -> str:
        """Check if condition is met using VLM."""
        frame = self.get_current_frame()
        response = self.vlm.query(
            frame,
            prompt=f"Answer yes or no: {condition}. Then briefly explain why."
        )
        return response

    def recent_summary(self, time_window: str = "1 minute") -> str:
        """Summarize recent activity."""
        recent_summaries = self.memory.get_recent(time_window)

        if not recent_summaries:
            return f"No activity recorded in the last {time_window}."

        # Use VLM to synthesize summaries
        return self.vlm.summarize(recent_summaries)

    def set_alert(self, condition: str) -> str:
        """Set up condition-based alert."""
        alert_id = self.alert_manager.add(condition)
        return f"Alert set: I'll notify you when '{condition}'. (ID: {alert_id})"
```

---

## Technical Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            JETSON AGX ORIN                                   │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         VIDEO PIPELINE (DeepStream)                     │ │
│  │                                                                         │ │
│  │   RTSP/USB ──► Decode ──► Preprocess ──► Inference ──► Postprocess    │ │
│  │      │          (NVDEC)                      │              │           │ │
│  │      │                                       │              │           │ │
│  │      │                              ┌────────┴────────┐     │           │ │
│  │      │                              │                 │     │           │ │
│  │      │                              ▼                 ▼     │           │ │
│  │      │                        ┌─────────┐      ┌─────────┐ │           │ │
│  │      │                        │ YOLOv8  │      │ SigLIP  │ │           │ │
│  │      │                        │ (nvinfer)│      │ (embed) │ │           │ │
│  │      │                        └────┬────┘      └────┬────┘ │           │ │
│  │      │                             │                │      │           │ │
│  └──────┼─────────────────────────────┼────────────────┼──────┼───────────┘ │
│         │                             │                │      │             │
│         │                             ▼                ▼      ▼             │
│  ┌──────┼─────────────────────────────────────────────────────────────────┐ │
│  │      │                    APPLICATION LAYER                             │ │
│  │      │                                                                  │ │
│  │      │    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │ │
│  │      │    │   Frame     │    │   Memory    │    │   Alert     │       │ │
│  │      └───►│   Buffer    │───►│   Store     │    │   Manager   │       │ │
│  │           │  (current)  │    │  (recent)   │    │             │       │ │
│  │           └──────┬──────┘    └──────┬──────┘    └──────┬──────┘       │ │
│  │                  │                  │                  │              │ │
│  │                  └────────────┬─────┴──────────────────┘              │ │
│  │                               │                                       │ │
│  │                               ▼                                       │ │
│  │                        ┌─────────────┐                                │ │
│  │                        │   Agent     │◄─── User Query                 │ │
│  │                        │   + Tools   │                                │ │
│  │                        └──────┬──────┘                                │ │
│  │                               │                                       │ │
│  │                               ▼                                       │ │
│  │    ┌─────────────┐     ┌─────────────┐                               │ │
│  │    │   NanoLLM   │◄────│   Tool      │                               │ │
│  │    │   (VILA)    │     │   Router    │                               │ │
│  │    └─────────────┘     └─────────────┘                               │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         WEB INTERFACE                                   │ │
│  │                                                                         │ │
│  │    FastAPI ◄──► WebSocket ◄──► React UI                               │ │
│  │                                                                         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Technology |
|-----------|---------------|------------|
| Video Pipeline | Decode, preprocess, distribute frames | DeepStream 7.x |
| Detection | Real-time object detection | YOLOv8-s + TensorRT |
| Embeddings | Frame similarity (for memory) | SigLIP via NanoLLM |
| VLM | Scene description, Q&A | VILA-7B AWQ via NanoLLM |
| Frame Buffer | Current frame access | Shared memory |
| Memory Store | Recent summaries, detections | In-memory (Redis optional) |
| Alert Manager | Condition monitoring | Python async |
| Agent | Query understanding, tool dispatch | Custom (lightweight) |
| API | HTTP + WebSocket endpoints | FastAPI |
| UI | Live view + chat | React + Video.js |

---

## Technical Constraints

### Container-First Architecture

**All code runs inside containers. There is no supported "local" execution path.**

| Principle | Rationale |
|-----------|-----------|
| Container is the runtime | Dependencies, GPU drivers, and environment are only validated in container |
| No local Python execution | Avoid "works on my machine" - container is the machine |
| Development inside containers | Use volume mounts for code, but execution is always containerized |
| Same image dev → prod | Development container = production container (with volume mounts) |

**Implications:**
- IDE runs on host, code executes in container
- All `make` / `npm` / `pytest` commands run via `docker exec` or `docker compose run`
- No `pip install` on host machine
- `.devcontainer/` provided for VS Code Remote Containers support

### Required: NVIDIA Ecosystem

| Component | Requirement | Rationale |
|-----------|-------------|-----------|
| Base Container | `dustynv/nano_llm:r36.4.0` | Validated for Jetson, includes TensorRT |
| Video Pipeline | NanoLLM VideoSource | Hardware-accelerated via jetson-utils |
| VLM Runtime | NanoLLM | Optimized for Jetson, streaming support |
| Detection | TensorRT engine | INT8 quantization, <10ms inference |

### Required: Best Practices

| Practice | Implementation |
|----------|----------------|
| Container-first development | All code runs in containers, never on bare host |
| Single container deployment | One Dockerfile, docker-compose for orchestration |
| Health monitoring | `/health` endpoint with GPU metrics |
| Structured logging | JSON logs with correlation IDs |
| Configuration management | Environment variables + YAML config |
| Graceful shutdown | Signal handling, resource cleanup |
| Error boundaries | Inference failures don't crash app |

### Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Video latency | <100ms | Frame capture to display |
| Detection latency | <15ms | Per frame |
| VLM response | <2s | Query to first token |
| Memory usage | <32GB | Leave headroom on 64GB Orin |
| Startup time | <60s | Container start to ready |

---

## Data Model

### Minimal State

```python
@dataclass
class CurrentState:
    """Real-time state - no persistence required."""

    # Current frame
    frame: np.ndarray
    frame_timestamp: datetime

    # Latest detections
    detections: List[Detection]

    # Latest VLM summary
    summary: str
    summary_timestamp: datetime


@dataclass
class RecentMemory:
    """Rolling window of recent activity."""

    # Last N summaries (e.g., 1 per 10 seconds)
    summaries: deque[TimestampedSummary]  # maxlen=60 for 10 min

    # Last N detection snapshots
    detection_history: deque[TimestampedDetections]  # maxlen=60

    def get_recent(self, seconds: int) -> List[TimestampedSummary]:
        """Get summaries from last N seconds."""
        cutoff = datetime.now() - timedelta(seconds=seconds)
        return [s for s in self.summaries if s.timestamp > cutoff]


@dataclass
class Alert:
    """Active alert definition."""

    id: str
    condition: str  # Natural language condition
    created_at: datetime
    triggered_count: int = 0
    last_triggered: Optional[datetime] = None
```

### No Database Required

For MVP:
- Current state in memory
- Recent memory in deque (fixed size, auto-evicts)
- Alerts in memory (lost on restart - acceptable for MVP)

Future: Add Redis for persistence if needed.

---

## API Design

### REST Endpoints

```yaml
# Health & Status
GET /health
  Response: { status, gpu_memory, inference_fps, uptime }

GET /status
  Response: { connected, source_url, detection_count, alerts_active }

# Video Source
POST /source/connect
  Body: { url: "rtsp://..." } or { device: "/dev/video0" }
  Response: { connected: true, resolution, fps }

POST /source/disconnect
  Response: { disconnected: true }

# Agent Queries
POST /query
  Body: { question: "How many people are visible?" }
  Response: { answer: "...", tool_used: "count_objects", latency_ms: 1234 }

# Alerts
GET /alerts
  Response: { alerts: [...] }

POST /alerts
  Body: { condition: "person enters frame" }
  Response: { alert_id: "...", condition: "..." }

DELETE /alerts/{id}
  Response: { deleted: true }
```

### WebSocket

```yaml
# Real-time updates
WS /ws/live

# Server sends:
- { type: "frame", data: base64_jpeg, timestamp: ... }
- { type: "detections", data: [...], timestamp: ... }
- { type: "summary", text: "...", timestamp: ... }
- { type: "alert", alert_id: "...", condition: "...", triggered_at: ... }

# Client sends:
- { type: "query", question: "..." }

# Server responds:
- { type: "answer", question: "...", answer: "...", latency_ms: ... }
```

---

## Project Structure

```
edge-vision/
├── docker/
│   ├── Dockerfile              # Based on dustynv/nano_llm
│   ├── docker-compose.yml      # Single service + optional Redis
│   └── entrypoint.sh
├── src/
│   ├── main.py                 # FastAPI app entry
│   ├── config.py               # Configuration loading
│   │
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── deepstream.py       # DeepStream pipeline setup
│   │   ├── detector.py         # YOLOv8 wrapper
│   │   └── vlm.py              # NanoLLM/VILA wrapper
│   │
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── agent.py            # Main agent class
│   │   ├── tools.py            # Tool implementations
│   │   └── intents.py          # Intent classification
│   │
│   ├── state/
│   │   ├── __init__.py
│   │   ├── current.py          # Current frame/detections
│   │   ├── memory.py           # Recent history
│   │   └── alerts.py           # Alert management
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py           # REST endpoints
│   │   └── websocket.py        # WebSocket handler
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logging.py          # Structured logging
│       └── metrics.py          # Health metrics
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── VideoFeed.tsx
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── DetectionOverlay.tsx
│   │   │   └── AlertPanel.tsx
│   │   └── hooks/
│   │       └── useWebSocket.ts
│   ├── package.json
│   └── vite.config.ts
│
├── config/
│   └── default.yaml            # Default configuration
│
├── scripts/
│   ├── setup-jetson.sh         # Device setup
│   └── export-models.sh        # TensorRT export
│
├── tests/
│   ├── test_agent.py
│   ├── test_tools.py
│   └── test_api.py
│
├── requirements.txt
└── README.md
```

---

## Configuration

```yaml
# config/default.yaml

video:
  source: "rtsp://192.168.1.100:554/stream"  # Or /dev/video0
  width: 1920
  height: 1080
  fps: 30

inference:
  detector:
    model: "yolov8s"
    precision: "int8"
    confidence_threshold: 0.5
  vlm:
    model: "Efficient-Large-Model/VILA1.5-7b"
    quantization: "awq"
    max_tokens: 256
  summary_interval_seconds: 10

memory:
  max_summaries: 60          # 10 minutes at 10s interval
  max_detection_history: 60

alerts:
  check_interval_seconds: 1
  cooldown_seconds: 30       # Don't re-trigger same alert

server:
  host: "0.0.0.0"
  port: 8080
  cors_origins: ["*"]

logging:
  level: "INFO"
  format: "json"
```

---

## Docker Configuration (Container-First)

**All execution happens inside containers.** The host machine only provides:
- IDE / editor
- Docker runtime
- GPU drivers

### Dockerfile

```dockerfile
# Based on NVIDIA's validated container
FROM dustynv/nano_llm:r36.4.0

# Install additional dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgstreamer1.0-0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application (production only - dev uses volume mounts)
COPY src/ ./src/
COPY config/ ./config/

# Copy frontend build
COPY frontend/dist/ ./static/

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s \
    CMD curl -f http://localhost:8080/health || exit 1

EXPOSE 8080

ENTRYPOINT ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### docker-compose.yml (Development)

```yaml
version: '3.8'

services:
  edge-vision:
    build: .
    runtime: nvidia
    ports:
      - "8080:8080"
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - VIDEO_SOURCE=${VIDEO_SOURCE:-/dev/video0}
    devices:
      - /dev/video0:/dev/video0  # USB camera
    volumes:
      # Development: mount source for hot-reload
      - ./src:/app/src:ro
      - ./config:/app/config:ro
      - ./tests:/app/tests:ro
      - model_cache:/root/.cache
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]

volumes:
  model_cache:
```

### Development Workflow

```bash
# ALL commands run inside container - never on host

# Start development environment
make dev                    # → docker compose up -d

# Run tests
make test                   # → docker compose exec edge-vision pytest

# Run linter
make lint                   # → docker compose exec edge-vision ruff check .

# Add a dependency (updates requirements.txt, rebuilds)
make add-dep DEP=requests   # → docker compose exec edge-vision pip install requests
                            # → docker compose exec edge-vision pip freeze > requirements.txt
                            # → docker compose build

# Open shell inside container
make shell                  # → docker compose exec edge-vision bash

# View logs
make logs                   # → docker compose logs -f
```

### Makefile

```makefile
.PHONY: dev test lint shell logs build

COMPOSE = docker compose
EXEC = $(COMPOSE) exec edge-vision

dev:
	$(COMPOSE) up -d

stop:
	$(COMPOSE) down

test:
	$(EXEC) pytest tests/ -v

lint:
	$(EXEC) ruff check src/

shell:
	$(EXEC) bash

logs:
	$(COMPOSE) logs -f

build:
	$(COMPOSE) build --no-cache

# Production build (no volume mounts)
prod:
	docker build -t edge-vision:latest .
	docker run --runtime nvidia -p 8080:8080 edge-vision:latest
```

---

## Development Phases

### Phase 1: Core Pipeline (Week 1-2)

- [ ] DeepStream pipeline with RTSP/USB input
- [ ] YOLOv8 detection integration
- [ ] Frame buffer for current frame access
- [ ] Basic FastAPI server with health endpoint
- [ ] WebSocket for live frame streaming

**Deliverable:** Live video with detection overlays in browser.

### Phase 2: VLM Integration (Week 2-3)

- [ ] NanoLLM/VILA integration
- [ ] Periodic summary generation
- [ ] Memory store for recent summaries
- [ ] `describe_now` tool implementation

**Deliverable:** Live video with auto-updating descriptions.

### Phase 3: Agent & Tools (Week 3-4)

- [ ] Agent with intent classification
- [ ] All tool implementations
- [ ] Chat interface in UI
- [ ] Query → response flow

**Deliverable:** Ask questions and get answers about live video.

### Phase 4: Alerts & Polish (Week 4-5)

- [ ] Alert manager implementation
- [ ] Alert UI panel
- [ ] Error handling & edge cases
- [ ] Performance optimization
- [ ] Documentation

**Deliverable:** Complete MVP ready for testing.

---

## Success Criteria

| Criterion | Measurement |
|-----------|-------------|
| Connects to RTSP/USB source | Manual test |
| Shows live video with detections | Visual check |
| Updates summary every 10s | Log verification |
| Answers "How many people?" correctly | >90% accuracy |
| Answers "What's happening?" with relevant description | Qualitative |
| Sets and triggers alert | Manual test |
| Runs stable for 1 hour | No crashes, no memory leak |
| Total latency <3s for query response | Timing measurement |

---

## What's Reusable

Components designed for reuse in other Jetson projects:

| Component | Reusability | Notes |
|-----------|-------------|-------|
| DeepStream pipeline wrapper | High | Any video input project |
| NanoLLM/VILA wrapper | High | Any VLM project on Jetson |
| TensorRT detection wrapper | High | Any detection project |
| Tool-based agent pattern | Medium | Pattern, not library |
| WebSocket live streaming | High | Any real-time UI |
| Health/metrics endpoint | High | Production standard |
| Docker/compose patterns | High | Deployment template |

---

## References

- DeepStream SDK: https://developer.nvidia.com/deepstream-sdk
- NanoLLM: https://github.com/dusty-nv/NanoLLM
- jetson-containers: https://github.com/dusty-nv/jetson-containers
- VILA: https://github.com/NVlabs/VILA
- Previous analysis: `vibe-check/03-JETSON-FIT.md`

---

*Revised MVP Spec - January 2026*
