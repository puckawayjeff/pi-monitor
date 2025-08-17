#!/bin/bash

# Pi-Monitor Installation Script (Bootstrapper)
# This script downloads the latest release, installs dependencies,
# and sets up the monitor as a systemd service.

# --- Configuration ---
# GitHub repository to fetch the release from.
GITHUB_REPO="puckawayjeff/pi-monitor"

INSTALL_DIR="/opt/pi-monitor"
PYTHON_VENV_DIR="$INSTALL_DIR/venv"

# --- Pre-flight Checks ---
if [ "$EUID" -ne 0 ]; then
  echo "This script must be run as root. Please use 'sudo ./install.sh' or 'wget -O - ... | sudo bash'"
  exit 1
fi

echo "--- Pi-Monitor Installer ---"
echo ""
echo "IMPORTANT: You may need to enable SPI and I2C via 'sudo raspi-config' for the display to work."
echo ""
# --- User Detection and Confirmation ---
# When running via 'sudo bash', SUDO_USER will be the non-root user. Default to 'pi' if not set.
SERVICE_USER=${SUDO_USER:-pi}
echo "Service will be installed for user: $SERVICE_USER"
echo ""

# --- Step 1: Install System Dependencies ---
echo "[1/7] Installing system dependencies..."
apt-get update
apt-get install -y curl python3 python3-pip python3-venv python3-dev libgpiod2

# --- Step 2: Find and Download Latest Release ---
echo "[2/7] Finding latest release from $GITHUB_REPO..."
# Use the GitHub API to get the URL for the latest release's tarball
LATEST_RELEASE_URL=$(curl -s "https://api.github.com/repos/$GITHUB_REPO/releases/latest" | grep "tarball_url" | awk -F '"' '{print $4}')

if [ -z "$LATEST_RELEASE_URL" ]; then
  echo "Error: Could not find the latest release URL. Please check the repository name."
  exit 1
fi

echo "Downloading from: $LATEST_RELEASE_URL"
# Download to a temporary file
TEMP_TAR_FILE=$(mktemp)
curl -L "$LATEST_RELEASE_URL" -o "$TEMP_TAR_FILE"

# --- Step 3: Set up Installation Directory ---
echo "[3/7] Creating installation directory at $INSTALL_DIR..."
# Clean up old installation if it exists
if [ -d "$INSTALL_DIR" ]; then
    echo "Existing installation found. Removing for a clean install."
    systemctl stop pi-monitor.service >/dev/null 2>&1
    rm -rf "$INSTALL_DIR"
fi
mkdir -p "$INSTALL_DIR"

# --- Step 4: Extract Project Files ---
echo "[4/7] Extracting project files..."
# Extract the tarball into the install directory. The --strip-components=1 part
# removes the top-level folder from the archive, placing files directly in $INSTALL_DIR.
tar -xzf "$TEMP_TAR_FILE" -C "$INSTALL_DIR" --strip-components=1
rm "$TEMP_TAR_FILE"
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"

# --- Step 5: Set up Python Virtual Environment ---
echo "[5/7] Creating Python virtual environment..."
sudo -u "$SERVICE_USER" python3 -m venv "$PYTHON_VENV_DIR"

echo "[6/7] Installing Python dependencies..."
# Directly use the pip from the virtual environment
"$PYTHON_VENV_DIR/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

# --- Step 6: Create and Configure systemd Service ---
echo "[7/7] Creating and enabling systemd service..."
SERVICE_FILE="/etc/systemd/system/pi-monitor.service"
cat > "$SERVICE_FILE" << EOL
[Unit]
Description=Pi-Monitor Service
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=1
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$PYTHON_VENV_DIR/bin/python $INSTALL_DIR/main.py

[Install]
WantedBy=multi-user.target
EOL

systemctl daemon-reload
systemctl enable pi-monitor.service
systemctl start pi-monitor.service

# --- Final Instructions ---
echo ""
echo "--- Installation Complete! ---"
echo "The Pi-Monitor service is now running."
echo "You can check its status with: sudo systemctl status pi-monitor.service"
echo "Configuration file is located at: $INSTALL_DIR/config.yaml"
echo "To view logs, use: sudo journalctl -u pi-monitor.service -f"
echo ""
echo "IMPORTANT: You may need to enable SPI and I2C via 'sudo raspi-config' for the display to work."