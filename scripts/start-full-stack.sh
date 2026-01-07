#!/bin/bash
# =============================================================================
# Full Stack Startup Script
# =============================================================================
# Starts all containers: redis, app, deepstream, vlm
#
# Usage:
#   RTSP_URI=rtsp://192.168.1.100:8554/webcam ./scripts/start-full-stack.sh
#
# Environment variables:
#   RTSP_URI      - Required. RTSP stream URL from Mac webcam script
#   STREAM_ID     - Optional. Identifier for the stream (default: stream_0)
#   VLM_MODEL     - Optional. VLM model name (default: VILA1.5-3b)
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

cd "$(dirname "$0")/.."

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Newport Demo - Full Stack${NC}"
echo -e "${BLUE}========================================${NC}"
echo

# Check for required RTSP_URI
if [ -z "$RTSP_URI" ]; then
    echo -e "${YELLOW}RTSP_URI not set.${NC}"
    echo
    echo "Please set the RTSP URI from your Mac streaming script."
    echo "Example:"
    echo "  export RTSP_URI=rtsp://192.168.1.100:8554/webcam"
    echo
    echo "Or run with:"
    echo "  RTSP_URI=rtsp://YOUR_MAC_IP:8554/webcam ./scripts/start-full-stack.sh"
    echo
    read -p "Enter your Mac's IP address: " mac_ip
    if [ -z "$mac_ip" ]; then
        echo -e "${RED}No IP provided. Exiting.${NC}"
        exit 1
    fi
    export RTSP_URI="rtsp://${mac_ip}:8554/webcam"
fi

echo -e "${GREEN}Configuration:${NC}"
echo "  RTSP_URI:   $RTSP_URI"
echo "  STREAM_ID:  ${STREAM_ID:-stream_0}"
echo "  VLM_MODEL:  ${VLM_MODEL:-Efficient-Large-Model/VILA1.5-3b}"
echo

# Check for required Docker images
echo -e "${YELLOW}Checking Docker images...${NC}"

check_image() {
    local image=$1
    if docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "$image"; then
        echo -e "  ${GREEN}✓${NC} $image"
        return 0
    else
        echo -e "  ${RED}✗${NC} $image (not found)"
        return 1
    fi
}

missing=0
check_image "nvcr.io/nvidia/deepstream:7.0-gc-triton-devel" || missing=1
check_image "dustynv/nano_llm:r36.4.0" || missing=1
check_image "redis:7-alpine" || missing=1

if [ $missing -eq 1 ]; then
    echo
    echo -e "${RED}Missing required images. Pull them with:${NC}"
    echo "  docker pull nvcr.io/nvidia/deepstream:7.0-gc-triton-devel"
    echo "  docker pull dustynv/nano_llm:r36.4.0"
    echo "  docker pull redis:7-alpine"
    exit 1
fi

echo
echo -e "${YELLOW}Stopping any existing containers...${NC}"
docker compose down 2>/dev/null || true

echo
echo -e "${YELLOW}Starting full stack...${NC}"
docker compose up -d

echo
echo -e "${GREEN}Stack started!${NC}"
echo
echo "View logs:"
echo "  docker compose logs -f          # All services"
echo "  docker compose logs -f app      # App only"
echo "  docker compose logs -f vlm      # VLM only"
echo "  docker compose logs -f deepstream # DeepStream only"
echo
echo "Check status:"
echo "  docker compose ps"
echo
echo "Access points:"
echo "  Dashboard:    http://localhost:8080"
echo "  Redis CLI:    docker compose exec redis redis-cli"
echo
echo "Stop:"
echo "  docker compose down"
