# AGILE Development Plan: Edge Vision MVP

## Overview

A focused backlog for building the Real-Time Video Intelligence MVP on NVIDIA Jetson, synthesized from NVIDIA documentation and our revised MVP spec.

**Product Goal:** Real-time video understanding with natural language interaction on edge hardware.

---

## Technology Stack (Validated)

| Component | Technology | Source |
|-----------|------------|--------|
| Base Container | `dustynv/nano_llm:r36.4.0` | [jetson-containers](https://github.com/dusty-nv/jetson-containers) |
| Video Pipeline | DeepStream 7.x + Python bindings | [NVIDIA DeepStream](https://developer.nvidia.com/deepstream-sdk) |
| VLM Inference | NanoLLM + VILA-7B AWQ | [NanoLLM](https://github.com/dusty-nv/NanoLLM) |
| Detection | YOLOv8-s TensorRT INT8 | [Ultralytics + TensorRT](https://docs.ultralytics.com/guides/nvidia-jetson/) |
| API Server | FastAPI + WebSocket | Standard Python |
| Frontend | React + Video.js | Standard Web |

---

## Epic 1: Development Environment

**Goal:** Reproducible development setup that matches production Jetson environment.

| ID | Story | Size | Acceptance Criteria |
|----|-------|------|---------------------|
| E1.1 | Set up base container from `dustynv/nano_llm` | S | Container runs on Jetson, GPU accessible |
| E1.2 | Create docker-compose.yml for local development | S | `docker compose up` starts all services |
| E1.3 | Configure volume mounts for code hot-reload | S | Code changes reflect without rebuild |
| E1.4 | Set up model cache volume | S | Models persist across container restarts |
| E1.5 | Create Makefile with common commands | S | `make run`, `make test`, `make build` work |
| E1.6 | Document development setup in README | S | New developer can start in <30 min |

---

## Epic 2: Video Input Pipeline

**Goal:** Receive video from RTSP or USB camera with hardware-accelerated decode.

| ID | Story | Size | Acceptance Criteria |
|----|-------|------|---------------------|
| E2.1 | Create DeepStream pipeline for RTSP input | M | Connects to RTSP URL, decodes frames |
| E2.2 | Create DeepStream pipeline for USB camera | M | Reads from /dev/video0, decodes frames |
| E2.3 | Add probe callback to extract frames as NumPy | M | Frames accessible in Python as np.ndarray |
| E2.4 | Implement frame buffer for current frame access | S | Latest frame available via `get_current_frame()` |
| E2.5 | Add pipeline health monitoring | S | Detect disconnection, log errors |
| E2.6 | Create abstraction layer for input source switching | M | Switch RTSP↔USB via config |

**Technical Notes:**
- Use `get_nvds_buf_surface()` for NumPy conversion per [DeepStream Python docs](https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_Python_Sample_Apps.html)
- Probe callbacks are synchronous - keep processing minimal
- Hardware decode via NVDEC is automatic in DeepStream

---

## Epic 3: Object Detection Integration

**Goal:** Real-time YOLOv8 detection with TensorRT optimization.

| ID | Story | Size | Acceptance Criteria |
|----|-------|------|---------------------|
| E3.1 | Export YOLOv8s to TensorRT INT8 engine | M | Engine file generated, loads on Jetson |
| E3.2 | Integrate YOLO as DeepStream nvinfer plugin | M | Detections in pipeline metadata |
| E3.3 | Create detection wrapper with Python API | S | `detector.detect(frame)` returns list |
| E3.4 | Implement detection result formatting | S | Standardized Detection dataclass |
| E3.5 | Add confidence threshold configuration | S | Configurable via YAML |
| E3.6 | Benchmark detection latency | S | Measure and log inference time |

**Technical Notes:**
- Target <15ms per frame on AGX Orin per [benchmarks](https://wiki.seeedstudio.com/YOLOv8-TRT-Jetson/)
- Use DeepStream's nvinfer for batched inference
- INT8 calibration with COCO subset

---

## Epic 4: VLM Integration

**Goal:** Scene descriptions and Q&A using VILA via NanoLLM.

| ID | Story | Size | Acceptance Criteria |
|----|-------|------|---------------------|
| E4.1 | Load VILA-7B AWQ model via NanoLLM | M | Model loads, responds to test prompt |
| E4.2 | Create VLM wrapper with describe/query methods | M | `vlm.describe(frame)`, `vlm.query(frame, question)` |
| E4.3 | Implement periodic summary generation | M | Summary updates every N seconds |
| E4.4 | Add streaming response support | M | Tokens stream to client as generated |
| E4.5 | Configure max tokens and temperature | S | Configurable via YAML |
| E4.6 | Handle VLM errors gracefully | S | Timeout, OOM don't crash app |

**Technical Notes:**
- Use NanoLLM's ChatHistory for conversation management per [NanoLLM docs](https://github.com/dusty-nv/NanoLLM)
- VILA-7B AWQ fits in ~8GB, leaves headroom for detection
- First load compiles TensorRT engine (~60s)

---

## Epic 5: Memory & State Management

**Goal:** Track recent activity for temporal queries.

| ID | Story | Size | Acceptance Criteria |
|----|-------|------|---------------------|
| E5.1 | Implement CurrentState dataclass | S | Holds frame, detections, timestamp |
| E5.2 | Implement RecentMemory with rolling window | M | Stores last N summaries, configurable window |
| E5.3 | Add detection history tracking | M | Query detections from last N seconds |
| E5.4 | Implement `get_recent()` method | S | Returns summaries in time range |
| E5.5 | Add memory size limits to prevent OOM | S | Configurable max items, auto-evict oldest |

**Technical Notes:**
- Use Python deque with maxlen for auto-eviction
- No database for MVP - in-memory only
- Consider Redis for future persistence

---

## Epic 6: Agent & Tools

**Goal:** Natural language interface with tool-based responses.

| ID | Story | Size | Acceptance Criteria |
|----|-------|------|---------------------|
| E6.1 | Create Agent class with tool registry | M | Agent loads, tools registered |
| E6.2 | Implement intent classification | M | Maps user query to tool |
| E6.3 | Implement `describe_now` tool | S | Returns VLM description of current frame |
| E6.4 | Implement `detect_objects` tool | S | Returns formatted detection list |
| E6.5 | Implement `count_objects` tool | S | Returns count of specified class |
| E6.6 | Implement `check_condition` tool | M | VLM answers yes/no with explanation |
| E6.7 | Implement `recent_summary` tool | M | Synthesizes recent activity |
| E6.8 | Implement `set_alert` tool | M | Registers condition to watch |
| E6.9 | Implement `clear_alert` tool | S | Removes alert by ID |
| E6.10 | Create tool response formatter | S | Consistent response structure |

**Technical Notes:**
- Consider NanoLLM's `bot_function` decorator for tool registration
- Intent classification can start simple (keyword matching), evolve to LLM-based
- Use structured output for tool dispatch

---

## Epic 7: Alert System

**Goal:** Watch for conditions and notify when met.

| ID | Story | Size | Acceptance Criteria |
|----|-------|------|---------------------|
| E7.1 | Create Alert dataclass | S | Stores condition, timestamps, trigger count |
| E7.2 | Implement AlertManager | M | Add, remove, list alerts |
| E7.3 | Create alert evaluation loop | M | Checks conditions periodically |
| E7.4 | Integrate VLM for condition checking | M | Uses `check_condition` for evaluation |
| E7.5 | Add cooldown to prevent spam | S | Configurable cooldown period |
| E7.6 | Emit alert events via WebSocket | M | Client receives alert notifications |

**Technical Notes:**
- Async evaluation loop with configurable interval
- Simple string conditions for MVP (VLM interprets)
- Future: structured condition DSL

---

## Epic 8: REST API

**Goal:** HTTP endpoints for control and queries.

| ID | Story | Size | Acceptance Criteria |
|----|-------|------|---------------------|
| E8.1 | Set up FastAPI application structure | S | App starts, serves /health |
| E8.2 | Implement `/health` endpoint | S | Returns status, GPU metrics |
| E8.3 | Implement `/status` endpoint | S | Returns connection state, stats |
| E8.4 | Implement `/source/connect` endpoint | M | Connects to RTSP/USB source |
| E8.5 | Implement `/source/disconnect` endpoint | S | Cleanly disconnects source |
| E8.6 | Implement `/query` endpoint | M | Sends query to agent, returns answer |
| E8.7 | Implement `/alerts` CRUD endpoints | M | GET, POST, DELETE for alerts |
| E8.8 | Add request validation with Pydantic | S | Invalid requests return 400 |
| E8.9 | Add structured error responses | S | Consistent error format |

**Technical Notes:**
- Use FastAPI's async support
- Pydantic models for request/response
- OpenAPI docs auto-generated

---

## Epic 9: WebSocket & Streaming

**Goal:** Real-time updates to client.

| ID | Story | Size | Acceptance Criteria |
|----|-------|------|---------------------|
| E9.1 | Set up WebSocket endpoint `/ws/live` | M | Client connects, stays connected |
| E9.2 | Stream JPEG frames to client | M | Client receives frame updates |
| E9.3 | Stream detection updates | S | Client receives detection JSON |
| E9.4 | Stream summary updates | S | Client receives new summaries |
| E9.5 | Handle query via WebSocket | M | Query/response over same connection |
| E9.6 | Stream alert notifications | S | Client receives triggered alerts |
| E9.7 | Handle client disconnect gracefully | S | No errors on disconnect |
| E9.8 | Add frame rate limiting | S | Configurable max FPS to client |

**Technical Notes:**
- Use FastAPI's WebSocket support
- JPEG encode frames for transmission (balance quality/size)
- Consider binary protocol for frames, JSON for metadata

---

## Epic 10: Frontend UI

**Goal:** Single-page interface for live view and interaction.

| ID | Story | Size | Acceptance Criteria |
|----|-------|------|---------------------|
| E10.1 | Set up React + Vite project | S | Dev server runs, builds production |
| E10.2 | Create WebSocket connection hook | M | Connects, reconnects on failure |
| E10.3 | Implement VideoFeed component | M | Displays live frames from WebSocket |
| E10.4 | Implement DetectionOverlay component | M | Draws boxes on video feed |
| E10.5 | Implement SummaryPanel component | S | Shows current VLM summary |
| E10.6 | Implement ChatInterface component | M | Input box, message history |
| E10.7 | Implement AlertPanel component | M | Shows active alerts, allows delete |
| E10.8 | Add connection status indicator | S | Shows connected/disconnected state |
| E10.9 | Add source configuration modal | M | Enter RTSP URL or select USB |
| E10.10 | Style with Tailwind CSS | M | Clean, functional appearance |

**Technical Notes:**
- Video.js or raw canvas for frame display
- Tailwind for rapid styling
- Keep it simple - function over form for MVP

---

## Epic 11: Configuration & Deployment

**Goal:** Production-ready container deployment.

| ID | Story | Size | Acceptance Criteria |
|----|-------|------|---------------------|
| E11.1 | Create production Dockerfile | M | Builds, includes all dependencies |
| E11.2 | Create production docker-compose.yml | S | Single command deployment |
| E11.3 | Implement YAML configuration loading | S | Config from file + env overrides |
| E11.4 | Add structured JSON logging | S | Logs parseable, include correlation IDs |
| E11.5 | Implement graceful shutdown | M | SIGTERM handled, resources cleaned |
| E11.6 | Create Jetson setup script | M | Provisions new device |
| E11.7 | Add health check to Dockerfile | S | Docker knows when app is healthy |
| E11.8 | Document deployment process | S | README covers production setup |

**Technical Notes:**
- Multi-stage build: frontend → backend
- Model cache in named volume
- NVIDIA runtime required

---

## Epic 12: Testing & Quality

**Goal:** Confidence in correctness and stability.

| ID | Story | Size | Acceptance Criteria |
|----|-------|------|---------------------|
| E12.1 | Set up pytest infrastructure | S | Tests run, report results |
| E12.2 | Write unit tests for Agent | M | Tool dispatch tested |
| E12.3 | Write unit tests for tools | M | Each tool has tests |
| E12.4 | Write integration test for API | M | Endpoints return expected responses |
| E12.5 | Create mock video source for testing | M | Tests run without real camera |
| E12.6 | Add type hints throughout | M | mypy passes |
| E12.7 | Add ruff linting | S | Code style consistent |
| E12.8 | Create stability test (1hr run) | M | No crashes, no memory leak |

---

## Backlog Summary

| Epic | Stories | S | M | L |
|------|---------|---|---|---|
| 1. Dev Environment | 6 | 6 | 0 | 0 |
| 2. Video Pipeline | 6 | 2 | 4 | 0 |
| 3. Detection | 6 | 4 | 2 | 0 |
| 4. VLM | 6 | 2 | 4 | 0 |
| 5. Memory/State | 5 | 3 | 2 | 0 |
| 6. Agent & Tools | 10 | 5 | 5 | 0 |
| 7. Alerts | 6 | 2 | 4 | 0 |
| 8. REST API | 9 | 5 | 4 | 0 |
| 9. WebSocket | 8 | 4 | 4 | 0 |
| 10. Frontend | 10 | 2 | 8 | 0 |
| 11. Deployment | 8 | 4 | 4 | 0 |
| 12. Testing | 8 | 2 | 6 | 0 |
| **Total** | **88** | **41** | **47** | **0** |

---

## Recommended Sprint Structure

### Sprint 1: Foundation
- Epic 1 (Dev Environment) - All
- Epic 2 (Video Pipeline) - E2.1, E2.2, E2.3, E2.4
- Epic 3 (Detection) - E3.1, E3.2

**Demo:** Live video with detection overlays in terminal/debug output.

### Sprint 2: Intelligence
- Epic 2 (Video Pipeline) - E2.5, E2.6
- Epic 3 (Detection) - E3.3, E3.4, E3.5, E3.6
- Epic 4 (VLM) - All
- Epic 5 (Memory) - All

**Demo:** Video with detections + periodic VLM summaries printed.

### Sprint 3: Interaction
- Epic 6 (Agent) - All
- Epic 7 (Alerts) - All
- Epic 8 (REST API) - All

**Demo:** Query via curl, get responses. Set alerts via API.

### Sprint 4: Interface
- Epic 9 (WebSocket) - All
- Epic 10 (Frontend) - All

**Demo:** Full UI with live video, chat, alerts.

### Sprint 5: Production
- Epic 11 (Deployment) - All
- Epic 12 (Testing) - All

**Demo:** Deploy to fresh Jetson, run stability test.

---

## Definition of Done

A story is complete when:

1. **Code** - Implementation complete and merged
2. **Tests** - Unit/integration tests pass
3. **Docs** - Code documented, README updated if needed
4. **Review** - Code reviewed (or self-reviewed for solo dev)
5. **Works on Jetson** - Tested on actual hardware

---

## Technical Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| DeepStream + NanoLLM integration issues | Medium | High | Test integration early (Sprint 1) |
| VLM latency too high | Low | Medium | VILA-3B fallback available |
| Memory pressure with all models loaded | Medium | High | Profile memory, tune batch sizes |
| WebSocket frame streaming bottleneck | Medium | Medium | Frame rate limiting, JPEG quality tuning |
| TensorRT engine compilation slow first run | Certain | Low | Pre-compile in container build |

---

## Dependencies

```
Sprint 1 ──► Sprint 2 ──► Sprint 3 ──► Sprint 4 ──► Sprint 5
   │            │            │            │
   │            │            │            └── Needs API working
   │            │            └── Needs VLM + Memory working
   │            └── Needs Video Pipeline working
   └── Needs Dev Environment working
```

Each sprint builds on previous. Parallel work possible within sprints.

---

## References

- [NanoLLM Documentation](https://dusty-nv.github.io/NanoLLM/)
- [NanoLLM GitHub](https://github.com/dusty-nv/NanoLLM)
- [jetson-containers](https://github.com/dusty-nv/jetson-containers)
- [DeepStream Python Apps](https://github.com/NVIDIA-AI-IOT/deepstream_python_apps)
- [DeepStream Documentation](https://docs.nvidia.com/metropolis/deepstream/dev-guide/)
- [Jetson Platform Services](https://docs.nvidia.com/jetson/jps/)
- [YOLOv8 on Jetson](https://docs.ultralytics.com/guides/nvidia-jetson/)
- [NVIDIA Jetson AI Lab](https://www.jetson-ai-lab.com/)

---

*AGILE Development Plan - January 2026*
