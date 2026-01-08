# Agent Memory Architecture

## Overview

The Newport Demo agent uses a **multi-layered memory architecture** to maintain state across different time horizons and provide contextual understanding of monitored environments. This document explains how "memory" manifests at each layer and links these mechanisms to concrete UX examples.

---

## Memory Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         MEMORY ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  LAYER 1: Ephemeral (Milliseconds → Seconds)                            │
│  ├── Pending frames buffer                                               │
│  ├── VLM inference queue                                                 │
│  └── WebSocket broadcast queue                                           │
│                                                                          │
│  LAYER 2: Working Memory (Seconds → Minutes)                            │
│  ├── StatusStateMachine (debounce state per stream)                     │
│  ├── MultiStreamVLMSampler (round-robin tracking)                       │
│  └── EventBus in-flight events                                          │
│                                                                          │
│  LAYER 3: Session Memory (Minutes → Hours)                              │
│  ├── Frontend Zustand stores (client-side)                              │
│  │   ├── streamStore: current statuses + history                        │
│  │   ├── alertStore: active + resolved alerts                           │
│  │   └── configStore: persisted to localStorage                         │
│  └── Redis pub/sub state (server-side)                                  │
│                                                                          │
│  LAYER 4: Persistent Memory (Hours → Forever)                           │
│  ├── SQLite configuration database                                       │
│  ├── Alert history table                                                 │
│  └── User-defined protocols                                              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Layer 1: Ephemeral Memory (Frames & Inference)

### What It Stores
- Raw video frames awaiting VLM processing
- Detection results from DeepStream
- Pending classification requests

### Implementation
**File: `vlm/src/vlm_subscriber.py:274-278`**
```python
# Store pending frame data
self._pending_frames[stream_id] = {
    "detections": detections,
    "frame_path": frame_path,
    "timestamp": data.get("timestamp", time.time())
}
```

### UX Example: Real-Time Frame Analysis

**User Scenario:** Staff member opens Room 103 in expanded view.

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Room 103 - Expanded View                                                │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                                                                     │ │
│  │                    [ Live Video Feed ]                              │ │
│  │                                                                     │ │
│  │    Pending frames: analyzing...                                     │ │
│  │                                                                     │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  Current Analysis: Processing frame 1847                                 │
│  Last VLM inference: 450ms ago                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**What's Happening:**
1. DeepStream writes latest frame to `/shared/frames/room_103/latest.jpg`
2. VLM subscriber stores frame path in `_pending_frames["room_103"]`
3. Round-robin sampler picks room_103 for next inference
4. Frame is processed, result published to Redis

---

## Layer 2: Working Memory (State Machines)

### What It Stores
- Debounce counters for status transitions
- Current vs pending severity states
- Round-robin sampling timestamps

### Implementation
**File: `vlm/src/protocol_evaluator.py:55-91`**
```python
class StatusStateMachine:
    """
    Tracks status transitions with debouncing.
    Requires N consecutive classifications before changing state
    to prevent flapping on transient misclassifications.
    """

    def __init__(self, debounce_count: int = 2):
        self.current: Severity = "green"
        self.pending: Optional[Severity] = None
        self.pending_count: int = 0

    def update(self, new_status: Severity) -> Optional[Severity]:
        if new_status != self.current:
            if new_status == self.pending:
                self.pending_count += 1
                if self.pending_count >= self.debounce_count:
                    # Status confirmed after N consecutive readings
                    self.current = new_status
                    return new_status
            else:
                # New pending status
                self.pending = new_status
                self.pending_count = 1
        return None
```

### UX Example: Debounced Status Changes

**User Scenario:** Resident in Room 104 briefly crouches to pick something up.

```
Timeline:
─────────────────────────────────────────────────────────────────────────
T+0s    VLM: "Person crouching" → YELLOW (pending_count=1)
        UI: Still shows GREEN ✓

T+10s   VLM: "Person standing, reading" → GREEN (reset pending)
        UI: Still shows GREEN ✓

T+20s   VLM: "Person reading in chair" → GREEN
        UI: Shows GREEN ✓
─────────────────────────────────────────────────────────────────────────

Result: No false alarm! Status stayed GREEN because the YELLOW
classification wasn't repeated twice in a row.
```

**Without Debouncing (Bad UX):**
```
T+0s    VLM: "Person crouching" → YELLOW
        UI: YELLOW ⚠️ Alert triggered!
        Staff rushes to room...

T+10s   VLM: "Person standing" → GREEN
        UI: GREEN ✓ False alarm.
        Staff annoyed.
```

### UX Example: Round-Robin Fair Sampling

