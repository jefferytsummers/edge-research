# CLAUDE.md - Newport Demo Development Guide

## Container-First Architecture

This project follows a **strict container-first architecture**. All development, testing, and execution MUST happen inside containers. Never run Python code or install dependencies directly on the host.

### Core Principles

1. **No local pip installs** - All Python dependencies live in containers
2. **No local test execution** - Tests run via `make test` inside containers
3. **No local Python execution** - All code runs inside appropriate containers
4. **Containers are the source of truth** - If it doesn't work in a container, it doesn't work

### Why Container-First?

- **Jetson deployment parity** - Development environment matches Jetson AGX Orin target
- **NGC/dustynv compatibility** - Uses official NVIDIA containers with GPU support
- **Reproducibility** - Same environment everywhere
- **Isolation** - No host Python pollution

---

## Container Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                     docker-compose.yml                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  deepstream  │  │     vlm      │  │     app      │          │
│  │  (NGC 7.0)   │  │  (nano_llm)  │  │  (FastAPI)   │          │
│  │              │  │              │  │              │          │
│  │  YOLOv8-s    │  │  VILA-7B     │  │  WebSocket   │          │
│  │  Detection   │  │  Protocol    │  │  Frontend    │          │
│  │              │  │  Evaluator   │  │              │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
│         └────────┬────────┴────────┬────────┘                   │
│                  │                 │                             │
│              ┌───▼─────────────────▼───┐                        │
│              │         redis           │                        │
│              │     (pub/sub bus)       │                        │
│              └─────────────────────────┘                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

| Container | Image | Purpose |
|-----------|-------|---------|
| `deepstream` | `nvcr.io/nvidia/deepstream:7.0-gc-triton-devel` | Multi-stream video decode + YOLOv8 detection |
| `vlm` | `dustynv/nano_llm:r36.4.0` | Protocol evaluation with VILA-7B |
| `app` | `python:3.11-slim` (custom) | FastAPI backend + React frontend |
| `redis` | `redis:7-alpine` | Pub/sub messaging between containers |

---

## Development Workflow

### Starting the Stack

```bash
# Start all containers
make dev

# View status
make status

# View logs (all)
make logs

# View logs (specific)
make logs-app
make logs-vlm
make logs-ds
```

### Running Tests

**ALWAYS use container-based testing:**

```bash
# Run all app tests (inside container)
make test

# Run tests with coverage
make test-cov
```

**NEVER use local testing commands** - The `test-local-*` targets exist only for CI environments that set up their own dependencies.

### Interactive Development

```bash
# Shell into app container
make shell-app

# Shell into VLM container
make shell-vlm

# Shell into DeepStream container
make shell-ds

# Redis CLI
make redis-cli
```

### Rebuilding

```bash
# Rebuild app container
make build-app

# Rebuild all containers
make build-all
```

---

## File Structure

```
edge-research/
├── app/                    # FastAPI + Frontend (custom container)
│   ├── Dockerfile         # Python 3.11-slim based
│   ├── requirements.txt   # Python dependencies
│   ├── src/               # FastAPI application
│   │   ├── main.py       # Entry point
│   │   ├── config.py     # Settings via pydantic-settings
│   │   ├── models.py     # Pydantic data models
│   │   ├── event_bus.py  # Redis pub/sub + local events
│   │   └── websocket.py  # WebSocket handlers
│   ├── tests/             # pytest tests
│   └── frontend/          # React + Vite + TypeScript
│
├── vlm/                    # VLM inference (dustynv container)
│   ├── src/
│   │   ├── protocol_evaluator.py  # Severity classification
│   │   └── vlm_subscriber.py      # Redis subscriber
│   └── tests/
│
├── deepstream/            # Video pipeline (NGC container)
│   ├── config/            # Pipeline configs
│   ├── src/
│   │   └── detection_publisher.py  # Detection → Redis
│   └── tests/
│
├── docker-compose.yml     # Container orchestration
├── Makefile               # Development commands
└── docs/                  # Documentation
```

