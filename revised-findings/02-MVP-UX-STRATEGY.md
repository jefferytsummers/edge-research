# MVP UX Strategy

## Target Users

### Primary: Security Operations / Facility Managers
- Monitor 1-8 camera feeds simultaneously
- Need real-time alerts without watching screens constantly
- Ask questions in plain English ("Is anyone in the loading dock?")
- Non-technical, expect consumer-grade simplicity

### Secondary: System Integrators
- Deploy and configure the system
- Connect to existing camera infrastructure (RTSP/ONVIF)
- Integrate with enterprise systems (MQTT, Kafka, webhooks)

---

## Core UX Flows

### Flow 1: Live Video Monitoring
```
┌─────────────────────────────────────────────────────────────┐
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ Cam 1   │ │ Cam 2   │ │ Cam 3   │ │ Cam 4   │  [+ Add]  │
│  │ ▶ LIVE  │ │ ▶ LIVE  │ │ ▶ LIVE  │ │ ▶ LIVE  │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
│                                                             │
│  Selected: Camera 1                                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                     │   │
│  │              [Live Video with Overlays]             │   │
│  │               Bounding boxes + labels               │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Ask: "What's happening in this scene?"        [Ask] │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  AI Response: "Two people are standing near the entrance.  │
│  One appears to be carrying a package."                    │
└─────────────────────────────────────────────────────────────┘
```

**Key UX Decisions:**
- WebRTC for sub-200ms video latency (browser-native, no plugins)
- Detection overlays always on (bounding boxes, tracking IDs)
- VLM query is opt-in (user clicks "Ask" or types question)
- Responses appear inline, don't interrupt video

---

### Flow 2: Alert Configuration
```
┌─────────────────────────────────────────────────────────────┐
│  Configure Alert for: Camera 1                              │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  Trigger Type:                                              │
│  ○ Object Detection (person, vehicle, package)              │
│  ○ Line Crossing (draw tripwire on video)                   │
│  ● AI Query (ask a question, alert on answer)               │
│                                                             │
│  AI Question:                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ "Is anyone in the restricted area?"                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Alert When: ○ Yes answer  ● Any activity  ○ No activity   │
│  Check Every: [5] seconds                                   │
│                                                             │
│  Notify Via:                                                │
│  ☑ Browser notification                                    │
│  ☑ Webhook: https://my-system.com/alerts                   │
│  ☐ Email                                                    │
│                                                             │
│                                        [Cancel] [Save]      │
└─────────────────────────────────────────────────────────────┘
```

**Key UX Decisions:**
- Natural language alerts (not just object detection rules)
- Configurable check frequency (balance latency vs. compute)
- Multiple notification channels
- Visual tripwire drawing for line-crossing alerts

---

### Flow 3: Stream Management
```
┌─────────────────────────────────────────────────────────────┐
│  Video Sources                                    [+ Add]   │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  ┌─────┬──────────────┬────────────┬────────┬───────────┐  │
│  │ ● │ Camera 1       │ 1080p@30   │ 45ms   │ [···]     │  │
│  │ ● │ Camera 2       │ 1080p@30   │ 52ms   │ [···]     │  │
│  │ ○ │ Camera 3       │ Offline    │ --     │ [···]     │  │
│  │ ● │ Camera 4       │ 720p@25    │ 38ms   │ [···]     │  │
│  └───┴────────────────┴────────────┴────────┴───────────┘  │
│                                                             │
│  Add Camera:                                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ○ RTSP URL: rtsp://user:pass@192.168.1.100/stream   │   │
│  │ ○ ONVIF Discovery (auto-detect)                      │   │
│  │ ○ USB Camera (/dev/video0)                           │   │
│  │ ○ CSI Camera (Jetson GPIO)                           │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Key UX Decisions:**
- Show connection status (green dot = live)
- Display real latency per stream
- Support multiple camera protocols
- ONVIF discovery for easy enterprise camera integration

---

## UI Technology Choices

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Web Framework | React/Vue + Vite | Fast dev, component reuse |
| Video Playback | WebRTC (native) | <200ms latency, hardware decode |
| State Management | React Query / SWR | Server state sync |
| Styling | Tailwind CSS | Rapid UI development |
| Real-time Updates | WebSocket | Metadata, alerts |
| Backend Communication | REST + WebSocket | Control + streaming |

---

## Responsive Design

### Desktop (Primary)
- Multi-camera grid (1x1, 2x2, 3x3, 4x4)
- Side panel for controls and AI chat
- Full keyboard shortcuts

### Tablet
- 2x2 grid max
- Swipe between cameras
- Floating AI query button

### Mobile (View-Only)
- Single camera view
- Alert notifications only
- No configuration

---

## Accessibility

- Keyboard navigation for all controls
- Screen reader support for alerts
- High contrast mode
- Audio alerts for critical events

---

## MVP Scope (V1)

**Included:**
- Single Jetson device management
- 1-4 camera streams
- Live video with detection overlays
- VLM query (one-shot questions)
- Basic alert configuration (object detection)
- Browser notifications

**Deferred (V2):**
- Multi-Jetson fleet management
- VLM-based continuous alerts
- Mobile apps
- Video recording/playback
- User authentication/roles

---

## Performance Targets

| Metric | Target | User Impact |
|--------|--------|-------------|
| Video latency | <200ms | Real-time feel |
| VLM response | <500ms | Conversational flow |
| Page load | <2s | First meaningful paint |
| Alert delivery | <1s | Timely notification |

---

*UX Strategy - January 2026*
