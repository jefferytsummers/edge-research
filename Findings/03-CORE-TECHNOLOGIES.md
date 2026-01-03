# Core Technologies: Importance & Significance

## 1. NVIDIA Jetson Platform

### What It Is
NVIDIA Jetson is a family of embedded AI computing modules designed for edge deployment. The platform combines GPU acceleration with ARM CPUs in a compact, power-efficient form factor.

### Why It Matters for MVP
- **Only viable platform** for running VLMs (3-20B parameters) at the edge with acceptable latency
- **Unified memory architecture** allows efficient sharing between CPU/GPU without copies
- **Deep Learning Accelerator (DLA)** offloads inference, freeing GPU for other tasks
- **Hardware video codecs (NVENC/NVDEC)** enable low-latency video processing

### Current Lineup (2025/2026)

| Module | GPU | Memory | AI Performance |
|--------|-----|--------|----------------|
| Orin Nano 8GB | 1024 CUDA cores | 8GB | 67 TOPS |
| Orin NX 16GB | 1024 CUDA cores | 16GB | 100 TOPS |
| AGX Orin 64GB | 2048 CUDA cores | 64GB | 275 TOPS |
| Thor 128GB | Blackwell | 128GB | 1000+ TOPS |

---

## 2. JetPack SDK

### What It Is
JetPack is the complete software stack for Jetson, bundling:
- Linux kernel (6.x in JetPack 7)
- CUDA, cuDNN, TensorRT
- Multimedia API (video encode/decode)
- VPI (Vision Programming Interface)

### Why It Matters
- **Single installation** provides all dependencies
- **JetPack 6.x/7.x** required for latest VLM support
- **Container support** via NVIDIA Container Runtime
- **Pre-configured** for AI workloads out of the box

---

## 3. TensorRT

### What It Is
NVIDIA's high-performance deep learning inference optimizer and runtime. Converts models from PyTorch/ONNX into optimized engines.

### Why It Matters for MVP
- **2-10x speedup** over framework inference (PyTorch, TensorFlow)
- **INT8/FP16 quantization** reduces memory and increases throughput
- **Layer fusion** combines operations to reduce memory bandwidth
- **Critical for 100-200ms target**: Without TensorRT, VLM latency would be 500ms+

### Key Optimizations
```
Input Model (ONNX/PyTorch)
    ↓ Layer Fusion
    ↓ Precision Calibration (FP16/INT8)
    ↓ Kernel Auto-Tuning
    ↓ Memory Optimization
Optimized TensorRT Engine
```

---

## 4. DeepStream SDK

### What It Is
GStreamer-based streaming analytics toolkit for building video AI pipelines.

### Why It Matters for MVP
- **Hardware acceleration** end-to-end (decode → infer → encode)
- **Multi-stream support** (30+ 1080p streams on AGX Orin)
- **< 24ms inference latency** achievable for detection models
- **Built-in tracking** (NvDCF, DeepSORT)
- **Output flexibility**: RTSP, WebRTC, Kafka, file

### Pipeline Architecture
```
┌─────────┐   ┌──────────┐   ┌─────────┐   ┌─────────┐   ┌──────────┐
│  Input  │ → │  Decode  │ → │ Infer   │ → │ Tracker │ → │  Output  │
│ (RTSP)  │   │ (NVDEC)  │   │(nvinfer)│   │(nvtrack)│   │ (WebRTC) │
└─────────┘   └──────────┘   └─────────┘   └─────────┘   └──────────┘
```

---

## 5. Triton Inference Server

### What It Is
Open-source inference serving platform supporting multiple frameworks and backends.

### Why It Matters for MVP
- **Multi-model serving** from single endpoint
- **Dynamic batching** maximizes GPU utilization
- **Model ensembles** chain preprocessing → inference → postprocessing
- **C-API on Jetson** eliminates HTTP/gRPC overhead for local inference

### Deployment Modes
| Mode | Use Case | Latency |
|------|----------|---------|
| C-API (Shared Library) | Embedded apps on Jetson | Lowest |
| gRPC | Microservices architecture | Low |
| HTTP/REST | Web applications | Medium |

