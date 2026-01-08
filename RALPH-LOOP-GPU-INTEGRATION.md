# RALPH-LOOP: GPU Integration for Newport Demo

> **Purpose:** Guide the GPU integration phase - connecting the MVP frontend/backend to actual GPU-accelerated inference on Jetson AGX Thor.

---

## Instructions for Ralph-Loop

### On Each Iteration:

1. **Read this file first** - Understand current state before taking action
2. **Update the State Diagram** - Mark completed items with `[x]`, in-progress with `[~]`
3. **Update Proven Solutions** - Document GPU-specific solutions
4. **Check hardware prerequisites** - Verify GPU access before testing
5. **Test incrementally** - Validate each layer before moving up the stack

### File Structure Rules:

| Section | Rule |
|---------|------|
| **Immutable** | Progress tracking only - never remove completed items |
| **Mutable** | Active work - update tasks, add/remove as needed |
| **Proven Solutions** | GPU-specific knowledge - only add, never remove |

---

## Project Context

**Previous Phase:** MVP Development (RALPH-LOOP.md) - COMPLETE
- All UI/API/persistence features implemented
- Mock VLM responses working
- WebSocket real-time updates working
- Detection fast-path (missing/fall) implemented

**This Phase:** GPU Integration
- Connect to real NVIDIA GPU via containers
- Enable actual VLM inference with nano_llm
- Enable DeepStream video pipeline with nvinfer
- Verify end-to-end flow on Jetson Thor

**Target Hardware:** NVIDIA Jetson AGX Thor Developer Kit (L4T R38.2.2)

---

## Hardware Prerequisites

### Current System (Verified)

| Component | Value | Status |
|-----------|-------|--------|
| **Device** | NVIDIA Jetson AGX Thor Developer Kit | ✅ |
| **L4T Version** | R38.2.2 | ✅ |
| **Kernel** | 6.8.12-tegra | ✅ |
| **GPU Memory** | Unified (shared with system RAM) | ✅ |

### Software Prerequisites

| Component | Version | Verification Command |
|-----------|---------|---------------------|
| **L4T** | R38.2.2 | `cat /etc/nv_tegra_release` |
| **Docker** | 24.0+ | `docker --version` |
| **NVIDIA Container Toolkit** | Installed | `nvidia-container-cli --version` |
| **Docker Compose** | 2.20+ | `docker compose version` |

### Container Image Compatibility (CRITICAL)

**L4T R38 requires R38-compatible container images.** The existing images are for R36:

| Container | Current Image (R36) | Needed for R38 |
|-----------|---------------------|----------------|
| **DeepStream** | `nvcr.io/nvidia/deepstream-l4t:8.0-samples-multiarch` | Check NGC for R38-compatible |
| **VLM** | `dustynv/nano_llm:r36.4.0` | `dustynv/nano_llm:r38.x.x` |

**Action Required:** Update Dockerfiles to use R38-compatible base images.

### Verification Commands

```bash
# Check L4T version (should show R38.2.2)
cat /etc/nv_tegra_release

# Check device model
cat /proc/device-tree/model

# Verify GPU is accessible
tegrastats  # Note: nvidia-smi doesn't work on Jetson

# Test Docker NVIDIA runtime
docker run --rm --gpus all nvcr.io/nvidia/l4t-base:r38.2.2 nvidia-smi || echo "Use tegrastats instead"

# Check available Docker images
docker images | grep -E "(dustynv|deepstream|nano|l4t)"
```

---

