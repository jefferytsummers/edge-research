# Technical Decisions Record

This document captures key technical decisions for the Video Intelligence Platform MVP, including rationale, alternatives considered, and implications.

---

## TDR-001: Hardware Platform

### Decision
**NVIDIA Jetson AGX Orin 64GB** as the primary deployment target.

### Context
Need edge hardware capable of running VLMs (3-7B parameters) with acceptable latency while processing video.

### Alternatives Considered

| Platform | AI Performance | VLM Support | Price | Verdict |
|----------|---------------|-------------|-------|---------|
| **Jetson AGX Orin 64GB** | 275 TOPS | Excellent (3-20B) | $1,999 | **Selected** |
| Jetson Orin Nano Super | 67 TOPS | Limited (3B max) | $249 | Too constrained |
| Qualcomm RB5 | 26 TOPS | Poor | ~$500 | Immature ecosystem |
| Google Coral | 4 TOPS | None | $150 | No LLM support |
| Cloud (AWS/GCP) | Unlimited | Excellent | Variable | Latency, privacy, cost |

### Rationale
- **Only viable edge platform** for VLMs at required latency
- 64GB unified memory handles 7B+ models comfortably
- Mature software ecosystem (NanoLLM, DeepStream, TensorRT)
- Hardware encode/decode for video processing
- Production-ready with JetPack 6.x support

### Implications
- ARM64 architecture requires specific builds
- Container-based deployment recommended
- Power consumption 15-60W depending on load
- Development can occur on x86 with ARM emulation, but testing requires real hardware

### Future Considerations
- Jetson Thor (2,070 TOPS, 128GB) available for scaling up
- Same software stack portable across Jetson generations

---

## TDR-002: Vision Language Model

### Decision
**VILA-7B with AWQ 4-bit quantization** as primary VLM, with VILA-3B fallback.

### Context
Need a VLM that runs on Jetson with <200ms latency for scene descriptions and can answer natural language questions about images.

### Alternatives Considered

| Model | Parameters | Memory | Latency (Orin) | Quality | Verdict |
|-------|------------|--------|----------------|---------|---------|
| **VILA-7B AWQ** | 7B | ~8GB | 120-150ms | High | **Selected** |
| VILA-3B | 3B | ~4GB | 50-80ms | Medium | Fallback |
| LLaVA-13B | 13B | ~16GB | 200-300ms | Higher | Too slow |
| Qwen2.5-VL-7B | 7B | ~8GB | 100-140ms | High | Alternative |
| GPT-4V (cloud) | Unknown | N/A | 1-3s | Highest | Latency/privacy |

### Rationale
- **NVIDIA-optimized** for Jetson via NanoLLM
- AWQ 4-bit quantization reduces memory without quality loss
- Vision encoder runs in TensorRT for acceleration
- Streaming output for responsive UX
- Well-documented deployment path

### Configuration
```python
# Model loading
model = NanoLLM.from_pretrained(
    "Efficient-Large-Model/VILA1.5-7b",
    quantization="awq",
    vision_encoder="TensorRT"
)

# Inference settings
response = model.generate(
    image,
    prompt,
    max_tokens=256,      # Limit for speed
    temperature=0.7,
    streaming=True
)
```

### Implications
- First model load takes 30-60s (TensorRT compilation)
- Subsequent loads use cached engines
- Memory overhead ~8GB, leaving headroom for detection models
- Multilingual support limited compared to Qwen

---

## TDR-003: Object Detection Model

### Decision
**YOLOv8-s with TensorRT INT8 quantization** for real-time detection.

### Context
Need fast, accurate object detection on video frames with minimal latency overhead.

### Alternatives Considered

| Model | Latency (Orin) | mAP | Memory | Verdict |
|-------|----------------|-----|--------|---------|
| **YOLOv8-s INT8** | 5-8ms | 44.9 | ~200MB | **Selected** |
| YOLOv8-m INT8 | 12-18ms | 50.2 | ~400MB | Alternative for accuracy |
| YOLOv8-l | 25-40ms | 52.9 | ~800MB | Too slow |
| Grounding DINO | 80-120ms | N/A | ~2GB | For open-vocab queries |
| NanoOWL | 30-50ms | N/A | ~500MB | For zero-shot |

