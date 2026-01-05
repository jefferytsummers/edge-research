# Reference Projects & Repositories

A curated list of proven open-source projects relevant to our Video Intelligence Platform MVP, organized by capability area.

---

## Quick Reference Matrix

### Overall Relevance to MVP

| Project | Video Processing | VLM/Detection | RAG/Search | Edge/Jetson | Relevance |
|---------|-----------------|---------------|------------|-------------|-----------|
| [VideoRAG (HKUDS)](#videorag-hkuds) | ✅ | ✅ | ✅ | ❌ | ⭐⭐⭐⭐⭐ |
| [Video-LLaVA](#video-llava) | ✅ | ✅ | ❌ | ❌ | ⭐⭐⭐⭐ |
| [jetson-inference](#jetson-inference) | ✅ | ✅ | ❌ | ✅ | ⭐⭐⭐⭐ |
| [clip-retrieval](#clip-retrieval) | ✅ | ❌ | ✅ | ❌ | ⭐⭐⭐⭐ |
| [PySceneDetect](#pyscenedetect) | ✅ | ❌ | ❌ | ✅ | ⭐⭐⭐⭐ |
| [Video-RAG-master](#video-rag-master) | ✅ | ✅ | ✅ | ❌ | ⭐⭐⭐⭐ |
| [jetson-containers](#jetson-containers) | ❌ | ✅ | ❌ | ✅ | ⭐⭐⭐⭐ |
| [LLaVA](#llava) | ❌ | ✅ | ❌ | ❌ | ⭐⭐⭐ |
| [video-RAG (utk7arsh)](#video-rag-utk7arsh) | ✅ | ✅ | ✅ | ❌ | ⭐⭐⭐ |
| [DeepStream-Yolo](#deepstream-yolo) | ✅ | ✅ | ❌ | ✅ | ⭐⭐⭐ |

---

## Category 1: Video RAG & Semantic Search

Projects that combine video understanding with retrieval-augmented generation.

| Project | Stars | Key Features | Tech Stack | Our Use |
|---------|-------|--------------|------------|---------|
| **[VideoRAG (HKUDS)](https://github.com/HKUDS/VideoRAG)** | 🔥 New | Cross-video understanding, knowledge graphs, handles 100s of hours on 24GB GPU | PyTorch, KG | RAG architecture reference |
| **[Video-RAG-master](https://github.com/Leon1207/Video-RAG-master)** | NeurIPS'25 | OCR, ASR, detection as auxiliary texts, lightweight single-turn retrieval | Any LVLM | Auxiliary text integration |
| **[starsuzi/VideoRAG](https://github.com/starsuzi/VideoRAG)** | Research | Frame selection mechanism, visual+textual retrieval | LVLM | Frame selection strategy |
| **[video-RAG (utk7arsh)](https://github.com/utk7arsh/video-RAG)** | Demo | Multimodal embeddings, natural language queries | BridgeTower, LanceDB, LLaVA | End-to-end reference |
| **[clip-retrieval](https://github.com/rom1504/clip-retrieval)** | 2.3k+ | CLIP embeddings at scale, FAISS indexing, hosted backend | CLIP, FAISS | Embedding pipeline |

### VideoRAG Architecture (HKUDS) - Most Relevant

```
Video Corpus → Frame Extraction → Multimodal Encoding → Knowledge Graph
                                                              ↓
User Query → Query Encoding → Graph Retrieval → Response Generation
```

**Key Insight:** Builds knowledge graphs spanning multiple videos with semantic dependencies - exactly what we need for cross-video queries.

---

## Category 2: Video Understanding VLMs

Vision-Language Models specifically designed for video comprehension.

| Project | Stars | Video Support | Edge-Ready | Key Innovation |
|---------|-------|---------------|------------|----------------|
| **[Video-LLaVA](https://github.com/PKU-YuanGroup/Video-LLaVA)** | 2.8k+ | Native | ❌ (needs adaptation) | Unified visual representation |
| **[LLaVA](https://github.com/haotian-liu/LLaVA)** | 20k+ | Via LLaVA-NeXT | Partial | Foundation model |
| **[PG-Video-LLaVA](https://github.com/mbzuai-oryx/Video-LLaVA)** | Research | Native + Audio | ❌ | Pixel-level grounding |
| **[VILA (NVIDIA)](https://github.com/NVlabs/VILA)** | Official | Native | ✅ Jetson | Our target VLM |

### Video-LLaVA Performance (EMNLP 2024)

| Benchmark | Video-LLaVA | vs Video-ChatGPT |
|-----------|-------------|------------------|
| MSRVTT | +5.8% | Baseline |
| MSVD | +9.9% | Baseline |
| TGIF | +18.6% | Baseline |
| ActivityNet | +10.1% | Baseline |

**Key Insight:** Video-LLaVA's unified visual representation approach could inform how we handle mixed image/video queries.

---

## Category 3: Jetson & Edge AI

Projects optimized for NVIDIA Jetson deployment.

| Project | Maintainer | Focus | Models Supported | Our Use |
|---------|------------|-------|------------------|---------|
| **[jetson-inference](https://github.com/dusty-nv/jetson-inference)** | NVIDIA | Detection, segmentation, WebRTC | detectNet, segNet, poseNet | Video streaming reference |
| **[jetson-containers](https://github.com/dusty-nv/jetson-containers)** | NVIDIA | Container ecosystem | NanoLLM, VILA, LLaVA, YOLO | Base container images |
| **[jetson-platform-services](https://github.com/NVIDIA-AI-IOT/jetson-platform-services)** | NVIDIA | Production microservices | DeepStream, VLM services | API patterns |
| **[DeepStream-Yolo](https://github.com/marcoslucianops/DeepStream-Yolo)** | Community | YOLO + DeepStream | YOLOv5-v11 | Detection pipeline |
| **[Azure-Jetson-DeepStream](https://github.com/Azure-Samples/NVIDIA-Deepstream-Azure-IoT-Edge-on-a-NVIDIA-Jetson-Nano)** | Microsoft | IoT Edge integration | DeepStream | Cloud connectivity |

### jetson-containers Package Availability

| Package | Description | Container Tag |
|---------|-------------|---------------|
| `nano_llm` | NanoLLM + VLMs | `dustynv/nano_llm:r36` |
| `llava` | LLaVA models | `dustynv/llava:r36` |
| `vila` | VILA models | `dustynv/vila:r36` |
| `deepstream` | DeepStream SDK | `nvcr.io/nvidia/deepstream-l4t` |
| `tritonserver` | Triton Inference | `nvcr.io/nvidia/tritonserver` |
| `whisper` | Audio transcription | `dustynv/whisper:r36` |

---

## Category 4: Scene Detection & Keyframes

Tools for intelligent video segmentation.

| Project | Method | Speed | Accuracy | Our Use |
|---------|--------|-------|----------|---------|
| **[PySceneDetect](https://github.com/Breakthrough/PySceneDetect)** | Content/Threshold | ~0.5x realtime | High | Primary scene detector |
| **[Video-Summarizer](https://github.com/Prerak-Sanghvi/Video-Summarizer)** | PySceneDetect + Whisper + BART | CPU-friendly | Good | Reference pipeline |
| **[TransNetV2](https://github.com/soCzech/TransNetV2)** | Deep learning | Faster | Higher | Alternative detector |
| **[katna](https://github.com/keplerlab/katna)** | Multiple methods | Variable | Good | Keyframe extraction |

### PySceneDetect Detectors

| Detector | Best For | Threshold |
|----------|----------|-----------|
| `ContentDetector` | Fast cuts, action | 27.0 (default) |
| `ThresholdDetector` | Fades, dissolves | 12.0 (default) |
| `AdaptiveDetector` | Mixed content | Auto |
| `HashDetector` | Duplicate detection | - |

**Code Pattern:**
```python
from scenedetect import detect, ContentDetector, split_video_ffmpeg

scenes = detect("video.mp4", ContentDetector(threshold=30.0))
split_video_ffmpeg("video.mp4", scenes)
```

---

## Category 5: Embeddings & Vector Search

Multimodal embedding and retrieval systems.

| Project | Embedding Model | Vector DB | Multimodal | Our Use |
|---------|-----------------|-----------|------------|---------|
| **[clip-retrieval](https://github.com/rom1504/clip-retrieval)** | CLIP | FAISS | Image+Text | Embedding reference |
| **[Multimodal-Image-Search](https://github.com/Snehil-Shah/Multimodal-Image-Search-Engine)** | CLIP | Qdrant | Image+Text | Search UI reference |
| **[sentence-transformers](https://github.com/UKPLab/sentence-transformers)** | Various | Any | Text | Text embeddings |
| **[open_clip](https://github.com/mlfoundations/open_clip)** | OpenCLIP | Any | Image+Text | Better CLIP variants |

### Embedding Dimensions Comparison

| Model | Dimensions | Speed | Quality | Jetson Support |
|-------|------------|-------|---------|----------------|
| CLIP ViT-B/32 | 512 | Fast | Good | ✅ |
| CLIP ViT-B/16 | 512 | Medium | Better | ✅ |
| SigLIP ViT-B/16 | 768 | Medium | Best | ✅ (via NanoLLM) |
| OpenCLIP ViT-L/14 | 768 | Slow | Highest | ⚠️ Memory |

---

## Category 6: LLM Agents & Tool Use

Agent frameworks for tool-augmented reasoning.

| Project | Pattern | Framework | Complexity | Our Use |
|---------|---------|-----------|------------|---------|
| **[ReAct (Original)](https://react-lm.github.io/)** | Think-Act-Observe | Paper | Reference | Agent design |
| **[LangChain Agents](https://github.com/langchain-ai/langchain)** | Multiple | LangChain | High | Avoid (too heavy) |
| **[LlamaIndex](https://github.com/run-llama/llama_index)** | RAG-focused | LlamaIndex | Medium | RAG patterns |
| **[Instructor](https://github.com/jxnl/instructor)** | Structured Output | Pydantic | Low | Tool calling |
| **[Outlines](https://github.com/outlines-dev/outlines)** | Constrained Gen | Custom | Low | Structured output |

### ReAct Loop Pattern (Our Target)

```
User Query
    ↓
┌─────────────────────────────────────────┐
│  THOUGHT: Reason about what to do       │
│  ACTION: Select and call tool           │
│  OBSERVATION: Process tool result       │
│  ... repeat until answer ready ...      │
│  ANSWER: Final response with citations  │
└─────────────────────────────────────────┘
```

**Key Insight:** Keep agent simple - custom implementation beats LangChain for edge deployment.

---

## Category 7: Commercial/API References

Products solving similar problems (for feature inspiration).

| Product | Focus | Pricing | Key Features |
|---------|-------|---------|--------------|
| **[Twelve Labs](https://twelvelabs.io)** | Video Search API | Per-minute | Semantic search, embeddings, generate |
| **[Runway](https://runwayml.com)** | Video Generation | Subscription | Gen-3, video understanding |
| **[Pexels AI](https://pexels.com)** | Stock Video Search | Free tier | Visual similarity |
| **[Mux](https://mux.com)** | Video Infrastructure | Per-minute | Streaming, analytics |
| **[Roboflow](https://roboflow.com)** | Computer Vision | Free tier | Detection, training |

### Twelve Labs API Features (Inspiration)

| Feature | Description | Our Equivalent |
|---------|-------------|----------------|
| `search` | Semantic video search | RAG agent + ChromaDB |
| `generate` | Video summaries | VLM descriptions |
| `embed` | Multimodal embeddings | SigLIP embeddings |
| `classify` | Video classification | Detection + VLM |

---

## Recommended Architecture Influences

Based on the research, here's how we should incorporate learnings:

### From VideoRAG (HKUDS)
- Knowledge graph structure for cross-video relationships
- Semantic dependency modeling
- Efficient processing on consumer GPUs

### From Video-LLaVA
- Unified visual representation approach
- Video-specific instruction tuning patterns

### From jetson-containers
- Container composition patterns
- Model caching strategies
- TensorRT integration

### From PySceneDetect
- Content-based detection for keyframes
- Adaptive thresholding

### From clip-retrieval
- FAISS indexing at scale
- Batch embedding generation

---

## Quick Start Commands

### Test PySceneDetect
```bash
pip install scenedetect[opencv]
scenedetect -i video.mp4 detect-content list-scenes save-images
```

### Test clip-retrieval
```bash
pip install clip-retrieval
clip-retrieval inference --input_dataset "my_images/" --output_folder "embeddings/"
```

### Test jetson-containers
```bash
git clone https://github.com/dusty-nv/jetson-containers
cd jetson-containers && bash install.sh
jetson-containers run $(autotag nano_llm)
```

### Test VideoRAG
```bash
git clone https://github.com/HKUDS/VideoRAG
cd VideoRAG && pip install -r requirements.txt
python demo.py --video_path sample.mp4 --query "What happens in this video?"
```

---

## Integration Priority

| Priority | Component | Reference Project | Effort |
|----------|-----------|-------------------|--------|
| 1 | Scene Detection | PySceneDetect | Low |
| 2 | VLM Inference | jetson-containers + NanoLLM | Medium |
| 3 | Embeddings | SigLIP (via NanoLLM) | Low |
| 4 | Vector Index | ChromaDB | Low |
| 5 | Detection | YOLOv8 + TensorRT | Medium |
| 6 | RAG Agent | Custom (ReAct pattern) | Medium |
| 7 | Cross-Video KG | VideoRAG patterns | High |

---

## Sources

- [VideoRAG (HKUDS)](https://github.com/HKUDS/VideoRAG) - KDD 2026
- [Video-LLaVA](https://github.com/PKU-YuanGroup/Video-LLaVA) - EMNLP 2024
- [LLaVA](https://github.com/haotian-liu/LLaVA) - NeurIPS 2023
- [jetson-inference](https://github.com/dusty-nv/jetson-inference) - NVIDIA
- [jetson-containers](https://github.com/dusty-nv/jetson-containers) - NVIDIA
- [PySceneDetect](https://github.com/Breakthrough/PySceneDetect)
- [clip-retrieval](https://github.com/rom1504/clip-retrieval)
- [Video-RAG-master](https://github.com/Leon1207/Video-RAG-master) - NeurIPS 2025
- [Twelve Labs](https://twelvelabs.io) - Commercial API
- [Awesome-LLMs-for-Video-Understanding](https://github.com/yunlong10/Awesome-LLMs-for-Video-Understanding)

---

*Reference Projects - January 2026*
