# Use Case Analysis: What Are We Actually Building?

## Current Stated Use Cases

From `mvp-docs/01-EXECUTIVE-SUMMARY.md`, the MVP claims to serve:

| User Type | Use Case | Core Need |
|-----------|----------|-----------|
| Security Analysts | Review incident footage | Find specific events |
| Operations Managers | Audit processes | Multi-video comparison |
| Compliance Officers | Evidence gathering | Export + citations |
| Developers | Test models | API + Playground |
| Content Creators | Video analysis | Metadata extraction |

**Problem:** 5 different user types with 5 different needs. That's not an MVP - that's a platform.

---

## Use Case Decomposition

Let me break down what each claimed capability actually requires:

### 1. "Ask questions about videos in plain English"

**What this requires:**
- Video processing pipeline
- Keyframe extraction
- VLM inference for descriptions
- Embedding generation
- Vector database
- RAG agent with reasoning
- Web UI with chat interface

**Verdict:** This is the core value prop, but it requires the entire stack.

### 2. "Find all moments where someone enters through the back door"

**What this requires:**
- Object detection (people)
- Spatial understanding (back door location)
- Temporal tracking
- Natural language understanding
- Cross-frame reasoning

**Verdict:** Requires VLM + detection + temporal reasoning. Complex.

### 3. "Cross-video search"

**What this requires:**
- Index spanning multiple videos
- Consistent embedding space
- Query routing
- Result aggregation

**Verdict:** Adds complexity. Could be V2.

### 4. "Model Playground"

**What this requires:**
- Interactive frame selection
- Multiple model options
- Configurable parameters
- Real-time feedback

**Verdict:** Useful for devs but separate concern from end-user product.

---

## What Jetson Owners Actually Want

Based on the Jetson community and common use cases:

| Real Use Case | Frequency | Jetson Fit |
|---------------|-----------|------------|
| Security camera monitoring | High | Excellent (real-time) |
| Industrial quality inspection | High | Excellent (low latency) |
| Robotics vision | High | Excellent (embedded) |
| Retail analytics | Medium | Good (privacy) |
| Drone/vehicle autonomy | Medium | Excellent (edge) |
| Video archive search | Low | Poor (not real-time) |

**Observation:** Most Jetson use cases are about **real-time** or **near-real-time** processing. Our MVP is about **batch processing of static video**.

---

## The Identity Crisis

Reading through the docs, I see at least 4 different products:

### Product A: Video Search Engine
"Find cars in my video library"
- Upload videos
- Index with embeddings
- Semantic search
- Browse results

### Product B: Video Q&A Chatbot
"What's happening in this scene?"
- Point at video/frame
- Ask questions
- Get natural language answers

### Product C: Object Detection Platform
"Run YOLO on my video"
- Process videos
- Detect objects
- Track over time
- Export detections

### Product D: AI Playground
"Test different models on my frames"
- Select model
- Adjust parameters
- Compare outputs

**Question:** Which ONE are we building?

---

## Use Case Priority Matrix

If I had to prioritize:

| Use Case | User Value | Technical Complexity | Jetson Fit | Priority |
|----------|------------|---------------------|------------|----------|
| Single video Q&A | High | Medium | Medium | **1** |
| Frame-level detection | High | Low | High | **2** |
| Semantic search (single video) | Medium | Medium | Medium | **3** |
| Cross-video search | Medium | High | Low | 4 |
| Model playground | Low (dev only) | Medium | High | 5 |
| Live stream support | High | High | Excellent | Future |

---

## Recommended Core Use Case

**Pick ONE of these as the MVP:**

### Option A: "Video Q&A Tool"
```
Upload video → Process → Ask questions → Get timestamped answers
```
- Single video at a time
- Focus on conversational interface
- VLM-heavy, detection as support
- No library management needed

### Option B: "Video Detection Report"
```
Upload video → Detect objects → Generate report → Export
```
- Focus on detection pipeline
- Structured output (CSV, JSON)
- No chat interface needed
- More aligned with Jetson strengths

### Option C: "Frame Search Engine"
```
Upload videos → Index frames → Search library → View results
```
- Focus on search experience
- No chat interface
- Gallery-style UX
- Simpler agent (just retrieval)

---

## Questions for Direction

1. **Who is the actual first user?** Not 5 personas - who will use this first?

2. **What's the killer query?** What question does this answer that nothing else can?

3. **Why Jetson?** If processing static video, why not just use a cloud GPU?

4. **What's the wedge?** What minimal feature gets users to adopt, then expand?

---

## References

- Use case claims: `mvp-docs/01-EXECUTIVE-SUMMARY.md:270-278`
- Feature scope: `mvp-docs/01-EXECUTIVE-SUMMARY.md:297-315`
- Architecture complexity: `mvp-docs/03-ARCHITECTURE.md:1-90`

---

*Use Case Analysis - January 2026*
