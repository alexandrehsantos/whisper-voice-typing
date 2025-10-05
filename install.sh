#!/bin/bash

# Voice Daemon Service Installer

set -e

USER=$(whoami)
SERVICE_NAME="voice-daemon"
DAEMON_SCRIPT="/home/fns/tools/voice-daemon.py"
SERVICE_FILE="$HOME/.config/systemd/user/${SERVICE_NAME}.service"

echo "=========================================="
echo "Voice Daemon Service Installer"
echo "=========================================="

# Install dependencies
echo "[1/5] Installing dependencies..."
pip install --user pynput faster-whisper pyaudio 2>&1 | grep -v "Requirement already satisfied" || true

# Make daemon executable
echo "[2/5] Making daemon executable..."
chmod +x "$DAEMON_SCRIPT"

# Create systemd user directory if it doesn't exist
echo "[3/5] Creating systemd user directory..."
mkdir -p "$HOME/.config/systemd/user"

# Create systemd service file
echo "[4/5] Creating systemd service..."
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Voice Input Daemon
After=graphical-session.target

[Service]
Type=simple
Environment="DISPLAY=:0"
Environment="XAUTHORITY=/home/$USER/.Xauthority"
ExecStart=/usr/bin/python3 $DAEMON_SCRIPT -m small
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF

# Reload systemd and enable service
echo "[5/5] Enabling service..."
systemctl --user daemon-reload
systemctl --user enable "$SERVICE_NAME"

echo ""
echo "=========================================="
echo "✓ Installation complete!"
echo "=========================================="
echo ""
echo "Usage:"
echo "  Start:   systemctl --user start $SERVICE_NAME"
echo "  Stop:    systemctl --user stop $SERVICE_NAME"
echo "  Status:  systemctl --user status $SERVICE_NAME"
echo "  Logs:    journalctl --user -u $SERVICE_NAME -f"
echo ""
echo "Auto-start on login is ENABLED"
echo ""
echo "Hotkey: Ctrl+Alt+V (press to record voice)"
echo "Model: Whisper Small (better accuracy)"
echo ""
echo "=========================================="
