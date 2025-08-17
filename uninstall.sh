#!/bin/bash

# Pi-Monitor Uninstallation Script

# --- Configuration ---
INSTALL_DIR="/opt/pi-monitor"
SERVICE_FILE="/etc/systemd/system/pi-monitor.service"

# --- Pre-flight Checks ---
# Must be run as root
if [ "$EUID" -ne 0 ]; then
  echo "This script must be run as root. Please use 'sudo ./uninstall.sh'"
  exit 1
fi

echo "--- Pi-Monitor Uninstaller ---"

# --- Step 1: Stop and Disable the Service ---
echo "[1/3] Stopping and disabling systemd service..."
systemctl stop pi-monitor.service
systemctl disable pi-monitor.service

# --- Step 2: Remove Service File ---
echo "[2/3] Removing systemd service file..."
rm -f "$SERVICE_FILE"
systemctl daemon-reload

# --- Step 3: Remove Installation Directory ---
echo "[3/3] Removing installation directory: $INSTALL_DIR..."
rm -rf "$INSTALL_DIR"

echo ""
echo "--- Uninstallation Complete! ---"
echo "Pi-Monitor has been removed from your system."