# AGILE Plan: Newport Demo

## Overview

Development backlog for the Newport Demo - a multi-stream behavioral monitoring proof-of-concept.

**Goal:** Demonstrate edge AI capabilities with multi-stream video, user-defined protocols, and an intuitive setup wizard.

**Builds On:** Core MVP architecture (EventBus, VLM integration, Agent patterns)

---

## Epic Summary

| Epic | Description | Size |
|------|-------------|------|
| N0 | Container-First Environment | S |
| N1 | Persistent Configuration | M |
| N2 | Setup Wizard UI | L |
| N3 | DeepStream Multi-Stream Pipeline | L |
| N4 | Protocol Evaluation Engine | M |
| N5 | Multi-Feed Dashboard | L |
| N6 | Alert System | M |
| N7 | Demo Mode & Polish | M |

---

## Epic N0: Container-First Environment

**Goal:** All code runs inside containers. No local execution supported.

| ID | Story | Size | Acceptance Criteria |
|----|-------|------|---------------------|
| N0.1 | Create Dockerfile with DeepStream + NanoLLM | M | Container builds, GPU accessible |
| N0.2 | Create docker-compose.yml for development | S | `docker compose up` starts services |
| N0.3 | Configure volumes for code hot-reload | S | Source changes reflect without rebuild |
| N0.4 | Create volume for persistent config | S | SQLite data persists across restarts |
| N0.5 | Create Makefile wrapping docker commands | S | `make dev`, `make test`, `make shell` work |
| N0.6 | Add container health checks | S | Docker knows when app is ready |

**Container-First Principles:**
- **No local Python** - all execution via `docker compose exec`
- **Same image dev → prod** - development = production + volume mounts
- **Makefile abstracts Docker** - developers run `make test`, not docker commands
- **Persistence via volumes** - config database survives container restarts

---

## Epic N1: Persistent Configuration

**Goal:** Store and retrieve setup configuration across sessions.

| ID | Story | Size | Acceptance Criteria |
|----|-------|------|---------------------|
| N1.1 | Create FeedConfig and ProtocolConfig data models | S | Pydantic models defined |
| N1.2 | Implement SQLite storage adapter | M | CRUD operations work |
| N1.3 | Create config API endpoints | M | GET/POST /api/config work |
| N1.4 | Add feed connection test endpoint | S | POST /api/config/feeds/test validates RTSP |
| N1.5 | Load config on app startup | S | Persisted config loads automatically |
| N1.6 | Handle migration for config changes | S | Schema versioning works |

**Technical Notes:**
- SQLite for simplicity (single file, no server)
- JSON fallback option for even simpler deployments
- Config file location: `/app/data/config.db`

---

## Epic N2: Setup Wizard UI

**Goal:** Guided setup flow for non-technical users.

| ID | Story | Size | Acceptance Criteria |
|----|-------|------|---------------------|
| N2.1 | Create wizard container component | S | 3-step wizard navigation |
| N2.2 | Build Step 1: Add Camera Feeds | M | Add/remove feeds, test connection |
| N2.3 | Build Step 2: Define Protocols | M | Text areas for GREEN/YELLOW/RED rules |
| N2.4 | Build Step 3: Review & Confirm | S | Summary view, save button |
| N2.5 | Add connection status indicators | S | Live status for each feed |
| N2.6 | Implement feed preview thumbnails | M | Show frame from each feed |
| N2.7 | Add protocol examples/templates | S | Pre-fill with sensible defaults |
| N2.8 | Create wizard state management | M | Track progress, handle back/next |
| N2.9 | Add loading states and error handling | S | Graceful error messages |

**Technical Notes:**
- React with Tailwind CSS
- Component library: shadcn/ui or similar
- State: React Context or Zustand

---

## Epic N3: DeepStream Multi-Stream Pipeline

**Goal:** Efficient batched processing of multiple camera feeds.

| ID | Story | Size | Acceptance Criteria |
|----|-------|------|---------------------|
| N3.1 | Create DeepStream pipeline configuration | M | Config file for N streams |
| N3.2 | Implement nvstreammux for stream batching | M | Multiple RTSP inputs batched |
| N3.3 | Add batched YOLOv8 inference | M | Detection runs on batched frames |
| N3.4 | Implement stream demuxing for per-stream data | M | Detections tagged with stream_id |
| N3.5 | Create DeepStream → EventBus bridge | M | Probe callback queues to async bus |
| N3.6 | Add dynamic stream add/remove | L | Add stream without restart |
| N3.7 | Implement stream health monitoring | S | Detect disconnections per stream |
| N3.8 | Add reconnection logic | M | Auto-reconnect dropped streams |

