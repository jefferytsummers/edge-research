# Edge AI Video Inference Research Findings

## Overview
Research documentation for building an MVP that enables real-time video inference with Vision Language Models (VLMs) on NVIDIA Jetson edge devices.

**Target Latency**: 100-200ms for annotated video, <500ms for VLM queries
**Primary Platform**: NVIDIA Jetson AGX Orin

---

## Document Index

| Document | Description |
|----------|-------------|
| [01-EXECUTIVE-SUMMARY.md](./01-EXECUTIVE-SUMMARY.md) | MVP use cases, technology stack, latency budget, risk assessment |
| [02-REFERENCE-APPLICATIONS.md](./02-REFERENCE-APPLICATIONS.md) | GitHub repos, container images, tutorials, code examples |
| [03-CORE-TECHNOLOGIES.md](./03-CORE-TECHNOLOGIES.md) | Deep dive into JetPack, TensorRT, DeepStream, Triton, NanoLLM, VLMs |
| [04-ARCHITECTURE-RECOMMENDATIONS.md](./04-ARCHITECTURE-RECOMMENDATIONS.md) | System architecture, API design, containerization, scaling |
| [05-COMPETITIVE-ANALYSIS.md](./05-COMPETITIVE-ANALYSIS.md) | Jetson vs Coral vs Qualcomm vs Hailo; cloud hybrid options |
| [06-QUICK-START-GUIDE.md](./06-QUICK-START-GUIDE.md) | Step-by-step setup guide, commands, troubleshooting |

---

## Key Findings Summary

### 1. Platform Recommendation
**NVIDIA Jetson AGX Orin 64GB** is the only viable platform for running VLMs (3-20B parameters) at the edge with acceptable latency.

### 2. Technology Stack
- **Video Pipeline**: DeepStream SDK 8.0 (GStreamer-based)
- **VLM Inference**: NanoLLM with TensorRT optimization
- **Model Serving**: Triton Inference Server (C-API for lowest latency)
- **Streaming**: WebRTC via jetson-inference

### 3. Latency Achievability
- **Detection-only**: <50ms achievable
- **Detection + VLM**: 100-200ms achievable with 3-7B models
- **Full VLM query**: 200-500ms depending on response length

### 4. Key Resources
- [Jetson AI Lab](https://www.jetson-ai-lab.com/) - Tutorials and benchmarks
- [jetson-containers](https://github.com/dusty-nv/jetson-containers) - Container ecosystem
- [Jetson Platform Services](https://docs.nvidia.com/jetson/jps/) - Production microservices

---

## Research Date
January 2026

## Sources
All information sourced from official NVIDIA documentation, developer blogs, GitHub repositories, and community resources.
