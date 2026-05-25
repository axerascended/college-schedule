#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/home/yc-user/college-schedule"
SERVICE_NAME="schedule"

cd "$APP_DIR"

echo "==> Pulling latest code..."
git fetch origin master
git reset --hard origin/master

echo "==> Installing dependencies..."
.venv/bin/pip install -r requirements.txt -q

echo "==> Running migrations..."
.venv/bin/alembic upgrade head

echo "==> Restarting application..."
sudo systemctl restart "${SERVICE_NAME}"

echo "==> Deploy finished."
sudo systemctl --no-pager status "${SERVICE_NAME}" | head -n 5