## Current State Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    GPU INTEGRATION STATE (Thor R38.2.2)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  LAYER 0: R38 CONTAINER COMPATIBILITY                                       │
│  ══════════════════════════════════════                                     │
│  [x] Find R38-compatible DeepStream image on NGC (DS 8.0 works!)            │
│  [~] Build R38-compatible VLM image (vila via jetson-containers)            │
│  [ ] Update deepstream/Dockerfile for R38                                   │
│  [ ] Update vlm/Dockerfile for R38                                          │
│  [x] Verify pyds wheel exists for R38/Python version (included in DS 8.0)   │
│                                                                              │
│  LAYER 1: HARDWARE & RUNTIME                                                │
│  ═══════════════════════════                                                │
│  [x] Jetson Thor hardware accessible                                        │
│  [x] L4T R38.2.2 installed                                                  │
│  [ ] NVIDIA Container Toolkit configured for R38                            │
│  [ ] Docker runtime=nvidia working with R38 images                          │
│                                                                              │
│  LAYER 2: CONTAINER IMAGES (R38)                                            │
│  ═══════════════════════════════                                            │
│  [ ] DeepStream R38-compatible image built                                  │
│  [ ] dustynv/nano_llm R38 image pulled                                      │
│  [ ] App container built (no GPU dependency)                                │
│  [ ] All images tested with GPU access on Thor                              │
│                                                                              │
│  LAYER 3: DEEPSTREAM PIPELINE                                               │
│  ════════════════════════════                                               │
│  [ ] TensorRT engine builds successfully on Thor                            │
│  [ ] RTSP stream connects and decodes                                       │
│  [ ] nvinfer runs person detection                                          │
│  [ ] Frames saved to /shared/frames                                         │
│  [ ] Detections published to Redis                                          │
│                                                                              │
│  LAYER 4: VLM INFERENCE                                                     │
│  ══════════════════════                                                     │
│  [ ] VILA model downloads (~15GB)                                           │
│  [ ] nano_llm imports successfully on R38                                   │
│  [ ] Model loads into GPU memory                                            │
│  [ ] Image+prompt inference works                                           │
│  [ ] Classification output formatted correctly                              │
│                                                                              │
│  LAYER 5: END-TO-END FLOW                                                   │
│  ════════════════════════                                                   │
│  [ ] RTSP → DeepStream → detections Redis channel                           │
│  [ ] Detections → VLM → summaries Redis channel                             │
│  [ ] Summaries → App → WebSocket → Browser                                  │
│  [ ] Q&A queries → VLM → responses                                          │
│  [ ] Full demo runs 30+ minutes stable                                      │
│                                                                              │
│  GPU MEMORY ALLOCATION (Thor has more headroom)                             │
│  ══════════════════════════════════════════════                             │
│  [ ] DeepStream: ~2GB (TensorRT engine)                                     │
│  [ ] VLM (VILA-3B q4): ~8GB                                                 │
│  [ ] Frame buffer: ~500MB                                                   │
│  [ ] Total: <12GB (Thor has 64GB+ unified memory)                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

