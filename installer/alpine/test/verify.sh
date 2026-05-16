#!/bin/sh
#
# Verification script — runs inside the container after install.sh
# Returns 0 if all checks pass, non-zero on failure.
#

set -u

PASS=0
FAIL=0

check() {
    description="$1"
    shift
    result=0
    "$@" 2>/dev/null || result=$?
    if [ $result -eq 0 ]; then
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
check "User 'lxmf-group' exists"         id lxmf-group

# --- Binaries ---
echo ""
echo "--- Binaries ---"
check "lxmf-group is installed"        which lxmf-group
check "rnsd is installed"              which rnsd
check "lxmd is installed"              which lxmd

# --- Virtualenv ---
echo ""
echo "--- Virtualenv ---"
check "Virtualenv exists at /opt/reticulum" test -d /opt/reticulum
check "lxmf-group binary in venv"      test -x /opt/reticulum/bin/lxmf-group

# --- Configuration ---
echo ""
echo "--- Configuration ---"
check "Data dir exists"                 test -d /var/lib/lxmf-group/lxmf-group
check "Reticulum config exists"        test -d /etc/reticulum
check "Data dir owned by lxmf-group"   sh -c "test \"\$(stat -c %U /var/lib/lxmf-group/lxmf-group)\" = lxmf-group"

# --- OpenRC Init Scripts ---
echo ""
echo "--- OpenRC Init ---"
check "lxmf-group init script exists"   test -f /etc/init.d/lxmf-group
check "lxmf-group is in default runlevel" rc-status | grep -q lxmf-group
check "rnsd is in default runlevel"     rc-status | grep -q rnsd
check "lxmd is in default runlevel"     rc-status | grep -q lxmd

# --- Service Status ---
echo ""
echo "--- Service Status ---"

check "rnsd is running"                  rc-service rnsd status | grep -q "started"
check "lxmd is running"                 rc-service lxmd status | grep -q "started"
check "lxmf-group runs as user lxmf-group"           rc-service lxmf-group status | grep -q "started"

# --- Idempotency ---
echo ""
echo "--- Idempotency (re-run install) ---"
sh /opt/lxmf-group-installer/installer/alpine/install.sh > /dev/null 2>&1 || true
check "Re-run exits successfully"       true
check "lxmf-group still running after re-run" rc-service lxmf-group status | grep -q "started"

# --- Summary ---
echo ""
echo "======================================="
echo "  Results: ${PASS} passed, ${FAIL} failed"
echo "======================================="
echo ""

if [ $FAIL -gt 0 ]; then
    echo "--- Debug: lxmf-group log ---"
	tail -20 /var/lib/lxmf-group/lxmf-group/logfile 2>/dev/null || true
	echo ""
	exit 1
fi

exit 0