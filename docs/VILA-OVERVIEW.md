# VILA: Visual Language Model for Edge AI

## What is VILA?

**VILA** (Visual Language Intelligence and Edge AI) is a family of state-of-the-art vision language models (VLMs) developed by NVIDIA and MIT. It's designed for diverse multimodal AI tasks across edge devices, data centers, and cloud environments.

### Key Facts

| Attribute | Details |
|-----------|---------|
| Developer | NVIDIA (NVlabs) + MIT |
| Model Family | VILA 1.0, VILA 1.5, NVILA |
| Architecture | Transformer (SigLIP vision encoder + LLaMA-based LLM) |
| Input Types | Images, Video, Text |
| Quantization | AWQ 4-bit for edge deployment |
| License | Apache 2.0 |

### Model Variants

| Model | Parameters | Use Case | Memory |
|-------|------------|----------|--------|
| VILA1.5-3b | 3B | Edge devices (Jetson Orin/Thor) | ~6GB |
| VILA1.5-8B | 8B | Larger edge / workstation | ~16GB |
| VILA1.5-13B | 13B | Data center | ~26GB |
| NVILA-15B | 15B | High accuracy applications | ~30GB |

**For our Newport Demo project, we use `VILA1.5-3b`** - optimized for Jetson edge deployment.

---

## What VILA Does

VILA is a **vision-language model** that can:

1. **Understand Images**: Analyze visual content and describe what's happening
2. **Answer Questions**: Respond to natural language queries about images
3. **Multi-Image Reasoning**: Compare and reason across multiple images
4. **In-Context Learning**: Learn from examples provided in the prompt
5. **Visual Chain-of-Thought**: Step-by-step reasoning about visual scenes

### Core Capabilities

```
┌─────────────────────────────────────────────────────────────────┐
│                         VILA Pipeline                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────┐    ┌──────────────┐    ┌─────────────────┐       │
│   │  Image  │───▶│ Vision Encoder│───▶│                 │       │
│   │ (Frame) │    │   (SigLIP)   │    │                 │       │
│   └─────────┘    └──────────────┘    │   LLM Decoder   │       │
│                         │            │   (LLaMA-based) │───▶ Text
│   ┌─────────┐    ┌──────▼───────┐    │                 │  Response
│   │  Text   │───▶│   Projector  │───▶│                 │       │
│   │(Prompt) │    │  (MLP/Attn)  │    │                 │       │
│   └─────────┘    └──────────────┘    └─────────────────┘       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Example Interactions

**Scene Description:**
```
Input: [Image of elderly person reading in chair]
Prompt: "Describe what you see in this image."
Output: "An elderly person is sitting comfortably in a rocking chair,
        reading a book. They appear relaxed and engaged with their reading."
```

**Protocol Classification:**
```
Input: [Image of room]
Prompt: "Classify this scene. GREEN=safe, YELLOW=attention, RED=critical"
Output: "GREEN|reading|Resident reading peacefully in their chair"
```

---

## How VILA Works in Our System

### Architecture Integration

```
┌─────────────────────────────────────────────────────────────────┐
│                    Newport Demo Pipeline                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐                      ┌──────────────┐        │
│  │  DeepStream  │  detections channel  │     VLM      │        │
│  │  Container   │─────────────────────▶│  Container   │        │
│  │              │                      │              │        │
│  │ • RTSP Input │  frame_buffer (tmpfs)│ • VILA1.5-3b │        │
│  │ • YOLO Det.  │─────────────────────▶│ • Protocol   │        │
│  │ • Person Det │                      │   Evaluator  │        │
│  └──────────────┘                      └──────┬───────┘        │
│                                               │                 │
│                                        summaries channel        │
│                                               │                 │
│                                               ▼                 │
│                                        ┌──────────────┐        │
│                                        │     App      │        │
│                                        │  Container   │        │
│                                        │              │        │
│                                        │ • WebSocket  │        │
│                                        │ • Dashboard  │        │
│                                        │ • Alerts     │        │
│                                        └──────────────┘        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **DeepStream** receives RTSP camera feed, runs YOLO person detection
2. **DeepStream** publishes detections + saves frame to shared tmpfs volume
3. **VLM Container** receives detection event via Redis
4. **VILA model** analyzes frame image with protocol-aware prompt
5. **Protocol Evaluator** maps VILA response to severity (GREEN/YELLOW/RED)
6. **VLM Container** publishes status summary via Redis
7. **App Container** receives summary, broadcasts to WebSocket clients

### VLM Subscriber Flow

