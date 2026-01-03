# Deployment Strategy & Build Pipeline

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DEVELOPMENT ENVIRONMENT                            │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                      │
│  │   Code      │ →  │   Build     │ →  │   Test      │                      │
│  │   (Local)   │    │  (x86/ARM)  │    │ (Emulator)  │                      │
│  └─────────────┘    └─────────────┘    └─────────────┘                      │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │ Push
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CI/CD PIPELINE                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   GitHub    │ →  │   Build     │ →  │    Test     │ →  │   Publish   │  │
│  │   Actions   │    │ ARM64 Image │    │   on Jetson │    │    to       │  │
│  │             │    │             │    │   (Self-    │    │   Registry  │  │
│  │             │    │             │    │   hosted)   │    │             │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │ OTA Update
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRODUCTION JETSON DEVICES                          │
│  ┌──────────────────────┐    ┌──────────────────────┐                       │
│  │   Jetson Device 1    │    │   Jetson Device N    │                       │
│  │   ┌──────────────┐   │    │   ┌──────────────┐   │                       │
│  │   │  Container   │   │    │   │  Container   │   │                       │
│  │   │  Runtime     │   │    │   │  Runtime     │   │                       │
│  │   └──────────────┘   │    │   └──────────────┘   │                       │
│  └──────────────────────┘    └──────────────────────┘                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Container Strategy

### Base Images (from NVIDIA NGC)
```dockerfile
# Option 1: Full JetPack base (largest, most compatible)
FROM nvcr.io/nvidia/l4t-jetpack:r36.4.0

# Option 2: NanoLLM pre-built (VLM ready)
FROM dustynv/nano_llm:r36.4.0

# Option 3: DeepStream (video pipeline ready)
FROM nvcr.io/nvidia/deepstream-l4t:8.0
```

### MVP Dockerfile
```dockerfile
# Build stage
FROM dustynv/nano_llm:r36.4.0 AS base

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# API server
EXPOSE 8080

# WebRTC
EXPOSE 8554
EXPOSE 8555

CMD ["python3", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Docker Compose (Development)
```yaml
version: '3.8'

services:
  mvp-api:
    build: .
    runtime: nvidia
    ports:
      - "8080:8080"   # REST API
      - "8554:8554"   # WebRTC signaling
      - "8555:8555"   # WebRTC media
    volumes:
      - ./config:/app/config
      - /tmp/argus_socket:/tmp/argus_socket  # CSI camera access
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - MODEL_NAME=Efficient-Large-Model/VILA1.5-3b
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]
```

---

## Build Pipeline (GitHub Actions)

### `.github/workflows/build-deploy.yml`
```yaml
name: Build and Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Set up QEMU (for ARM64)
        uses: docker/setup-qemu-action@v3

      - name: Login to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build ARM64 image
        uses: docker/build-push-action@v5
        with:
          context: .
          platforms: linux/arm64
          push: ${{ github.event_name != 'pull_request' }}
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  test-on-jetson:
    needs: build
    runs-on: self-hosted  # Jetson device as runner
    if: github.event_name != 'pull_request'
    steps:
      - name: Pull latest image
        run: |
          docker pull ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}

      - name: Run smoke tests
        run: |
          docker run --rm --runtime nvidia \
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }} \
            python3 -m pytest tests/smoke/ -v

      - name: Run inference benchmark
        run: |
          docker run --rm --runtime nvidia \
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }} \
            python3 scripts/benchmark.py --quick
