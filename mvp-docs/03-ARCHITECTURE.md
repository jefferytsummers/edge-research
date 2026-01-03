# System Architecture

## Overview

The Video Intelligence Platform follows a modular, container-based architecture optimized for NVIDIA Jetson edge deployment. The system processes uploaded videos through an AI pipeline, indexes content for semantic search, and exposes a RAG-powered agent for natural language queries.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                   CLIENT LAYER                                       │
│                                                                                      │
│  ┌──────────────────────────────┐  ┌──────────────────────────────────────────────┐ │
│  │        Web Browser           │  │              REST API Clients               │ │
│  │   React SPA + Video.js       │  │            (Python, curl, etc.)             │ │
│  └──────────────┬───────────────┘  └───────────────────────┬────────────────────┘ │
└─────────────────┼──────────────────────────────────────────┼────────────────────────┘
                  │ HTTPS                                    │ HTTPS
                  ▼                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                   EDGE DEVICE (Jetson AGX Orin)                      │
│                                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────────────┐ │
│  │                              API GATEWAY                                        │ │
│  │                           (Nginx / Traefik)                                     │ │
│  │                      TLS Termination, Rate Limiting                             │ │
│  └────────────────────────────────────────┬───────────────────────────────────────┘ │
│                                           │                                          │
│  ┌────────────────────────────────────────┼───────────────────────────────────────┐ │
│  │                          APPLICATION LAYER                                      │ │
│  │                                        │                                        │ │
│  │    ┌───────────────────────────────────┴───────────────────────────────────┐   │ │
│  │    │                        FastAPI Server                                  │   │ │
│  │    │                                                                        │   │ │
│  │    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │ │
│  │    │  │   Video     │  │   Agent     │  │   Search    │  │  Playground │  │   │ │
│  │    │  │   Routes    │  │   Routes    │  │   Routes    │  │   Routes    │  │   │ │
│  │    │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │   │ │
│  │    │                                                                        │   │ │
│  │    └────────────────────────────────────────────────────────────────────────┘   │ │
│  │                                        │                                        │ │
│  │    ┌───────────────────────────────────┴───────────────────────────────────┐   │ │
│  │    │                       Service Layer                                    │   │ │
│  │    │                                                                        │   │ │
│  │    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │ │
│  │    │  │   Video     │  │   Agent     │  │   Index     │  │  Inference  │  │   │ │
│  │    │  │   Service   │  │   Service   │  │   Service   │  │   Service   │  │   │ │
│  │    │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │   │ │
│  │    └────────────────────────────────────────────────────────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────────────┐ │
│  │                          PROCESSING LAYER                                       │ │
│  │                                                                                 │ │
│  │  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────────────┐  │ │
│  │  │   Celery Worker   │  │   Celery Worker   │  │        Redis              │  │ │
│  │  │   (GPU Tasks)     │  │   (CPU Tasks)     │  │   (Broker + Cache)        │  │ │
│  │  └───────────────────┘  └───────────────────┘  └───────────────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────────────┐ │
│  │                          INFERENCE LAYER                                        │ │
│  │                                                                                 │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │ │
│  │  │   NanoLLM   │  │   YOLOv8    │  │   SigLIP    │  │   PySceneDetect     │  │ │
│  │  │   (VLM)     │  │  (Detect)   │  │  (Embed)    │  │   (Keyframes)       │  │ │
│  │  │             │  │             │  │             │  │                     │  │ │
│  │  │  VILA-7B    │  │  TensorRT   │  │  TensorRT   │  │   CPU-based         │  │ │
│  │  │  AWQ 4-bit  │  │  INT8       │  │             │  │                     │  │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────────────┐ │
│  │                          STORAGE LAYER                                          │ │
│  │                                                                                 │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────────┐ │ │
│  │  │    PostgreSQL   │  │    ChromaDB     │  │         File Storage            │ │ │
│  │  │    (Metadata)   │  │    (Vectors)    │  │    (Videos, Frames, Models)     │ │ │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. API Gateway (Nginx/Traefik)