```python
# Simplified flow from vlm_subscriber.py

class VLMSubscriber:
    def __init__(self):
        self.vlm = NanoLLMWrapper("Efficient-Large-Model/VILA1.5-3b")
        self.evaluator = ProtocolEvaluator(protocols)

    async def process_frame(self, stream_id, frame_path):
        # 1. VILA classifies the scene against protocols
        classification = self.vlm.classify(frame_path, protocols)
        # Returns: "GREEN|reading|Resident reading in rocking chair"

        # 2. Parse into structured status
        status = self.evaluator.parse_response(classification)
        # Returns: StreamStatus(severity="green", icon="📗", ...)

        # 3. Apply debouncing (prevent flapping)
        if self.state_machine.update(status.severity):
            await self.publish_summary(status)
```

---

## How We Utilize VILA

### 1. Protocol-Based Scene Classification

Users define behavioral protocols in natural language:

```python
protocols = ProtocolConfig(
    green_rules="Reading, watching TV, sleeping normally, eating meals, sitting calmly",
    yellow_rules="Out of camera view, crouching in corners, minor injuries, pacing erratically",
    red_rules="Unconscious on ground, severe injury, room is empty, self-harm behavior"
)
```

VILA receives these protocols as context and classifies scenes accordingly.

### 2. Structured Output Format

We prompt VILA to respond in a parseable format:

```
SEVERITY|ICON|MESSAGE

Examples:
- GREEN|reading|Resident reading in rocking chair
- YELLOW|pacing|Person walking back and forth repeatedly
- RED|unconscious|Person lying motionless on floor
```

### 3. Multi-Stream Round-Robin Sampling

With multiple camera feeds, we sample streams in rotation:

```python
class MultiStreamVLMSampler:
    """
    With N streams and ~500ms VLM latency:
    - 4 streams = each sampled every 2 seconds
    - 8 streams = each sampled every 4 seconds
    """
    def __init__(self, streams, interval_per_stream=10.0):
        self.streams = streams
        self.interval = interval_per_stream
```

### 4. Debounced State Transitions

To prevent alert fatigue from transient misclassifications:

```python
class StatusStateMachine:
    """
    Requires N consecutive same-classifications before changing state.
    GREEN → YELLOW: 2 consecutive YELLOW classifications
    YELLOW → RED: 2 consecutive RED classifications
    """
```

---

## Performance Characteristics

### On Jetson AGX Thor (R38)

| Metric | Value |
|--------|-------|
| Model Load Time | ~10-15 seconds (first run) |
| Inference Latency | ~300-500ms per image |
| Memory Usage | ~6GB VRAM |
| Quantization | AWQ 4-bit |
| Throughput | ~2-3 images/second |

### Optimization Techniques

1. **AWQ Quantization**: 4-bit weights reduce memory 4x with minimal accuracy loss
2. **Token Compression**: VILA1.5 uses 196 tokens per image (vs 729 in v1.0)
3. **TensorRT-LLM**: Optional backend for further acceleration
4. **Batch Processing**: Can process multiple images in single inference

---

## Model Files & Caching

### First Run

On first inference, VILA downloads model weights from HuggingFace:

```
~/.cache/huggingface/hub/
├── models--Efficient-Large-Model--VILA1.5-3b/
│   ├── config.json
│   ├── model-00001-of-00002.safetensors  (~3GB)
│   ├── model-00002-of-00002.safetensors  (~3GB)
│   ├── tokenizer.json
│   └── ...
```

### Docker Volume Caching

In our setup, model cache is persisted via Docker volume:

```yaml
# docker-compose.yml
volumes:
  model_cache:
    driver: local

services:
  vlm:
    volumes:
      - model_cache:/root/.cache/huggingface
```

This ensures models are downloaded once and reused across container restarts.

---

## References

- [VILA GitHub Repository](https://github.com/NVlabs/VILA)
- [VILA1.5-3b on HuggingFace](https://huggingface.co/Efficient-Large-Model/VILA1.5-3b)
- [NVIDIA Technical Blog: Visual Language Models with VILA](https://developer.nvidia.com/blog/visual-language-models-on-nvidia-hardware-with-vila/)
- [NVIDIA Edge AI Getting Started](https://developer.nvidia.com/blog/getting-started-with-edge-ai-on-nvidia-jetson-llms-vlms-and-foundation-models-for-robotics/)
- [VILA CVPR 2024 Paper](https://openaccess.thecvf.com/content/CVPR2024/papers/Lin_VILA_On_Pre-training_for_Visual_Language_Models_CVPR_2024_paper.pdf)

---

## Quick Reference

### Running VILA Inference

```bash
# Using jetson-containers
jetson-containers run $(jetson-containers autotag vila) \
  python3 -c "
from nano_llm import NanoLLM
model = NanoLLM.from_pretrained('Efficient-Large-Model/VILA1.5-3b')
response = model.generate('Describe this image', image='frame.jpg')
print(response)
"
```

### Testing GPU Access

```bash
# Verify CUDA is available in vila container
jetson-containers run $(jetson-containers autotag vila) \
  python3 -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```
