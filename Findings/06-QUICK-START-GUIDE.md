# Quick Start Guide: MVP Development

## Prerequisites

### Hardware
- NVIDIA Jetson AGX Orin 64GB Developer Kit (recommended)
- OR Jetson Orin Nano Super 8GB (budget option)
- Power supply (included with dev kit)
- NVMe SSD (256GB+ recommended for model storage)
- Ethernet or WiFi connection
- Test camera (USB, CSI, or RTSP IP camera)

### Software
- JetPack 6.2+ installed via SDK Manager
- Git, Docker, and docker-compose

---

## Phase 1: Environment Setup (Day 1)

### 1.1 Flash JetPack
```bash
# On host machine, use SDK Manager
# Download from: https://developer.nvidia.com/sdk-manager
# Select JetPack 6.2 or later
# Flash to your Jetson device
```

### 1.2 Initial System Configuration
```bash
# On Jetson device
sudo apt update && sudo apt upgrade -y

# Enable max performance mode
sudo nvpmodel -m 0
sudo jetson_clocks

# Verify CUDA installation
nvcc --version
```

### 1.3 Install jetson-containers
```bash
git clone https://github.com/dusty-nv/jetson-containers
cd jetson-containers
bash install.sh
```

---

## Phase 2: Video Pipeline Validation (Day 2-3)

### 2.1 Test Camera Input
```bash
# USB camera test
gst-launch-1.0 v4l2src device=/dev/video0 ! videoconvert ! autovideosink

# RTSP camera test
gst-launch-1.0 rtspsrc location="rtsp://user:pass@camera-ip:554/stream" ! decodebin ! autovideosink

# CSI camera test (if using IMX camera)
gst-launch-1.0 nvarguscamerasrc ! 'video/x-raw(memory:NVMM),width=1920,height=1080' ! nvvidconv ! autovideosink
```

### 2.2 Run jetson-inference Detection Demo
```bash
cd jetson-containers
jetson-containers run $(autotag jetson-inference)

# Inside container
cd /jetson-inference/build/aarch64/bin
./detectnet /dev/video0
```

### 2.3 Test WebRTC Streaming
```bash
# In jetson-inference container
./detectnet --input-codec=h264 /dev/video0 webrtc://@:8554/output

# Open browser to: http://<jetson-ip>:8554
```

---

## Phase 3: VLM Integration (Day 4-7)

### 3.1 Run NanoLLM with VLM
```bash
cd jetson-containers

# Pull and run NanoLLM with VILA model
jetson-containers run $(autotag nano_llm) \
  python3 -m nano_llm.studio

# Access Agent Studio at http://<jetson-ip>:8050
```

### 3.2 Test Live VLM Query
```bash
# Run Live LLaVA demo
jetson-containers run $(autotag nano_llm) \
  python3 -m nano_llm.chat --model Efficient-Large-Model/VILA-7b \
  --prompt "Describe what you see" \
  --video-input /dev/video0
```

### 3.3 Simple Python VLM Integration
```python
# save as test_vlm.py
from nano_llm import NanoLLM
from nano_llm.plugins import VideoSource

# Load model
model = NanoLLM.from_pretrained("Efficient-Large-Model/VILA1.5-3b")

# Create video source
video = VideoSource("/dev/video0")

# Query frame
frame = video.capture()
response = model.generate(frame, "What is happening in this image?")
print(response)
```

---

## Phase 4: Build Custom Pipeline (Week 2)

### 4.1 Project Structure
```
mvp-video-vlm/
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── video.py
│   │   └── vlm.py
│   └── main.py
├── config/
│   └── default.yaml
└── requirements.txt
```

### 4.2 Minimal FastAPI Server
```python
# src/main.py
from fastapi import FastAPI, WebSocket
from fastapi.responses import StreamingResponse
import asyncio

app = FastAPI()

@app.get("/api/streams")
async def list_streams():
    return {"streams": ["camera-1"]}

@app.post("/api/streams/{stream_id}/query")
async def query_stream(stream_id: str, prompt: str):
    # Integrate with VLM here
    return {"response": "VLM response placeholder"}

@app.websocket("/ws/metadata")
async def metadata_websocket(websocket: WebSocket):
    await websocket.accept()
    while True:
        # Send detection metadata
        await websocket.send_json({"detections": []})
        await asyncio.sleep(0.1)
```

### 4.3 Docker Configuration
```dockerfile
# docker/Dockerfile
FROM dustynv/nano_llm:r36.4.0

WORKDIR /app
COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY src/ ./src/
CMD ["python3", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

---

## Phase 5: Latency Optimization (Week 3)

### 5.1 Benchmark Current Performance
```python
import time

start = time.perf_counter()
# ... inference code ...
end = time.perf_counter()
print(f"Inference latency: {(end-start)*1000:.2f}ms")
```

### 5.2 Optimization Checklist
```bash
# Enable max clocks
sudo jetson_clocks --show
sudo jetson_clocks

# Check power mode
sudo nvpmodel -q

# Monitor GPU usage
tegrastats
```

### 5.3 Model Optimization
```bash
# Convert to TensorRT (detection model)
trtexec --onnx=yolov8s.onnx --saveEngine=yolov8s.engine --fp16

# Use 4-bit quantized VLM
# Already optimized in NanoLLM for AWQ models
```

---

## Key Commands Reference

| Task | Command |
|------|---------|
| Check Jetson stats | `tegrastats` |
| GPU memory usage | `nvidia-smi` or `tegrastats` |
| Enable max performance | `sudo nvpmodel -m 0 && sudo jetson_clocks` |
| List cameras | `v4l2-ctl --list-devices` |
| Test RTSP stream | `ffprobe rtsp://...` |
| Run NanoLLM | `jetson-containers run $(autotag nano_llm)` |
| Build TensorRT engine | `trtexec --onnx=model.onnx --saveEngine=model.engine` |

---

## Troubleshooting

### VLM runs out of memory
- Use smaller model (VILA-3B instead of 7B)
- Reduce batch size / output tokens
- Check for memory leaks with `tegrastats`

### Video latency too high
- Use hardware decode: `nvv4l2decoder` in GStreamer
- Reduce resolution if not needed
- Check network latency for RTSP sources

### WebRTC not connecting
- Check firewall: ports 8554, 8555 (WebRTC)
- Verify STUN/TURN for non-local networks
- Test with Chrome/Chromium first

### Detection accuracy issues
- Verify model input resolution
- Check preprocessing (normalize, resize)
- Try different model variants

---

## Resources

- **Jetson AI Lab**: https://www.jetson-ai-lab.com/
- **NanoLLM Docs**: https://dusty-nv.github.io/NanoLLM/
- **DeepStream Docs**: https://docs.nvidia.com/metropolis/deepstream/
- **jetson-containers**: https://github.com/dusty-nv/jetson-containers
- **NVIDIA Forums**: https://forums.developer.nvidia.com/c/agx-autonomous-machines/jetson-embedded-systems/

---

*Last Updated: January 2026*
