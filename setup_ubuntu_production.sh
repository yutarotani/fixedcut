#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   chmod +x setup_ubuntu_production.sh
#   ./setup_ubuntu_production.sh
#
# What this script does (Ubuntu):
# 1) Installs Python and build tools
# 2) Creates a virtual environment
# 3) Installs app dependencies + production dependencies (gunicorn)
# 4) Creates/updates a systemd service for this app
# 5) Starts and enables the service

APP_NAME="fixedcut"
APP_USER="${SUDO_USER:-$USER}"
APP_GROUP="${APP_USER}"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_DIR}/.venv-linux"
SERVICE_FILE="/etc/systemd/system/${APP_NAME}.service"
PYTHON_BIN="${VENV_DIR}/bin/python"
GUNICORN_BIN="${VENV_DIR}/bin/gunicorn"

echo "[1/6] Installing OS packages..."
sudo apt-get update -y
sudo apt-get install -y \
  python3 \
  python3-venv \
  python3-pip \
  build-essential

echo "[2/6] Creating virtual environment..."
python3 -m venv "${VENV_DIR}"

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

echo "[3/6] Upgrading pip/setuptools/wheel..."
"${PYTHON_BIN}" -m pip install --upgrade pip setuptools wheel

echo "[4/6] Installing Python dependencies..."
"${PYTHON_BIN}" -m pip install -r "${PROJECT_DIR}/requirements.txt"
"${PYTHON_BIN}" -m pip install -r "${PROJECT_DIR}/requirements_production.txt"

echo "[5/6] Creating systemd service..."
sudo tee "${SERVICE_FILE}" > /dev/null <<EOF
[Unit]
Description=FixedCut Flask App (Gunicorn)
After=network.target

[Service]
Type=simple
User=${APP_USER}
Group=${APP_GROUP}
WorkingDirectory=${PROJECT_DIR}
Environment=PYTHONUNBUFFERED=1
ExecStart=${GUNICORN_BIN} -w 1 -b 0.0.0.0:8000 server:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "[6/6] Reloading and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable "${APP_NAME}.service"
sudo systemctl restart "${APP_NAME}.service"

echo "Done. Service status:"
sudo systemctl --no-pager status "${APP_NAME}.service" || true

echo "Logs (latest):"
sudo journalctl -u "${APP_NAME}.service" -n 50 --no-pager || true
