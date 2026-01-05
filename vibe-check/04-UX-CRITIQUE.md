# UX Critique: Does the Interface Make Sense?

## Current UX Overview

From `mvp-docs/01-EXECUTIVE-SUMMARY.md`, we have 5 UX flows:

1. **Upload and Process** - Drag-drop videos with processing options
2. **Video Library Browser** - Grid view of videos with stats
3. **Video Detail View** - Player with detection overlays + Q&A
4. **Agent Chat Interface** - ChatGPT-style multi-video Q&A
5. **Model Playground** - Developer tool for testing models

---

## UX Concerns

### Problem 1: Too Many Entry Points

```
User opens app → Where do I go?

┌─────────────────────────────────────────────────┐
│  [Library]  [Agent]  [Upload]  [Playground]     │
│                                                 │
│     Which one do I click first?                 │
└─────────────────────────────────────────────────┘
```

**Issue:** 4 top-level navigation items before user understands the product.

**Fix:** Single entry point that guides the journey.

---

### Problem 2: Upload vs Process Confusion

From the Upload flow:
```
Processing Options:
☑ Scene detection (extract keyframes)
☑ Object detection (YOLOv8)
☑ VLM descriptions (VILA-7B)
☐ Audio transcription (Whisper)
```

**Issues:**
- Why would a user turn OFF scene detection?
- What happens if they uncheck VLM descriptions?
- Does unchecking YOLO break the agent later?
- "VILA-7B" means nothing to most users

**Fix:** Either process everything automatically, or make options meaningful to non-technical users.

---

### Problem 3: Library vs Agent Split

Current design separates:
- **Library** = Browse videos, search, view details
- **Agent** = Ask questions across videos

**Issue:** These should be the same thing. User mental model:
```
"I want to find something in my videos"
    → Could be search
    → Could be a question
    → Shouldn't matter which tab I'm on
```

**Fix:** Unified interface where search and Q&A coexist.

---

### Problem 4: Video Detail Complexity

The Video Detail View tries to do too much:

```
┌─────────────────────────────┬──────────────────┐
│                             │ Scene Info       │
│                             │ ───────────      │
│   Video Player              │ Timestamp        │
│   + Detection overlays      │ Scene #          │
│                             │ Objects list     │
│                             │ VLM description  │
├─────────────────────────────┴──────────────────┤
│ Timeline with keyframes                        │
├────────────────────────────────────────────────┤
│ Ask about this video: [________________] [Ask] │
└────────────────────────────────────────────────┘
```

**Issues:**
- Player controls compete with detection overlays
- Timeline competes with object list
- Q&A input at bottom (below the fold)
- Where do answers appear?

---

### Problem 5: Playground for Who?

```
Model Playground
├── Select frame or upload
├── Choose detection model
├── Choose VLM model
├── Enter custom prompt
└── View raw results
```

**Issues:**
- 0% of end users need this
- Developers want a CLI/API, not a GUI
- Takes attention away from the real product

**Fix:** Remove from MVP entirely. Add as `/dev` route later.

---

### Problem 6: Agent Chat Ambiguity

The Agent Chat tries to be intelligent about context:
```
Agent                              Context: All Videos (4)
```

**Issues:**
- "Context: All Videos" - what if I only want one?
- How do I change context? Not shown in wireframe.
- Chat history - where is it stored?
- Can I have multiple conversations?

---

## Alternative UX Approaches

### Alternative A: Search-First

**Concept:** Everything starts with a search bar.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Video Intelligence                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  🔍 "person walking near entrance"                   [Ask] │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Try: "Find all cars" • "What happened at 2:30?" • "Count people"│
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  Recent Results                                                  │
│  ┌────────┐ ┌────────┐ ┌────────┐                              │
│  │ 🖼     │ │ 🖼     │ │ 🖼     │                              │
│  │ 0:45   │ │ 2:12   │ │ 3:55   │                              │
│  └────────┘ └────────┘ └────────┘                              │
│                                                                  │
│  [+ Upload Video]                                                │
└─────────────────────────────────────────────────────────────────┘
```

**Pros:**
- Single clear action
- Works for search AND questions
- Results inline

**Cons:**
- No library browsing
- Assumes user has videos already

---

### Alternative B: Chat-First

**Concept:** ChatGPT-style, but for video.

```
┌─────────────────────────────────────────────────────────────────┐
│  Video Intelligence                              [4 videos] [+] │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  Welcome! I can answer questions about your videos.       │  │
│  │                                                           │  │
│  │  You have 4 videos indexed. Try asking:                   │  │
│  │  • "Summarize warehouse_footage.mp4"                      │  │
│  │  • "Find all people in my videos"                         │  │
│  │  • "When does the delivery truck arrive?"                 │  │
│  │                                                           │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Ask about your videos...                             [▶]  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Pros:**
- Familiar chat paradigm
- Single interface
- Clear onboarding

**Cons:**
- Less discoverable features
- No visual browsing

---

### Alternative C: Document-Style (Like Notion)

