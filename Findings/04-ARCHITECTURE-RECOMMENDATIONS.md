# Architecture Recommendations for MVP

## System Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                     │
│  ┌─────────────┐  ┌─────────────────┐  ┌──────────────────────────────────┐  │
│  │ Web Browser │  │ Mobile App      │  │ Enterprise Integration          │  │
│  │ (WebRTC)    │  │ (WebRTC/HLS)    │  │ (REST/gRPC/MQTT)                │  │
│  └──────┬──────┘  └────────┬────────┘  └────────────────┬─────────────────┘  │
└─────────┼──────────────────┼────────────────────────────┼────────────────────┘
          │                  │                            │
          ▼                  ▼                            ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                           EDGE GATEWAY (Optional)                             │
│                    Load Balancing / TLS Termination                          │
└────────────────────────────────────┬─────────────────────────────────────────┘
                                     │
                                     ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                          JETSON DEVICE                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                        API LAYER                                         │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────────┐   │ │
│  │  │ WebRTC Server│  │ REST API     │  │ WebSocket (Events)           │   │ │
│  │  │ (Video Out)  │  │ (Control)    │  │ (Real-time Metadata)         │   │ │
│  │  └──────────────┘  └──────────────┘  └──────────────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                     PROCESSING LAYER                                     │ │
│  │  ┌─────────────────────────────┐  ┌─────────────────────────────────┐   │ │
│  │  │     DeepStream Pipeline     │  │        NanoLLM / VLM            │   │ │
│  │  │  • Video Decode (NVDEC)     │  │  • Vision Encoding (TensorRT)   │   │ │
│  │  │  • Object Detection         │  │  • Language Model (AWQ 4-bit)   │   │ │
│  │  │  • Tracking (NvDCF)         │  │  • Response Generation          │   │ │
│  │  │  • Annotation Overlay       │  │                                 │   │ │
│  │  │  • Video Encode (NVENC)     │  │                                 │   │ │
│  │  └─────────────────────────────┘  └─────────────────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                      MODEL LAYER                                         │ │
│  │  ┌─────────────────────────────┐  ┌─────────────────────────────────┐   │ │
│  │  │   Triton Inference Server   │  │     Model Repository            │   │ │
│  │  │  • TensorRT Backend         │  │  • YOLOv8 (Detection)           │   │ │
│  │  │  • Python Backend (VLM)     │  │  • VILA-7B (VLM)                 │   │ │
│  │  │  • Dynamic Batching         │  │  • CLIP (Vision Encoder)        │   │ │
│  │  └─────────────────────────────┘  └─────────────────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
          ▲
          │ RTSP / CSI / USB
┌─────────┴────────────────────────────────────────────────────────────────────┐
│                            VIDEO SOURCES                                      │
│  ┌─────────────┐  ┌─────────────────┐  ┌──────────────────────────────────┐  │
│  │ IP Cameras  │  │ CSI Cameras     │  │ USB Cameras / Video Files        │  │
│  │ (RTSP/ONVIF)│  │ (IMX477, etc.)  │  │                                  │  │
│  └─────────────┘  └─────────────────┘  └──────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Recommended Implementation Approaches

### Approach A: Jetson Platform Services (Fastest to MVP)

**Pros**:
- Pre-built microservices with REST APIs
- VLM service already integrated
- Production-ready patterns
- Minimal custom code

**Cons**:
- Less flexibility for custom workflows
- Tied to NVIDIA's service architecture

**Steps**:
1. Install Jetson Platform Services (part of JetPack 6.x+)
2. Configure VLM AI Service with desired model
3. Add video streams via REST API
4. Connect WebRTC output to web UI
5. Subscribe to metadata/alerts via API

---

### Approach B: Custom DeepStream + NanoLLM Pipeline (Maximum Control)

**Pros**:
- Full control over processing pipeline
- Can optimize for specific latency targets
- Easier to add custom preprocessing/postprocessing

**Cons**:
- More development effort
- Need to build API layer

**Steps**:
1. Build DeepStream pipeline for video ingestion
2. Integrate NanoLLM for VLM inference
3. Create custom GStreamer elements or probes for frame extraction
4. Build REST/WebSocket API layer
5. Add WebRTC output via jetson-inference

---

### Approach C: Holoscan SDK (Lowest Latency, Complex Pipelines)

**Pros**:
- Designed for ultra-low-latency applications
- Operator-based architecture is highly modular
- Same code runs from Jetson to data center

**Cons**:
- Steeper learning curve
- More suited for sensor fusion/medical imaging

**Best For**: When <50ms latency is critical

---

## Data Flow Patterns

