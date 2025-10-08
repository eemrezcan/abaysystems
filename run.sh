#!/usr/bin/env bash
set -euo pipefail

# .env yükle
set -a
source /opt/abaysystems/.env
set +a

# sanal ortam
source /opt/abaysystems/venv/bin/activate

# Uvicorn (gerekirse "main:app" → "app.main:app" yap)
exec uvicorn main:app \
  --host 127.0.0.1 \
  --port 8000 \
  --workers 2 \
  --proxy-headers
