# Video Intelligence Platform - MVP Documentation

## Product Overview

A multi-modal edge AI platform that transforms video into searchable, queryable knowledge using Vision Language Models (VLMs), object detection, and RAG-powered natural language agents.

```
Upload Video → Process (VLM + Detection) → Index → Ask Questions in Plain English
```

---

## Documentation Index

| Document | Description | Audience |
|----------|-------------|----------|
| [01-EXECUTIVE-SUMMARY.md](./01-EXECUTIVE-SUMMARY.md) | Product vision, UX flows, feature scope | Product, Stakeholders |
| [02-TECHNICAL-DECISIONS.md](./02-TECHNICAL-DECISIONS.md) | ADRs for all major technology choices | Engineering |
| [03-ARCHITECTURE.md](./03-ARCHITECTURE.md) | System design, components, data flows | Engineering |
| [04-DEPLOYMENT-DEVOPS.md](./04-DEPLOYMENT-DEVOPS.md) | CI/CD, Docker, Jetson setup, operations | DevOps, Engineering |
| [05-REFERENCE-PROJECTS.md](./05-REFERENCE-PROJECTS.md) | Relevant open-source repos and tools | Engineering |

---

## Quick Reference

### Core Stack

| Layer | Technology |
|-------|------------|
| Hardware | Jetson AGX Orin 64GB |
| VLM | VILA-7B (AWQ 4-bit) via NanoLLM |
| Detection | YOLOv8-s (TensorRT INT8) |
| Embeddings | SigLIP ViT-B/16 |
| Vector DB | ChromaDB |
| Backend | FastAPI + Celery + Redis |
| Frontend | React + Vite + Tailwind |
| Container | Docker with NVIDIA runtime |

### Performance Targets

| Metric | Target |
|--------|--------|
| Video processing | <2 min per minute of video |
| Semantic search | <500ms |
| Agent response | <3s |
| Detection latency | <10ms |
| VLM latency | <200ms |

---

## Getting Started

### Development
```bash
git clone https://github.com/myorg/video-intelligence.git
cd video-intelligence
docker-compose -f docker/docker-compose.dev.yml up -d
uvicorn src.main:app --reload
```

### Production (Jetson)
```bash
# On Jetson device
cd /opt/video-intelligence
docker-compose pull
docker-compose up -d
```

---

## Key Features

### V1 (MVP)
- [x] Video upload and processing
- [x] Keyframe extraction (scene detection)
- [x] Object detection (YOLOv8)
- [x] VLM descriptions (VILA-7B)
- [x] Semantic search (ChromaDB)
- [x] RAG agent with tool use
- [x] Web UI

### V2 (Planned)
- [ ] URL/YouTube import
- [ ] Audio transcription
- [ ] Live stream integration
- [ ] Multi-user authentication
- [ ] Export/reporting

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Web Browser (React)                          │
└───────────────────────────────────┬─────────────────────────────────┘
                                    │
┌───────────────────────────────────┼─────────────────────────────────┐
│                        Jetson AGX Orin                               │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │  Nginx → FastAPI → Celery Workers → NanoLLM / YOLO / ChromaDB   ││
│  └─────────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │  PostgreSQL (metadata) │ Redis (queue) │ Files (videos/frames)  ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

---

*Video Intelligence Platform MVP - January 2026*