Legend: [x] Complete  [~] Partial/In-Progress  [ ] Not Started
```

---

## Immutable: Completed Work (Progress Updates Only)

> **Rule:** Only add to this section. Never remove items. Mark completion dates.

### Prerequisites from MVP Phase ✅
- [x] docker-compose.yml with runtime: nvidia configured
- [x] DeepStream Dockerfile with pyds + python3-gi
- [x] VLM Dockerfile extending dustynv/nano_llm
- [x] NanoLLMWrapper class with load() and describe()/classify() methods
- [x] VLMSubscriber Redis integration
- [x] DeepStream pipeline with frame extraction
- [x] Detection publishing to Redis
- [x] App WebSocket forwarding

---

## Mutable: Active Tasks (Update as Work Progresses)

> **Rule:** Update freely. Check off completed items, add new discoveries, reprioritize as needed.

### Priority 0: R38 Container Compatibility (BLOCKER)

> **CRITICAL:** Current Dockerfiles use R36 base images which are incompatible with Thor's R38.2.2.
> Must resolve before any GPU testing can proceed.

#### P0.1 Research R38-Compatible Images
- [ ] Check NGC for DeepStream R38 images:
  ```bash
  # Browse: https://catalog.ngc.nvidia.com/orgs/nvidia/containers/deepstream-l4t
  # Look for tags containing "r38" or compatible with JetPack 6.2+
  ```
- [ ] Check dustynv for R38 nano_llm images:
  ```bash
  # Browse: https://hub.docker.com/r/dustynv/nano_llm/tags
  # Look for r38.x.x tags
  docker pull dustynv/nano_llm:r38.2.2 2>/dev/null || echo "Check available tags"
  ```
- [ ] Check pyds wheel availability for R38:
  ```bash
  # Browse: https://github.com/NVIDIA-AI-IOT/deepstream_python_apps/releases
  # Need wheel matching: Python 3.x + aarch64 + DeepStream version for R38
  ```

#### P0.2 Update Dockerfiles for R38
- [ ] Update `vlm/Dockerfile`:
  ```dockerfile
  # Change FROM line to R38-compatible image
  # FROM dustynv/nano_llm:r36.4.0  # OLD
  FROM dustynv/nano_llm:r38.x.x    # NEW (find exact tag)
  ```
- [ ] Update `deepstream/Dockerfile`:
  ```dockerfile
  # Change FROM line to R38-compatible image
  # FROM nvcr.io/nvidia/deepstream-l4t:8.0-samples-multiarch  # OLD
  FROM nvcr.io/nvidia/deepstream-l4t:X.X-samples-multiarch    # NEW (find R38 version)
  ```
- [ ] Update pyds wheel URL in deepstream/Dockerfile to match new DeepStream version

#### P0.3 Alternative: Build from L4T Base
If no pre-built R38 images exist:
- [ ] Consider building from `nvcr.io/nvidia/l4t-base:r38.2.2`
- [ ] Install DeepStream SDK manually
- [ ] Install nano_llm from source

### Priority 1: Hardware Setup (After P0)

#### P1.1 Thor Environment Verification
- [x] Verify L4T version: `cat /etc/nv_tegra_release`
  - Confirmed: `# R38 (release), REVISION: 2.2`
- [x] Verify device: `cat /proc/device-tree/model`
  - Confirmed: `NVIDIA Jetson AGX Thor Developer Kit`
- [ ] Verify GPU with tegrastats: `tegrastats`
- [ ] Check Docker: `docker --version`
- [ ] Test NVIDIA runtime with R38 base:
  ```bash
  docker run --rm --gpus all nvcr.io/nvidia/l4t-base:r38.2.2 cat /etc/nv_tegra_release
  ```

#### P1.2 Configure Project
- [ ] Set environment variables:
  ```bash
  export RTSP_URI="rtsp://YOUR_CAMERA_IP:554/stream"
  export VLM_MODEL="Efficient-Large-Model/VILA1.5-3b"
  ```

### Priority 2: Container Verification (After P0 & P1)

#### P2.1 Build R38 Container Images
- [ ] Build DeepStream container (after Dockerfile updated):
  ```bash
  docker compose build deepstream
  ```
- [ ] Build/Pull VLM container (after Dockerfile updated):
  ```bash
  docker compose build vlm
  ```
- [ ] Build app container (no R38 dependency):
  ```bash
  docker compose build app
  ```

#### P2.2 Test Container GPU Access on Thor
- [ ] Test DeepStream container GPU:
  ```bash
  docker compose run --rm deepstream python3 -c "import pyds; print('pyds OK')"
  ```
- [ ] Test VLM container GPU:
  ```bash
  docker compose run --rm vlm python3 -c "import nano_llm; print('nano_llm OK')"
  ```
- [ ] Test VLM model loading:
  ```bash
  docker compose run --rm vlm python3 -c "
  from nano_llm import NanoLLM
  model = NanoLLM.from_pretrained('Efficient-Large-Model/VILA1.5-3b', quantization='q4f16_ft')
  print('Model loaded!')
  "
  ```

### Priority 3: DeepStream Pipeline (After P2)

