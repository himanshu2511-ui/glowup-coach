#!/bin/sh
# ─── Glowup Coach — Production Startup Script ────────────────────────────────
# NOTE: Table creation is handled by SQLAlchemy create_all() inside the
# FastAPI lifespan (main.py). Gunicorn must start IMMEDIATELY so Render
# can detect the open port within its timeout window.
# Alembic is used for FUTURE schema migrations, not initial startup.

set -e

echo "🚀 Starting Glowup Coach API on port ${PORT:-8000}..."
exec gunicorn main:app \
    --workers "${WEB_CONCURRENCY:-2}" \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind "0.0.0.0:${PORT:-8000}" \
    --timeout 120 \
    --keep-alive 5 \
    --access-logfile - \
    --error-logfile -
