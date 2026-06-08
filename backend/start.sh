#!/bin/sh
# ─── Glowup Coach — Production Startup Script ────────────────────────────────
# Retries DB migrations with backoff, then starts gunicorn.

set -e

MAX_RETRIES=10
WAIT=3

echo "🔄 Running database migrations..."

for i in $(seq 1 $MAX_RETRIES); do
    if alembic upgrade head 2>&1; then
        echo "✅ Migrations complete"
        break
    fi

    if [ "$i" -eq "$MAX_RETRIES" ]; then
        echo "❌ Migrations failed after $MAX_RETRIES attempts. Aborting."
        exit 1
    fi

    echo "⏳ DB not ready (attempt $i/$MAX_RETRIES) — retrying in ${WAIT}s..."
    sleep $WAIT
    WAIT=$((WAIT * 2))   # exponential backoff: 3s, 6s, 12s, ...
done

echo "🚀 Starting Glowup Coach API..."
exec gunicorn main:app \
    --workers "${WEB_CONCURRENCY:-2}" \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind "0.0.0.0:${PORT:-8000}" \
    --timeout 120 \
    --keep-alive 5 \
    --access-logfile - \
    --error-logfile -