#### P3.1 First Run (TensorRT Build)
- [ ] Start DeepStream with test RTSP source:
  ```bash
  RTSP_URI="rtsp://test-camera:554/stream" docker compose up deepstream
  ```
- [ ] Monitor TensorRT engine build (time varies by model):
  - Watch logs: `docker compose logs -f deepstream`
  - Look for: "Building TensorRT Engine..."
  - Complete when: "Pipeline is running"
- [ ] Verify engine cached (path depends on DeepStream version):
  ```bash
  docker compose exec deepstream find /opt -name "*.engine" 2>/dev/null
  ```

#### P3.2 Detection Verification
- [ ] Check Redis for detection messages:
  ```bash
  docker compose exec redis redis-cli SUBSCRIBE detections
  ```
- [ ] Verify frame files exist:
  ```bash
  docker compose exec app ls -la /shared/frames/stream_0/
  ```
- [ ] Confirm detection format includes:
  - `stream_id`
  - `frame_path`
  - `detections[]` with `class_id`, `bbox`, `confidence`

### Priority 4: VLM Inference Integration

#### P4.1 Enable Real VLM Inference
- [ ] Modify `vlm/src/vlm_subscriber.py` - remove mock fallback:
  - File: `vlm/src/vlm_subscriber.py:125-127`
  - Current: Returns mock response if model not loaded
  - Change: Require model to be loaded, fail if not

- [ ] Test VLM inference standalone:
  ```bash
  docker compose exec vlm python3 -c "
  from PIL import Image
  from nano_llm import NanoLLM

  model = NanoLLM.from_pretrained('Efficient-Large-Model/VILA1.5-3b', quantization='q4f16_ft')
  img = Image.open('/shared/frames/stream_0/latest.jpg')
  response = model.generate('Describe what you see in this image.', image=img)
  print(response)
  "
  ```

#### P4.2 Protocol Classification Testing
- [ ] Test classification prompt format:
  ```bash
  docker compose exec vlm python3 -c "
  from PIL import Image
  from nano_llm import NanoLLM

  model = NanoLLM.from_pretrained('Efficient-Large-Model/VILA1.5-3b', quantization='q4f16_ft')
  img = Image.open('/shared/frames/stream_0/latest.jpg')

  prompt = '''Analyze this image and classify the situation.

  User's protocols:
  - GREEN (safe): Reading, watching TV, sleeping normally, eating meals, sitting calmly
  - YELLOW (attention): Out of camera view, crouching in corners, minor injuries
  - RED (critical): Unconscious on ground, severe injury, room is empty

  Respond with EXACTLY this format (one line):
  SEVERITY|ICON|MESSAGE

  Where SEVERITY is GREEN, YELLOW, or RED.
  ICON is one word: reading, tv, sleeping, eating, calm, exercise, unclear, injury, distress, pacing, emergency, missing, danger, unconscious
  MESSAGE is a brief one-sentence status.
  '''

  response = model.generate(prompt, image=img, max_new_tokens=50)
  print(repr(response))
  "
  ```

- [ ] Verify response format: `SEVERITY|ICON|MESSAGE`

#### P4.3 VLM Performance Tuning
- [ ] Measure inference latency:
  ```python
  import time
  start = time.time()
  response = model.generate(prompt, image=img, max_new_tokens=50)
  print(f"Inference time: {time.time() - start:.2f}s")
  ```
  - Target: < 1 second per inference
- [ ] Adjust quantization if needed:
  - `q4f16_ft` (default, ~8GB) - fastest
  - `fp16` (~12GB) - more accurate
- [ ] Adjust `max_new_tokens` if responses truncated

### Priority 5: End-to-End Testing

#### P5.1 Full Stack Launch
- [ ] Start all services:
  ```bash
  make dev
  # or: docker compose up -d
  ```
- [ ] Verify all containers healthy:
  ```bash
  make status
  # All should show "healthy" or "running"
  ```

