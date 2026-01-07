# Technical Decision Records

Technical decisions for the Newport Demo project.

## TDR-001: Hardware Platform - Jetson AGX Orin 64GB

**Status:** Accepted

**Context:** Need edge AI platform for multi-stream video processing with VLM inference.

**Decision:** NVIDIA Jetson AGX Orin 64GB Developer Kit

**Rationale:**
- 275 TOPS INT8 inference performance
- 64GB unified memory (crucial for VLM + detection + multi-stream decode)
- 8x 4K60 NVDEC hardware decode
- Native TensorRT, DeepStream, CUDA support
- Active community (dustynv containers, jetson-containers)

---

## TDR-002: Vision Language Model - VILA-7B AWQ

**Status:** Accepted

**Context:** Need VLM for scene description and protocol classification.

**Decision:** VILA-7B with AWQ 4-bit quantization via NanoLLM

**Rationale:**
- Optimized for Jetson via dustynv/nano_llm container
- AWQ quantization fits in ~8GB memory
- 120-150ms inference latency on Orin
- Good balance of quality and speed for edge deployment

**Container:** `dustynv/nano_llm:r36.4.0`

---

## TDR-003: Object Detection - YOLOv8-s TensorRT INT8

**Status:** Accepted

**Context:** Need real-time person detection for fast-path alerts.

**Decision:** YOLOv8-small with TensorRT INT8 quantization

**Rationale:**
- 5-8ms inference latency
- Excellent person detection accuracy
- Native TensorRT export from Ultralytics
- Runs efficiently alongside VLM in batched DeepStream pipeline

**Export Command:**
```bash
yolo export model=yolov8s.pt format=engine device=0 int8=True
```

---

## TDR-009: Video Processing - DeepStream Multi-Stream

**Status:** Accepted

**Context:** Need efficient multi-stream video decode and batched inference.

**Decision:** NVIDIA DeepStream 7.x with nvstreammux

**Rationale:**
- Hardware-accelerated NVDEC for multiple RTSP streams
- nvstreammux enables batched inference across streams
- Native integration with TensorRT models
- Python bindings for probe callbacks
- Proven at scale (JPS reference architecture)

**Container:** `nvcr.io/nvidia/deepstream:7.0-gc-triton-devel`

---

## TDR-010: Containerization - Multi-Container Docker Compose

**Status:** Accepted

**Context:** Need isolated, reproducible deployment with official containers.

**Decision:** Docker Compose with NVIDIA Container Runtime

**Rationale:**
- Use official NGC/community containers without modification
- Redis pub/sub for inter-container messaging
- tmpfs shared volume for frame passing
- Independent scaling/updating of components
- Matches NVIDIA JPS reference pattern

**Services:**
1. `deepstream` - NGC DeepStream for video/detection
2. `vlm` - dustynv/nano_llm for VLM inference
3. `app` - Custom FastAPI + React
4. `redis` - Message broker

---

## References

- [Jetson AGX Orin Specs](https://developer.nvidia.com/embedded/jetson-agx-orin)
- [NanoLLM Documentation](https://dusty-nv.github.io/NanoLLM/)
- [DeepStream Documentation](https://docs.nvidia.com/metropolis/deepstream/dev-guide/)
- [YOLOv8 on Jetson](https://docs.ultralytics.com/guides/nvidia-jetson/)
