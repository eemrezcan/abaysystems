#!/usr/bin/env bash
set -euo pipefail
cd /opt/abaysystems

# .env'yi yükle
set -a; source /opt/abaysystems/.env; set +a

# venv
source /opt/abaysystems/venv/bin/activate

# kodu güncelle
git fetch --all
git reset --hard origin/main  || git reset --hard origin/master

# bağımlılıkları güncelle (requirements varsa)
[ -f requirements.txt ] && pip install -r requirements.txt || true

# migrate
alembic upgrade head || python -m alembic upgrade head

# servis restart
sudo systemctl restart abaysystems.service
sleep 1
systemctl --no-pager -l status abaysystems.service | sed -n '1,12p'
echo "✅ Backend deploy bitti."
