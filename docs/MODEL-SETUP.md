# Model Setup Guide

Instructions for setting up VLM and detection models for Newport Demo.

## VILA-7B AWQ (Vision Language Model)

### Container

```yaml
image: dustynv/nano_llm:r36.4.0
```

### Model Details

| Property | Value |
|----------|-------|
| Model | VILA-1.5-7B |
| Quantization | AWQ 4-bit |
| Memory | ~8GB |
| First Load | 30-60s (TensorRT compilation) |
| Inference | 120-150ms |

### First-Time Setup

The model downloads automatically on first run (~8GB download).

```bash
# Start VLM container
docker compose up vlm

# Watch logs for model download
docker compose logs -f vlm
```

### Manual Download (Optional)

```bash
# Inside container
python -c "from nano_llm import NanoLLM; NanoLLM.from_pretrained('Efficient-Large-Model/VILA1.5-7b')"
```

### Verification

```python
from nano_llm import NanoLLM

model = NanoLLM.from_pretrained("Efficient-Large-Model/VILA1.5-7b")
response = model.generate("Describe this image", image_path="/path/to/test.jpg")
print(response)
```

---

## YOLOv8-s TensorRT INT8 (Object Detection)

### Container

```yaml
image: nvcr.io/nvidia/deepstream:7.0-gc-triton-devel
```

### Model Details

| Property | Value |
|----------|-------|
| Model | YOLOv8-small |
| Quantization | TensorRT INT8 |
| Memory | ~200MB |
| Inference | 5-8ms |

### Export Command

```bash
# Install ultralytics
pip install ultralytics

# Export to TensorRT INT8
yolo export model=yolov8s.pt format=engine device=0 int8=True
```

### Calibration Dataset

INT8 quantization requires calibration images:

```bash
# Use COCO validation set or custom dataset
yolo export model=yolov8s.pt format=engine device=0 int8=True \
    data=/path/to/calibration/images
```

### Pre-built Engine

For quick start, use FP16 (no calibration needed):

```bash
yolo export model=yolov8s.pt format=engine device=0 half=True
```

### Verification

```python
from ultralytics import YOLO

model = YOLO("yolov8s.engine")
results = model.predict("/path/to/test.jpg")
print(results[0].boxes)
```

---

## Model Cache Volume

Models are cached in Docker volume for persistence:

```yaml
volumes:
  model_cache:  # Mounted at /root/.cache in VLM container
```

To clear cache:
```bash
docker volume rm edge-research_model_cache
```

---

## Troubleshooting

### Out of Memory

**Symptom:** Container crashes or hangs during model load.

**Solution:**
1. Check memory with `tegrastats`
2. Ensure no other GPU processes running
3. Try FP16 quantization instead of INT8 for YOLOv8

### Slow First Load

**Symptom:** VLM takes 5+ minutes on first run.

**Explanation:** TensorRT engine compilation happens once on first load. Subsequent loads use cached engine.

**Solution:** Be patient on first run, or pre-warm models:
```bash
make shell-vlm
python -c "from nano_llm import NanoLLM; NanoLLM.from_pretrained('Efficient-Large-Model/VILA1.5-7b')"
```

### TensorRT Version Mismatch

**Symptom:** Engine load fails with version error.

**Solution:** Re-export engine on the target device:
```bash
# Delete old engine
rm yolov8s.engine

# Re-export
yolo export model=yolov8s.pt format=engine device=0
```

---

## References

- [NanoLLM Models](https://dusty-nv.github.io/NanoLLM/models.html)
- [VILA on Jetson](https://www.jetson-ai-lab.com/tutorial_vila.html)
- [YOLOv8 TensorRT Export](https://docs.ultralytics.com/integrations/tensorrt/)
