#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════╗
# ║          Glowup Coach — One-Command Dev Launcher         ║
# ╚══════════════════════════════════════════════════════════╝
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT/backend"
FRONTEND_DIR="$ROOT/frontend"
BACKEND_LOG="/tmp/glowup_backend.log"
FRONTEND_LOG="/tmp/glowup_frontend.log"

echo ""
echo "╔════════════════════════════════════════╗"
echo "║       ✨ Glowup Coach Launcher         ║"
echo "╚════════════════════════════════════════╝"
echo ""

# ── Kill existing processes ──────────────────────────────────
echo "🧹 Clearing ports 8000 and 5173..."
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
lsof -ti :5173 | xargs kill -9 2>/dev/null || true
sleep 1

# ── Python env setup ─────────────────────────────────────────
echo "🐍 Setting up Python environment..."
cd "$BACKEND_DIR"
if [ ! -d "venv" ]; then
  python3 -m venv venv
  echo "  ✅ Created virtualenv"
fi
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "  ✅ Python dependencies installed"

# ── Ensure data directory ────────────────────────────────────
mkdir -p "$ROOT/data"

# ── Start backend ────────────────────────────────────────────
echo "🚀 Starting FastAPI backend on :8000..."
cd "$BACKEND_DIR"
source venv/bin/activate
nohup uvicorn main:app --host 0.0.0.0 --port 8000 --reload \
  > "$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!
echo "  PID: $BACKEND_PID  |  Logs: $BACKEND_LOG"

# Wait for backend to be ready
echo "  ⏳ Waiting for backend..."
for i in {1..20}; do
  if lsof -ti :8000 &>/dev/null; then
    echo "  ✅ Backend ready!"
    break
  fi
  sleep 1
done

# ── Frontend setup ───────────────────────────────────────────
echo "📦 Setting up frontend..."
cd "$FRONTEND_DIR"
if [ ! -d "node_modules" ]; then
  npm install
  echo "  ✅ npm packages installed"
fi

# ── Start frontend ───────────────────────────────────────────
echo "🎨 Starting Vite frontend on :5173..."
nohup npm run dev > "$FRONTEND_LOG" 2>&1 &
FRONTEND_PID=$!
echo "  PID: $FRONTEND_PID  |  Logs: $FRONTEND_LOG"

# Wait for frontend
echo "  ⏳ Waiting for frontend..."
for i in {1..15}; do
  if lsof -ti :5173 &>/dev/null; then
    echo "  ✅ Frontend ready!"
    break
  fi
  sleep 1
done

# ── Health check ─────────────────────────────────────────────
echo ""
echo "🩺 Health check..."
curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "  ⚠️  Backend might still be starting..."

# ── Summary ──────────────────────────────────────────────────
echo ""
echo "╔════════════════════════════════════════╗"
echo "║            🎉 All Systems Go!          ║"
echo "╠════════════════════════════════════════╣"
echo "║  App:      http://localhost:5173       ║"
echo "║  API:      http://localhost:8000       ║"
echo "║  API Docs: http://localhost:8000/docs  ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo "Logs: $BACKEND_LOG  |  $FRONTEND_LOG"
echo ""
echo "Press Ctrl+C to stop all services."

# ── Trap cleanup ─────────────────────────────────────────────
cleanup() {
  echo ""
  echo "🛑 Shutting down..."
  kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
  lsof -ti :8000 | xargs kill -9 2>/dev/null || true
  lsof -ti :5173 | xargs kill -9 2>/dev/null || true
  echo "✅ Done."
}
trap cleanup EXIT INT TERM

# ── Keep script alive ────────────────────────────────────────
wait
