# Competitive Analysis & Alternatives

## Edge AI Platform Comparison

### NVIDIA Jetson (Recommended)

| Aspect | Details |
|--------|---------|
| **Products** | Orin Nano ($249), AGX Orin ($1999), Thor (TBD) |
| **AI Performance** | 67-275 TOPS (Orin), 1000+ TOPS (Thor) |
| **VLM Capability** | 3B-120B parameters depending on model |
| **Framework Support** | PyTorch, TensorFlow, ONNX, TensorRT, CUDA |
| **Video Processing** | DeepStream SDK, hardware encode/decode |
| **Ecosystem** | Mature, extensive documentation, active community |
| **Power** | 7-60W depending on model |

**Verdict**: Best choice for VLM + video inference MVP. Only platform with proven VLM support at edge.

---

### Google Coral Edge TPU

| Aspect | Details |
|--------|---------|
| **Products** | Dev Board ($150), USB Accelerator ($60) |
| **AI Performance** | 4 TOPS (INT8 only) |
| **VLM Capability** | Not supported (no LLM/VLM capability) |
| **Framework Support** | TensorFlow Lite only |
| **Video Processing** | Limited, software-based |
| **Ecosystem** | Good for simple detection tasks |
| **Power** | 2-4W |

**Verdict**: Not suitable for MVP. No VLM support, limited to INT8 TFLite models.

---

### Qualcomm Robotics RB5/RB6

| Aspect | Details |
|--------|---------|
| **Products** | RB5 (~$500), RB6 (TBD) |
| **AI Performance** | 15-26 TOPS |
| **VLM Capability** | Limited, Llama 2-7B with significant effort |
| **Framework Support** | SNPE, QNN, TensorFlow Lite, ONNX |
| **Video Processing** | Hardware ISP, encode/decode |
| **Ecosystem** | Growing, Android-focused |
| **Power** | 5-15W |

**Verdict**: Possible alternative but VLM ecosystem is immature. Better for mobile/drone applications.

---

### AMD Xilinx Kria

| Aspect | Details |
|--------|---------|
| **Products** | KV260 ($250), KR260 (~$350) |
| **AI Performance** | Up to 4.5 TOPS (DPU) |
| **VLM Capability** | Not supported |
| **Framework Support** | Vitis AI, ONNX, TensorFlow |
| **Video Processing** | FPGA-based, flexible but complex |
| **Ecosystem** | Specialized, smaller community |
| **Power** | 5-35W |

**Verdict**: Not suitable. FPGA flexibility is overkill for this use case, no VLM support.

---

### Hailo-8

| Aspect | Details |
|--------|---------|
| **Products** | Hailo-8 module (~$100), Hailo-15 |
| **AI Performance** | 26 TOPS |
| **VLM Capability** | Very limited LLM support, no VLM |
| **Framework Support** | TensorFlow, ONNX, PyTorch (via Hailo Model Zoo) |
| **Video Processing** | Pairs well with RPi5 |
| **Ecosystem** | Growing, focused on vision |
| **Power** | 2.5W typical |

**Verdict**: Excellent for detection-only applications. No VLM support.

---

### Raspberry Pi 5 + Accelerator

| Aspect | Details |
|--------|---------|
| **Products** | RPi5 ($80) + Hailo/Coral ($100) |
| **AI Performance** | 26 TOPS (with Hailo-8) |
| **VLM Capability** | Very limited (sub-1B models only) |
| **Framework Support** | Depends on accelerator |
| **Video Processing** | Limited hardware support |
| **Ecosystem** | Huge hobbyist community |
| **Power** | 5-15W |

**Verdict**: Good for prototyping detection. Not viable for VLM workloads.

---

## Summary Matrix

| Platform | VLM Support | Video Pipeline | Latency Target | Price |
|----------|-------------|----------------|----------------|-------|
| **Jetson AGX Orin** | Excellent (3-20B) | Excellent | 100-200ms achievable | $1,999 |
| Jetson Orin Nano | Good (up to 4B) | Good | 150-300ms | $249 |
| Qualcomm RB5 | Limited | Good | TBD | ~$500 |
| Google Coral | None | Limited | N/A | $150 |
| AMD Kria | None | Flexible | N/A | $250 |
| Hailo-8 | None | Good | 50-100ms (detection) | ~$100 |
| RPi5 + Accel | None | Limited | N/A | $180 |

---

## Cloud-Edge Hybrid Alternatives

If edge VLM proves too challenging, consider hybrid architectures:

### Option 1: Edge Detection + Cloud VLM
```
Camera → Jetson (Detection) → Cloud API (VLM Query)
                                     ↓
                              Response (500ms-2s)
```

**Pros**: Simpler edge device, more powerful VLMs
**Cons**: Latency 500ms+, network dependency, ongoing API costs

### Option 2: Tiered Processing
```
                    ┌─ Simple queries → Edge VLM (3B)
Camera → Detection ─┤
                    └─ Complex queries → Cloud VLM (70B+)
```

**Pros**: Best of both worlds
**Cons**: Added complexity, still has cloud latency for complex queries

### Cloud VLM Options
| Provider | Model | Latency | Cost |
|----------|-------|---------|------|
| OpenAI | GPT-4V | 1-3s | $0.01/image |
| Anthropic | Claude 3 Vision | 1-3s | $0.01/image |
| Google | Gemini Pro Vision | 0.5-2s | $0.0025/image |
| AWS Bedrock | Claude/Titan | 1-3s | Varies |

---

## Open-Source VLM Alternatives

If NVIDIA VILA/NanoLLM doesn't meet needs:

| Model | Parameters | Memory | Notes |
|-------|------------|--------|-------|
| LLaVA 1.5/1.6 | 7B/13B | 8-16GB | Well-tested on Jetson |
| Qwen2.5-VL | 3B/7B | 4-8GB | Strong multilingual |
| Moondream2 | 1.8B | ~3GB | Ultra-efficient |
| SmolVLM | 1.7B | ~3GB | HuggingFace optimized |
| Apple FastVLM | Various | ~4GB | Fastest vision encoder |
| DeepSeek-VL2 | 4.5B (MoE) | ~6GB | Fast MoE architecture |

---

## Recommendation for MVP

**Primary**: Jetson AGX Orin 64GB
- Provides headroom for VLM experimentation
- Proven ecosystem with NanoLLM + DeepStream
- Can scale down to Orin Nano after optimization

**Fallback**: Cloud hybrid if edge latency proves insufficient
- Edge handles video pipeline and detection
- Route complex VLM queries to cloud
- Implement caching for repeated queries

---

*Last Updated: January 2026*
