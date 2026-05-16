#!/bin/sh
#
# lxmf-group Uninstaller for Alpine Linux
#
# Removes the OpenRC service, virtualenv, and system binaries.
# Leaves configuration and user data intact.
#
# Usage: sudo sh uninstall.sh
#

set -u

if [ "$(id -u)" -ne 0 ]; then
    echo "Error: This script must be run as root (sudo)."
    exit 1
fi

echo "==> lxmf-group Uninstaller (Alpine)"
echo ""

# ---------- Stop & Disable ----------

echo "--- Stopping and disabling service ---"
rc-service lxmf-group stop 2>/dev/null || true
rc-update del lxmf-group default 2>/dev/null || true

# ---------- Service Files ----------

echo "--- Removing OpenRC init script ---"
rm -f /etc/init.d/lxmf-group

# ---------- Binary ----------

echo "--- Removing executable and virtualenv ---"
rm -f /usr/local/bin/lxmf-group
rm -rf /opt/lxmf-group
echo "    Removed virtualenv at /opt/lxmf-group"

# ---------- Summary ----------

echo ""
echo "==========================================="
echo "  Uninstallation complete!"
echo "==========================================="
echo ""
echo "Note: The data directory (/var/lib/lxmf-group/lxmf-group) and the user 'lxmf-group' were NOT removed."
echo "If you wish to remove them completely, run:"
echo "    rm -rf /var/lib/lxmf-group/lxmf-group"
echo "    deluser lxmf-group"
echo ""