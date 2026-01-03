# Core Knowledge: Edge AI Video Inference MVP

## The One-Liner
Real-time VLM-powered video analytics on Jetson AGX Orin, achieving 100-200ms latency for annotated video and <500ms for natural language queries.

---

## Platform Decision: NVIDIA Jetson AGX Orin 64GB

**Why This and Only This:**
- Only edge platform capable of running 3-20B parameter VLMs with acceptable latency
- 275 TOPS AI performance, 64GB unified memory
- Hardware video codecs (NVENC/NVDEC) for <5ms encode/decode
- Mature ecosystem: NanoLLM, DeepStream, Triton, jetson-containers
- Production support through JetPack 6.x (sustaining) and 7.x (new)

**Alternatives Considered & Rejected:**
| Platform | Why Not |
|----------|---------|
| Google Coral | 4 TOPS, no VLM capability |
| Qualcomm RB5 | 26 TOPS, immature VLM ecosystem |
| Hailo-8 | Great for detection, no VLM |
| RPi5 + Accelerator | No VLM capability |

**New: Jetson Thor Available (Aug 2025)**
- 2,070 FP4 TOPS (7.5x Orin), 128GB memory, $3,499 dev kit
- Blackwell GPU architecture
- Overkill for MVP, but future-proof option

---

## Technology Stack (Locked In)

```
┌─────────────────────────────────────────────────────────────┐
│                    API LAYER (FastAPI)                      │
│         REST + WebSocket + WebRTC (browser-native)          │
├─────────────────────────────────────────────────────────────┤
│  NanoLLM (VLM)          │   DeepStream SDK 8.0 (Video)     │
│  VILA/LLaVA/Qwen        │   Detection + Tracking + Encode  │
├─────────────────────────────────────────────────────────────┤
│                   TensorRT 10.x (Optimization)              │
│              INT8 detection, AWQ 4-bit VLM                  │
├─────────────────────────────────────────────────────────────┤
│                   JetPack 6.x / 7.x                         │
│            CUDA 12.x + cuDNN + Multimedia API               │
├─────────────────────────────────────────────────────────────┤
│                 NVIDIA Jetson AGX Orin 64GB                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Latency Budget (Validated)

| Stage | Time | Notes |
|-------|------|-------|
| Video Capture | 5-15ms | CSI fastest, RTSP adds latency |
| Decode (NVDEC) | 3-5ms | Hardware accelerated |
| Preprocessing | 2-5ms | Resize, normalize |
| Detection (YOLOv8 INT8) | 2-10ms | TensorRT optimized |
| VLM Query (3-7B AWQ) | 50-150ms | Token limit critical |
| Encode (NVENC) | 3-5ms | Hardware accelerated |
| Network/Display | 10-30ms | WebRTC adaptive |
| **Total** | **75-220ms** | Within target |

**Key Insight:** Detection-only hits <50ms. VLM adds 50-150ms. Keep VLM responses short.

---

## Model Recommendations

| Use Case | Model | Memory | Latency |
|----------|-------|--------|---------|
| Fastest VLM | VILA 1.5-3B | ~4GB | 50-80ms |
| Balanced | Qwen2.5-VL-7B AWQ | ~8GB | 80-120ms |
| Quality | LLaVA-13B AWQ | ~16GB | 120-180ms |
| Detection | YOLOv8-s INT8 | ~500MB | 2-10ms |

---

## What Jetson Platform Services Gives Us

Pre-built microservices (15+) available in JetPack 6.x:
- **VLM AI Service**: REST API for VILA/LLaVA inference
- **DeepStream AI Service**: Multi-stream detection with PeopleNet/YOLOv8
- **Analytics Service**: Tripwire, ROI, counting
- **Video Storage Toolkit (VST)**: Camera discovery, streaming, storage
- **Zero-Shot Detection**: NanoOWL (no retraining needed)
- **Grounding DINO**: Open-vocabulary detection

**AI-NVR Reference App** combines all services into production-ready workflow.

---

## Key Resources (Bookmarked)

| Resource | URL | Use |
|----------|-----|-----|
| Jetson AI Lab | jetson-ai-lab.com | Tutorials, benchmarks |
| jetson-containers | github.com/dusty-nv/jetson-containers | Container ecosystem |
| NanoLLM Docs | dusty-nv.github.io/NanoLLM | VLM API reference |
| Jetson Platform Services | docs.nvidia.com/jetson/jps | Production microservices |
| DeepStream SDK | docs.nvidia.com/metropolis/deepstream | Video pipeline docs |

---

## Risk Mitigations (Pre-Solved)

| Risk | Mitigation |
|------|------------|
| VLM latency | Use 3-7B models, AWQ 4-bit, limit output tokens |
| Memory exhaustion | Unified memory, shared buffers, model offloading |
| Network bottlenecks | WebRTC adaptive bitrate, edge-only processing |
| Model compatibility | Use jetson-containers (pre-validated) |
| Production stability | Jetson Platform Services patterns |

---

*Compacted from original research - January 2026*
