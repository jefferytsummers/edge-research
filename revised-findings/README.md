# Revised Findings: Edge AI Video Inference MVP

## Overview

Compacted research findings focused on actionable MVP development for real-time VLM-powered video analytics on NVIDIA Jetson edge devices.

**Target:** 100-200ms latency for annotated video, <500ms for VLM queries

---

## Document Index

| Document | Purpose |
|----------|---------|
| [01-CORE-KNOWLEDGE.md](./01-CORE-KNOWLEDGE.md) | Compacted tech stack, platform decisions, latency budget |
| [02-MVP-UX-STRATEGY.md](./02-MVP-UX-STRATEGY.md) | Live streaming UX: user flows, wireframes, accessibility |
| [03-DEPLOYMENT-PIPELINE.md](./03-DEPLOYMENT-PIPELINE.md) | CI/CD, containers, OTA updates, testing |
| [04-MARKET-ANALYSIS.md](./04-MARKET-ANALYSIS.md) | TAM, adoption signals, pricing, competition |
| [05-PRODUCT-SOLUTIONS.md](./05-PRODUCT-SOLUTIONS.md) | Ready-to-use Jetson software, containers, tools |
| [06-STATIC-VIDEO-UX.md](./06-STATIC-VIDEO-UX.md) | **Static/web video UX + RAG agent architecture** |

---

## Two MVP Approaches

### Track A: Static Video + RAG Agent (Recommended Start)
Simpler to build, no WebRTC complexity, enables multi-video RAG queries.
- Upload/URL video processing
- Keyframe extraction + indexing
- VLM descriptions + embeddings
- Natural language agent with tool use

### Track B: Live Streaming (Production Goal)
Real-time surveillance and monitoring use cases.
- WebRTC streaming
- Live detection overlays
- Real-time VLM alerts
- Camera integration (RTSP/ONVIF)

---

## Quick Reference

### Platform
**Jetson AGX Orin 64GB** - $1,999, 275 TOPS, 64GB unified memory

### Stack
```
NanoLLM (VLM) + DeepStream (Video) + FastAPI (API) + WebRTC (Streaming)
                           ↓
                   JetPack 6.x + TensorRT
```

### Latency (Achievable)
| Pipeline | Target | Actual |
|----------|--------|--------|
| Video + Detection | <100ms | 75ms |
| Video + VLM Query | <500ms | 200-300ms |

### Market
| Metric | Value |
|--------|-------|
| AI Video Analytics TAM | $5B → $17B (2025-2030) |
| CAGR | 23% |
| Enterprise VLM Adoption | 90% Fortune 500 by 2026 |

---

## MVP Build Pipeline

```bash
# Local development
docker-compose -f docker-compose.dev.yml up

# Build for Jetson
docker buildx build --platform linux/arm64 -t mvp:latest .

# Deploy to device
docker-compose pull && docker-compose up -d
```

---

## Next Steps (Recommended: Start with Track A)

### Phase 1: Static Video Platform
1. Set up Jetson AGX Orin with JetPack 6.2
2. Deploy NanoLLM + YOLO containers
3. Build FastAPI backend with video processing pipeline
4. Implement ChromaDB for vector storage
5. Build RAG agent with tool use (detection, VLM, search)
6. Create web UI for upload + chat

### Phase 2: Add Live Streaming
7. Integrate DeepStream for video pipeline
8. Add WebRTC streaming output
9. Implement real-time detection overlays
10. Connect live streams to RAG index

---

*Revised Findings - January 2026*