**Technical Notes:**
- DeepStream 7.x with Python bindings
- nvstreammux batch-size = number of streams
- Probe on nvinfer src pad for detections
- Thread-safe queue bridges to asyncio

**Reference:**
```python
# DeepStream multi-source config
[source0]
enable=1
type=4
uri=rtsp://192.168.1.101:554/stream

[source1]
enable=1
type=4
uri=rtsp://192.168.1.102:554/stream

[streammux]
batch-size=4
width=1920
height=1080
```

---

## Epic N4: Protocol Evaluation Engine

**Goal:** Map VLM descriptions to user-defined severity levels.

| ID | Story | Size | Acceptance Criteria |
|----|-------|------|---------------------|
| N4.1 | Create ProtocolEvaluator class | M | Takes description, returns severity |
| N4.2 | Implement VLM-based rule matching | M | Prompt engineering for classification |
| N4.3 | Create icon selection logic | S | Severity + context → icon |
| N4.4 | Implement round-robin VLM sampling | M | Fair sampling across streams |
| N4.5 | Add detection-based fast path | S | Missing person → RED without VLM |
| N4.6 | Create status state machine | M | Track transitions, debounce |
| N4.7 | Emit status.changed events | S | EventBus integration |
| N4.8 | Add confidence scoring | S | Low confidence → YELLOW fallback |

**Technical Notes:**
- VLM prompt returns: `SEVERITY|ICON|MESSAGE`
- Fast path for critical detections (no person in frame)
- Debounce: require N consecutive classifications before change

**Reference:**
```python
class StatusStateMachine:
    def __init__(self, debounce_count=2):
        self.current = "green"
        self.pending = None
        self.pending_count = 0

    def update(self, new_status: str) -> Optional[str]:
        """Returns status only when confirmed."""
        if new_status != self.current:
            if new_status == self.pending:
                self.pending_count += 1
                if self.pending_count >= self.debounce_count:
                    self.current = new_status
                    self.pending = None
                    return new_status
            else:
                self.pending = new_status
                self.pending_count = 1
        return None
```

---

## Epic N5: Multi-Feed Dashboard

**Goal:** At-a-glance view of all monitored feeds.

| ID | Story | Size | Acceptance Criteria |
|----|-------|------|---------------------|
| N5.1 | Create dashboard grid layout | M | Responsive N-column grid |
| N5.2 | Build FeedCard component | M | Video + icon + status + severity |
| N5.3 | Implement WebSocket status updates | M | Real-time severity changes |
| N5.4 | Add severity-based sorting | S | RED feeds bubble to top |
| N5.5 | Create expanded feed view | M | Full-screen single feed |
| N5.6 | Add per-feed Q&A interface | M | Ask questions about specific feed |
| N5.7 | Build status history timeline | M | Per-feed history view |
| N5.8 | Implement frame streaming | M | Low-FPS thumbnails for grid |
| N5.9 | Add connection status indicators | S | Show disconnected feeds |
| N5.10 | Create settings modal | S | Edit config without wizard |

**Technical Notes:**
- Grid: 2 columns on tablet, 3-4 on desktop
- Frame streaming: 1 FPS for grid, higher for expanded
- Sort order: RED > YELLOW > GREEN, then alphabetical

---

## Epic N6: Alert System

**Goal:** Actionable notifications for YELLOW and RED conditions.

| ID | Story | Size | Acceptance Criteria |
|----|-------|------|---------------------|
| N6.1 | Create Alert data model | S | Includes stream_id, severity, timestamps |
| N6.2 | Implement AlertManager | M | Create, acknowledge, resolve alerts |
| N6.3 | Auto-create alerts on status change | S | YELLOW/RED → new alert |
| N6.4 | Build alerts page UI | M | List view with actions |
| N6.5 | Add alert acknowledgment flow | S | Mark as seen |
| N6.6 | Add alert resolution flow | S | Mark as resolved with notes |
| N6.7 | Implement alert badge on nav | S | Count of active alerts |
| N6.8 | Add alert sound/notification | S | Audio cue for RED alerts |
| N6.9 | Create "Check other cameras" action | M | RED missing → search other feeds |
| N6.10 | Persist alert history | S | Alerts survive restart |

**Technical Notes:**
- Alerts table in SQLite
- Sound: HTML5 Audio API, user must interact first
- "Check other cameras" queries VLM on other feeds

