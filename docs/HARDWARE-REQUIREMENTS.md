# Hardware Requirements

Hardware specifications and setup for Newport Demo.

## Target Platform: Jetson AGX Orin 64GB

### Specifications

| Component | Specification |
|-----------|---------------|
| GPU | Ampere architecture, 2048 CUDA cores, 64 Tensor cores |
| AI Performance | 275 TOPS INT8 |
| Memory | 64GB LPDDR5 (unified CPU/GPU) |
| Video Decode | 8x 4K60 NVDEC |
| Storage | NVMe recommended (500GB+) |
| Power | 15W - 60W configurable |

### Memory Budget (Multi-Stream)

| Component | Memory Usage |
|-----------|-------------|
| DeepStream (4 streams) | ~4GB |
| YOLOv8-s TensorRT | ~200MB |
| VILA-7B AWQ | ~8GB |
| Redis | ~100MB |
| App Container | ~500MB |
| System/Headroom | ~10GB |
| **Available for scaling** | **~40GB** |

### What Jetson Owners Actually Want

| Use Case | Frequency | Jetson Fit |
|----------|-----------|------------|
| Security camera monitoring | High | Excellent (real-time, multi-stream) |
| Industrial quality inspection | High | Excellent (low latency, precision) |
| Robotics vision | High | Excellent (embedded, power efficient) |
| Retail analytics | Medium | Good (privacy, on-premise) |
| Behavioral monitoring | Medium | Excellent (this project!) |

### Jetson's Sweet Spot

**Real-time edge AI with:**
- Multiple video streams (RTSP, USB, file)
- Low-latency inference (<100ms detection, <500ms VLM)
- Privacy-first (no cloud required)
- 24/7 operation capability
- GPU-accelerated everything

---

## Software Requirements

### JetPack Version

**JetPack 6.0** (L4T R36.x) or later

Includes:
- CUDA 12.2
- TensorRT 8.6
- cuDNN 8.9
- DeepStream 7.0
- OpenCV 4.8

### Container Runtime

NVIDIA Container Runtime configured as default Docker runtime.

```json
// /etc/docker/daemon.json
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

---

## Performance Tuning

### Power Mode

Set to MAXN for maximum performance:
```bash
sudo nvpmodel -m 0
sudo jetson_clocks
```

### Monitoring

Use `tegrastats` for real-time resource monitoring:
```bash
tegrastats --interval 1000
```

Key metrics:
- GPU utilization
- Memory usage
- CPU/GPU temperatures
- Power consumption

---

## Network Requirements

| Requirement | Specification |
|-------------|---------------|
| RTSP Cameras | Gigabit Ethernet recommended |
| Dashboard Access | Port 8080 (HTTP) |
| Redis | Port 6379 (internal) |

---

## References

- [Jetson AGX Orin Developer Kit](https://developer.nvidia.com/embedded/jetson-agx-orin-developer-kit)
- [JetPack SDK](https://developer.nvidia.com/embedded/jetpack)
- [Jetson Power Management](https://docs.nvidia.com/jetson/archives/r36.3/DeveloperGuide/SD/PlatformPowerAndPerformance/JetsonOrinNxSeriesAndJetsonAgxOrinSeries.html)