**Responsibilities:**
- TLS termination
- Rate limiting
- Request routing
- Static file serving (frontend)
- WebSocket proxy

**Configuration:**
```nginx
upstream api {
    server 127.0.0.1:8080;
}

server {
    listen 443 ssl http2;

    # TLS
    ssl_certificate /etc/ssl/cert.pem;
    ssl_certificate_key /etc/ssl/key.pem;

    # Static frontend
    location / {
        root /var/www/frontend;
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

### 2. FastAPI Server

**Responsibilities:**
- REST API endpoints
- WebSocket connections
- Request validation
- Authentication (future)
- Task orchestration

**Project Structure:**
```
src/
├── main.py                 # FastAPI app initialization
├── api/
│   ├── __init__.py
│   ├── videos.py           # Video CRUD endpoints
│   ├── agent.py            # Agent chat endpoints
│   ├── search.py           # Search endpoints
│   ├── playground.py       # Model playground endpoints
│   └── websocket.py        # Real-time updates
├── services/
│   ├── __init__.py
│   ├── video_service.py    # Video business logic
│   ├── agent_service.py    # Agent orchestration
│   ├── index_service.py    # Vector indexing
│   └── inference_service.py # Model inference
├── models/
│   ├── __init__.py
│   ├── video.py            # Video data models
│   ├── frame.py            # Frame data models
│   └── query.py            # Query/response models
├── tasks/
│   ├── __init__.py
│   ├── processing.py       # Video processing tasks
│   └── indexing.py         # Indexing tasks
├── core/
│   ├── __init__.py
│   ├── config.py           # Configuration
│   ├── database.py         # Database connections
│   └── dependencies.py     # FastAPI dependencies
└── utils/
    ├── __init__.py
    ├── video.py            # Video utilities
    └── embeddings.py       # Embedding utilities
```

**Key Endpoints:**
```python
# Video Management
POST   /api/videos              # Upload video
GET    /api/videos              # List videos
GET    /api/videos/{id}         # Get video details
DELETE /api/videos/{id}         # Delete video
GET    /api/videos/{id}/frames  # Get keyframes
GET    /api/videos/{id}/status  # Get processing status

# Agent
POST   /api/agent/query         # Send query to agent
GET    /api/agent/history       # Get conversation history
WS     /ws/agent                # Real-time agent chat

# Search
POST   /api/search/semantic     # Semantic search
POST   /api/search/objects      # Object-based search
POST   /api/search/temporal     # Time-based search

# Playground
POST   /api/playground/detect   # Run detection
POST   /api/playground/vlm      # Run VLM query
POST   /api/playground/embed    # Generate embeddings
```

---

### 3. Celery Workers

**Responsibilities:**
- Background video processing
- GPU task scheduling
- Retry handling
- Progress reporting

**Task Flow:**
```
┌─────────────────────────────────────────────────────────────────────┐
│                     VIDEO PROCESSING PIPELINE                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  upload_video                                                        │
│       │                                                              │
│       ▼                                                              │
│  ┌─────────────────┐                                                │
│  │ validate_video  │  CPU task: check format, duration, size        │
│  └────────┬────────┘                                                │
│           │                                                          │
│           ▼                                                          │
│  ┌─────────────────┐                                                │
│  │ extract_keyframes│  CPU task: scene detection, frame extraction  │
│  └────────┬────────┘                                                │
│           │                                                          │
│           ├──────────────────────────────────────┐                  │
│           │                                      │                  │
│           ▼                                      ▼                  │
│  ┌─────────────────┐                    ┌─────────────────┐        │
│  │ run_detection   │  GPU task         │ run_vlm         │  GPU   │
│  │ (batch frames)  │                    │ (per keyframe)  │        │
│  └────────┬────────┘                    └────────┬────────┘        │
│           │                                      │                  │
│           └──────────────────┬───────────────────┘                  │
│                              │                                      │
│                              ▼                                      │
│                     ┌─────────────────┐                             │
│                     │ generate_embeddings│  GPU task                │
│                     └────────┬────────┘                             │
│                              │                                      │
│                              ▼                                      │
│                     ┌─────────────────┐                             │
│                     │ index_video     │  CPU task: ChromaDB insert  │
│                     └────────┬────────┘                             │
│                              │                                      │
│                              ▼                                      │
│                          complete                                    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Worker Configuration:**
```python
# celery_config.py
from celery import Celery

app = Celery(
    "video_intelligence",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "tasks.processing.run_detection": {"queue": "gpu"},
        "tasks.processing.run_vlm": {"queue": "gpu"},
        "tasks.processing.generate_embeddings": {"queue": "gpu"},
        "tasks.processing.*": {"queue": "cpu"},
    },
    worker_prefetch_multiplier=1,  # One task at a time for GPU
)
```

