#!/bin/bash
#
# Test runner — builds and runs the installer test in a Docker container.
# This test runs reticulum-installer first (to set up rnsd/lxmd), then
# runs lxmf-group installer to test integration.
#
# Usage: bash test/run.sh
#

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
CONTAINER_NAME="lxmf-group-installer-test-alpine"
IMAGE_NAME="lxmf-group-installer-test-alpine"

cleanup() {
    echo ""
    echo "--- Cleaning up ---"
    docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
}
trap cleanup EXIT

echo "==> lxmf-group Installer Test (Alpine)"
echo ""

# --- Build ---
echo "--- Building test image ---"
docker build -t "$IMAGE_NAME" -f "${SCRIPT_DIR}/Dockerfile" "$PROJECT_DIR"
echo ""

# --- Start container ---
echo "--- Starting container ---"
docker run -d \
    --name "$CONTAINER_NAME" \
    "$IMAGE_NAME"

# Wait for container to be ready
echo "    Waiting for container to initialize..."
sleep 5
echo "    Container ready."
echo ""

# --- Clone and run reticulum-installer first ---
echo "--- Cloning and running reticulum-installer ---"
docker exec "$CONTAINER_NAME" sh -c "cd /tmp && git clone https://codeberg.org/melsner/reticulum-installer.git"
docker exec "$CONTAINER_NAME" sh /tmp/reticulum-installer/alpine/install.sh
echo ""

# --- Wait for services to settle ---
echo "--- Waiting for rnsd/lxmd to start ---"
sleep 20
echo ""

# --- Run lxmf-group installer ---
echo "--- Running lxmf-group install.sh ---"
docker exec "$CONTAINER_NAME" sh /opt/lxmf-group-installer/installer/alpine/install.sh
echo ""

# --- Wait for services to settle ---
echo "--- Waiting for lxmf-group to start ---"
sleep 10

# --- Run verification ---
echo "--- Running verification ---"
docker exec "$CONTAINER_NAME" sh /opt/lxmf-group-installer/installer/alpine/test/verify.sh
RESULT=$?
echo ""

exit $RESULT