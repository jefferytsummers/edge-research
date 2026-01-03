# Alternative UX: Static/Web Video + RAG Agent

## Why This Approach First

| Live Streaming (02-MVP-UX) | Static/Web Video (This Doc) |
|---------------------------|------------------------------|
| WebRTC complexity | Simple HTTP/REST |
| Real-time latency critical | Batch processing OK |
| Single-purpose (surveillance) | Multi-purpose platform |
| Hardware camera integration | Any video source |
| Production-focused | Development + Production |

**Start here because:**
1. Easier to build and test (no streaming infrastructure)
2. Same VLM/detection models work for both
3. Natural foundation for RAG agent (indexed video knowledge)
4. Can process YouTube, uploads, URLs, local files
5. Extends to live streaming later

---

## Core Concept: Video Intelligence Platform

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         VIDEO INTELLIGENCE PLATFORM                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐    │
│   │   Upload    │   │  URL/Web    │   │   YouTube   │   │   Live      │    │
│   │   Video     │   │   Video     │   │   Import    │   │  (Future)   │    │
│   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘    │
│          └─────────────────┴─────────────────┴─────────────────┘            │
│                                     │                                        │
│                                     ▼                                        │
│                    ┌────────────────────────────────┐                       │
│                    │       Video Processing         │                       │
│                    │  • Frame extraction            │                       │
│                    │  • Scene detection             │                       │
│                    │  • Object detection (YOLO)     │                       │
│                    │  • VLM descriptions            │                       │
│                    └────────────────┬───────────────┘                       │
│                                     │                                        │
│                                     ▼                                        │
│                    ┌────────────────────────────────┐                       │
│                    │       Knowledge Index          │                       │
│                    │  • Embeddings (frames + text)  │                       │
│                    │  • Temporal metadata           │                       │
│                    │  • Object/scene graph          │                       │
│                    └────────────────┬───────────────┘                       │
│                                     │                                        │
│                                     ▼                                        │
│                    ┌────────────────────────────────┐                       │
│                    │         RAG Agent              │                       │
│                    │  • Natural language queries    │                       │
│                    │  • Multi-video reasoning       │                       │
│                    │  • Temporal search             │                       │
│                    │  • Tool use (detection, VLM)   │                       │
│                    └────────────────────────────────┘                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Target Users

### Primary: Analysts & Researchers
- Process video datasets for insights
- Ask complex questions across multiple videos
- Extract structured data from unstructured video

### Secondary: Developers
- Test VLM/detection models on sample videos
- Build custom video analysis pipelines
- API-first integration with other systems

### Tertiary: Content Creators
- Analyze video content for SEO
- Generate descriptions and metadata
- Search across video libraries

---

## Core UX Flows

