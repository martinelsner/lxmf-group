#!/usr/bin/env bash
#
# Verification script — runs inside the container after install.sh
# Returns 0 if all checks pass, non-zero on failure.
#

set -euo pipefail

PASS=0
FAIL=0

check() {
    local description="$1"
    shift
    if "$@" > /dev/null 2>&1; then
        echo "  ✓ ${description}"
        PASS=$((PASS + 1))
    else
        echo "  ✗ ${description}"
        FAIL=$((FAIL + 1))
    fi
}

echo ""
echo "======================================="
echo "  lxmf-group Installer — Verification"
echo "======================================="

# --- User & Group ---
echo ""
echo "--- User & Group ---"
check "Group 'lxmf-group' exists"          getent group lxmf-group
check "User 'lxmf-group' exists"           id lxmf-group

# --- Binaries ---
echo ""
echo "--- Binaries ---"
check "lxmf-group is installed"           which lxmf-group
check "rnsd is installed"                 which rnsd
check "lxmd is installed"                 which lxmd

# --- Virtualenv ---
echo ""
echo "--- Virtualenv ---"
check "Virtualenv exists at /opt/reticulum" test -d /opt/reticulum
check "lxmf-group binary in venv"          test -x /opt/reticulum/bin/lxmf-group

# --- Configuration ---
echo ""
echo "--- Configuration ---"
check "Data dir exists"                   test -d /var/lib/lxmf-group/lxmf-group
check "Reticulum config exists"           test -d /etc/reticulum
check "Data dir owned by lxmf-group"       sh -c "test \"\$(stat -c %U /var/lib/lxmf-group/lxmf-group)\" = lxmf-group"

# --- Systemd Unit Files ---
echo ""
echo "--- Systemd Units ---"
check "lxmf-group.service file installed" test -f /etc/systemd/system/lxmf-group.service
check "lxmf-group.service is enabled"     systemctl is-enabled lxmf-group.service
check "rnsd.service is enabled"           systemctl is-enabled rnsd.service
check "lxmd.service is enabled"           systemctl is-enabled lxmd.service

# --- Service Status ---
echo ""
echo "--- Service Status ---"

check "rnsd.service is active"            systemctl is-active rnsd.service
check "lxmd.service is active"            systemctl is-active lxmd.service
check "lxmf-group.service is active"      systemctl is-active lxmf-group.service

# Check that processes are actually running under the reticulum user
check "lxmf-group runs as user lxmf-group"      sh -c "pgrep -u lxmf-group -f lxmf-group > /dev/null"
check "rnsd runs as user reticulum"        sh -c "pgrep -u reticulum -f rnsd > /dev/null"
check "lxmd runs as user reticulum"        sh -c "pgrep -u reticulum -f lxmd > /dev/null"

# --- Idempotency ---
echo ""
echo "--- Idempotency (re-run install) ---"
bash /opt/lxmf-group-installer/installer/debian/install.sh > /dev/null 2>&1
check "Re-run exits successfully"         true
check "lxmf-group still active after re-run" systemctl is-active lxmf-group.service

# --- Summary ---
echo ""
echo "======================================="
echo "  Results: ${PASS} passed, ${FAIL} failed"
echo "======================================="
echo ""

if [[ $FAIL -gt 0 ]]; then
    # Dump logs for debugging
    echo "--- Debug: lxmf-group journal ---"
    journalctl -u lxmf-group.service --no-pager -n 20 2>/dev/null || true
    echo ""
    echo "--- Debug: rnsd journal ---"
    journalctl -u rnsd.service --no-pager -n 20 2>/dev/null || true
    echo ""
    echo "--- Debug: lxmd journal ---"
    journalctl -u lxmd.service --no-pager -n 20 2>/dev/null || true
    exit 1
fi

exit 0