```

---

## OTA Update Strategy

### Option A: Pull-Based (Simple)
```bash
# On Jetson device (cron or systemd timer)
docker pull ghcr.io/myorg/mvp-video-vlm:latest
docker-compose up -d --force-recreate
```

### Option B: Push-Based (AWS Greengrass)
```
┌─────────────┐     ┌─────────────────┐     ┌─────────────┐
│   GitHub    │ →   │  AWS Greengrass │ →   │   Jetson    │
│   Actions   │     │     Cloud       │     │   Devices   │
└─────────────┘     └─────────────────┘     └─────────────┘
```
- Automatic rollback on failure
- Device authentication
- Deployment groups (canary → production)

### Option C: NVIDIA OTA (JetPack Native)
```bash
# A/B partition update (failsafe)
# Device boots from partition A, updates B
# Swap on next boot, auto-rollback if fails
sudo nv_update_engine --apply /path/to/update.tar.gz
```

### Recommended: Option A for MVP, Option B for Production
- MVP: Simple docker-compose with cron-based pulls
- Production: AWS Greengrass for fleet management and rollback

---

## Local Development Workflow

### Prerequisites
```bash
# 1. Jetson device with JetPack 6.2+
# 2. Docker + NVIDIA Container Runtime
# 3. Git

# Verify NVIDIA runtime
docker run --rm --runtime nvidia nvidia-smi
```

### Quick Start
```bash
# Clone repository
git clone https://github.com/myorg/mvp-video-vlm.git
cd mvp-video-vlm

# Start development stack
docker-compose -f docker-compose.dev.yml up

# API available at http://localhost:8080
# WebRTC at http://localhost:8554
```

### Hot Reload (Development)
```yaml
# docker-compose.dev.yml
services:
  mvp-api:
    volumes:
      - ./src:/app/src:ro  # Mount source for hot reload
    command: uvicorn src.main:app --reload --host 0.0.0.0 --port 8080
```

---

## Testing Strategy

### Test Pyramid
```
          ┌───────────┐
          │   E2E     │  Few: Full pipeline, WebRTC
          │           │
       ┌──┴───────────┴──┐
       │   Integration   │  Some: API + VLM, Video + Detection
       │                 │
    ┌──┴─────────────────┴──┐
    │      Unit Tests       │  Many: Pure functions, utilities
    │                       │
    └───────────────────────┘
```

### Test Commands
```bash
# Unit tests (fast, no GPU needed)
pytest tests/unit/ -v

# Integration tests (requires GPU)
pytest tests/integration/ -v --gpu

# E2E smoke test (on Jetson)
pytest tests/e2e/ -v --jetson

# Benchmark suite
python scripts/benchmark.py --full
```

### CI Test Matrix
| Test Type | Where | When |
|-----------|-------|------|
| Unit | GitHub Actions (x86) | Every PR |
| Integration | Self-hosted Jetson | Merge to main |
| E2E | Self-hosted Jetson | Release tags |
| Benchmark | Self-hosted Jetson | Weekly |

---

## Deployment Checklist

### Pre-Deployment
- [ ] All tests passing on Jetson runner
- [ ] Benchmark meets latency targets (<200ms video, <500ms VLM)
- [ ] Docker image size acceptable (<15GB)
- [ ] Memory usage under 32GB (leave headroom)
- [ ] Config validated for target cameras

### Deployment
- [ ] Pull new image on target device
- [ ] Stop existing containers gracefully
- [ ] Start new containers
- [ ] Verify health endpoint responds
- [ ] Verify video streams connecting
- [ ] Run smoke tests

### Post-Deployment
- [ ] Monitor logs for 15 minutes
- [ ] Check memory/GPU utilization stable
- [ ] Verify latency metrics
- [ ] Test alert delivery

---

## Rollback Procedure

```bash
# Quick rollback to previous version
docker-compose down
docker tag ghcr.io/myorg/mvp-video-vlm:previous ghcr.io/myorg/mvp-video-vlm:latest
docker-compose up -d

# Or use explicit version
docker-compose pull ghcr.io/myorg/mvp-video-vlm:v1.0.0
docker-compose up -d
```

---

## Monitoring

### Health Endpoint
```python
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "gpu_memory_used": get_gpu_memory(),
        "streams_active": len(active_streams),
        "vlm_loaded": vlm_model is not None,
        "uptime_seconds": get_uptime()
    }
```

### Key Metrics to Monitor
| Metric | Alert Threshold |
|--------|-----------------|
| GPU Memory | >90% |
| CPU Usage | >80% |
| Inference Latency (P99) | >300ms |
| Stream Disconnects | >3/hour |
| VLM Errors | >1% |

---

*Deployment Pipeline - January 2026*
