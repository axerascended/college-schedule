#!/usr/bin/env bash
# Настройка домена: nginx → uvicorn:8000, опционально HTTPS (Let's Encrypt).
# Запуск на ВМ: sudo bash deploy/setup-domain.sh
# Переменные: DOMAIN (обязательно), CERTBOT_EMAIL (для HTTPS, необязательно).

set -euo pipefail

DOMAIN="${DOMAIN:-da.servers31.ru}"
APP_DIR="/home/yc-user/college-schedule"
NGINX_SITE="/etc/nginx/sites-available/schedule"
NGINX_ENABLED="/etc/nginx/sites-enabled/schedule"

echo "==> Domain: ${DOMAIN}"

echo "==> Installing nginx and certbot..."
sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq nginx certbot python3-certbot-nginx

echo "==> Configuring nginx reverse proxy..."
sed "s/DOMAIN_PLACEHOLDER/${DOMAIN}/g" "${APP_DIR}/deploy/nginx-schedule.conf" | sudo tee "${NGINX_SITE}" >/dev/null
sudo ln -sf "${NGINX_SITE}" "${NGINX_ENABLED}"
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl reload nginx

echo "==> HTTP proxy ready. Check: http://${DOMAIN}/login"
echo "    (DNS A-запись должна указывать на публичный IP этой ВМ)"

if command -v dig >/dev/null 2>&1; then
  echo "==> DNS check (dig):"
  dig +short A "${DOMAIN}" || true
fi

if [[ -n "${CERTBOT_EMAIL:-}" ]]; then
  echo "==> Requesting HTTPS certificate..."
  sudo certbot --nginx -d "${DOMAIN}" \
    --non-interactive --agree-tos -m "${CERTBOT_EMAIL}" \
    --redirect
  echo "==> HTTPS ready: https://${DOMAIN}/login"
else
  echo "==> HTTPS skipped (set CERTBOT_EMAIL to enable certbot)."
  echo "    Example:"
  echo "    sudo CERTBOT_EMAIL=you@mail.ru bash ${APP_DIR}/deploy/setup-domain.sh"
fi
