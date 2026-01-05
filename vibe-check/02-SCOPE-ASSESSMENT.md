# Scope Assessment: How's Our Aim?

## The Honest Answer

**We're trying to do too much.**

The current MVP documentation describes a full-featured product, not a minimum viable product.

---

## Scope Inventory

### From Executive Summary - "V1 Scope"

| Feature | Components Required | Dev Effort |
|---------|---------------------|------------|
| Video upload (files) | FastAPI, storage | Low |
| Scene detection + keyframes | PySceneDetect, FFmpeg | Low |
| Object detection (YOLO) | TensorRT, inference pipeline | Medium |
| VLM descriptions | NanoLLM, VILA | Medium |
| ChromaDB vector index | ChromaDB, embeddings | Low |
| Semantic search | Query pipeline, UI | Medium |
| RAG agent chat | Agent framework, tools | High |
| Web UI (React) | React, Video.js | Medium |
| REST API | FastAPI, OpenAPI | Low |

**Total: 9 major features** for "V1"

---

## Architecture Inventory

From `mvp-docs/03-ARCHITECTURE.md`:

### Layer Count: 6 Layers
1. Client Layer (Web + API clients)
2. API Gateway (Nginx)
3. Application Layer (FastAPI + 4 route groups)
4. Processing Layer (Celery + Redis)
5. Inference Layer (4 models)
6. Storage Layer (3 storage systems)

### Service Count: 12+ Services
- Nginx
- FastAPI
- Celery Worker (GPU)
- Celery Worker (CPU)
- Redis
- PostgreSQL
- ChromaDB
- NanoLLM (VLM)
- YOLOv8 (Detection)
- SigLIP (Embeddings)
- PySceneDetect
- Frontend (React)

### Database Count: 3
- PostgreSQL (metadata)
- ChromaDB (vectors)
- File system (videos/frames)

---

## Complexity Score

| Dimension | Count | Typical MVP | Status |
|-----------|-------|-------------|--------|
| User types | 5 | 1-2 | Over |
| UX flows | 5 | 1-2 | Over |
| Backend services | 6+ | 2-3 | Over |
| ML models | 4 | 1-2 | Over |
| Databases | 3 | 1 | Over |
| API endpoints | 15+ | 5-8 | Over |
| Docker containers | 4+ | 1-2 | Over |

**Verdict:** This is more like a V3 than a V1.

---

## The Scope Creep Map

```
Started With                    Grew Into
───────────────                 ─────────────────────────────────────────

"Video Q&A"     ──────────►     Video upload
                                + Scene detection
                                + Object detection
                                + VLM descriptions
                                + Embeddings
                                + Vector database
                                + Semantic search
                                + Temporal search
                                + Object tracking
                                + RAG agent
                                + Tool use framework
                                + Citation system
                                + Chat interface
                                + Video library
                                + Model playground
                                + REST API
                                + WebSocket updates
                                + Cross-video queries
```

---

## What a Real MVP Looks Like

### True Minimum Viable Product

```
Video file → Extract frames → Run VLM → Store → Query

That's it.
```

**Features:**
- Upload ONE video
- Extract 10-20 keyframes
- Run VLM description on each
- Store in simple JSON
- Text search over descriptions
- Return matching frames

**No:**
- No library management
- No object detection (VLM handles it)
- No agent reasoning
- No vector embeddings (just text search)
- No real-time updates
- No cross-video anything

### MVP+ (What We Should Target)

```
Video → Keyframes → VLM + Detection → Embeddings → Simple Search → Q&A
```

**Add:**
- Semantic search via embeddings
- Simple single-turn Q&A (no multi-step agent)
- Basic detection overlay

**Still No:**
- Multi-video
- Complex agent reasoning
- Playground
- Cross-video queries

---

## The 80/20 Analysis

What gives 80% of the value with 20% of the work?

| Feature | Value | Effort | Keep? |
|---------|-------|--------|-------|
| VLM descriptions | 40% | 20% | **Yes** |
| Semantic search | 25% | 15% | **Yes** |
| Object detection | 15% | 15% | Maybe |
| Simple Q&A | 15% | 10% | **Yes** |
| RAG agent | 5% | 25% | **No** (V2) |
| Playground | 0% | 15% | **No** |

---

## Recommended Scope Reduction

### Cut List (move to V2+)

| Feature | Why Cut |
|---------|---------|
| RAG Agent with tools | Complex, can use simple Q&A first |
| Cross-video queries | Single video is fine for MVP |
| Model Playground | Developer feature, not user feature |
| Temporal search | VLM can answer "when" questions |
| Object tracking | Overkill for static video |
| WebSocket updates | Polling works fine |
| Multiple detection models | One model is enough |

### Keep List

| Feature | Why Keep |
|---------|----------|
| Video upload | Core flow |
| Keyframe extraction | Enables everything else |
| VLM descriptions | Primary value |
| Embeddings + search | Enables queries |
| Simple Q&A | User interface |
| Basic UI | Need to interact |

---

## Alternative MVP Definitions

### MVP A: "Video Describer" (2-3 weeks)
- Upload video
- Extract keyframes (PySceneDetect)
- Run VLM on each keyframe
- Display timeline with descriptions
- Text search over descriptions

### MVP B: "Frame Finder" (3-4 weeks)
- Upload video
- Extract + embed keyframes
- Semantic search UI
- Gallery view of results
- No chat, no agent

### MVP C: "Video Chat" (4-6 weeks)
- Upload video
- Full processing pipeline
- Simple Q&A (not agent)
- Single-turn responses
- Citations to frames

---

## Honest Assessment

| Question | Answer |
|----------|--------|
| Is scope clear? | No - too many features |
| Is aim straight? | No - trying to be 4 products |
| Is it achievable? | Yes, but not as "MVP" |
| Time to build (current)? | 3-4 months |
| Time to build (cut down)? | 3-6 weeks |

---

## References

- V1 Scope: `mvp-docs/01-EXECUTIVE-SUMMARY.md:297-306`
- Architecture layers: `mvp-docs/03-ARCHITECTURE.md:9-85`
- Agent tools: `mvp-docs/03-ARCHITECTURE.md:530-577`
- Technical decisions: `mvp-docs/02-TECHNICAL-DECISIONS.md:1-541`

---

*Scope Assessment - January 2026*