---

## 6. NanoLLM

### What It Is
Lightweight, high-performance library optimized for LLM/VLM inference on Jetson.

### Why It Matters for MVP
- **First-class Jetson support** (vs. fighting with vLLM/TensorRT-LLM)
- **4-bit quantization (AWQ)** runs larger models on limited memory
- **Vision encoder in TensorRT** accelerates multimodal pipeline
- **Streaming output** for real-time responses

### VLM Support
- VILA 1.5 / Cosmos Nemotron (NVIDIA's latest)
- LLaVA 1.5/1.6
- Llama 3.2 Vision
- Qwen2.5-VL
- And more via HuggingFace integration

---

## 7. Vision Language Models (VLMs)

### What They Are
Multimodal AI models that understand both images/video and text, enabling natural language queries about visual content.

### Why They Matter for MVP
- **Semantic understanding** beyond object detection ("Is anyone acting suspiciously?")
- **Flexible queries** without retraining
- **Natural language alerts** ("Notify me if a truck enters the loading dock")

### Recommended Models for Jetson

| Model | Parameters | Memory | Best For |
|-------|------------|--------|----------|
| VILA 1.5-3B | 3B | ~4GB | Orin Nano, fastest |
| Qwen2.5-VL-7B | 7B | ~8GB | Balance of speed/quality |
| LLaVA-13B | 13B | ~16GB | Higher accuracy |
| Llama 3.2 Vision 11B | 11B | ~14GB | Conversational |

### Latency Considerations
- **Vision encoding**: 20-50ms (TensorRT-optimized CLIP/SigLIP)
- **Text generation**: 30-150ms for short responses (depends on output length)
- **Total VLM query**: 50-200ms on AGX Orin with 4-bit model

---

## 8. WebRTC

### What It Is
Web standard for real-time communication with peer-to-peer video/audio streaming.

### Why It Matters for MVP
- **Browser-native** playback without plugins
- **Adaptive bitrate** handles varying network conditions
- **Low latency** (sub-100ms possible on local network)
- **Hardware-accelerated** encoding on Jetson via GStreamer

### jetson-inference Integration
```python
# Full-duplex WebRTC with detection
./detectnet --input-codec=h264 webrtc://@:8554/input webrtc://@:8554/output
```

---

## 9. Jetson Platform Services

### What It Is
Collection of production-ready microservices with REST APIs for common edge AI tasks.

### Why It Matters for MVP
- **Pre-built VLM service** with stream management APIs
- **Reduces time-to-production** vs. building from scratch
- **Standardized interfaces** for integration with enterprise systems
- **Reference architectures** for AI-NVR, analytics, etc.

### Available Services
- VLM AI Service
- DeepStream AI Service
- Analytics (tripwire, ROI)
- Zero-shot Detection (NanoOWL)
- Grounding DINO
- Video Storage Toolkit

---

## Technology Stack Synergy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER APPLICATION / WEB UI                        │
├─────────────────────────────────────────────────────────────────────────┤
│                     REST APIs / WebRTC / gRPC                           │
├───────────────────┬───────────────────┬─────────────────────────────────┤
│  Jetson Platform  │     NanoLLM       │      Custom Services            │
│     Services      │    (VLM Engine)   │                                 │
├───────────────────┴───────────────────┴─────────────────────────────────┤
│                   Triton Inference Server (Model Serving)               │
├─────────────────────────────────────────────────────────────────────────┤
│                   DeepStream SDK (Video Pipeline)                       │
├─────────────────────────────────────────────────────────────────────────┤
│                   TensorRT (Optimized Inference)                        │
├─────────────────────────────────────────────────────────────────────────┤
│                   JetPack SDK (CUDA, cuDNN, VPI, Multimedia)            │
├─────────────────────────────────────────────────────────────────────────┤
│                   NVIDIA Jetson Hardware (Orin/Thor)                    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

*Last Updated: January 2026*