**File: `vlm/src/vlm_subscriber.py:30-81`**
```python
class MultiStreamVLMSampler:
    def __init__(self, streams: List[str], interval_per_stream: float = 10.0):
        self.streams = streams
        self.interval = interval_per_stream
        self.current_index = 0
        self._last_sample: Dict[str, float] = {}
```

**User Scenario:** 4 cameras monitored simultaneously.

```
VLM Sampling Schedule (500ms per inference):
─────────────────────────────────────────────────────────────────────────
T+0.0s   → Room 101 analyzed
T+0.5s   → Room 102 analyzed
T+1.0s   → Room 103 analyzed
T+1.5s   → Room 104 analyzed
T+2.0s   → Room 101 analyzed (cycle repeats)
...
─────────────────────────────────────────────────────────────────────────

Each room gets VLM analysis every ~2 seconds with 4 streams.
Detection (YOLO) runs continuously on ALL streams simultaneously.
```

**Dashboard View:**
```
┌───────────────────────────────────────────────────────────────────────┐
│  Newport Demo                                    ● Monitoring Active   │
├───────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌─────────────────────┐  ┌─────────────────────┐                     │
│  │ Room 101            │  │ Room 102            │                     │
│  │ 📗 Reading          │  │ 📺 Watching TV      │                     │
│  │ Updated: 2s ago     │  │ Updated: 1.5s ago   │  ← Round-robin      │
│  └─────────────────────┘  └─────────────────────┘    ensures fair     │
│                                                       updates          │
│  ┌─────────────────────┐  ┌─────────────────────┐                     │
│  │ Room 103            │  │ Room 104            │                     │
│  │ 🔍 Unclear          │  │ 😴 Sleeping         │                     │
│  │ Updated: 1s ago     │  │ Updated: 0.5s ago   │                     │
│  └─────────────────────┘  └─────────────────────┘                     │
│                                                                        │
└───────────────────────────────────────────────────────────────────────┘
```

---

## Layer 3: Session Memory (Frontend Stores)

### What It Stores
- Current status for all streams
- Status history (last 50 entries per stream)
- Active and resolved alerts
- WebSocket connection state

### Implementation
**File: `app/frontend/src/store/streamStore.ts:22-52`**
```typescript
export const useStreamStore = create<StreamState>()((set) => ({
  statuses: {},           // Current status per stream
  history: {},            // Status history per stream
  isConnected: false,

  updateStatus: (status) =>
    set((state) => {
      const prevStatus = state.statuses[status.stream_id];
      const newHistory = { ...state.history };

      // Add to history if severity changed
      if (prevStatus && prevStatus.severity !== status.severity) {
        const streamHistory = newHistory[status.stream_id] || [];
        newHistory[status.stream_id] = [
          {
            severity: status.severity,
            description: status.description,
            timestamp: status.timestamp,
          },
          ...streamHistory,
        ].slice(0, MAX_HISTORY_ENTRIES);  // Keep last 50
      }
      // ...
    }),
}));
```

### UX Example: Status History Timeline

**User Scenario:** Staff reviews what happened in Room 104 over the past hour.

```
┌───────────────────────────────────────────────────────────────────────┐
│  Room 104 - Status History                           [← Back to Grid] │
├───────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Current: 🚨 RED - CRITICAL                                           │
│  "Resident appears unconscious on the ground"                         │
│                                                                        │
│  ─────────────────────────────────────────────────────────────────────│
│  History (Session Memory - stored in browser):                        │
│                                                                        │
│  • 14:32 - 🚨 RED    - Unconscious detected (CURRENT)                 │
│  • 14:28 - 🔍 YELLOW - Resident crouching near bed                    │
│  • 14:15 - 😴 GREEN  - Resident sleeping normally                     │
│  • 13:45 - 📺 GREEN  - Resident watching TV                           │
│  • 13:30 - 🍽️ GREEN  - Resident eating lunch                          │
│  • 13:00 - 📗 GREEN  - Resident reading magazine                      │
│                                                                        │
│  [Load More History]  ← Would fetch from SQLite persistence           │
│                                                                        │
└───────────────────────────────────────────────────────────────────────┘
```

**How Memory Enables This:**
1. `streamStore.history["room_104"]` contains last 50 status changes
2. Each entry captured when `updateStatus()` detects severity change
3. Timeline sorted newest-first for quick incident review
4. Staff can trace the progression: GREEN → YELLOW → RED

### UX Example: Alert Acknowledgment Flow

