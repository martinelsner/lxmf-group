#!/usr/bin/env bash
#
# lxmf-group Installer for Debian
#
# Installs lxmf-group as a systemd service with a dedicated
# system user, hardened unit files, and default configurations.
#
# This script is designed to work alongside reticulum-installer.
# If rnsd and lxmd were installed with reticulum-installer, this
# script will automatically detect and use their paths.
#
# Usage: sudo bash install.sh
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DATA_DIR="/var/lib/lxmf-group"
VENV_DIR="/opt/reticulum"

# ---------- Preflight ----------

if [[ $EUID -ne 0 ]]; then
    echo "Error: This script must be run as root (sudo)."
    exit 1
fi

echo "==> lxmf-group Installer"
echo ""

# ---------- Detect Reticulum Paths ----------

echo "--- Detecting Reticulum and LXMD installations ---"

# Check if rnsd exists in standard locations
if [[ -x "/opt/reticulum/bin/rnsd" ]]; then
    echo "    Using rnsd from /opt/reticulum (reticulum-installer detected)"
elif [[ -x "/usr/local/bin/rnsd" ]]; then
    echo "    Using rnsd from /usr/local/bin"
else
    echo "    Warning: rnsd not found, will install if needed"
fi

if [[ -x "/opt/reticulum/bin/lxmd" ]]; then
    echo "    Using lxmd from /opt/reticulum (reticulum-installer detected)"
elif [[ -x "/usr/local/bin/lxmd" ]]; then
    echo "    Using lxmd from /usr/local/bin"
else
    echo "    Warning: lxmd not found, will install if needed"
fi

# ---------- Dependencies ----------

echo ""
echo "--- Installing system dependencies ---"
apt-get update
apt-get install -y python3 python3-pip python3-venv python3-cryptography
echo "    System packages installed."

# ---------- Virtual Environment ----------

echo ""
echo "--- Installing lxmf-group ---"
if [[ ! -d "$VENV_DIR" ]]; then
    python3 -m venv "$VENV_DIR"
    echo "    Created virtualenv at $VENV_DIR"
fi
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install git+https://codeberg.org/melsner/lxmf_group.git
echo "    lxmf-group installed in virtualenv."

# Symlink binary to system PATH
ln -sf "$VENV_DIR/bin/lxmf-group" "/usr/local/bin/lxmf-group"
echo "    Symlinked lxmf-group -> /usr/local/bin/lxmf-group"

# ---------- User & Group ----------

echo ""
echo "--- Creating system user and group ---"

if ! getent group lxmf-group > /dev/null 2>&1; then
    groupadd --system lxmf-group
    echo "    Created group: lxmf-group"
else
    echo "    Group 'lxmf-group' already exists."
fi

if ! id lxmf-group > /dev/null 2>&1; then
    useradd \
        --system \
        --gid lxmf-group \
        --groups dialout \
        --shell /usr/sbin/nologin \
        lxmf-group
    echo "    Created user: lxmf-group (with dialout access for RNodes)"
else
    echo "    User 'lxmf-group' already exists."
    usermod --append --groups dialout lxmf-group 2>/dev/null || true
fi

# Ensure data directory exists
mkdir -p "$DATA_DIR/lxmf-group"
chown -R lxmf-group:lxmf-group "$DATA_DIR"
chmod 750 "$DATA_DIR"
echo "    Data directory created at ${DATA_DIR}"

# ---------- Systemd Units ----------

echo ""
echo "--- Installing systemd service file ---"

# Create the service file dynamically based on detected paths
cat > /etc/systemd/system/lxmf-group.service << EOF
[Unit]
Description=LXMF Group Server
After=network.target rnsd.service
Wants=network.target rnsd.service
Requires=lxmd.service

[Service]
Type=simple
User=lxmf-group
Group=lxmf-group
ExecStart=${VENV_DIR}/bin/lxmf-group --data ${DATA_DIR}/lxmf-group --rnsconfig /etc/reticulum
Restart=on-failure
RestartSec=10s

NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=full
ProtectHome=yes
ReadWritePaths=${DATA_DIR}/lxmf-group
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
RestrictNamespaces=yes
LockPersonality=yes
RestrictRealtime=yes
RestrictSUIDSGID=yes
PrivateDevices=no

[Install]
WantedBy=multi-user.target
EOF

cp /etc/systemd/system/lxmf-group.service "${SCRIPT_DIR}/lxmf-group.service"
echo "    Installed lxmf-group.service"

systemctl daemon-reload
echo "    Reloaded systemd daemon."

# ---------- Enable & Start ----------

echo ""
echo "--- Enabling and starting service ---"

systemctl enable lxmf-group.service
systemctl start lxmf-group.service
echo "    lxmf-group: enabled and started."

# ---------- Summary ----------

echo ""
echo "==========================================="
echo "  Installation complete!"
echo "==========================================="
echo ""
echo "  IMPORTANT: rnsd must be running before lxmf-group starts."
echo "  lxmf-group connects to the shared rnsd instance via"
echo "  require_shared_instance=True and will exit if rnsd is not running."
echo ""
echo "  Service:"
echo "    lxmf-group -> systemctl status lxmf-group"
echo ""
echo "  Data directory:"
echo "    ${DATA_DIR}/lxmf-group"
echo ""
	echo "  Reticulum config:"
	echo "    /etc/reticulum"
echo ""
echo "  Logs:"
echo "    journalctl -u lxmf-group -f"
echo ""
echo "  To reconfigure, edit the config files and run:"
echo "    systemctl restart lxmf-group"
echo ""
echo "  IMPORTANT: On first run, a claim token is printed to the"
echo "  journal. Send that token as a message to the Admin Group"
echo "  from your LXMF client to become admin."
echo ""
echo "    journalctl -u lxmf-group --output=cat | grep -i token"
echo ""