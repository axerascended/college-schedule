#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/home/yc-user/college-schedule"
REPO_URL="https://github.com/axerascended/college-schedule.git"
SERVICE_NAME="schedule"

echo "==> Installing system packages..."
sudo apt-get update -qq
sudo apt-get install -y -qq git python3.11 python3.11-venv

if [[ ! -d "$APP_DIR/.git" ]]; then
  echo "==> Cloning repository..."
  git clone "$REPO_URL" "$APP_DIR"
else
  echo "==> Repository already exists at $APP_DIR"
fi

cd "$APP_DIR"
chmod +x deploy/deploy.sh

echo "==> Creating virtualenv..."
python3.11 -m venv .venv
.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -r requirements.txt -q

if [[ ! -f .env ]]; then
  echo "==> Creating .env..."
  secret_key="$(openssl rand -hex 32)"
  cat > .env <<EOF
SECRET_KEY=${secret_key}
DATABASE_URL=sqlite:////home/yc-user/college-schedule/data/schedule.db
DEBUG=false
EOF
fi

mkdir -p data

echo "==> Running migrations..."
.venv/bin/alembic upgrade head

if [[ ! -f data/.seeded ]]; then
  echo "==> Seeding demo data..."
  .venv/bin/python -m app.scripts.seed
  touch data/.seeded
fi

echo "==> Installing systemd unit..."
sudo cp deploy/schedule.service /etc/systemd/system/${SERVICE_NAME}.service
sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}"
sudo systemctl restart "${SERVICE_NAME}"

echo "==> Done. Service status:"
sudo systemctl --no-pager status "${SERVICE_NAME}"
