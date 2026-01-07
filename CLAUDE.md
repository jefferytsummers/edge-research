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
│  │  (NGC 8.0)   │  │  (nano_llm)  │  │  (FastAPI)   │          │
│  │              │  │              │  │              │          │
│  │  Detection   │  │  VILA        │  │  WebSocket   │          │
│  │  + pyds      │  │  Protocol    │  │  Frontend    │          │
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

| Container | Base Image | Custom | Purpose |
|-----------|------------|--------|---------|
| `deepstream` | `nvcr.io/nvidia/deepstream-l4t:8.0-samples-multiarch` | Yes | Video decode + detection (ARM64/Jetson) |
| `vlm` | `dustynv/nano_llm:r36.4.0` | Yes | Protocol evaluation with VILA |
| `app` | `python:3.11-slim` | Yes | FastAPI backend + React frontend |
| `redis` | `redis:7-alpine` | No | Pub/sub messaging between containers |

---

## NGC Container Python Development

**CRITICAL**: NGC containers (DeepStream, etc.) do NOT include Python bindings pre-installed. You MUST use custom Dockerfiles that extend the base images.

### Why Custom Dockerfiles Are Required

NGC containers are optimized for C++ applications. For Python development:

1. **pyds (DeepStream Python bindings)** - Not included, must be installed separately
2. **python3-gi (GObject introspection)** - Often missing or incomplete
3. **Python 3.12 venv requirement** - DS 8.0 requires virtual environments for pip

### Standard Pattern for NGC-Based Containers

```dockerfile
# 1. Start from NGC base image
FROM nvcr.io/nvidia/deepstream-l4t:8.0-samples-multiarch

# 2. Install apt dependencies (GStreamer/GObject bindings)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-gi python3-gst-1.0 python3-venv python3-pip wget \
    && rm -rf /var/lib/apt/lists/*

# 3. Create venv with --system-site-packages (inherits apt packages)
RUN python3 -m venv /opt/venv --system-site-packages
ENV PATH="/opt/venv/bin:$PATH"

# 4. Install pyds wheel (version must match DeepStream version)
# Filename format: pyds-{version}-cp{pyver}-cp{pyver}-linux_{arch}.whl
RUN wget -q https://github.com/NVIDIA-AI-IOT/deepstream_python_apps/releases/download/v1.2.2/pyds-1.2.2-cp312-cp312-linux_aarch64.whl \
    && pip install pyds-1.2.2-cp312-cp312-linux_aarch64.whl

# 5. Install application dependencies
RUN pip install --no-cache-dir redis opencv-python-headless
```

### Version Compatibility Matrix

| DeepStream | pyds | Python | Platform | Base Image |
|------------|------|--------|----------|------------|
| 8.0 | 1.2.2 | 3.12 | Jetson (L4T) | `deepstream-l4t:8.0-samples-multiarch` |
| 8.0 | 1.2.2 | 3.12 | x86_64 | `deepstream:8.0-samples-multiarch` |
| 7.1 | 1.2.0 | 3.10 | Jetson | `deepstream-l4t:7.1-samples-multiarch` |

### pyds Wheel Downloads

Pre-built wheels are available at:
- https://github.com/NVIDIA-AI-IOT/deepstream_python_apps/releases

Filename format: `pyds-{version}-cp{pyver}-cp{pyver}-linux_{arch}.whl`

**Example for DS 8.0 (Python 3.12):**
- **Jetson/ARM64**: `pyds-1.2.2-cp312-cp312-linux_aarch64.whl`
- **x86_64**: `pyds-1.2.2-cp312-cp312-linux_x86_64.whl`

### Common Mistakes to Avoid

| Mistake | Why It Fails | Correct Approach |
|---------|--------------|------------------|
| Using NGC image directly without Dockerfile | No pyds, no python3-gi | Always extend with custom Dockerfile |
| `pip install` without venv | Python 3.12 blocks system pip | Use `python3 -m venv` first |
| Creating venv without `--system-site-packages` | Loses python3-gi from apt | Always use `--system-site-packages` |
| Wrong pyds version | API incompatibility | Match pyds version to DS version |
| Using x86 image on Jetson | Architecture mismatch | Use `-l4t` images for Jetson |

### dusty-nv Container Notes

The `dustynv/nano_llm` container already includes most Python dependencies but may need:
- `redis` for pub/sub
- `Pillow` for image handling

These are lightweight additions via pip in the Dockerfile.

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
├── vlm/                    # VLM inference (extends dustynv/nano_llm)
│   ├── Dockerfile         # Adds redis, Pillow
│   ├── src/
│   │   ├── protocol_evaluator.py  # Severity classification
│   │   └── vlm_subscriber.py      # Redis subscriber
│   └── tests/
│
├── deepstream/            # Video pipeline (extends NGC DeepStream)
│   ├── Dockerfile         # Adds pyds, python3-gi, redis, opencv
│   ├── config/            # Pipeline configs (nvinfer, labels)
│   ├── src/
│   │   └── deepstream_pipeline.py  # GStreamer pipeline → Redis
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
