#!/bin/sh
#
# lxmf-group Installer for Alpine Linux
#
# Installs lxmf-group as an OpenRC service with a dedicated
# system user, init script, and default configurations.
#
# This script is designed to work alongside reticulum-installer.
# If rnsd and lxmd were installed with reticulum-installer, this
# script will automatically detect and use their paths.
#
# Usage: sudo sh install.sh
#

set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

DATA_DIR="/var/lib/lxmf-group"
VENV_DIR="/opt/reticulum"

# ---------- Preflight ----------

if [ "$(id -u)" -ne 0 ]; then
    echo "Error: This script must be run as root (sudo)."
    exit 1
fi

echo "==> lxmf-group Installer (Alpine)"
echo ""

# ---------- Detect Reticulum Paths ----------

echo "--- Detecting Reticulum and LXMD installations ---"

if [ -x "/opt/reticulum/bin/rnsd" ]; then
    echo "    Using rnsd from /opt/reticulum (reticulum-installer detected)"
elif [ -x "/usr/local/bin/rnsd" ]; then
    echo "    Using rnsd from /usr/local/bin"
else
    echo "    Warning: rnsd not found, will install if needed"
fi

if [ -x "/opt/reticulum/bin/lxmd" ]; then
    echo "    Using lxmd from /opt/reticulum (reticulum-installer detected)"
elif [ -x "/usr/local/bin/lxmd" ]; then
    echo "    Using lxmd from /usr/local/bin"
else
    echo "    Warning: lxmd not found, will install if needed"
fi

# ---------- Dependencies ----------

echo ""
echo "--- Installing system dependencies ---"
apk add python3 python3-dev py3-pip py3-virtualenv py3-cryptography py3-cffi build-base libffi-dev pkgconf
echo "    System packages installed."

# ---------- Virtual Environment ----------

echo ""
echo "--- Installing lxmf-group ---"
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv --system-site-packages "$VENV_DIR"
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
    addgroup -S lxmf-group
    echo "    Created group: lxmf-group"
else
    echo "    Group 'lxmf-group' already exists."
fi

if ! id lxmf-group > /dev/null 2>&1; then
    adduser -S -G lxmf-group -s /sbin/nologin -D lxmf-group
    addgroup lxmf-group dialout 2>/dev/null || true
    echo "    Created user: lxmf-group (with dialout access for RNodes)"
else
    echo "    User 'lxmf-group' already exists."
    addgroup lxmf-group dialout 2>/dev/null || true
fi

# Ensure data directory exists
mkdir -p "$DATA_DIR/lxmf-group"
chown -R lxmf-group:lxmf-group "$DATA_DIR"
chmod 750 "$DATA_DIR"
echo "    Data directory created at ${DATA_DIR}/lxmf-group"

# ---------- OpenRC Init Script ----------

echo ""
echo "--- Installing OpenRC init script ---"

cat > /etc/init.d/lxmf-group << EOF
#!/sbin/openrc-run

name="lxmf-group"
description="LXMF Group Server"
command="$VENV_DIR/bin/lxmf-group"
command_args="--data ${DATA_DIR}/lxmf-group --rnsconfig /etc/reticulum"
command_user="lxmf-group"
pidfile="/run/\${RC_SVCNAME}.pid"
output_log="${DATA_DIR}/lxmf-group/logfile"
error_log="${DATA_DIR}/lxmf-group/logfile"

depend() {
    need net
    after rnsd lxmd
}

start() {
    ebegin "Starting \${name}"
    start-stop-daemon --start --make-pidfile --background --pidfile "\${pidfile}" --user "\${command_user}" --exec "\${command}" -- \${command_args}
    eend \$?
}
EOF

chmod +x /etc/init.d/lxmf-group
cp /etc/init.d/lxmf-group "${SCRIPT_DIR}/lxmf-group.initd"
echo "    Installed /etc/init.d/lxmf-group"

# ---------- Enable & Start ----------

echo ""
echo "--- Enabling and starting service ---"

rc-update add lxmf-group default
rc-service lxmf-group start
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
echo "    lxmf-group -> rc-service lxmf-group status"
echo ""
echo "  Data directory:"
echo "    ${DATA_DIR}/lxmf-group"
echo ""
	echo "  Reticulum config:"
	echo "    /etc/reticulum"
echo ""
echo "  Logs:"
echo "    tail -f ${DATA_DIR}/lxmf-group/logfile"
echo ""
echo "  To reconfigure, edit the config files and run:"
echo "    rc-service lxmf-group restart"
echo ""
echo "  IMPORTANT: On first run, a claim token is printed to the"
echo "  log. Send that token as a message to the Admin Group"
echo "  from your LXMF client to become admin."
echo ""
echo "    grep -i token ${DATA_DIR}/lxmf-group/logfile"
echo ""