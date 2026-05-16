#!/usr/bin/env bash
#
# lxmf-group Uninstaller for Debian
#
# Removes the systemd service, virtualenv, and system binaries.
# Leaves configuration and user data intact.
#
# Usage: sudo bash uninstall.sh
#

set -uo pipefail

if [[ $EUID -ne 0 ]]; then
    echo "Error: This script must be run as root (sudo)."
    exit 1
fi

echo "==> lxmf-group Uninstaller"
echo ""

# ---------- Stop & Disable ----------

echo "--- Stopping and disabling service ---"
systemctl stop lxmf-group.service 2>/dev/null || true
systemctl disable lxmf-group.service 2>/dev/null || true

# ---------- Service Files ----------

echo "--- Removing systemd service file ---"
rm -f /etc/systemd/system/lxmf-group.service
systemctl daemon-reload

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
echo "    userdel lxmf-group"
echo ""