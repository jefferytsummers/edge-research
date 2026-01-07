# =============================================================================
# DeepStream L4T with Python Bindings (pyds)
# =============================================================================
# Based on NGC DeepStream L4T 8.0 samples image
# Adds: pyds (Python bindings), GStreamer Python, Redis, OpenCV
#
# NOTE: NGC containers do NOT include pyds pre-installed.
# We download the official pre-built wheel from GitHub releases.
# =============================================================================

FROM nvcr.io/nvidia/deepstream-l4t:8.0-samples-multiarch

# -----------------------------------------------------------------------------
# Install Python bindings prerequisites
# - python3-gi: GObject introspection for Python (required for GStreamer)
# - python3-gst-1.0: GStreamer Python bindings
# - python3-venv: Required for Python 3.12 pip installs
# -----------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-gi \
    python3-gi-cairo \
    python3-dev \
    python3-gst-1.0 \
    python3-venv \
    python3-pip \
    libgirepository-2.0-dev \
    libcairo2-dev \
    gir1.2-gst-rtsp-server-1.0 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------------------
# Create virtual environment with system site-packages
# This inherits python3-gi and python3-gst-1.0 from apt
# -----------------------------------------------------------------------------
RUN python3 -m venv /opt/venv --system-site-packages
ENV PATH="/opt/venv/bin:$PATH"

# -----------------------------------------------------------------------------
# Install pyds (DeepStream Python bindings)
# Version must match DeepStream version: pyds 1.2.2 <-> DS 8.0
# Pre-built wheels: https://github.com/NVIDIA-AI-IOT/deepstream_python_apps/releases
# -----------------------------------------------------------------------------
RUN wget -q https://github.com/NVIDIA-AI-IOT/deepstream_python_apps/releases/download/v1.2.2/pyds-1.2.2-cp312-cp312-linux_aarch64.whl \
    && pip install --no-cache-dir pyds-1.2.2-cp312-cp312-linux_aarch64.whl \
    && rm pyds-1.2.2-cp312-cp312-linux_aarch64.whl

# -----------------------------------------------------------------------------
# Install additional Python packages for our application
# -----------------------------------------------------------------------------
RUN pip install --no-cache-dir \
    redis \
    opencv-python-headless \
    numpy

WORKDIR /app

# Verify non-GPU imports (pyds requires nvidia runtime, verified at container start)
RUN python3 -c "import gi; import cv2; import redis; print('Build-time imports OK')"

# Note: pyds import will be verified at runtime when nvidia runtime is available