**Concept:** Each video is a "document" with AI-generated content.

```
┌─────────────────────────────────────────────────────────────────┐
│  ← All Videos    warehouse_footage.mp4           [Ask ▾] [···] │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ## Summary                                                      │
│  5:32 duration • 47 scenes • Last processed 2 hours ago         │
│                                                                  │
│  This video shows warehouse operations including workers         │
│  loading pallets, forklift movement, and inventory management.   │
│                                                                  │
│  ## Timeline                                                     │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ ▓▓░░░░░░▓▓▓░░░░░░▓░░░░░░░░▓▓▓▓░░░░░░░░░░░░▓░░░░░░░░░░░░░│ │
│  │  Activity distribution over time                          │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ## Key Moments                                                  │
│                                                                  │
│  ┌──────────┐  0:45 - Shift change, 4 workers arrive           │
│  │ 🖼       │  Detection: person (4), door (1)                 │
│  └──────────┘                                                   │
│                                                                  │
│  ┌──────────┐  2:34 - Forklift loading operation               │
│  │ 🖼       │  Detection: person (2), forklift (1), pallet (3) │
│  └──────────┘                                                   │
│                                                                  │
│  ## Objects Detected                                             │
│  [person: 142] [forklift: 23] [pallet: 89] [box: 234]          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Pros:**
- Everything visible at once
- Scrollable, scannable
- Feels like a report

**Cons:**
- Less interactive
- Questions need separate modal

---

### Alternative D: Minimal (Command Line Mentality)

**Concept:** Power user interface, like a terminal.

```
┌─────────────────────────────────────────────────────────────────┐
│  vip>                                                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  > list                                                          │
│  4 videos indexed:                                               │
│    [1] warehouse_footage.mp4 (5:32, 47 scenes)                   │
│    [2] parking_lot.mp4 (12:05, 89 scenes)                        │
│    [3] drone_flyover.mp4 (3:18, 32 scenes)                       │
│    [4] retail_cam.mp4 (8:45, processing...)                      │
│                                                                  │
│  > search "forklift" in 1                                        │
│  Found 23 matches in warehouse_footage.mp4:                      │
│    0:45 - forklift enters frame (conf: 0.94)                     │
│    1:12 - forklift loading pallet (conf: 0.91)                   │
│    ...                                                           │
│                                                                  │
│  > ask "how many people work the morning shift?"                │
│  Based on warehouse_footage.mp4, I observed 4 distinct           │
│  people arriving between 0:00-1:00, suggesting a morning         │
│  shift of 4 workers. [See: 0:12, 0:23, 0:34, 0:45]              │
│                                                                  │
│  > _                                                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Pros:**
- Extremely simple
- All operations visible
- Easy to build
- Power users love it

**Cons:**
- Intimidating for non-technical users
- No visual preview

---

## Recommended UX Direction

Given the concerns about scope and Jetson fit, I'd recommend:

### For MVP: Search-First (Alternative A)

**Why:**
- Single clear purpose
- Minimal UI development
- Focus on core value: finding things in video
- Can evolve into chat later

### For Real-Time Pivot: Dashboard-First

If pivoting to real-time edge processing:

```
┌─────────────────────────────────────────────────────────────────┐
│  Edge Monitor                    ● Live    [4 sources connected]│
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │ Camera 1    │ │ Camera 2    │ │ Camera 3    │ │ Camera 4    ││
│  │ [live view] │ │ [live view] │ │ [live view] │ │ [live view] ││
│  │ 2 people    │ │ 1 vehicle   │ │ 0 detects   │ │ 3 people    ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
│                                                                  │
│  Recent Events                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 🔴 14:32 Camera 1: Person entered restricted area         │  │
│  │ ⚪ 14:28 Camera 2: Vehicle parked                         │  │
│  │ ⚪ 14:15 Camera 1: Person exited frame                    │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  [View All Events]  [Configure Alerts]  [Search History]        │
└─────────────────────────────────────────────────────────────────┘
```

This would properly leverage Jetson's real-time capabilities.

---

## Questions to Resolve UX

Before finalizing UX, answer:

1. **What's the first thing a user does?**
   - Upload a video?
   - Connect a camera?
   - Search existing content?

2. **What's the primary output?**
   - Answers to questions?
   - Detection alerts?
   - Reports/exports?

3. **Who configures the system?**
   - Same user who queries?
   - Separate admin?

4. **How much time do users spend?**
   - Quick lookups (seconds)?
   - Deep analysis (minutes)?
   - Continuous monitoring (hours)?

---

## References

- Current UX flows: `mvp-docs/01-EXECUTIVE-SUMMARY.md:79-266`
- Upload options: `mvp-docs/01-EXECUTIVE-SUMMARY.md:105-112`
- Agent interface: `mvp-docs/01-EXECUTIVE-SUMMARY.md:180-221`
- Playground: `mvp-docs/01-EXECUTIVE-SUMMARY.md:223-266`

---

*UX Critique - January 2026*