#### P5.2 Browser Verification
- [ ] Open browser to `http://JETSON_IP:8080`
- [ ] Verify WebSocket connects (green indicator)
- [ ] Verify feed cards show real status updates
- [ ] Verify status descriptions change based on scene
- [ ] Test Q&A: Ask "What is the person doing?"

#### P5.3 Stability Testing
- [ ] Run for 30+ minutes continuously
- [ ] Monitor GPU memory: `tegrastats`
- [ ] Monitor for:
  - Memory leaks (increasing GPU/RAM usage)
  - WebSocket disconnections
  - VLM inference failures
  - Frame buffer overflow

### Priority 6: Performance Optimization

#### P6.1 GPU Memory Optimization
- [ ] Monitor GPU memory during operation:
  ```bash
  watch -n 1 tegrastats
  ```
- [ ] If memory pressure:
  - Reduce VLM batch size
  - Increase VLM sampling interval
  - Reduce frame resolution

#### P6.2 Latency Optimization
- [ ] Measure end-to-end latency:
  - Frame capture → Detection → VLM → Browser
  - Target: < 5 seconds
- [ ] Tune `SAMPLE_INTERVAL` in DeepStream (default: 30 frames)
- [ ] Tune VLM sampling interval (default: 10 seconds per stream)

---

## Discovered Unknowns

> Add blockers and new requirements here as they emerge during integration

- [x] **RESOLVED:** DeepStream 8.0 works on Thor R38.2.2
  - Tested: `docker run --rm --runtime=nvidia nvcr.io/nvidia/deepstream-l4t:8.0-samples-multiarch python3 -c "import torch; print(torch.cuda.is_available())"`
  - CUDA 13.0 + Python 3.12.3 confirmed working
- [~] **IN PROGRESS:** nano_llm R38 image - building via jetson-containers
  - Pre-built dustynv/nano_llm only has r36.4.0 (incompatible - CUDA error 801)
  - jetson-containers `build nano_llm` has infinite recursion bug (llvm:21 dependency)
  - **SOLUTION:** Building `vila` package instead (includes VILA model support without nano_llm wrapper)
  - Build command: `jetson-containers build vila`
  - **BUILD PROGRESS (2026-01-07 23:21):** Stage 9/27 (PyTorch 2.10) - 64% of CUDA kernels compiled (2207/3468)
  - Stages 1-8 cached: build-essential, pip_cache, cuda_13.0, cudastack, python, numpy, cmake, onnx
  - Monitor: `tail -f /tmp/vila-build.log`
- [x] **RESOLVED:** DeepStream 8.0 is for L4T R38 (confirmed working)
- [ ] **TBD:** pyds wheel for R38/Python 3.12 combination (included in DS 8.0 image)
- [ ] **TBD:** Actual VLM inference latency on Thor
- [ ] **TBD:** GPU memory with both containers running simultaneously
- [ ] **TBD:** RTSP reconnection behavior on network interruption

---

## Proven Solutions

> **Rule:** Document GPU-specific solutions here as they are discovered.

### Template: Add New Solutions

```markdown
### {{Solution Title}}

**Problem:** {{What was the issue?}}

**Solution:**
\`\`\`{{language}}
{{Code or configuration}}
\`\`\`

**Key insight:** {{Why this works / what to remember}}
```

---

### L4T R38 Container Compatibility (CRITICAL)

**Problem:** Container images built for L4T R36 don't work on R38 systems (Thor).

**Why this matters:**
- CUDA libraries inside container must match host L4T version
- TensorRT engines are not portable across L4T versions
- Python bindings (pyds, nano_llm) link against specific CUDA versions

**Solution:** Use R38-compatible base images:
```dockerfile
# VLM container - find R38 tag
FROM dustynv/nano_llm:r38.x.x  # Check Docker Hub for exact tag

# DeepStream container - find R38-compatible version
FROM nvcr.io/nvidia/deepstream-l4t:X.X-samples-multiarch  # Check NGC
```