### Flow 1: Video Upload & Processing

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Upload Video                                                               │
│  ───────────────────────────────────────────────────────────────────────── │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │                    ┌───────────────────┐                            │   │
│  │                    │   ➕ Drop video   │                            │   │
│  │                    │   or click to     │                            │   │
│  │                    │   browse          │                            │   │
│  │                    └───────────────────┘                            │   │
│  │                                                                     │   │
│  │   Or paste URL:  ┌────────────────────────────────────────┐        │   │
│  │                  │ https://youtube.com/watch?v=...        │        │   │
│  │                  └────────────────────────────────────────┘        │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Processing Options:                                                        │
│  ☑ Extract keyframes (1 per scene change)                                  │
│  ☑ Run object detection (YOLOv8)                                           │
│  ☑ Generate VLM descriptions (every 5 seconds)                             │
│  ☐ Full frame-by-frame analysis (slow)                                     │
│  ☐ Audio transcription (Whisper)                                           │
│                                                                             │
│                                               [Cancel]  [Process Video]     │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Processing Status:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Processing: drone_footage.mp4                                              │
│  ───────────────────────────────────────────────────────────────────────── │
│                                                                             │
│  ████████████████████████░░░░░░░░░░░░░░░░░░░░  58%                         │
│                                                                             │
│  ✓ Video loaded (1920x1080, 30fps, 5:32 duration)                          │
│  ✓ Keyframes extracted (47 frames)                                         │
│  ● Running object detection... (frame 28/47)                                │
│  ○ VLM descriptions pending                                                 │
│  ○ Building knowledge index                                                 │
│                                                                             │
│  Estimated time remaining: 2:15                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Flow 2: Video Browser & Timeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Video: drone_footage.mp4                                    [← Back]       │
│  ───────────────────────────────────────────────────────────────────────── │
│                                                                             │
│  ┌─────────────────────────────────────────────┐  ┌───────────────────────┐│
│  │                                             │  │ Detections            ││
│  │                                             │  │ ─────────────────     ││
│  │         [Video Player with Overlays]        │  │ 🚗 car (12)          ││
│  │          Bounding boxes + labels            │  │ 🚶 person (8)        ││
│  │                                             │  │ 🌳 tree (45)         ││
│  │                                             │  │ 🏠 building (6)      ││
│  │                                             │  │                       ││
│  │                           advancement        │  │ Scene: outdoor,       ││
│  │    ◀ ▶ ▮▮   advancement 2:34 / 5:32         │  │ aerial, suburban      ││
│  └─────────────────────────────────────────────┘  └───────────────────────┘│
│                                                                             │
│  Timeline (keyframes):                                                      │
│  ┌────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐  │
│  │ 🖼 │ 🖼 │ 🖼 │ 🖼 │ 🖼 │ 🖼 │ 🖼 │ 🖼 │ 🖼 │ 🖼 │ 🖼 │ 🖼 │ 🖼 │ 🖼 │  │
│  │0:00│0:15│0:28│0:45│1:02│1:18│1:35│2:01│2:34│3:05│3:42│4:10│4:48│5:20│  │
│  └────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘  │
│                              ▲ current position                             │
│                                                                             │
│  VLM Description (2:34):                                                    │
│  "A residential neighborhood viewed from above. Several cars are parked     │
│   on driveways. One person is walking a dog on the sidewalk. The trees     │
│   are in full foliage, suggesting summer."                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Flow 3: RAG Agent Chat (Core Differentiator)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Video Intelligence Agent                                       [Settings] │
│  ───────────────────────────────────────────────────────────────────────── │
│                                                                             │
│  Context: drone_footage.mp4, warehouse_cam.mp4, parking_lot.mp4            │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  You: "Find all moments where a red vehicle appears"                │   │
│  │                                                                     │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │                                                                     │   │
│  │  Agent: I found 3 occurrences of red vehicles across your videos:  │   │
│  │                                                                     │   │
│  │  1. **drone_footage.mp4** @ 1:23-1:45                              │   │
│  │     Red pickup truck driving through intersection                   │   │
│  │     [▶ Jump to clip]  [📷 View frame]                              │   │
│  │                                                                     │   │
│  │  2. **parking_lot.mp4** @ 0:45-0:52                                │   │
│  │     Red sedan parking in spot B-12                                  │   │
│  │     [▶ Jump to clip]  [📷 View frame]                              │   │
│  │                                                                     │   │
│  │  3. **parking_lot.mp4** @ 3:18-3:25                                │   │
│  │     Same red sedan departing                                        │   │
│  │     [▶ Jump to clip]  [📷 View frame]                              │   │
│  │                                                                     │   │
│  │  Would you like me to analyze these clips further or track the     │   │
│  │  red vehicles across all footage?                                   │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Ask about your videos...                                      [Send]│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Suggested questions:                                                       │
│  • "Summarize what happens in each video"                                  │
│  • "How many people appear total across all videos?"                       │
│  • "Find any unusual or suspicious activity"                               │
│  • "Create a timeline of all vehicle movements"                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Flow 4: Multi-Model Playground

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Model Playground                                               [Settings] │
│  ───────────────────────────────────────────────────────────────────────── │
│                                                                             │
│  Input:                                                                     │
│  ┌─────────────────────────────────────────┐                               │
│  │                                         │  Source: drone_footage.mp4    │
│  │        [Selected Frame @ 2:34]          │  Frame: 1542 / 9960           │
│  │                                         │  Resolution: 1920x1080        │
│  └─────────────────────────────────────────┘                               │
│                                                                             │
│  Models:                                                                    │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐            │
│  │ ☑ YOLOv8-s      │ │ ☑ VILA-7B       │ │ ☐ Grounding DINO │            │
│  │   Detection      │ │   VLM Query      │ │   Open Vocab     │            │
│  │   Latency: 8ms   │ │   Latency: 120ms │ │   Latency: 85ms  │            │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘            │
│                                                                             │
│  VLM Prompt:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Describe the scene in detail. Focus on any activity or objects     │   │
│  │ that seem out of place.                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│                                                              [Run Models]   │
│  ───────────────────────────────────────────────────────────────────────── │
│                                                                             │
│  Results:                                                                   │
│                                                                             │
│  YOLOv8-s (8ms):                     VILA-7B (120ms):                      │
│  ┌─────────────────────────────┐     ┌─────────────────────────────┐       │
│  │ • person: 0.92 [x,y,w,h]   │     │ This is an aerial view of a │       │
│  │ • car: 0.88 [x,y,w,h]      │     │ suburban neighborhood. A    │       │
│  │ • car: 0.85 [x,y,w,h]      │     │ person is walking their dog │       │
│  │ • dog: 0.78 [x,y,w,h]      │     │ on the sidewalk. Nothing    │       │
│  │ • tree: 0.95 [x,y,w,h]     │     │ appears unusual; this seems │       │
│  │ ...                         │     │ like a typical residential  │       │
│  └─────────────────────────────┘     │ scene on a sunny day.       │       │
│                                      └─────────────────────────────┘       │
│                                                                             │
│  [Export JSON]  [Copy Results]  [Add to Report]                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## RAG Agent Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              RAG AGENT                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  User Query: "Find moments where people are running"                        │
│                      │                                                       │
│                      ▼                                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        QUERY UNDERSTANDING                             │  │
│  │  • Intent: temporal_search                                             │  │
│  │  • Entities: person, running (action)                                  │  │
│  │  • Scope: all indexed videos                                           │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                      │                                                       │
│                      ▼                                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        TOOL SELECTION                                  │  │
│  │                                                                        │  │
│  │  Available Tools:                                                      │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐  │  │
│  │  │ vector_search│ │ detection    │ │ vlm_query    │ │ temporal_    │  │  │
│  │  │              │ │              │ │              │ │ filter       │  │  │
│  │  │ Semantic     │ │ Run YOLO on  │ │ Ask VLM      │ │ Filter by    │  │  │
│  │  │ similarity   │ │ frame        │ │ about frame  │ │ timestamp    │  │  │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘  │  │
│  │                                                                        │  │
│  │  Selected: vector_search → vlm_query (verify)                          │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                      │                                                       │
│                      ▼                                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        KNOWLEDGE INDEX                                 │  │
│  │                                                                        │  │
│  │  ┌─────────────────────┐    ┌─────────────────────┐                   │  │
│  │  │   Frame Embeddings  │    │   Text Embeddings   │                   │  │
│  │  │   (CLIP/SigLIP)     │    │   (VLM descriptions)│                   │  │
│  │  │                     │    │                     │                   │  │
│  │  │   video1_f001.emb   │    │   "person walking"  │                   │  │
│  │  │   video1_f002.emb   │    │   "car driving"     │                   │  │
│  │  │   ...               │    │   ...               │                   │  │
│  │  └─────────────────────┘    └─────────────────────┘                   │  │
│  │                                                                        │  │
│  │  Vector DB: ChromaDB / FAISS / Milvus                                  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                      │                                                       │
│                      ▼                                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        RESPONSE GENERATION                             │  │
│  │                                                                        │  │
│  │  Retrieved: 5 candidate frames                                         │  │
│  │  VLM Verified: 3 confirmed "running" activity                          │  │
│  │  Response: Formatted with timestamps, thumbnails, links                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Technical Architecture

