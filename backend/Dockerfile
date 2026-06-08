# ════════════════════════════════════════════════════════════════════════════════
# Glowup Coach — Production Dockerfile
# Multi-stage build: smaller final image, non-root user, gunicorn + uvicorn workers
# ════════════════════════════════════════════════════════════════════════════════

# ─── Stage 1: dependency builder ────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# System deps needed to compile some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc g++ libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt


# ─── Stage 2: runtime image ─────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Runtime system dependencies for MediaPipe + OpenCV headless
# NOTE: python:3.11-slim is based on Debian Bookworm where:
#   libgl1-mesa-glx was split → use libgl1
#   libxrender-dev  is build-only → use libxrender1 (runtime)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libglib2.0-0 \
        libgl1 \
        libsm6 \
        libxext6 \
        libxrender1 \
        libgomp1 \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Create non-root user for security
RUN groupadd -r glowup && useradd -r -g glowup -d /app glowup

# Copy application source
COPY . .

# Create writable directories, make startup script executable, set ownership
RUN mkdir -p /app/data /app/reports && \
    chmod +x /app/start.sh && \
    chown -R glowup:glowup /app

USER glowup

EXPOSE 8000

# Health check so Render/Docker knows when the service is ready
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production: start.sh runs migrations then launches gunicorn
CMD ["/app/start.sh"]
