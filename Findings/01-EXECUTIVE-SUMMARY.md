# Executive Summary: Edge AI Video Inference MVP

## Vision
Build a low-latency AI video inference system that enables users to select live video feeds, pair them with Vision Language Models (VLMs), and run real-time inference on NVIDIA Jetson edge devices. The system provides inference results as metadata, visualizations, or annotated video feeds with target latency of 100-200ms.

---

## MVP Use Cases

### 1. Real-Time Video Q&A
- Query live video streams with natural language ("Is anyone in the restricted area?", "What's the current traffic pattern?")
- Trigger alerts based on VLM responses
- **Latency Target**: 200-500ms for text responses

### 2. Annotated Video Feed
- Object detection overlays (bounding boxes, labels)
- Real-time segmentation visualization
- **Latency Target**: 100-200ms end-to-end (achievable with DeepStream + TensorRT)

### 3. Metadata/Analytics Stream
- JSON/gRPC metadata output for downstream systems
- Event-driven alerts (tripwire crossing, object appearance)
- Integration with enterprise systems (MQTT, Kafka, REST)

---

## Recommended Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Hardware** | Jetson AGX Orin 64GB | Supports VLMs up to 20B parameters; 275 TOPS |
| **Base Platform** | JetPack 6.x / 7.x | Ubuntu 24.04, CUDA 12.x, TensorRT 10.x |
| **VLM Inference** | NanoLLM + TensorRT | Optimized for Jetson; 4-bit quantization support |
| **Video Pipeline** | DeepStream SDK 8.0 | GStreamer-based, <24ms inference latency possible |
| **Model Serving** | Triton Inference Server | Multi-framework, C-API for zero-overhead on Jetson |
| **Streaming** | WebRTC (jetson-inference) | Hardware-accelerated, browser-compatible |
| **APIs** | Jetson Platform Services | Pre-built REST APIs for VLM, detection, analytics |

---

## Latency Budget Analysis (Target: 100-200ms)

| Stage | Estimated Latency |
|-------|-------------------|
| Video Capture (CSI/RTSP) | 5-15ms |
| Decode (NVDEC) | 3-5ms |
| Preprocessing | 2-5ms |
| Inference (YOLOv8 INT8) | 2-10ms |
| VLM Query (3B model) | 50-150ms |
| Encode (NVENC) | 3-5ms |
| Network/Display | 10-30ms |
| **Total** | **75-220ms** |

*Note: Pure detection workflows hit <50ms; VLM adds 50-150ms overhead depending on model size and output length*

---

## Hardware Recommendations by Use Case

| Use Case | Hardware | VLM Capacity | Price |
|----------|----------|--------------|-------|
| **Prototype/Demo** | Jetson Orin Nano Super | Up to 4B (VILA-3B, Qwen2.5-VL-3B) | $249 |
| **Production MVP** | Jetson AGX Orin 64GB | Up to 20B (LLaVA-13B, Llama-3.2-11B) | ~$1,999 |
| **Multi-stream/Large VLM** | Jetson Thor 128GB | Up to 120B | TBD |

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| VLM latency exceeds target | Use smaller models (3-7B), INT4 quantization, token limits |
| Memory constraints | Use Cosmos Nemotron AWQ 4-bit, shared memory buffers |
| Network bottlenecks | WebRTC adaptive bitrate, edge inference only |
| Model compatibility | Leverage jetson-containers ecosystem |

---

## Recommended Phase 1 Implementation

1. **Set up Jetson AGX Orin** with JetPack 6.2
2. **Deploy jetson-containers** with NanoLLM + VILA/LLaVA
3. **Build GStreamer pipeline** using DeepStream for video ingestion
4. **Integrate WebRTC server** for browser-based viewing
5. **Expose REST APIs** using Jetson Platform Services patterns
6. **Benchmark latency** with representative workloads

---

## Key Success Metrics

- End-to-end latency <200ms for annotated video
- Support for 1080p @ 30fps input streams
- VLM response time <500ms for simple queries
- Stable operation over 24+ hours

---

*Generated: January 2026*
*Sources: NVIDIA Developer Documentation, Jetson AI Lab, jetson-containers project*