---

### 4. Inference Layer

**Model Loading Strategy:**
```python
class InferenceService:
    """Singleton service for model management."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # Load models once at startup
        self.vlm = NanoLLM.from_pretrained(
            "Efficient-Large-Model/VILA1.5-7b",
            quantization="awq"
        )

        self.detector = YOLO("yolov8s.engine")  # TensorRT engine

        # SigLIP shared with VLM vision encoder
        self.embedder = self.vlm.vision_encoder

    def detect(self, frame: np.ndarray) -> List[Detection]:
        results = self.detector(frame)
        return self._parse_detections(results)

    def describe(self, frame: np.ndarray, prompt: str) -> str:
        return self.vlm.generate(frame, prompt, max_tokens=256)

    def embed_image(self, frame: np.ndarray) -> np.ndarray:
        return self.embedder.encode_image(frame)

    def embed_text(self, text: str) -> np.ndarray:
        return self.embedder.encode_text(text)
```

**Memory Layout (AGX Orin 64GB):**
```
┌─────────────────────────────────────────────────────────────────────┐
│                     GPU MEMORY (64GB Unified)                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  VILA-7B AWQ (4-bit)                              ~8 GB     │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  YOLOv8-s TensorRT Engine                        ~0.5 GB    │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  SigLIP Vision Encoder (shared with VLM)         (included) │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Working Memory (inference buffers)              ~2 GB      │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  System + OS                                      ~2 GB     │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Available for additional models / scaling       ~51 GB    │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 5. Storage Layer

**PostgreSQL (Metadata):**
```sql
-- Videos table
CREATE TABLE videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    source_url TEXT,
    duration_seconds FLOAT NOT NULL,
    resolution_width INT NOT NULL,
    resolution_height INT NOT NULL,
    fps FLOAT NOT NULL,
    total_frames INT NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Frames table
CREATE TABLE frames (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
    frame_number INT NOT NULL,
    timestamp_seconds FLOAT NOT NULL,
    is_keyframe BOOLEAN DEFAULT FALSE,
    scene_id INT,
    thumbnail_path TEXT,
    vlm_description TEXT,
    embedding_id VARCHAR(255),  -- Reference to ChromaDB
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Detections table
CREATE TABLE detections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    frame_id UUID REFERENCES frames(id) ON DELETE CASCADE,
    class_name VARCHAR(100) NOT NULL,
    confidence FLOAT NOT NULL,
    bbox_x INT NOT NULL,
    bbox_y INT NOT NULL,
    bbox_width INT NOT NULL,
    bbox_height INT NOT NULL,
    tracking_id INT
);

-- Indexes
CREATE INDEX idx_frames_video_id ON frames(video_id);
CREATE INDEX idx_frames_timestamp ON frames(video_id, timestamp_seconds);
CREATE INDEX idx_detections_frame_id ON detections(frame_id);
CREATE INDEX idx_detections_class ON detections(class_name);
```

**ChromaDB (Vectors):**
```python
# Collection schema
collection = client.create_collection(
    name="video_frames",
    metadata={"hnsw:space": "cosine"}
)

