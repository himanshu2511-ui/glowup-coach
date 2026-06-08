#!/bin/sh
# ─── Glowup Coach — Production Startup Script ────────────────────────────────
# Runs DB migrations then starts gunicorn.
# Used as the Docker CMD in production.

set -e   # exit immediately on any error

echo "🔄 Running database migrations..."
alembic upgrade head
echo "✅ Migrations complete"

echo "🚀 Starting Glowup Coach API..."
exec gunicorn main:app \
    --workers "${WEB_CONCURRENCY:-2}" \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind "0.0.0.0:${PORT:-8000}" \
    --timeout 120 \
    --keep-alive 5 \
    --access-logfile - \
    --error-logfile -