### Rationale
- **8ms inference** leaves room for VLM in latency budget
- INT8 quantization with TensorRT is well-supported
- COCO-trained covers common objects (people, vehicles, etc.)
- Ultralytics provides easy export to TensorRT

### Configuration
```bash
# Export to TensorRT
yolo export model=yolov8s.pt format=engine device=0 int8=True

# Or via trtexec
trtexec --onnx=yolov8s.onnx \
        --saveEngine=yolov8s.engine \
        --int8 \
        --workspace=4096
```

### Implications
- INT8 requires calibration dataset (COCO subset works)
- 80 COCO classes cover most use cases
- Custom classes require fine-tuning + re-export
- Can run multiple models simultaneously (detection + VLM)

---

## TDR-004: Vector Database

### Decision
**ChromaDB** for embedding storage and similarity search.

### Context
Need vector storage for frame embeddings (CLIP) and text embeddings (VLM descriptions) to enable semantic search.

### Alternatives Considered

| Database | Type | Scalability | Complexity | Verdict |
|----------|------|-------------|------------|---------|
| **ChromaDB** | Embedded | 1M vectors | Low | **Selected** |
| FAISS | Library | 100M+ vectors | Medium | Alternative |
| Milvus | Server | Billions | High | Overkill for MVP |
| Pinecone | Cloud | Unlimited | Low | Privacy concern |
| pgvector | PostgreSQL | 10M vectors | Medium | Alternative |

### Rationale
- **Zero infrastructure** - embedded, single file
- Python-native API, simple integration
- Sufficient for MVP scale (tens of thousands of frames)
- Metadata filtering (video_id, timestamp, etc.)
- Easy migration to FAISS or Milvus later if needed

### Configuration
```python
import chromadb
from chromadb.config import Settings

# Initialize
client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="/data/chroma",
    anonymized_telemetry=False
))

# Create collection
collection = client.create_collection(
    name="video_frames",
    metadata={"hnsw:space": "cosine"}
)

# Add embeddings
collection.add(
    ids=["frame_001", "frame_002"],
    embeddings=[embedding1, embedding2],
    metadatas=[
        {"video_id": "vid_abc", "timestamp": 30.5},
        {"video_id": "vid_abc", "timestamp": 35.2}
    ],
    documents=["Person walking near entrance", "Car parking"]
)

# Query
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=10,
    where={"video_id": "vid_abc"}  # Optional filter
)
```

### Implications
- Single-node only (no distributed deployment)
- Persists to disk, survives restarts
- Memory usage scales with collection size
- Rebuild index if upgrading ChromaDB versions

---

## TDR-005: Embedding Model

### Decision
**SigLIP (ViT-B/16)** for image embeddings, same model for text via CLIP compatibility.

### Context
Need embeddings for semantic similarity search across frames and text descriptions.

### Alternatives Considered

| Model | Dimensions | Latency | Quality | Verdict |
|-------|------------|---------|---------|---------|
| **SigLIP ViT-B/16** | 768 | 15-25ms | High | **Selected** |
| CLIP ViT-B/32 | 512 | 10-15ms | Good | Faster, lower quality |
| CLIP ViT-L/14 | 768 | 40-60ms | Higher | Too slow |
| OpenCLIP | 1024 | 30-50ms | Higher | Memory heavy |

### Rationale
- **TensorRT optimized** in NanoLLM stack
- Shared with VILA's vision encoder (efficiency)
- Good balance of speed and quality
- Text-image alignment for cross-modal search

### Configuration
```python
from nano_llm import NanoLLM

# SigLIP is built into NanoLLM's vision encoder
model = NanoLLM.from_pretrained("Efficient-Large-Model/VILA1.5-7b")

# Get image embedding
image_embedding = model.embed_image(frame)  # Shape: (768,)

# Get text embedding
text_embedding = model.embed_text("person walking")  # Shape: (768,)
```