# Document structure
{
    "id": "frame_uuid",
    "embedding": [0.1, 0.2, ...],  # 768-dim SigLIP
    "metadata": {
        "video_id": "video_uuid",
        "frame_number": 1542,
        "timestamp_seconds": 51.4,
        "scene_id": 12
    },
    "document": "VLM description text"  # For text search
}
```

**File Storage:**
```
/data/
├── videos/
│   ├── {video_id}/
│   │   ├── original.mp4           # Original upload
│   │   ├── metadata.json          # Video metadata
│   │   └── frames/
│   │       ├── 0001.jpg           # Keyframe thumbnails
│   │       ├── 0002.jpg
│   │       └── ...
├── models/
│   ├── vila-7b-awq/               # VLM weights
│   ├── yolov8s.engine             # TensorRT engine
│   └── siglip/                    # Embedding model
└── chroma/
    └── video_frames/              # ChromaDB persistence
```

---

### 6. RAG Agent Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         RAG AGENT                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  User Query: "Find all red vehicles across my videos"               │
│                         │                                            │
│                         ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    QUERY UNDERSTANDING                          ││
│  │                                                                  ││
│  │  LLM analyzes query to extract:                                 ││
│  │  • Intent: search                                                ││
│  │  • Object: vehicle                                               ││
│  │  • Attribute: red (color)                                        ││
│  │  • Scope: all videos                                             ││
│  └─────────────────────────────────────────────────────────────────┘│
│                         │                                            │
│                         ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    PLAN GENERATION                              ││
│  │                                                                  ││
│  │  1. semantic_search("red vehicle")                              ││
│  │  2. For each result: vlm_verify("Is there a red vehicle?")      ││
│  │  3. Aggregate and rank results                                   ││
│  └─────────────────────────────────────────────────────────────────┘│
│                         │                                            │
│                         ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    TOOL EXECUTION                               ││
│  │                                                                  ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ ││
│  │  │ semantic_search │  │  vlm_query      │  │  get_frame      │ ││
│  │  │                 │  │                 │  │                 │ ││
│  │  │ Query ChromaDB  │  │ Ask VILA about  │  │ Retrieve frame  │ ││
│  │  │ with embedding  │  │ specific frame  │  │ from storage    │ ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘ ││
│  │                                                                  ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ ││
│  │  │ run_detection   │  │  temporal_filter│  │  aggregate      │ ││
│  │  │                 │  │                 │  │                 │ ││
│  │  │ Run YOLO on     │  │ Filter by time  │  │ Combine results │ ││
│  │  │ specific frame  │  │ range           │  │ from tools      │ ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘ ││
│  └─────────────────────────────────────────────────────────────────┘│
│                         │                                            │
│                         ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    RESPONSE GENERATION                          ││
│  │                                                                  ││
│  │  LLM synthesizes results with:                                  ││
│  │  • Natural language summary                                      ││
│  │  • Cited timestamps and video references                         ││
│  │  • Clickable links to frames                                     ││
│  │  • Follow-up suggestions                                         ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Tool Definitions:**
```python
TOOLS = [
    {
        "name": "semantic_search",
        "description": "Search for frames semantically similar to a text query",
        "parameters": {
            "query": "Text description to search for",
            "video_ids": "Optional list of video IDs to search within",
            "limit": "Maximum number of results (default 10)"
        }
    },
    {
        "name": "vlm_query",
        "description": "Ask the VLM a question about a specific frame",
        "parameters": {
            "frame_id": "ID of the frame to analyze",
            "question": "Question to ask about the frame"
        }
    },
    {
        "name": "run_detection",
        "description": "Run object detection on a specific frame",
        "parameters": {
            "frame_id": "ID of the frame to analyze"
        }
    },
    {
        "name": "temporal_filter",
        "description": "Filter results by time range",
        "parameters": {
            "video_id": "Video to filter",
            "start_time": "Start timestamp in seconds",
            "end_time": "End timestamp in seconds"
        }
    },
    {
        "name": "get_frame",
        "description": "Retrieve frame image and metadata",
        "parameters": {
            "frame_id": "ID of the frame to retrieve"
        }
    },
    {
        "name": "list_videos",
        "description": "List all available videos with metadata",
        "parameters": {}
    }
]
```

---

## Data Flow Diagrams

### Video Upload Flow
```
┌────────┐     ┌──────────┐     ┌────────────┐     ┌────────────┐
│ Client │────▶│  FastAPI │────▶│   Redis    │────▶│   Celery   │
│        │     │          │     │  (Queue)   │     │  (Worker)  │
└────────┘     └──────────┘     └────────────┘     └─────┬──────┘
                                                         │
                    ┌────────────────────────────────────┘
                    │
                    ▼
    ┌───────────────────────────────────────────────────────────┐
    │                   Processing Pipeline                      │
    │                                                            │
    │  1. Save video to /data/videos/{id}/original.mp4          │
    │  2. Extract metadata (duration, fps, resolution)           │
    │  3. Run scene detection, extract keyframes                 │
    │  4. For each keyframe:                                     │
    │     a. Run YOLOv8 detection                                │
    │     b. Run VILA VLM description                            │
    │     c. Generate SigLIP embedding                           │
    │  5. Insert embeddings into ChromaDB                        │
    │  6. Update PostgreSQL metadata                             │
    │  7. Mark video as "indexed"                                │
    │                                                            │
    └───────────────────────────────────────────────────────────┘
                    │
                    ▼
              ┌──────────┐
              │  WebSocket │─────▶ Client (progress updates)
              └──────────┘
