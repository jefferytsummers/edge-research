# Newport Demo: Multi-Stream Behavioral Monitoring

## Overview

A proof-of-concept edge AI application demonstrating **multi-stream video monitoring** with **user-defined behavioral rules** for a behavioral health facility use case.

**One-liner:** "AI-powered resident monitoring with custom protocols across multiple camera feeds."

---

## Use Case

### Context

Special housing unit for behavioral health practice. Staff currently perform manual room checks to ensure resident safety and compliance. The facility needs:

- Continuous monitoring across multiple rooms/cameras
- Customizable protocols for different resident situations
- Real-time status indicators with severity levels
- Actionable alerts for critical situations

### Value Proposition

- **Reduce manual checks** by providing continuous AI-powered monitoring
- **Faster response** to critical situations (unconscious residents, room departures)
- **Customizable rules** that adapt to different resident protocols
- **At-a-glance status** across all monitored areas

---

## Demo Features

### 1. Self-Setup Wizard

A snappy, guided setup flow where users:

1. **Select camera feeds** (RTSP URLs or simulated feeds for demo)
2. **Name each feed** (e.g., "Room 101", "Room 102", "Common Area")
3. **Write protocols** using natural language rules

### 2. Protocol-Based Monitoring

Users define rules using natural language that map to severity levels:

```
GREEN RULES (Safe behavior):
"Give me green icons and descriptions for safe behavior such as reading, watching tv, sleeping normally."

YELLOW RULES (Attention needed):
"Give me yellow icons and descriptions for questionable behavior or activity such as being out of line of sight or any basic injuries."

RED RULES (Immediate action):
"Give me red icons and descriptions with actions. If the resident has vacated their room in an unauthorized way provide an action to check other cameras. If the resident appears unconscious or gravely injured we should immediately notify on-staff help."
```

### 3. Multi-Feed Dashboard

All camera feeds displayed in a grid with:

| Feed | Icon | Status Description |
|------|------|-------------------|
| Room 101 | ![green_book] | Resident reading in rocking chair. |
| Room 102 | ![green_tv] | Resident watching tv or movie programs. |
| Room 103 | ![yellow_spy] | Resident crouched in corner, unsure of activity. |
| Room 104 | ![yellow_bandage] | Resident bumped their head and seems to be in pain. |
| Room 105 | ![red_siren] | Resident appears unconscious on the ground. [See Alerts] |
| Room 106 | ![red_runner] | Resident has left their room. [Check Common Areas?] |

### 4. Persistent State

- Setup configuration persists across sessions
- Protocols remain configured after restart
- Alert history preserved

---

## UI Design