### Implications
- 768-dimensional vectors (moderate storage)
- Cosine similarity for matching
- Same embedding space for images and text
- Pre-computed during video processing, not at query time

---

## TDR-006: Web Framework (Backend)

### Decision
**FastAPI** for REST API, **Celery** for background processing.

### Context
Need async-capable API server with background task processing for video analysis.

### Alternatives Considered

| Framework | Async | Performance | Ecosystem | Verdict |
|-----------|-------|-------------|-----------|---------|
| **FastAPI** | Native | Excellent | Rich | **Selected** |
| Flask | Via extension | Good | Mature | Less modern |
| Django | Via channels | Good | Full-featured | Overkill |
| Litestar | Native | Excellent | Growing | Less mature |

### Rationale
- **Native async/await** for concurrent requests
- Automatic OpenAPI documentation
- Pydantic validation built-in
- Excellent performance with uvicorn
- Simple integration with Celery for background tasks

### Configuration
```python
# main.py
from fastapi import FastAPI, BackgroundTasks
from celery import Celery

app = FastAPI(title="Video Intelligence API")
celery = Celery("tasks", broker="redis://localhost:6379/0")

@app.post("/api/videos")
async def upload_video(file: UploadFile):
    video_id = save_video(file)
    # Queue background processing
    process_video.delay(video_id)
    return {"video_id": video_id, "status": "processing"}

@celery.task
def process_video(video_id: str):
    # Long-running video analysis
    extract_keyframes(video_id)
    run_detection(video_id)
    run_vlm(video_id)
    build_index(video_id)
```

### Implications
- Redis required for Celery broker
- Worker processes separate from API server
- WebSocket support for real-time updates
- Scales horizontally with more workers

---

## TDR-007: Web Framework (Frontend)

### Decision
**React 18 with Vite** and **Tailwind CSS**.

### Context
Need responsive web UI for video browsing, chat interface, and model playground.

### Alternatives Considered

| Framework | Learning Curve | Performance | Ecosystem | Verdict |
|-----------|---------------|-------------|-----------|---------|
| **React + Vite** | Medium | Excellent | Huge | **Selected** |
| Vue 3 + Vite | Low | Excellent | Large | Alternative |
| SvelteKit | Low | Excellent | Growing | Less mature |
| Next.js | Medium | Excellent | Huge | SSR overkill |

### Rationale
- **Largest ecosystem** for components and libraries
- Vite for fast development builds
- Tailwind for rapid UI development
- react-query for server state management
- Existing team familiarity (assumed)

### Key Libraries
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-router-dom": "^6.0.0",
    "@tanstack/react-query": "^5.0.0",
    "tailwindcss": "^3.4.0",
    "video.js": "^8.0.0",
    "lucide-react": "^0.300.0"
  }
}
```

### Implications
- SPA architecture (API-first)
- Video.js for playback with overlay support
- WebSocket for real-time updates
- Bundle size ~200KB gzipped

---

## TDR-008: Agent Framework

### Decision
**Custom tool-use agent** built on NanoLLM with structured function calling.

### Context
Need RAG agent that can reason over video content, use tools (search, VLM, detection), and provide cited responses.

### Alternatives Considered

| Framework | Flexibility | Overhead | Edge Support | Verdict |
|-----------|-------------|----------|--------------|---------|
| **Custom (NanoLLM)** | High | Low | Native | **Selected** |
| LangChain | High | High | Partial | Too heavy |
| LlamaIndex | High | Medium | Partial | Alternative |
| Semantic Kernel | Medium | Medium | Partial | .NET focused |

### Rationale
- **Minimal dependencies** - just NanoLLM + tools
- Full control over prompts and tool definitions
- Optimized for edge (no cloud calls required)
- Simpler debugging and customization

### Architecture
```python
class VideoAgent:
    def __init__(self, vlm, vector_db, detector):
        self.vlm = vlm
        self.vector_db = vector_db
        self.detector = detector
        self.tools = {
            "semantic_search": self.semantic_search,
            "run_detection": self.run_detection,
            "vlm_query": self.vlm_query,
            "get_frame": self.get_frame,
        }

    def query(self, user_input: str, context: List[str]) -> str:
        # 1. Understand intent
        plan = self.plan_response(user_input)

        # 2. Execute tools
        results = []
        for tool_call in plan.tool_calls:
            result = self.tools[tool_call.name](**tool_call.args)
            results.append(result)

        # 3. Generate response with citations
        response = self.generate_response(user_input, results)
        return response
