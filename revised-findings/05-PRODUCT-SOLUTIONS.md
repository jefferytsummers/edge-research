# Product-Ready Jetson Software Solutions

## NVIDIA First-Party Solutions

### Jetson Platform Services (JPS)
**Status:** Production-ready, included in JetPack 6.x+

Pre-built microservices for rapid edge AI development:

| Service | Description | API |
|---------|-------------|-----|
| **VLM AI Service** | VILA/LLaVA deployment with REST API | REST |
| **DeepStream AI Service** | Multi-stream detection (PeopleNet, YOLOv8) | REST |
| **Analytics Service** | Tripwire, ROI, counting | REST |
| **Video Storage Toolkit (VST)** | Camera discovery, RTSP/ONVIF, recording | REST |
| **Zero-Shot Detection (NanoOWL)** | OWL-ViT optimized, no training needed | REST |
| **Grounding DINO** | Open-vocabulary detection | REST |
| **SDR (Stream Discovery)** | Dynamic stream management | REST |
| **Redis Message Bus** | Inter-service communication | Pub/Sub |
| **API Gateway** | Unified access point | REST/gRPC |
| **System Monitoring** | Health, metrics, alerts | REST |

**Reference App: AI-NVR**
- Combines VST + DeepStream + Analytics
- Production-ready video recording + AI inference
- Web UI included

```bash
# Quick start
sudo apt install nvidia-jetson-services
sudo systemctl start jetson-ai-nvr
# Access at http://localhost:80
```

---

### NanoLLM
**Status:** Production-ready for VLM inference

Lightweight LLM/VLM library optimized for Jetson:
- 4-bit AWQ quantization
- TensorRT vision encoder acceleration
- Streaming output
- Agent Studio (web UI for testing)

**Supported VLMs:**
| Model | Parameters | Memory | Speed |
|-------|------------|--------|-------|
| VILA 1.5-3B | 3B | ~4GB | Fastest |
| VILA 1.5-7B | 7B | ~8GB | Balanced |
| LLaVA 1.6-7B | 7B | ~8GB | Balanced |
| Qwen2.5-VL-7B | 7B | ~8GB | Multilingual |
| Llama 3.2 Vision 11B | 11B | ~14GB | Largest |

```bash
# Deploy via container
jetson-containers run $(autotag nano_llm) \
  python3 -m nano_llm.studio
```

---

### DeepStream SDK 8.0
**Status:** Production-ready

GStreamer-based video analytics toolkit:
- Hardware-accelerated decode/encode
- 30+ simultaneous 1080p streams (AGX Orin)
- Built-in tracking (NvDCF, DeepSORT)
- TensorRT integration
- Output: RTSP, WebRTC, Kafka, file

```bash
# Container deployment
docker run --runtime nvidia -it \
  nvcr.io/nvidia/deepstream-l4t:8.0 \
  deepstream-app -c /opt/nvidia/deepstream/deepstream/samples/configs/deepstream-app/source4_1080p_dec_infer-resnet_tracker_sgie_tiled_display_int8.txt
```

---

### Triton Inference Server
**Status:** Production-ready on Jetson

Multi-framework model serving:
- TensorRT, ONNX, PyTorch backends
- Dynamic batching
- Model versioning
- **C-API for Jetson** (zero network overhead)

```bash
# Container deployment
docker run --runtime nvidia -p 8000:8000 -p 8001:8001 -p 8002:8002 \
  -v /models:/models \
  nvcr.io/nvidia/tritonserver:25.01-py3-jetson \
  tritonserver --model-repository=/models
```

---

### Holoscan SDK
**Status:** Production-ready for ultra-low-latency

Operator-based framework for sensor processing:
- <10ms pipeline latency achievable
- Same code: Jetson → data center
- Best for medical/industrial vision

```python
from holoscan.core import Application
from holoscan.operators import FormatConverterOp, InferenceOp

class MyApp(Application):
    def compose(self):
        source = VideoStreamReplayerOp(self, "source")
        inference = InferenceOp(self, "inference", model_path="model.onnx")
        sink = HolovizOp(self, "sink")
        self.add_flow(source, inference)
        self.add_flow(inference, sink)
```

---

## Third-Party Commercial Solutions

### Advantech MIC-717-OX
**Type:** AI-NVR Appliance

- Jetson Orin NX based
- Pre-integrated Metropolis Microservices
- iService cloud management
- OTA updates included
- **Target:** Retail, security

### e-con Systems Darsi Pro
**Type:** AI Compute Box (CES 2026)

- Up to 100 TOPS
- 8x GMSL camera support
- JetPack 6+ compatible
- Rugged industrial enclosure
- Cloud device management
- **Target:** Autonomous systems, industrial