**Research URLs:**
- NGC DeepStream: https://catalog.ngc.nvidia.com/orgs/nvidia/containers/deepstream-l4t
- dustynv nano_llm: https://hub.docker.com/r/dustynv/nano_llm/tags
- dustynv jetson-containers: https://github.com/dusty-nv/jetson-containers

**Key insight:** Always match container L4T version to host L4T version. Mixing versions causes cryptic CUDA/TensorRT errors.

---

### NVIDIA Container Runtime Configuration

**Problem:** Containers don't have GPU access.

**Solution:** Ensure `/etc/docker/daemon.json` includes:
```json
{
    "runtimes": {
        "nvidia": {
            "path": "nvidia-container-runtime",
            "runtimeArgs": []
        }
    },
    "default-runtime": "nvidia"
}
```

Then restart Docker:
```bash
sudo systemctl restart docker
```

**Key insight:** On Jetson, `nvidia` should be the default runtime since there's no CPU-only mode that makes sense.

---

### nano_llm Model Loading

**Problem:** First model load takes 10+ minutes and downloads ~15GB.

**Solution:** Use persistent volume for model cache:
```yaml
# docker-compose.yml
vlm:
  volumes:
    - model_cache:/root/.cache

volumes:
  model_cache:  # Persists across container restarts
```

**Key insight:** The `model_cache` volume stores HuggingFace models and TensorRT engine caches. First run is slow, subsequent runs are fast.

---

### DeepStream TensorRT Engine Caching

**Problem:** TensorRT engine rebuild on every container restart.

**Solution:** Mount persistent volume for engine cache:
```yaml
deepstream:
  volumes:
    - ds_engine_cache:/opt/nvidia/deepstream/deepstream-X.X/samples/models
    # Note: Path varies by DeepStream version - check actual path in container
```

**Key insight:** Engine files (`.engine`) are specific to:
- GPU model (Thor vs Orin vs Xavier)
- TensorRT version
- L4T version (R38 engines incompatible with R36)
- Model configuration

Rebuilds are needed when GPU, TensorRT, or L4T version changes.

---

### GPU Memory Monitoring on Jetson

**Problem:** `nvidia-smi` doesn't work on Jetson (no discrete GPU).

**Solution:** Use `tegrastats` or read sysfs:
```bash
# Real-time monitoring
tegrastats

# Programmatic reading
cat /sys/kernel/debug/nvmap/iovmm/maps | grep total

# In Python
import subprocess
result = subprocess.run(['tegrastats', '--interval', '1000'], capture_output=True, timeout=2)
```

**Key insight:** Jetson uses unified memory - GPU and CPU share the same RAM. "GPU memory" is just a portion of system RAM allocated for GPU operations.

---

## Quick Commands Reference

```bash
# === THOR VERIFICATION ===
cat /etc/nv_tegra_release        # Check L4T version (should show R38.2.2)
cat /proc/device-tree/model      # Confirm Thor device
tegrastats                        # Monitor GPU/CPU/memory (NOT nvidia-smi)
jtop                              # Interactive monitor (install: pip install jetson-stats)

# === R38 IMAGE RESEARCH ===
# Check NGC for DeepStream R38 images:
# https://catalog.ngc.nvidia.com/orgs/nvidia/containers/deepstream-l4t
# Check dustynv for nano_llm R38:
# https://hub.docker.com/r/dustynv/nano_llm/tags

# === CONTAINER MANAGEMENT ===
make dev                          # Start full stack (AFTER R38 images configured)
make stop                         # Stop all containers
make status                       # Check container health
make logs                         # Follow all logs
make logs-vlm                     # Follow VLM logs
make logs-ds                      # Follow DeepStream logs

# === DEBUGGING ===
make shell-vlm                    # Shell into VLM container
make shell-ds                     # Shell into DeepStream container
make redis-cli                    # Redis CLI

# === TESTING (AFTER R38 IMAGES READY) ===
docker compose exec vlm python3 -c "import nano_llm"      # Test nano_llm import
docker compose exec deepstream python3 -c "import pyds"   # Test pyds import

# === REDIS MONITORING ===
docker compose exec redis redis-cli SUBSCRIBE detections  # Watch detections
docker compose exec redis redis-cli SUBSCRIBE summaries   # Watch VLM summaries

# === GPU MEMORY (Thor unified memory) ===
tegrastats  # Shows RAM/GPU memory usage
# Or from inside container:
docker compose exec vlm python3 -c "
import torch
if torch.cuda.is_available():
    print(f'CUDA available, device: {torch.cuda.get_device_name(0)}')
    print(f'GPU Memory: {torch.cuda.memory_allocated()/1e9:.1f}GB')
"
```

