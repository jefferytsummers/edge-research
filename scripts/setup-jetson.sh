#!/bin/bash
# setup-jetson.sh - Jetson AGX Orin setup script for Newport Demo
#
# This script configures a fresh Jetson AGX Orin for running the
# Newport Demo multi-stream behavioral monitoring application.

set -e

echo "=== Newport Demo - Jetson Setup ==="
echo ""

# Check if running on Jetson
if [ ! -f /etc/nv_tegra_release ]; then
    echo "Warning: This script is designed for NVIDIA Jetson devices."
    echo "Continuing anyway for development purposes..."
fi

# Check for root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo ./setup-jetson.sh)"
    exit 1
fi

echo "Step 1: Updating system packages..."
apt-get update
apt-get upgrade -y

echo ""
echo "Step 2: Installing Docker and NVIDIA Container Runtime..."
# Docker should be pre-installed on JetPack, but ensure it's there
apt-get install -y docker.io docker-compose-v2

# Ensure NVIDIA Container Runtime is configured
if [ ! -f /etc/docker/daemon.json ]; then
    cat > /etc/docker/daemon.json << EOF
{
    "runtimes": {
        "nvidia": {
            "path": "nvidia-container-runtime",
            "runtimeArgs": []
        }
    },
    "default-runtime": "nvidia"
}
EOF
    systemctl restart docker
fi

echo ""
echo "Step 3: Adding user to docker group..."
usermod -aG docker $SUDO_USER || true

echo ""
echo "Step 4: Installing Redis CLI (for debugging)..."
apt-get install -y redis-tools

echo ""
echo "Step 5: Configuring performance mode..."
# Set to maximum performance mode
if command -v nvpmodel &> /dev/null; then
    echo "Setting nvpmodel to MAXN (maximum performance)..."
    nvpmodel -m 0
    jetson_clocks
fi

echo ""
echo "Step 6: Creating project directories..."
mkdir -p /opt/newport-demo
mkdir -p /data/newport-demo/model_cache
mkdir -p /data/newport-demo/config
mkdir -p /data/newport-demo/redis

# Set permissions
chown -R $SUDO_USER:$SUDO_USER /opt/newport-demo
chown -R $SUDO_USER:$SUDO_USER /data/newport-demo

echo ""
echo "Step 7: Pulling container images (this may take a while)..."
docker pull nvcr.io/nvidia/deepstream:7.0-gc-triton-devel
docker pull dustynv/nano_llm:r36.4.0
docker pull redis:7-alpine

echo ""
echo "Step 8: Verifying GPU access..."
docker run --rm --runtime nvidia nvidia/cuda:12.2-base nvidia-smi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Clone the newport-demo repository to /opt/newport-demo"
echo "  2. Run 'make dev' to start all containers"
echo "  3. Access the dashboard at http://localhost:8080"
echo ""
echo "System information:"
echo "  - JetPack version: $(cat /etc/nv_tegra_release 2>/dev/null || echo 'N/A')"
echo "  - Docker version: $(docker --version)"
echo "  - GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo 'N/A')"
echo ""
echo "Monitor system resources with: tegrastats"