---

## Inter-Container Communication

All containers communicate via Redis pub/sub:

```
┌─────────────┐     detections     ┌─────────────┐
│ deepstream  │ ─────────────────► │     vlm     │
│             │                    │             │
│  Publishes: │                    │ Subscribes: │
│  detections │                    │ detections  │
└─────────────┘                    │             │
                                   │  Publishes: │
                                   │  summaries  │
                                   └──────┬──────┘
                                          │
                                   summaries
                                          │
                                          ▼
                                   ┌─────────────┐
                                   │     app     │
                                   │             │
                                   │ Subscribes: │
                                   │ summaries   │
                                   │ detections  │
                                   │             │
                                   │ → WebSocket │
                                   │   clients   │
                                   └─────────────┘
```

### Redis Channels

| Channel | Publisher | Subscribers | Payload |
|---------|-----------|-------------|---------|
| `detections` | deepstream | vlm, app | `{stream_id, boxes, frame_path, timestamp}` |
| `summaries` | vlm | app | `{stream_id, severity, icon, description}` |
| `queries` | app | vlm | `{stream_id, question, request_id}` |
| `responses` | vlm | app | `{request_id, answer}` |

---

## Shared Volumes

| Volume | Type | Purpose |
|--------|------|---------|
| `frame_buffer` | tmpfs | Zero-copy frame sharing (DeepStream → VLM) |
| `model_cache` | persistent | VLM model weights |
| `config_data` | persistent | SQLite configuration |
| `redis_data` | persistent | Redis persistence |

---

## Development Guidelines for Claude

### DO:

- Use `make dev` to start the stack
- Use `make test` to run tests
- Use `make shell-app` to debug interactively
- Use `make logs-app` to view logs
- Edit files in `app/src/`, `vlm/src/`, `deepstream/src/`
- Rebuild containers after changing Dockerfile or requirements

### DO NOT:

- Run `pip install` on the host
- Run `python` or `pytest` directly on the host
- Create virtual environments on the host
- Install system packages for development
- Bypass containers for "quick testing"

### When Tests Fail:

1. Check container logs: `make logs-app`
2. Shell into container: `make shell-app`
3. Run tests interactively: `pytest tests/ -v`
4. Debug with: `python -c "from src.models import ..."`

### When Adding Dependencies:

1. Edit `app/requirements.txt` (or vlm/deepstream equivalent)
2. Rebuild: `make build-app`
3. Restart: `make restart-app` or `make dev`

---

## Health Checks

All containers have health checks:

```bash
# Check container health
make status

# Or directly:
docker compose ps
```

| Container | Health Check |
|-----------|--------------|
| `app` | `curl http://localhost:8080/health` |
| `redis` | `redis-cli ping` |
| `vlm` | `python -c "import nano_llm"` |
| `deepstream` | `curl http://localhost:8554/health` |

---

## Common Issues

### "Container not running"

```bash
make dev     # Start containers
make status  # Check status
make logs    # View startup logs
```

### "Tests fail with import errors"

You're probably running tests locally. Use:
```bash
make test    # NOT pytest directly
```

### "Redis connection refused"

```bash
make status          # Is redis running?
make redis-cli       # Can you connect?
make restart-redis   # Try restarting
```

### "GPU not available"

DeepStream and VLM containers require NVIDIA runtime:
- Check Docker is configured with nvidia-container-toolkit
- Verify GPU with: `docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi`

---

## Project Status

See `AGILE-PLAN.md` for full backlog. Current focus:

- **Sprint N1**: Multi-container foundation (in progress)
- **Sprint N2**: DeepStream + VLM pipeline
- **Sprint N3**: Setup Wizard + Dashboard UI
- **Sprint N4**: Alerts + Polish
- **Sprint N5**: Demo mode

---

## Quick Reference

```bash
# Start development
make dev

# View logs
make logs

# Run tests
make test

# Shell access
make shell-app

# Stop everything
make stop

# Rebuild after changes
make build-app && make dev
```