**File: `app/frontend/src/store/alertStore.ts:16-46`**
```typescript
export const useAlertStore = create<AlertState>()((set) => ({
  alerts: [],

  acknowledgeAlert: (alertId) =>
    set((state) => ({
      alerts: state.alerts.map((a) =>
        a.id === alertId ? { ...a, acknowledged: true } : a
      ),
    })),

  resolveAlert: (alertId) =>
    set((state) => ({
      alerts: state.alerts.map((a) =>
        a.id === alertId
          ? { ...a, resolved_at: new Date().toISOString() }
          : a
      ),
    })),
}));
```

**User Scenario:** Staff responds to Room 104 emergency.

```
Alert Lifecycle (stored in alertStore):
─────────────────────────────────────────────────────────────────────────

1. ALERT CREATED (status changed to RED)
┌─────────────────────────────────────────────────────────────────────┐
│ 🚨 Room 104 - UNCONSCIOUS RESIDENT                     [Acknowledge]│
│ Detected: 14:32:01                                                  │
│ "Resident appears to be lying face-down on floor"                   │
└─────────────────────────────────────────────────────────────────────┘

2. ACKNOWLEDGED (staff clicks button)
┌─────────────────────────────────────────────────────────────────────┐
│ 🚨 Room 104 - UNCONSCIOUS RESIDENT                ✓ Acknowledged   │
│ Detected: 14:32:01 | Ack'd: 14:33:15                                │
│ "Resident appears to be lying face-down on floor"    [Mark Resolved]│
└─────────────────────────────────────────────────────────────────────┘

3. RESOLVED (incident handled)
┌─────────────────────────────────────────────────────────────────────┐
│ ✓ Room 104 - RESOLVED                                               │
│ Duration: 8 minutes                                                 │
│ "Staff responded - resident was exercising on floor"                │
└─────────────────────────────────────────────────────────────────────┘
─────────────────────────────────────────────────────────────────────────
```

---

## Layer 4: Persistent Memory (Protocols & Config)

### What It Stores
- Camera feed configurations (RTSP URLs, names)
- User-defined behavioral protocols
- Alert history beyond current session

### Implementation
**File: `app/frontend/src/store/configStore.ts:31-83`**
```typescript
export const useConfigStore = create<ConfigState>()(
  persist(                    // ← Zustand persist middleware
    (set) => ({
      feeds: [],
      protocols: defaultProtocols,
      isConfigured: false,
      // ... actions
    }),
    {
      name: 'newport-config',  // ← localStorage key
    }
  )
);
```

### UX Example: Protocol Memory Across Sessions

**User Scenario:** Facility administrator sets up custom protocols.

```
SETUP WIZARD - Step 2: Define Protocols
─────────────────────────────────────────────────────────────────────────

🟢 GREEN - Safe Behavior
┌─────────────────────────────────────────────────────────────────────┐
│ Reading, watching TV, sleeping normally in bed, eating meals,       │
│ sitting calmly, taking medication as scheduled, exercising,         │
│ video calls with family                                             │
└─────────────────────────────────────────────────────────────────────┘

🟡 YELLOW - Needs Attention
┌─────────────────────────────────────────────────────────────────────┐
│ Out of camera view, crouching in corners, minor injuries,           │
│ pacing erratically, signs of distress, refusing medication,         │
│ arguments with staff                                                │
└─────────────────────────────────────────────────────────────────────┘

🔴 RED - Immediate Action Required
┌─────────────────────────────────────────────────────────────────────┐
│ Unconscious on ground, severe injury, room is empty,                │
│ self-harm behavior, medical emergency, attempting to leave,         │
│ violence toward self or others                                      │
└─────────────────────────────────────────────────────────────────────┘

                                           [Back]  [Save & Continue →]
─────────────────────────────────────────────────────────────────────────
```

**After Saving:**
```javascript
// Persisted to localStorage under 'newport-config'
{
  "feeds": [
    {"stream_id": "a1b2c3", "name": "Room 101", "source_uri": "rtsp://..."},
    {"stream_id": "d4e5f6", "name": "Room 102", "source_uri": "rtsp://..."},
  ],
  "protocols": {
    "green_rules": "Reading, watching TV, sleeping normally...",
    "yellow_rules": "Out of camera view, crouching in corners...",
    "red_rules": "Unconscious on ground, severe injury..."
  },
  "isConfigured": true
}
```

**Memory in Action - Next Day:**
```
User opens Newport Demo → Config loads from localStorage →
No wizard needed → Straight to monitoring dashboard with
all protocols intact.
```

### UX Example: Protocol-Driven Classification

**How user protocols become agent "memory":**

