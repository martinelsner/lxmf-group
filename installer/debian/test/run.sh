#!/usr/bin/env bash
#
# Test runner — builds and runs the installer test in a Docker container.
# This test runs reticulum-installer first (to set up rnsd/lxmd), then
# runs lxmf-group installer to test integration.
#
# Usage: bash test/run.sh
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
CONTAINER_NAME="lxmf-group-installer-test"
IMAGE_NAME="lxmf-group-installer-test"

cleanup() {
    echo ""
    echo "--- Cleaning up ---"
    docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
}
trap cleanup EXIT

echo "==> lxmf-group Installer Test"
echo ""

# --- Build ---
echo "--- Building test image ---"
docker build -t "$IMAGE_NAME" -f "${SCRIPT_DIR}/Dockerfile" "$PROJECT_DIR"
echo ""

# --- Start container with systemd ---
echo "--- Starting container ---"
docker run -d \
    --name "$CONTAINER_NAME" \
    --privileged \
    --cgroupns=host \
    -v /sys/fs/cgroup:/sys/fs/cgroup:rw \
    "$IMAGE_NAME"

# Wait for systemd to be ready
echo "    Waiting for systemd to initialize..."
for i in $(seq 1 30); do
    if docker exec "$CONTAINER_NAME" systemctl is-system-running --wait 2>/dev/null | grep -qE "running|degraded"; then
        break
    fi
    sleep 1
done
echo "    Container ready."
echo ""

# --- Clone and run reticulum-installer first ---
echo "--- Cloning and running reticulum-installer ---"
docker exec "$CONTAINER_NAME" bash -c "cd /tmp && git clone https://codeberg.org/melsner/reticulum-installer.git"
docker exec "$CONTAINER_NAME" bash /tmp/reticulum-installer/debian/install.sh
echo ""

# --- Wait for services to settle ---
echo "--- Waiting for rnsd/lxmd to start ---"
sleep 10

# --- Run lxmf-group installer ---
echo "--- Running lxmf-group install.sh ---"
docker exec "$CONTAINER_NAME" bash /opt/lxmf-group-installer/installer/debian/install.sh
echo ""

# --- Wait for services to settle ---
echo "--- Waiting for lxmf-group to start ---"
sleep 10

# --- Run verification ---
echo "--- Running verification ---"
docker exec "$CONTAINER_NAME" bash /opt/lxmf-group-installer/installer/debian/test/verify.sh
RESULT=$?

exit $RESULT