### Pattern 1: Annotated Video Stream
```
Camera → Decode → Detection → Tracking → Overlay → Encode → WebRTC → Browser
                      ↓
                 Metadata → WebSocket → Client
```

### Pattern 2: VLM Query Loop
```
Camera → Frame Sampler (1-5 FPS) → VLM Query → Response
                ↓                                  ↓
           Continuous Stream              Alert/Metadata Output
```

### Pattern 3: Hybrid Detection + VLM
```
Camera → Decode → Detection → [IF object detected] → VLM Query
                      ↓                                   ↓
              Annotated Video                     Semantic Alert
```

---

## API Design Recommendations

### Stream Management
```http
POST   /api/streams                 # Add new video stream
GET    /api/streams                 # List active streams
DELETE /api/streams/{id}            # Remove stream
GET    /api/streams/{id}/snapshot   # Get current frame
```

### VLM Interaction
```http
POST   /api/vlm/query               # One-shot query with image
POST   /api/streams/{id}/query      # Query specific stream
PUT    /api/streams/{id}/alert      # Set continuous alert prompt
GET    /api/streams/{id}/alerts     # Get triggered alerts
```

### Real-time Output
```
WebRTC: ws://device:8554/stream/{id}     # Annotated video
WebSocket: ws://device:8080/metadata     # Real-time events JSON
```

### Metadata Event Format
```json
{
  "timestamp": "2026-01-03T12:00:00.123Z",
  "stream_id": "camera-1",
  "frame_number": 12345,
  "detections": [
    {
      "class": "person",
      "confidence": 0.95,
      "bbox": [100, 150, 200, 400],
      "tracking_id": 42
    }
  ],
  "vlm_response": {
    "query": "Describe the scene",
    "response": "A person is walking toward the entrance"
  }
}
```

---

## Resource Allocation Strategy (AGX Orin 64GB)

| Component | GPU Resources | Memory |
|-----------|---------------|--------|
| Video Decode (4 streams 1080p) | NVDEC (dedicated) | ~200MB |
| Detection (YOLOv8-s INT8) | ~10% GPU | ~500MB |
| VLM (VILA-7B AWQ) | ~60% GPU | ~8GB |
| Video Encode (4 streams) | NVENC (dedicated) | ~200MB |
| Tracking (NvDCF) | ~5% GPU | ~100MB |
| System/Overhead | ~25% GPU | ~2GB |

**Total**: ~11GB VRAM used, 53GB available for scaling

---

## Scaling Considerations

### Single Jetson Limits
| Metric | Orin Nano | AGX Orin 64GB |
|--------|-----------|---------------|
| Max 1080p streams (detection only) | 4-8 | 30+ |
| Max 1080p streams (with VLM) | 1-2 | 4-8 |
| VLM queries per second | 2-5 | 10-20 |

### Multi-Jetson Architecture
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Jetson #1  │     │  Jetson #2  │     │  Jetson #3  │
│ (Streams    │     │ (Streams    │     │ (VLM-only   │
│  1-4)       │     │  5-8)       │     │  queries)   │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           ▼
                   ┌───────────────┐
                   │  Aggregation  │
                   │    Server     │
                   └───────────────┘
```

---

## Containerization Strategy

### Base Container
```dockerfile
FROM nvcr.io/nvidia/l4t-jetpack:r36.4.0

# Install DeepStream
RUN apt-get update && apt-get install -y deepstream-8.0

# Install NanoLLM dependencies
RUN pip3 install nano-llm transformers
```

### Docker Compose Setup
```yaml
version: '3.8'
services:
  video-pipeline:
    image: custom-deepstream:latest
    runtime: nvidia
    ports:
      - "8554:8554"  # WebRTC
    volumes:
      - /tmp/argus_socket:/tmp/argus_socket  # CSI camera access

  vlm-service:
    image: dustynv/nano_llm:r36.4.0
    runtime: nvidia
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]

  api-gateway:
    image: custom-api:latest
    ports:
      - "8080:8080"
    depends_on:
      - video-pipeline
      - vlm-service
```

---

## Performance Optimization Checklist

- [ ] Use INT8 quantization for detection models
- [ ] Use AWQ 4-bit quantization for VLMs
- [ ] Enable DLA offloading for compatible layers
- [ ] Use unified memory to avoid CPU-GPU copies
- [ ] Set maximum clock speeds (`jetson_clocks`)
- [ ] Use NVDEC/NVENC for all video transcoding
- [ ] Limit VLM output tokens for faster responses
- [ ] Sample frames for VLM (1-5 FPS vs full framerate)
- [ ] Use connection pooling for API clients
- [ ] Enable TensorRT engine caching

---

*Last Updated: January 2026*