**File: `vlm/src/vlm_subscriber.py:153-186`**
```python
def classify(self, image_path: str, protocols: ProtocolConfig) -> str:
    prompt = f"""Analyze this image and classify the situation.

User's protocols:
- GREEN (safe): {protocols.green_rules}
- YELLOW (attention): {protocols.yellow_rules}
- RED (critical): {protocols.red_rules}

Respond with EXACTLY this format (one line):
SEVERITY|ICON|MESSAGE
"""
    response = self._model.generate(prompt, image=image, max_new_tokens=50)
    return response
```

**User Scenario:** Resident in Room 103 is pacing.

```
VLM Input:
- Image: /shared/frames/room_103/latest.jpg (shows person walking back and forth)
- Protocol memory: "YELLOW: pacing erratically, signs of distress"

VLM Output:
"YELLOW|pacing|Resident pacing back and forth near window, appears agitated"

Dashboard Update:
┌─────────────────────┐
│ Room 103            │
│ 🚶 Pacing           │
│ ● YELLOW - Attention│
└─────────────────────┘

Because "pacing" was in the user's YELLOW rules, the VLM classified
it appropriately. If a different facility had "pacing" as GREEN
(normal exercise), the classification would differ.
```

---

## Memory Flow: Complete UX Journey

### Scenario: Emergency Detection in Room 104

```
TIME    LAYER           ACTION                        UX IMPACT
─────────────────────────────────────────────────────────────────────────
14:32:00  L1 (Ephemeral)   DeepStream detects person    (Background)
                          on ground, writes frame

14:32:01  L1 (Ephemeral)   Frame stored in              (Background)
                          _pending_frames["room_104"]

14:32:02  L2 (Working)     VLM classifies → RED         Status change
                          StateMachine: pending=RED,    pending...
                          count=1

14:32:12  L2 (Working)     VLM confirms → RED           Status CONFIRMED!
                          StateMachine: current=RED     (debounce passed)

14:32:12  L3 (Session)     streamStore.updateStatus()   Dashboard turns RED
                          history.push({RED, desc})     History updated

14:32:12  L3 (Session)     alertStore.addAlert()        Alert appears!
                                                       Sound plays!

14:33:00  L3 (Session)     Staff clicks "Acknowledge"   Alert marked ack'd
                          alertStore.acknowledge()

14:40:00  L3 (Session)     Staff clicks "Resolve"       Alert moved to
                          alertStore.resolve()         history

14:40:00  L4 (Persistent)  Alert saved to SQLite        Survives restart
                          for compliance reporting
─────────────────────────────────────────────────────────────────────────
```

---

## Memory Design Principles

### 1. Debouncing Prevents Alert Fatigue
The `StatusStateMachine` requires 2 consecutive matching classifications before changing state. This prevents:
- Momentary misclassifications from triggering false alarms
- Rapid status oscillation ("flapping")
- Staff becoming desensitized to alerts

### 2. History Enables Incident Review
The `streamStore.history` maintains up to 50 entries per stream, allowing:
- Post-incident timeline reconstruction
- Pattern identification over time
- Compliance documentation

### 3. Protocols Are "Semantic Memory"
User-defined protocols act as the agent's long-term semantic memory:
- Define what behaviors mean (GREEN vs YELLOW vs RED)
- Customizable per facility/use case
- Persist across sessions and restarts

### 4. Layered Persistence Balances Performance & Durability
| Layer | Storage | Survives Restart? | Purpose |
|-------|---------|-------------------|---------|
| L1 Ephemeral | tmpfs/RAM | No | Fast frame processing |
| L2 Working | In-process | No | Debounce, sampling |
| L3 Session | localStorage | Browser only | Current session state |
| L4 Persistent | SQLite | Yes | Configuration, audit trail |

---

## Technical Reference

### Key Files
| File | Memory Responsibility |
|------|----------------------|
| `vlm/src/vlm_subscriber.py:274` | Pending frames buffer |
| `vlm/src/protocol_evaluator.py:55` | StatusStateMachine |
| `vlm/src/vlm_subscriber.py:30` | MultiStreamVLMSampler |
| `app/src/event_bus.py:69` | Event routing |
| `app/frontend/src/store/streamStore.ts` | Status & history |
| `app/frontend/src/store/alertStore.ts` | Alert lifecycle |
| `app/frontend/src/store/configStore.ts` | Persistent config |

### Memory Capacities
| Component | Capacity | Configurable |
|-----------|----------|--------------|
| Pending frames | 1 per stream | Fixed |
| Status history | 50 entries/stream | `MAX_HISTORY_ENTRIES` |
| Debounce count | 2 readings | `StatusStateMachine.__init__` |
| VLM sample interval | 10s/stream | `interval_per_stream` |
| Alert retention | Unlimited | SQLite storage |

---

*Memory Architecture Documentation - January 2026*
