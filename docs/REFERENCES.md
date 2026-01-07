# Reference Projects

Curated references for Jetson edge AI development.

## Core Dependencies

### jetson-containers
**Repository:** https://github.com/dusty-nv/jetson-containers

Pre-built Docker containers optimized for Jetson:
- NanoLLM, VILA, LLaVA
- PyTorch, TensorFlow
- ROS, Isaac
- And 100+ more packages

```bash
# Example: Run NanoLLM container
jetson-containers run dustynv/nano_llm:r36.4.0
```

### NanoLLM
**Repository:** https://github.com/dusty-nv/NanoLLM
**Documentation:** https://dusty-nv.github.io/NanoLLM/

Optimized LLM/VLM inference for Jetson:
- Plugin architecture for pipelines
- Video input via jetson-utils
- Streaming generation
- Multi-modal support

### DeepStream SDK
**Documentation:** https://docs.nvidia.com/metropolis/deepstream/dev-guide/

NVIDIA's streaming analytics toolkit:
- Hardware-accelerated video decode
- Batched inference with TensorRT
- Multi-stream processing
- Python bindings

### DeepStream-Yolo
**Repository:** https://github.com/marcoslucianops/DeepStream-Yolo

YOLO models in DeepStream:
- YOLOv8, YOLOv9, YOLO-NAS
- TensorRT optimization
- Custom parser for detection metadata

---

## Jetson AI Lab

**Website:** https://www.jetson-ai-lab.com/

Tutorials and examples:
- [VILA on Jetson](https://www.jetson-ai-lab.com/tutorial_vila.html)
- [NanoVLM](https://www.jetson-ai-lab.com/tutorial_nano-vlm.html)
- [Live LLaVA](https://www.jetson-ai-lab.com/tutorial_live-llava.html)

---

## NVIDIA Resources

### Jetson Platform Services (JPS)
**Documentation:** https://docs.nvidia.com/jetson/jps/

Reference architecture for AI services:
- Microservice containers
- REST/WebSocket APIs
- VLM integration patterns

### jetson-inference
**Repository:** https://github.com/dusty-nv/jetson-inference

Classic Jetson AI examples:
- Image classification
- Object detection
- Semantic segmentation
- WebRTC streaming

---

## YOLOv8 on Jetson

**Documentation:** https://docs.ultralytics.com/guides/nvidia-jetson/

Official Ultralytics guide:
- TensorRT export
- INT8 quantization
- DeepStream integration
- Performance benchmarks

---

## Community Resources

### NVIDIA Developer Forums
**URL:** https://forums.developer.nvidia.com/c/agx-autonomous-machines/jetson-embedded-systems/

Active community for:
- Troubleshooting
- Performance optimization
- Use case discussions

### Jetson Projects
**URL:** https://developer.nvidia.com/embedded/community/jetson-projects

Community project showcase with source code.

---

## Container Images Used

| Image | Purpose |
|-------|---------|
| `dustynv/nano_llm:r36.4.0` | VLM inference (VILA-7B) |
| `nvcr.io/nvidia/deepstream:7.0-gc-triton-devel` | Video processing + detection |
| `redis:7-alpine` | Message broker |
| `python:3.11-slim` | App container base |