```

### Agent Query Flow
```
┌────────┐     ┌──────────┐     ┌────────────┐     ┌────────────┐
│ Client │────▶│  FastAPI │────▶│   Agent    │────▶│   Tools    │
│        │     │          │     │  Service   │     │            │
└────────┘     └──────────┘     └─────┬──────┘     └─────┬──────┘
                                      │                   │
                                      │    ┌──────────────┘
                                      │    │
                                      ▼    ▼
                               ┌──────────────────┐
                               │   Tool Router    │
                               └────────┬─────────┘
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           │                            │                            │
           ▼                            ▼                            ▼
    ┌──────────────┐           ┌──────────────┐           ┌──────────────┐
    │  ChromaDB    │           │   NanoLLM    │           │   YOLOv8     │
    │  (Search)    │           │   (VLM)      │           │  (Detect)    │
    └──────────────┘           └──────────────┘           └──────────────┘
           │                            │                            │
           └────────────────────────────┼────────────────────────────┘
                                        │
                                        ▼
                               ┌──────────────────┐
                               │ Response with    │
                               │ citations        │
                               └────────┬─────────┘
                                        │
                                        ▼
                                    Client
```

---

## Security Considerations

### Network Security
- TLS termination at gateway
- API rate limiting
- CORS configuration for frontend
- No external network dependencies for inference

### Data Security
- Videos stored on local encrypted volume
- No cloud uploads (privacy-first)
- Temporary files cleaned after processing

### Future Enhancements
- JWT authentication
- Role-based access control
- Audit logging
- API key management

---

## Scalability

### Horizontal Scaling (Future)
```
                    ┌─────────────────┐
                    │  Load Balancer  │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
  ┌───────────┐       ┌───────────┐       ┌───────────┐
  │ Jetson #1 │       │ Jetson #2 │       │ Jetson #3 │
  │ (API +    │       │ (API +    │       │ (Workers  │
  │  Workers) │       │  Workers) │       │  Only)    │
  └───────────┘       └───────────┘       └───────────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                    ┌────────┴────────┐
                    │  Shared Redis   │
                    │  Shared Postgres│
                    │  Shared ChromaDB│
                    └─────────────────┘
```

### Vertical Scaling
- Upgrade to Jetson Thor (128GB, 2070 TOPS)
- Run larger VLMs (13B+)
- Process more concurrent videos

---

*Architecture Document - January 2026*