### Seeed Studio reComputer
**Type:** Pre-configured Jetson Modules

- Orin Nano/NX/AGX variants
- Compact form factor
- Developer-friendly
- **Target:** Prototyping, small deployments

### RidgeRun
**Type:** Commercial GStreamer Components

- GstInference (TensorRT plugin)
- GstRtspSink (RTSP server)
- Professional support
- **Target:** Custom video pipelines

---

## Cloud/Fleet Management Solutions

### AWS Greengrass
**Jetson Support:** Official

- Container deployment to edge
- OTA updates with rollback
- Device shadows (twin)
- ML model deployment
- **Best for:** AWS-centric enterprises

### Allxon
**Type:** Device Management Platform

- JetPack OTA delivery
- Remote monitoring
- Multi-device management
- **Best for:** Fleet deployments

### Balena
**Type:** Container Fleet Management

- Git-based deployments
- Delta updates (bandwidth efficient)
- Multi-container support
- **Best for:** IoT fleets

---

## Container Ecosystem

### jetson-containers
**Repository:** github.com/dusty-nv/jetson-containers

Pre-built, validated containers:

| Container | Contents |
|-----------|----------|
| `nano_llm` | NanoLLM + VLM models |
| `jetson-inference` | Detection, segmentation, WebRTC |
| `deepstream` | DeepStream SDK |
| `tritonserver` | Triton Inference Server |
| `transformers` | HuggingFace + TensorRT |
| `ollama` | Ollama LLM server |
| `vllm` | vLLM inference engine |

```bash
# Quick deploy any container
jetson-containers run $(autotag nano_llm)
```

### NVIDIA NGC
Official container registry:

| Image | Description |
|-------|-------------|
| `nvcr.io/nvidia/l4t-jetpack:r36.4.0` | Base JetPack |
| `nvcr.io/nvidia/deepstream-l4t:8.0` | DeepStream |
| `nvcr.io/nvidia/tritonserver:25.01-py3-jetson` | Triton |

---

## Development Tools

### NVIDIA SDK Manager
- Flash JetPack to device
- Install CUDA, TensorRT, cuDNN
- Supports all Jetson devices

### Nsight Systems
- GPU profiling
- Timeline analysis
- Identify bottlenecks

### TensorRT
- Model optimization
- INT8/FP16 quantization
- Engine building

```bash
# Build optimized engine
trtexec --onnx=model.onnx --saveEngine=model.engine --fp16 --workspace=4096
```

### Jetson Power GUI
- Power mode selection
- Clock control
- Thermal monitoring

---

## Recommended Stack for MVP

```
┌─────────────────────────────────────────────────────────────┐
│                    Web UI (React + WebRTC)                  │
├─────────────────────────────────────────────────────────────┤
│                    FastAPI (Custom APIs)                    │
├─────────────────────────────────────────────────────────────┤
│  Jetson Platform Services  │     NanoLLM                    │
│  (VST, Analytics, SDR)     │     (VILA-7B AWQ)              │
├─────────────────────────────────────────────────────────────┤
│                    DeepStream SDK 8.0                       │
│              (Video Pipeline + Detection)                   │
├─────────────────────────────────────────────────────────────┤
│                    jetson-containers                        │
│              (Base: dustynv/nano_llm:r36.4.0)               │
├─────────────────────────────────────────────────────────────┤
│                    JetPack 6.2                              │
├─────────────────────────────────────────────────────────────┤
│                 Jetson AGX Orin 64GB                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Evaluation Commands

```bash
# 1. Verify Jetson setup
sudo nvpmodel -q
tegrastats

# 2. Test NanoLLM VLM
jetson-containers run $(autotag nano_llm) \
  python3 -m nano_llm.chat --model Efficient-Large-Model/VILA1.5-3b

# 3. Test DeepStream detection
jetson-containers run $(autotag deepstream) \
  deepstream-app -c /opt/nvidia/deepstream/deepstream/samples/configs/deepstream-app/source1_usb_dec_infer_resnet_int8.txt

# 4. Test Jetson Platform Services (if installed)
curl http://localhost:30080/api/v1/health

# 5. Benchmark inference latency
jetson-containers run $(autotag nano_llm) \
  python3 -c "
from nano_llm import NanoLLM
import time
model = NanoLLM.from_pretrained('Efficient-Large-Model/VILA1.5-3b')
start = time.time()
response = model.generate('test', 'Describe this.')
print(f'Latency: {(time.time()-start)*1000:.0f}ms')
"
```

---

*Product Solutions Reference - January 2026*