### Backend Stack
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            BACKEND SERVICES                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐                   │
│  │   FastAPI     │  │   Celery      │  │   Redis       │                   │
│  │   (REST API)  │  │   (Workers)   │  │   (Queue +    │                   │
│  │               │  │               │  │    Cache)     │                   │
│  └───────┬───────┘  └───────┬───────┘  └───────────────┘                   │
│          │                  │                                               │
│          ▼                  ▼                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                         INFERENCE LAYER                                │ │
│  │                                                                        │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │ │
│  │  │  NanoLLM    │  │  YOLOv8     │  │  CLIP       │  │  Whisper    │   │ │
│  │  │  (VLM)      │  │  (Detect)   │  │  (Embed)    │  │  (Audio)    │   │ │
│  │  │             │  │             │  │             │  │             │   │ │
│  │  │  VILA-7B    │  │  TensorRT   │  │  SigLIP     │  │  Optional   │   │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                         STORAGE LAYER                                  │ │
│  │                                                                        │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                    │ │
│  │  │  PostgreSQL │  │  ChromaDB   │  │  MinIO/S3   │                    │ │
│  │  │  (Metadata) │  │  (Vectors)  │  │  (Videos)   │                    │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                    │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### API Design

```python
# Video Management
POST   /api/videos                    # Upload video file or URL
GET    /api/videos                    # List all processed videos
GET    /api/videos/{id}               # Get video metadata + frames
DELETE /api/videos/{id}               # Remove video and index

# Processing
POST   /api/videos/{id}/process       # Start processing pipeline
GET    /api/videos/{id}/status        # Get processing status
GET    /api/videos/{id}/frames        # Get extracted keyframes
GET    /api/videos/{id}/detections    # Get all detections

# Single Frame Analysis
POST   /api/analyze/frame             # Analyze single image
POST   /api/analyze/detect            # Run detection on image
POST   /api/analyze/vlm               # Run VLM query on image

# RAG Agent
POST   /api/agent/query               # Natural language query
GET    /api/agent/history             # Get conversation history
POST   /api/agent/feedback            # Rate response quality

# Search
POST   /api/search/semantic           # Semantic search across videos
POST   /api/search/temporal           # Search by time range
POST   /api/search/objects            # Search by detected objects
```