```

### Implications
- Custom prompts for tool selection
- Structured output parsing
- Citation tracking for all claims
- Can swap LLM backend (local VLM vs cloud API)

---

## TDR-009: Video Processing Library

### Decision
**OpenCV + FFmpeg** for video I/O, **PySceneDetect** for keyframe extraction.

### Context
Need to decode videos, extract frames, and detect scene changes efficiently.

### Alternatives Considered

| Library | Speed | Features | Jetson Support | Verdict |
|---------|-------|----------|----------------|---------|
| **OpenCV + FFmpeg** | Good | Complete | Excellent | **Selected** |
| DeepStream | Excellent | GPU-accelerated | Excellent | Too complex for static |
| Decord | Excellent | Minimal | Good | Less features |
| moviepy | Slow | High-level | Good | Too slow |

### Rationale
- **FFmpeg handles all codecs** (H.264, H.265, VP9, etc.)
- OpenCV provides frame-level access
- PySceneDetect for intelligent keyframe selection
- Well-documented, widely used
- Can upgrade to DeepStream for live streaming later

### Configuration
```python
import cv2
from scenedetect import detect, ContentDetector

# Scene detection
scenes = detect("video.mp4", ContentDetector(threshold=30.0))

# Extract keyframes
cap = cv2.VideoCapture("video.mp4")
for scene in scenes:
    cap.set(cv2.CAP_PROP_POS_FRAMES, scene.start_frame)
    ret, frame = cap.read()
    if ret:
        process_frame(frame)
```

### Implications
- CPU-based decode (GPU via NVDEC available but complex)
- Scene detection adds processing time (~0.5x realtime)
- Memory usage scales with frame buffer
- Format support depends on FFmpeg build

---

## TDR-010: Containerization Strategy

### Decision
**Docker with NVIDIA Container Runtime**, single multi-stage Dockerfile.

### Context
Need reproducible deployment across development and production Jetson devices.

### Alternatives Considered

| Strategy | Complexity | Reproducibility | Size | Verdict |
|----------|------------|-----------------|------|---------|
| **Single container** | Low | High | Large (~15GB) | **Selected** |
| Multi-container | Medium | High | Smaller each | Future option |
| Native install | Low | Low | N/A | Not portable |
| Kubernetes | High | High | N/A | Overkill |

### Rationale
- **Single container** simplifies deployment
- NVIDIA base images include CUDA, TensorRT
- jetson-containers provides validated builds
- Multi-container can be added later for scaling

### Dockerfile Structure
```dockerfile
# Base: NanoLLM with VLM support
FROM dustynv/nano_llm:r36.4.0

# System dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY src/ /app/src/
WORKDIR /app

# Ports
EXPOSE 8080

# Entrypoint
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Implications
- Large image size (~15GB with models)
- First pull is slow, subsequent are cached
- NVIDIA runtime required (`--runtime nvidia`)
- Volume mounts for data persistence

---

## Decision Summary

| ID | Decision | Status |
|----|----------|--------|
| TDR-001 | Jetson AGX Orin 64GB | ✅ Approved |
| TDR-002 | VILA-7B AWQ | ✅ Approved |
| TDR-003 | YOLOv8-s INT8 | ✅ Approved |
| TDR-004 | ChromaDB | ✅ Approved |
| TDR-005 | SigLIP ViT-B/16 | ✅ Approved |
| TDR-006 | FastAPI + Celery | ✅ Approved |
| TDR-007 | React + Vite + Tailwind | ✅ Approved |
| TDR-008 | Custom tool-use agent | ✅ Approved |
| TDR-009 | OpenCV + FFmpeg + PySceneDetect | ✅ Approved |
| TDR-010 | Single Docker container | ✅ Approved |

---

*Technical Decisions Record - January 2026*