### Setup Wizard Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Newport Demo - Setup Wizard                                    Step 1 of 3 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Add Camera Feeds                                                          │
│   ─────────────────                                                         │
│                                                                              │
│   ┌────────────────────────────────────────────────────────────────────┐   │
│   │  Feed Name:     [ Room 101                           ]             │   │
│   │  Source:        [ rtsp://192.168.1.101:554/stream    ]             │   │
│   │                                               [Test Connection]    │   │
│   └────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   Added Feeds:                                                              │
│   ┌────────────────────────────────────────────────────────────────────┐   │
│   │  ✓ Room 101  -  rtsp://192.168.1.101:554/stream        [Remove]   │   │
│   │  ✓ Room 102  -  rtsp://192.168.1.102:554/stream        [Remove]   │   │
│   │  ○ Room 103  -  (connecting...)                                    │   │
│   └────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   [+ Add Another Feed]                                                      │
│                                                                              │
│                                                      [Back]  [Next: Rules]  │
└─────────────────────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Newport Demo - Setup Wizard                                    Step 2 of 3 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Define Monitoring Protocols                                               │
│   ───────────────────────────                                               │
│                                                                              │
│   🟢 GREEN - Safe Behavior                                                  │
│   ┌────────────────────────────────────────────────────────────────────┐   │
│   │  Describe what constitutes safe, normal behavior:                  │   │
│   │                                                                     │   │
│   │  [ Reading, watching TV, sleeping normally in bed, eating meals,  ]│   │
│   │  [ sitting calmly, exercising normally                            ]│   │
│   │                                                                     │   │
│   └────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   🟡 YELLOW - Needs Attention                                               │
│   ┌────────────────────────────────────────────────────────────────────┐   │
│   │  Describe behavior that needs staff awareness:                     │   │
│   │                                                                     │   │
│   │  [ Out of camera view, crouching in corners, minor injuries,      ]│   │
│   │  [ pacing erratically, signs of distress                          ]│   │
│   │                                                                     │   │
│   └────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   🔴 RED - Immediate Action Required                                        │
│   ┌────────────────────────────────────────────────────────────────────┐   │
│   │  Describe critical situations requiring immediate response:        │   │
│   │                                                                     │   │
│   │  [ Unconscious on ground, severe injury, room is empty/resident   ]│   │
│   │  [ has left, self-harm behavior, medical emergency                ]│   │
│   │                                                                     │   │
│   └────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│                                                    [Back]  [Next: Review]   │
└─────────────────────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Newport Demo - Setup Wizard                                    Step 3 of 3 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Review Configuration                                                      │
│   ────────────────────                                                      │
│                                                                              │
│   Camera Feeds (4)                                                          │
│   ┌────────────────────────────────────────────────────────────────────┐   │
│   │  • Room 101  -  rtsp://192.168.1.101:554/stream                   │   │
│   │  • Room 102  -  rtsp://192.168.1.102:554/stream                   │   │
│   │  • Room 103  -  rtsp://192.168.1.103:554/stream                   │   │
│   │  • Common Area  -  rtsp://192.168.1.200:554/stream                │   │
│   └────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   Protocols                                                                 │
│   ┌────────────────────────────────────────────────────────────────────┐   │
│   │  🟢 GREEN: Reading, watching TV, sleeping normally...             │   │
│   │  🟡 YELLOW: Out of view, minor injuries, pacing...                │   │
│   │  🔴 RED: Unconscious, severe injury, room empty...                │   │
│   └────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   ☑ Save configuration for future sessions                                 │
│                                                                              │
│                                               [Back]  [Start Monitoring →]  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Main Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Newport Demo                           ● Monitoring    [Settings] [Alerts] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐          │
│  │                             │  │                             │          │
│  │      [ Room 101 Feed ]      │  │      [ Room 102 Feed ]      │          │
│  │                             │  │                             │          │
│  ├─────────────────────────────┤  ├─────────────────────────────┤          │
│  │ 📗 Reading in rocking chair │  │ 📺 Watching TV programs     │          │
│  │ ● Green - Safe              │  │ ● Green - Safe              │          │
│  └─────────────────────────────┘  └─────────────────────────────┘          │
│                                                                              │
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐          │
│  │                             │  │                             │          │
│  │      [ Room 103 Feed ]      │  │      [ Room 104 Feed ]      │          │
│  │                             │  │                             │          │
│  ├─────────────────────────────┤  ├─────────────────────────────┤          │
│  │ 🔍 Crouched in corner,      │  │ 🚨 UNCONSCIOUS ON FLOOR     │          │
│  │    unclear activity         │  │ [Click to View Alert →]     │          │
│  │ ● Yellow - Attention        │  │ ● Red - CRITICAL            │          │
│  └─────────────────────────────┘  └─────────────────────────────┘          │
│                                                                              │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Recent Activity:                                                           │
│  • 14:32 - Room 104: Status changed to RED (unconscious detected)          │
│  • 14:28 - Room 103: Status changed to YELLOW (resident out of view)       │
│  • 14:15 - Room 102: Status changed to GREEN (watching TV)                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Expanded Feed View (Click on any feed)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Room 103 - Expanded View                                    [← Back to Grid]│
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                                                                        │  │
│  │                                                                        │  │
│  │                        [ Large Video Feed ]                            │  │
│  │                                                                        │  │
│  │                                                                        │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  Current Status                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ 🔍 YELLOW - Needs Attention                                           │  │
│  │                                                                        │  │
│  │ Resident crouched in corner of room, facing away from camera.         │  │
│  │ Unable to determine current activity. Recommend visual check.         │  │
│  │                                                                        │  │
│  │ Last updated: 14:32:05                                                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  Ask a Question                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐ [Ask] │
│  │ Is the resident showing signs of distress?                      │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                              │
│  Status History                                                             │
│  • 14:28 - Changed to YELLOW (out of primary view)                         │
│  • 14:15 - GREEN (reading magazine)                                        │
│  • 13:45 - GREEN (resting in bed)                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Alerts Page

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Newport Demo - Alerts                                       [← Back to Grid]│
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  🚨 ACTIVE CRITICAL ALERTS (1)                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ ┌─────────────────────────────────────────────────────────────────┐   │  │
│  │ │ 🚨 Room 104 - UNCONSCIOUS RESIDENT                              │   │  │
│  │ │                                                                  │   │  │
│  │ │ Detected: 14:32:01                                              │   │  │
│  │ │ Duration: 2 minutes                                             │   │  │
│  │ │                                                                  │   │  │
│  │ │ AI Assessment:                                                  │   │  │
│  │ │ Resident appears to be lying face-down on floor near bed.       │   │  │
│  │ │ No visible movement detected for 45 seconds. Possible fall      │   │  │
│  │ │ or medical emergency.                                           │   │  │
│  │ │                                                                  │   │  │
│  │ │ [View Live Feed]  [Mark Acknowledged]  [Request Emergency Help] │   │  │
│  │ └─────────────────────────────────────────────────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ⚠️ Attention Needed (2)                                                    │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ • Room 103 - Resident out of primary view (14:28)       [View Feed]  │  │
│  │ • Room 106 - Unusual pacing behavior (14:22)            [View Feed]  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  Alert History (Today)                                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ • 13:15 - Room 102 - RED resolved (false positive, resident napping) │  │
│  │ • 11:30 - Room 101 - YELLOW resolved (returned to view)              │  │
│  │ • 09:45 - Room 105 - RED resolved (staff responded to fall)          │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Icon System

### Status Icons

| Severity | Icon | Meaning | Example Scenarios |
|----------|------|---------|-------------------|
| GREEN | 📗 | Safe - Reading | Reading book or magazine |
| GREEN | 📺 | Safe - Media | Watching TV or movies |
| GREEN | 😴 | Safe - Resting | Sleeping normally in bed |
| GREEN | 🍽️ | Safe - Eating | Having a meal |
| GREEN | 🧘 | Safe - Calm | Sitting or meditating calmly |
| YELLOW | 🔍 | Attention - Unclear | Out of view or unclear activity |
| YELLOW | 🩹 | Attention - Minor injury | Visible minor injury |
| YELLOW | 😰 | Attention - Distress | Signs of emotional distress |
| YELLOW | 🚶 | Attention - Pacing | Erratic pacing behavior |
| RED | 🚨 | Critical - Medical | Unconscious or severe injury |
| RED | 🏃 | Critical - Missing | Resident left room |
| RED | ⚠️ | Critical - Danger | Self-harm or dangerous behavior |

---

## Architecture: Multi-Stream with DeepStream

This demo **requires DeepStream** for efficient multi-stream processing. Here's why and how:

### Why DeepStream for Multi-Stream

From our feasibility analysis:

> "NanoLLM VideoSource is single-stream focused... For multi-stream (V2), could run multiple VideoSource instances or switch to DeepStream for video decode only"

For 4-8+ simultaneous camera feeds:
- **DeepStream** uses a single GPU decode pipeline for all streams
- **NanoLLM VideoSource** would need one instance per stream (inefficient)

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         JETSON AGX ORIN                                      │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    DeepStream Multi-Stream Pipeline                     │ │
│  │                                                                         │ │
│  │   RTSP 1 ──┐                                                           │ │
│  │   RTSP 2 ──┼──► nvstreammux ──► nvinfer ──► Batched Detection         │ │
│  │   RTSP 3 ──┤        │          (YOLOv8)         │                      │ │
│  │   RTSP 4 ──┘        │                           │                      │ │
│  │                     │                           ▼                      │ │
│  │                     │                    ┌─────────────┐               │ │
│  │                     │                    │ Per-Stream  │               │ │
│  │                     │                    │ Demux       │               │ │
│  │                     │                    └──────┬──────┘               │ │
│  │                     │                           │                      │ │
│  └─────────────────────┼───────────────────────────┼──────────────────────┘ │
│                        │                           │                        │
│                        ▼                           ▼                        │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         Event Bus                                       │ │
│  │                                                                         │ │
│  │   frame.new[stream_id] ──► Per-Stream VLM Queue                        │ │
│  │   detection.complete[stream_id] ──► Protocol Evaluator                 │ │
│  │   status.changed[stream_id] ──► UI + Alert Manager                     │ │
│  │                                                                         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                      Per-Stream Processing                              │ │
│  │                                                                         │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │ │
│  │  │ VLM Sampler  │  │ Protocol     │  │ Status       │                  │ │
│  │  │ (Round-robin)│  │ Evaluator    │  │ Manager      │                  │ │
│  │  │              │  │              │  │              │                  │ │
│  │  │ 1 VLM call   │  │ Matches user │  │ Tracks per-  │                  │ │
│  │  │ per N sec    │  │ rules to     │  │ stream state │                  │ │
│  │  │ per stream   │  │ GREEN/YELLOW │  │ and history  │                  │ │
│  │  │              │  │ /RED         │  │              │                  │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                  │ │
│  │                                                                         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         Application Layer                               │ │
│  │                                                                         │ │
│  │   FastAPI ──► WebSocket ──► React Dashboard                            │ │
│  │                                                                         │ │
│  │   SQLite/JSON for persistent configuration                             │ │
│  │                                                                         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Multi-Stream VLM Strategy

With 4+ streams and VLM taking ~500ms per inference:

```python
class MultiStreamVLMSampler:
    """Round-robin VLM sampling across streams."""

    def __init__(self, streams: List[str], interval_per_stream: float = 10.0):
        self.streams = streams
        self.interval = interval_per_stream
        self.current_index = 0

    async def sample_next(self):
        """Sample one stream at a time, rotating through all."""
        stream_id = self.streams[self.current_index]
        frame = await self.get_latest_frame(stream_id)

        # VLM inference
        description = await self.vlm.describe(frame)

        # Emit event
        await self.bus.emit(Event(
            type="description.new",
            data={"stream_id": stream_id, "text": description}
        ))

        # Rotate to next stream
        self.current_index = (self.current_index + 1) % len(self.streams)
```

With 4 streams and 500ms VLM latency:
- Each stream gets a VLM update every ~2 seconds
- Detection runs continuously on all streams
- Status updates prioritize RED conditions

---

## Data Model

### Persistent Configuration

```python
@dataclass
class FeedConfig:
    """Single camera feed configuration."""
    id: str                    # UUID
    name: str                  # "Room 101"
    source_url: str            # "rtsp://..."
    enabled: bool = True


@dataclass
class ProtocolConfig:
    """User-defined monitoring protocols."""
    green_rules: str           # Natural language description
    yellow_rules: str
    red_rules: str


@dataclass
class AppConfig:
    """Full application configuration - persisted to disk."""
    feeds: List[FeedConfig]
    protocols: ProtocolConfig
    created_at: datetime
    updated_at: datetime
```

### Runtime State

```python
@dataclass
class StreamStatus:
    """Current status for one stream."""
    stream_id: str
    severity: Literal["green", "yellow", "red"]
    icon: str                  # Emoji icon
    description: str           # AI-generated description
    timestamp: datetime
    confidence: float


@dataclass
class ActiveAlert:
    """Alert requiring attention."""
    id: str
    stream_id: str
    severity: Literal["yellow", "red"]
    description: str
    detected_at: datetime
    acknowledged: bool = False
    resolved_at: Optional[datetime] = None
```

---

## Protocol Evaluation

### How Rules Become Status

```python
class ProtocolEvaluator:
    """Maps VLM descriptions to protocol severity levels."""

    def __init__(self, protocols: ProtocolConfig, vlm):
        self.protocols = protocols
        self.vlm = vlm

    async def evaluate(self, stream_id: str, description: str, detections: List) -> StreamStatus:
        """Evaluate current scene against user protocols."""

        # First: Check for obvious RED conditions (person missing, etc.)
        if self._check_critical_detections(detections):
            return self._create_red_status(stream_id, detections)

        # Use VLM to classify against user rules
        prompt = f"""
Based on the following scene description, classify the situation.

Scene: {description}

User's protocols:
- GREEN (safe): {self.protocols.green_rules}
- YELLOW (attention): {self.protocols.yellow_rules}
- RED (critical): {self.protocols.red_rules}

Respond with:
1. Severity: GREEN, YELLOW, or RED
2. Icon suggestion (one word: reading, tv, sleeping, unclear, injury, emergency, missing)
3. Brief status message (one sentence)

Format: SEVERITY|ICON|MESSAGE
"""

        response = await self.vlm.query(prompt)
        return self._parse_response(stream_id, response)
```

### Icon Mapping

```python
ICON_MAP = {
    # Green icons
    "reading": "📗",
    "tv": "📺",
    "sleeping": "😴",
    "eating": "🍽️",
    "calm": "🧘",
    "exercise": "🏃‍♂️",

    # Yellow icons
    "unclear": "🔍",
    "injury": "🩹",
    "distress": "😰",
    "pacing": "🚶",

    # Red icons
    "emergency": "🚨",
    "missing": "🏃",
    "danger": "⚠️",
    "unconscious": "🚨",
}
```

---

## API Design

### Configuration Endpoints

```yaml
# Setup wizard
POST /api/config/feeds
  Body: { name: "Room 101", source_url: "rtsp://..." }
  Response: { feed_id: "...", status: "connected" }

DELETE /api/config/feeds/{feed_id}

POST /api/config/protocols
  Body: {
    green_rules: "...",
    yellow_rules: "...",
    red_rules: "..."
  }

GET /api/config
  Response: { feeds: [...], protocols: {...} }

# Test connection
POST /api/config/feeds/test
  Body: { source_url: "rtsp://..." }
  Response: { success: true, resolution: "1920x1080", fps: 30 }
```

### Monitoring Endpoints

```yaml
GET /api/status
  Response: {
    streams: [
      { stream_id: "...", severity: "green", icon: "📗", description: "..." },
      ...
    ],
    active_alerts: 2
  }

GET /api/alerts
  Response: { alerts: [...] }

POST /api/alerts/{id}/acknowledge

POST /api/alerts/{id}/resolve
```

### WebSocket

```yaml
WS /ws/live

# Server sends:
- { type: "status_update", stream_id: "...", severity: "...", icon: "...", description: "..." }
- { type: "alert_new", alert: {...} }
- { type: "frame", stream_id: "...", data: base64_jpeg }

# Client sends:
- { type: "query", stream_id: "...", question: "Is the resident in distress?" }
```

---

## Tech Stack

| Component | Technology | Reason |
|-----------|------------|--------|
| Multi-Stream Decode | DeepStream nvstreammux | Efficient batched decode |
| Detection | YOLOv8-s TensorRT (batched) | Person detection across all streams |
| VLM | NanoLLM + VILA-7B | Scene understanding |
| Event Bus | Python asyncio | Application-level events |
| API | FastAPI + WebSocket | Real-time updates |
| Frontend | React + Tailwind | Dashboard UI |
| Persistence | SQLite or JSON file | Configuration storage |
| Container | dustynv/nano_llm + DeepStream | Base runtime |

---

## Development Phases

### Phase 1: Setup Wizard & Persistence
- React wizard component with 3 steps
- SQLite/JSON configuration storage
- Feed connection testing
- Protocol input forms

### Phase 2: DeepStream Multi-Stream Pipeline
- nvstreammux configuration for N streams
- Batched YOLOv8 detection
- Per-stream frame routing
- Event bus integration

### Phase 3: Protocol Evaluation
- VLM-based rule matching
- Icon selection logic
- Status state machine
- Round-robin VLM sampling

### Phase 4: Dashboard & Alerts
- Multi-feed grid view
- Real-time status updates
- Alert management UI
- Expanded feed view with Q&A

### Phase 5: Polish & Demo
- Demo video feeds (simulated)
- Error handling
- Performance optimization
- Documentation

---

## Demo Mode

For presentations without live cameras:

```python
class DemoFeedSimulator:
    """Simulates camera feeds with pre-recorded scenarios."""

    SCENARIOS = {
        "room_101": "demo/videos/reading_scenario.mp4",
        "room_102": "demo/videos/watching_tv.mp4",
        "room_103": "demo/videos/unclear_corner.mp4",
        "room_104": "demo/videos/fall_emergency.mp4",
    }
```

Pre-recorded videos cycle through different status conditions to demonstrate:
- GREEN → YELLOW transitions
- YELLOW → RED escalations
- Alert triggering and acknowledgment
- Staff response workflows

---

## Relationship to MVP

This demo **extends** the core MVP architecture:

| MVP (Single-Stream) | Newport Demo (Multi-Stream) |
|---------------------|----------------------------|
| NanoLLM VideoSource | DeepStream nvstreammux |
| Single EventBus | Stream-aware EventBus |
| Generic alerts | Protocol-based evaluation |
| Basic UI | Dashboard + Wizard |
| No persistence | SQLite configuration |

The core event patterns, VLM integration, and agent tools remain the same.

---

*Newport Demo Spec - January 2026*