---

## Data Models

### Video Document
```json
{
  "id": "vid_abc123",
  "source": "upload",
  "original_url": null,
  "filename": "drone_footage.mp4",
  "duration_seconds": 332,
  "resolution": [1920, 1080],
  "fps": 30,
  "total_frames": 9960,
  "file_size_bytes": 245000000,
  "status": "processed",
  "created_at": "2026-01-03T12:00:00Z",
  "processing": {
    "keyframes_extracted": 47,
    "detections_run": true,
    "vlm_descriptions": true,
    "audio_transcribed": false,
    "indexed": true
  }
}
```

### Frame Document
```json
{
  "id": "frm_xyz789",
  "video_id": "vid_abc123",
  "frame_number": 1542,
  "timestamp_seconds": 51.4,
  "is_keyframe": true,
  "scene_id": 12,
  "thumbnail_url": "/api/videos/vid_abc123/frames/1542/thumbnail",
  "detections": [
    {"class": "person", "confidence": 0.92, "bbox": [100, 200, 150, 400]},
    {"class": "car", "confidence": 0.88, "bbox": [500, 300, 200, 150]}
  ],
  "vlm_description": "A person walking their dog on a suburban sidewalk...",
  "embedding_id": "emb_001"
}
```

---

## Processing Pipeline

```python
async def process_video(video_id: str, options: ProcessingOptions):
    """
    Main video processing pipeline.
    Runs as Celery task for background processing.
    """
    video = await get_video(video_id)

    # Stage 1: Extract keyframes (scene detection)
    keyframes = await extract_keyframes(
        video.path,
        method="scene_detect",  # or "fixed_interval"
        min_scene_length=1.0,   # seconds
    )
    await update_status(video_id, "keyframes_extracted", len(keyframes))

    # Stage 2: Run detection on keyframes
    if options.run_detection:
        for frame in keyframes:
            detections = await run_yolo(frame.image)
            await save_detections(frame.id, detections)
        await update_status(video_id, "detections_complete")

    # Stage 3: Generate VLM descriptions
    if options.run_vlm:
        for frame in keyframes:
            description = await run_vlm(
                frame.image,
                prompt="Describe this scene in detail."
            )
            await save_description(frame.id, description)
        await update_status(video_id, "vlm_complete")

    # Stage 4: Generate embeddings
    for frame in keyframes:
        image_embedding = await run_clip(frame.image)
        text_embedding = await run_clip(frame.vlm_description)
        await save_embeddings(frame.id, image_embedding, text_embedding)

    # Stage 5: Index in vector DB
    await index_video(video_id)
    await update_status(video_id, "indexed")
```

---

## MVP Scope

### V1 (Start Here)
- [ ] Video upload (local files)
- [ ] Keyframe extraction (scene detection)
- [ ] YOLOv8 detection on keyframes
- [ ] VLM descriptions (VILA-7B)
- [ ] Simple web UI (video browser + chat)
- [ ] Basic semantic search ("find cars")
- [ ] REST API

### V2
- [ ] URL/YouTube import
- [ ] RAG agent with tool use
- [ ] Multi-video queries
- [ ] Audio transcription (Whisper)
- [ ] Export (JSON, CSV, clips)
- [ ] Batch processing queue

### V3
- [ ] Live stream integration
- [ ] Custom model upload
- [ ] Fine-tuning interface
- [ ] Enterprise auth (SSO)
- [ ] Multi-tenant

---

## Why This First?

| Benefit | Impact |
|---------|--------|
| No WebRTC complexity | 2-3 weeks saved |
| Reusable VLM/detection code | Same models for live |
| RAG foundation | Core differentiator |
| Testable without hardware cameras | Faster iteration |
| Works on any video source | Broader use cases |
| Natural upgrade path to live | Investment protected |

---

## Comparison: Live vs Static UX

| Feature | Live (02-MVP) | Static (This) | Both |
|---------|---------------|---------------|------|
| Real-time alerts | ✓ | ○ | |
| Video upload | ○ | ✓ | |
| YouTube import | ○ | ✓ | |
| RAG agent | ○ | ✓ | |
| Detection overlays | ✓ | ✓ | ✓ |
| VLM queries | ✓ | ✓ | ✓ |
| Multi-video search | ○ | ✓ | |
| WebRTC streaming | ✓ | ○ | |
| Batch processing | ○ | ✓ | |
| Temporal search | ○ | ✓ | |
| Model playground | ○ | ✓ | |

**Recommendation:** Build Static first (V1), add Live streaming as V2/V3 feature.

---

*Static Video UX Strategy - January 2026*