---

## Epic N7: Demo Mode & Polish

**Goal:** Polished demo experience without live cameras.

| ID | Story | Size | Acceptance Criteria |
|----|-------|------|---------------------|
| N7.1 | Create demo video dataset | M | 4 videos with varying scenarios |
| N7.2 | Implement DemoFeedSimulator | M | Plays videos as fake RTSP |
| N7.3 | Add demo mode toggle | S | Switch between live/demo |
| N7.4 | Create scripted scenario transitions | M | Timed status changes |
| N7.5 | Add demo reset button | S | Reset to initial state |
| N7.6 | Performance optimization | M | Profile and optimize |
| N7.7 | Error boundary components | S | Graceful failure UI |
| N7.8 | Add loading skeletons | S | Better perceived performance |
| N7.9 | Write demo script/walkthrough | S | Documentation for presenters |

**Technical Notes:**
- Demo videos: ~30 seconds each, looping
- Use ffmpeg to serve as RTSP for consistency
- Scripted transitions show full range of features

---

## Backlog Summary

| Epic | Stories | S | M | L |
|------|---------|---|---|---|
| N0. Container-First | 6 | 5 | 1 | 0 |
| N1. Configuration | 6 | 4 | 2 | 0 |
| N2. Setup Wizard | 9 | 4 | 5 | 0 |
| N3. DeepStream Pipeline | 8 | 2 | 5 | 1 |
| N4. Protocol Evaluation | 8 | 4 | 4 | 0 |
| N5. Dashboard | 10 | 3 | 7 | 0 |
| N6. Alert System | 10 | 6 | 4 | 0 |
| N7. Demo Mode | 9 | 5 | 4 | 0 |
| **Total** | **66** | **33** | **32** | **1** |

---

## Sprint Structure

### Sprint N1: Container Foundation
- Epic N0 (Container-First) - All
- Epic N1 (Configuration) - All
- Epic N3 (DeepStream) - N3.1, N3.2, N3.3

**Demo:** `make dev` starts container, multi-stream decode running, config persists.

### Sprint N2: Pipeline & Evaluation
- Epic N3 (DeepStream) - N3.4, N3.5, N3.6, N3.7, N3.8
- Epic N4 (Protocol Evaluation) - All

**Demo:** Streams classified as GREEN/YELLOW/RED based on rules.

### Sprint N3: UI - Wizard & Dashboard
- Epic N2 (Setup Wizard) - All
- Epic N5 (Dashboard) - N5.1 through N5.5

**Demo:** Full setup flow, basic dashboard showing feeds.

### Sprint N4: UI - Polish & Alerts
- Epic N5 (Dashboard) - N5.6 through N5.10
- Epic N6 (Alert System) - All

**Demo:** Complete UI with alerts and Q&A.

### Sprint N5: Demo & Polish
- Epic N7 (Demo Mode) - All

**Demo:** Full polished demo ready for presentation.

---

## Dependencies on Core MVP

The Newport Demo depends on these MVP components:

| MVP Component | Newport Usage |
|---------------|---------------|
| EventBus | Extended with stream_id in events |
| VLM Integration | Used by ProtocolEvaluator |
| Agent & Tools | Per-feed Q&A interface |
| WebSocket Handler | Multi-stream event forwarding |

**New Components (Newport-specific):**
- DeepStream multi-stream pipeline
- Protocol evaluation engine
- Setup wizard
- SQLite persistence
- Multi-feed dashboard

---

## Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| DeepStream Python complexity | Medium | High | Reference deepstream_python_apps |
| VLM latency with many streams | High | Medium | Round-robin sampling, fast detection path |
| Memory pressure (4+ streams) | Medium | High | Profile early, limit resolution |
| Demo video quality | Low | Medium | Use real facility footage if available |
| Dynamic stream add/remove | High | Medium | MVP: require restart, enhance later |

---

## Success Criteria

| Criterion | Measurement |
|-----------|-------------|
| `make dev` starts full environment | Container starts, app accessible |
| All tests pass via `make test` | Tests run inside container |
| Setup wizard completes in <2 minutes | User test |
| 4 streams at 720p, 15fps | Performance test |
| Status updates within 5 seconds | Timing |
| Correct classification >85% | Manual evaluation |
| RED alerts appear within 3 seconds | Timing |
| Config persists across container restart | Functional test (volume persistence) |
| Demo runs 30 minutes stable | Stability test |

---

*Newport Demo AGILE Plan - January 2026*
