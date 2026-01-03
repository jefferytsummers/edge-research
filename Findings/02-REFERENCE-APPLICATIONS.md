# Reference Applications & Codebases

## Official NVIDIA Resources

### jetson-containers (Primary)
**Repository**: https://github.com/dusty-nv/jetson-containers
**Description**: Modular container build system providing the latest AI/ML packages for NVIDIA Jetson
**Relevance**: Core foundation for VLM deployment; includes NanoLLM, VILA, LLaVA, llama.cpp, vLLM, MLC, transformers, ollama

```bash
# Quick start
git clone https://github.com/dusty-nv/jetson-containers
bash jetson-containers/install.sh
jetson-containers run $(autotag nano_llm)
```

---

### jetson-inference
**Repository**: https://github.com/dusty-nv/jetson-inference
**Description**: Hello AI World guide with TensorRT and deep vision primitives
**Key Features**:
- Built-in WebRTC server for low-latency streaming
- detectNet, segNet, poseNet, actionNet examples
- GStreamer integration with videoSource/videoOutput

```bash
# WebRTC streaming with detection
./detectnet --input-codec=h264 csi://0 webrtc://@:8554/output
```

---

### Jetson Platform Services
**Repository**: https://github.com/NVIDIA-AI-IOT/jetson-platform-services
**Documentation**: https://docs.nvidia.com/jetson/jps/
**Description**: Production-ready microservices with REST APIs for edge AI

**Key Services**:
| Service | Description |
|---------|-------------|
| VLM AI Service | VILA/LLaVA deployment with REST API |
| DeepStream AI Service | Multi-stream detection with PeopleNet/YOLOv8 |
| Analytics Service | Tripwire, ROI analytics |
| Zero-Shot Detection | NanoOWL (OWL-ViT optimized) |
| Grounding DINO | Open-vocabulary detection |

---

### NanoLLM
**Repository**: https://github.com/dusty-nv/jetson-containers/tree/master/packages/llm/nano_llm
**Documentation**: https://dusty-nv.github.io/NanoLLM/
**Tutorials**: https://www.jetson-ai-lab.com/tutorial_nano-llm.html

**Key Examples**:
- Live LLaVA: https://www.jetson-ai-lab.com/tutorial_live-llava.html
- Video Query Agent
- Multimodal RAG with event filters

```python
# Simple VLM inference
from nano_llm import NanoLLM
model = NanoLLM.from_pretrained("Efficient-Large-Model/VILA-7b")
response = model.generate(image, "Describe what you see")
```

---

### DeepStream SDK
**Documentation**: https://docs.nvidia.com/metropolis/deepstream/dev-guide/
**NGC Container**: nvcr.io/nvidia/deepstream-l4t:8.0

**Reference Pipelines**:
```
nvv4l2decoder → nvstreammux → nvinfer → nvtracker → nvosd → nvvideoconvert → nveglglessink
```

**Sample Apps**:
- deepstream-app (multi-stream detection)
- deepstream-test5 (IoT integration)
- deepstream-occupancy-analytics

---

### Triton Inference Server for Jetson
**Documentation**: https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/user_guide/jetson.html
**Releases**: https://github.com/triton-inference-server/server/releases

**Key Features on Jetson**:
- C-API for zero-overhead integration
- TensorRT, ONNX, PyTorch backends
- GPU + DLA execution support
- Dynamic batching

---

### Holoscan SDK
**Repository**: https://github.com/nvidia-holoscan/holoscan-sdk
**Documentation**: https://docs.nvidia.com/holoscan/
**Description**: AI sensor processing for ultra-low-latency applications

**Best For**:
- Medical imaging / surgical video
- Industrial inspection
- Custom sensor fusion

```python
# Holoscan operator example
class InferenceOp(Operator):
    def compute(self, op_input, op_output, context):
        tensor = op_input.receive("in")
        result = self.model.infer(tensor)
        op_output.emit(result, "out")
```

---

### NVIDIA Isaac ROS
**Repository**: https://github.com/NVIDIA-ISAAC-ROS
**Documentation**: https://developer.nvidia.com/isaac/ros

**Perception Packages**:
- isaac_ros_visual_slam
- isaac_ros_object_detection
- isaac_ros_pose_estimation
- isaac_ros_foundationpose

---

## Third-Party / Community Resources

### Ultralytics YOLO on Jetson
**Guide**: https://docs.ultralytics.com/guides/deepstream-nvidia-jetson/
**Description**: YOLOv8/v11 with DeepStream and TensorRT

### RidgeRun GstInference
**Documentation**: https://developer.ridgerun.com/wiki/index.php/GstInference
**Description**: Commercial GStreamer inference elements with TensorRT

### VILA (Vision Language Models)
**Repository**: https://github.com/NVlabs/VILA
**Description**: NVIDIA's state-of-the-art VLM family; now Cosmos Nemotron

---

## Container Images on NGC

| Image | Use Case |
|-------|----------|
| `nvcr.io/nvidia/l4t-jetpack:r36.4.0` | Base JetPack |
| `nvcr.io/nvidia/deepstream-l4t:8.0` | DeepStream SDK |
| `dustynv/nano_llm:r36.4.0` | NanoLLM + VLMs |
| `nvcr.io/nvidia/tritonserver:25.01-py3-jetson` | Triton Server |

---

## Recommended Learning Path

1. **Start**: jetson-containers quick start
2. **Video Pipeline**: DeepStream deepstream-app samples
3. **VLM Basics**: NanoLLM tutorials on Jetson AI Lab
4. **Live VLM**: Live LLaVA tutorial
5. **Production**: Jetson Platform Services reference workflows
6. **Optimization**: TensorRT model optimization guides

---

*Last Updated: January 2026*
