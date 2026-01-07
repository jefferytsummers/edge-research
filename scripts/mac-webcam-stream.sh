#!/bin/bash
# =============================================================================
# Mac Webcam RTSP Streaming Script
# =============================================================================
# This script streams your Mac webcam as an RTSP source for the Newport Demo.
#
# Prerequisites:
#   brew install mediamtx ffmpeg
#
# Usage:
#   ./scripts/mac-webcam-stream.sh
#
# The script will:
#   1. Start MediaMTX RTSP server on port 8554
#   2. Capture your webcam and stream to the RTSP server
#   3. Display the RTSP URL to use on the Jetson
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
RTSP_PORT=8554
STREAM_NAME="webcam"
FRAMERATE=15
RESOLUTION="1280x720"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Mac Webcam RTSP Streaming Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo

# Check for required tools
check_dependencies() {
    echo -e "${YELLOW}Checking dependencies...${NC}"

    if ! command -v mediamtx &> /dev/null; then
        echo -e "${RED}ERROR: mediamtx not found${NC}"
        echo "Install with: brew install mediamtx"
        exit 1
    fi

    if ! command -v ffmpeg &> /dev/null; then
        echo -e "${RED}ERROR: ffmpeg not found${NC}"
        echo "Install with: brew install ffmpeg"
        exit 1
    fi

    echo -e "${GREEN}All dependencies found!${NC}"
    echo
}

# Get Mac's IP address
get_ip_address() {
    # Try to get the primary network interface IP
    IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "localhost")
    echo "$IP"
}

# List available video devices
list_devices() {
    echo -e "${YELLOW}Available video devices:${NC}"
    ffmpeg -f avfoundation -list_devices true -i "" 2>&1 | grep -E "^\[AVFoundation" | grep -i "video" || true
    echo
}

# Start RTSP server in background
start_rtsp_server() {
    echo -e "${YELLOW}Starting MediaMTX RTSP server on port ${RTSP_PORT}...${NC}"

    # Kill any existing mediamtx process
    pkill -f mediamtx 2>/dev/null || true
    sleep 1

    # Start mediamtx in background
    mediamtx &
    MEDIAMTX_PID=$!

    # Wait for server to start
    sleep 2

    if ! kill -0 $MEDIAMTX_PID 2>/dev/null; then
        echo -e "${RED}ERROR: Failed to start MediaMTX${NC}"
        exit 1
    fi

    echo -e "${GREEN}MediaMTX started (PID: $MEDIAMTX_PID)${NC}"
    echo
}

# Stream webcam
stream_webcam() {
    local device_id="${1:-0}"
    local ip=$(get_ip_address)

    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}RTSP Stream URL:${NC}"
    echo -e "${GREEN}  rtsp://${ip}:${RTSP_PORT}/${STREAM_NAME}${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo
    echo -e "${YELLOW}Streaming from device ${device_id} at ${RESOLUTION} ${FRAMERATE}fps${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop streaming${NC}"
    echo

    # Stream webcam to RTSP server
    ffmpeg -f avfoundation \
        -framerate "$FRAMERATE" \
        -video_size "$RESOLUTION" \
        -i "${device_id}" \
        -c:v libx264 \
        -preset ultrafast \
        -tune zerolatency \
        -b:v 2M \
        -maxrate 2M \
        -bufsize 1M \
        -pix_fmt yuv420p \
        -g 30 \
        -f rtsp \
        "rtsp://localhost:${RTSP_PORT}/${STREAM_NAME}"
}

# Cleanup on exit
cleanup() {
    echo
    echo -e "${YELLOW}Stopping streams...${NC}"
    pkill -f mediamtx 2>/dev/null || true
    echo -e "${GREEN}Done!${NC}"
}

trap cleanup EXIT

# Main
main() {
    check_dependencies
    list_devices

    # Ask for device ID
    echo -e "${YELLOW}Enter video device ID (default: 0):${NC}"
    read -r device_id
    device_id="${device_id:-0}"

    start_rtsp_server
    stream_webcam "$device_id"
}

main "$@"