---

## Success Criteria Checklist

| Criterion | Target | Status |
|-----------|--------|--------|
| Thor hardware accessible | Direct access confirmed | ✅ |
| L4T version correct | R38.2.2 | ✅ |
| R38 DeepStream image found | Compatible base image identified | ⬜ |
| R38 nano_llm image found | Compatible base image identified | ⬜ |
| Dockerfiles updated for R38 | Both containers build | ⬜ |
| NVIDIA runtime working | Container GPU test passes | ⬜ |
| DeepStream TensorRT builds | Engine created successfully | ⬜ |
| DeepStream detections | Redis receives detection messages | ⬜ |
| VLM model loads | nano_llm.from_pretrained succeeds | ⬜ |
| VLM inference works | Image classification returns valid format | ⬜ |
| End-to-end flow | Browser shows real VLM status | ⬜ |
| Latency acceptable | < 5 seconds camera to browser | ⬜ |
| Stability | 30 minute continuous operation | ⬜ |
| GPU memory stable | No memory growth over time | ⬜ |

Status legend: ✅ Done | ⬜ Not started | 🔄 In progress

---

## Container Configuration Reference

### Current Dockerfile Base Images (NEED UPDATE FOR R38)

| Container | Current (R36) | Needs R38 Equivalent |
|-----------|---------------|----------------------|
| **deepstream** | `nvcr.io/nvidia/deepstream-l4t:8.0-samples-multiarch` | TBD - check NGC |
| **vlm** | `dustynv/nano_llm:r36.4.0` | TBD - check Docker Hub |
| **app** | `python:3.11-slim` | No change needed |

### docker-compose.yml GPU Settings

```yaml
deepstream:
  runtime: nvidia                          # Use NVIDIA runtime
  environment:
    - NVIDIA_VISIBLE_DEVICES=all           # Access all GPUs
  # ...

vlm:
  runtime: nvidia
  environment:
    - NVIDIA_VISIBLE_DEVICES=all
  # ...
```

### Key Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RTSP_URI` | `rtsp://192.168.1.100:8554/webcam` | RTSP stream URL |
| `STREAM_ID` | `stream_0` | Identifier for this stream |
| `SAMPLE_INTERVAL` | `30` | Frames between detections |
| `VLM_MODEL` | `Efficient-Large-Model/VILA1.5-3b` | VLM model name |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection |

### Volume Mounts

| Volume | Purpose | Persistence |
|--------|---------|-------------|
| `model_cache` | VLM model weights | Persistent |
| `ds_engine_cache` | TensorRT engines | Persistent |
| `frame_buffer` | Shared frames (tmpfs) | Ephemeral |
| `config_data` | SQLite database | Persistent |

---

*Last Updated: 2026-01-07 23:21*
*Phase: GPU Integration*
*Target: Jetson AGX Thor (L4T R38.2.2)*
*Previous: MVP Development (RALPH-LOOP.md)*
*Status: IN PROGRESS - Building vila container (Stage 9/27 PyTorch - 64%)*
