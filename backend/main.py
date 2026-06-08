"""
Glowup Coach — FastAPI Backend
Handles auth, facial analysis, leaderboard, and WebSocket notifications.
"""
import json
import os
import tempfile
import logging
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import (
    FastAPI, Depends, HTTPException, UploadFile, File,
    WebSocket, WebSocketDisconnect, status, Query,
)
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

import models
import schemas
import auth as auth_module
import analyzer
import scorer as scorer_module
import guidance as guidance_module
from pdf_report import generate_pdf
from database import engine, get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ─── CORS origins (resolved before app creation) ──────────────────────────────

_raw_origins     = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000")
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]


# ─── Startup ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs("data", exist_ok=True)
    models.Base.metadata.create_all(bind=engine)
    logger.info("✅ Glowup Coach backend started")
    yield


app = FastAPI(
    title="Glowup Coach API",
    description="AI-powered facial aesthetics coaching platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── WebSocket Manager ────────────────────────────────────────────────────────

class ScanNotificationManager:
    def __init__(self):
        self.connections: dict[str, WebSocket] = {}      # user_id → WS
        self.lb_connections: list[WebSocket]   = []      # leaderboard subscribers

    async def connect(self, user_id: str, ws: WebSocket):
        await ws.accept()
        self.connections[user_id] = ws

    def disconnect(self, user_id: str):
        self.connections.pop(user_id, None)

    async def connect_lb(self, ws: WebSocket):
        await ws.accept()
        self.lb_connections.append(ws)

    def disconnect_lb(self, ws: WebSocket):
        try:
            self.lb_connections.remove(ws)
        except ValueError:
            pass

    async def send(self, user_id: str, payload: dict):
        ws = self.connections.get(user_id)
        if ws:
            try:
                await ws.send_text(json.dumps(payload))
            except Exception:
                self.disconnect(user_id)

    async def broadcast_leaderboard(self, payload: dict):
        """Push a leaderboard update to all subscribed clients."""
        dead = []
        for ws in self.lb_connections:
            try:
                await ws.send_text(json.dumps(payload))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect_lb(ws)


ws_manager = ScanNotificationManager()


# ─── Auth Endpoints ───────────────────────────────────────────────────────────

@app.post("/auth/signup", response_model=schemas.TokenResponse, status_code=201)
def signup(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.username == payload.username).first():
        raise HTTPException(status_code=409, detail="Username already taken")
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = models.User(
        username=payload.username,
        email=payload.email,
        hashed_password=auth_module.hash_password(payload.password),
        gender=payload.gender,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = auth_module.create_access_token({"sub": str(user.id)})
    return schemas.TokenResponse(
        access_token=token,
        user=schemas.UserResponse.model_validate(user),
    )


@app.post("/auth/login", response_model=schemas.TokenResponse)
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == payload.username).first()
    if not user or not auth_module.verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = auth_module.create_access_token({"sub": str(user.id)})
    return schemas.TokenResponse(
        access_token=token,
        user=schemas.UserResponse.model_validate(user),
    )


@app.post("/auth/logout")
def logout(
    credentials=Depends(auth_module.bearer_scheme),
    current_user: models.User = Depends(auth_module.get_current_user),
):
    auth_module.blacklist_token(credentials.credentials)
    return {"message": "Logged out successfully"}


@app.get("/auth/me", response_model=schemas.UserResponse)
def me(current_user: models.User = Depends(auth_module.get_current_user)):
    return schemas.UserResponse.model_validate(current_user)


@app.patch("/auth/gender", response_model=schemas.UserResponse)
def update_gender(
    payload: schemas.GenderUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_module.get_current_user),
):
    current_user.gender = payload.gender
    db.commit()
    db.refresh(current_user)
    return schemas.UserResponse.model_validate(current_user)


@app.delete("/auth/account", status_code=204)
def delete_account(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_module.get_current_user),
):
    db.delete(current_user)
    db.commit()


# ─── Analysis Endpoints ───────────────────────────────────────────────────────

@app.post("/analyze", response_model=schemas.AnalysisResult)
async def analyze_frame_endpoint(
    frame: UploadFile = File(...),
    gender_override: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_module.get_current_user),
):
    """
    Accepts a single JPEG frame, runs MediaPipe analysis, returns per-feature scores.
    Call this endpoint once every ~3 seconds during the 30 s scan session.
    The frontend averages results across calls to produce the final score.
    """
    image_bytes = await frame.read()
    if len(image_bytes) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Frame too large (max 5 MB)")

    metrics = analyzer.analyze_frame(image_bytes)
    if not metrics:
        raise HTTPException(
            status_code=422,
            detail="No face detected. Ensure good lighting and face is centred.",
        )

    effective_gender = gender_override or current_user.gender or "prefer_not_to_say"
    score_result = scorer_module.compute_score(metrics, effective_gender)
    tips = guidance_module.generate_tips(score_result["feature_scores"], effective_gender)

    return schemas.AnalysisResult(
        total_score=score_result["total_score"],
        details=score_result["feature_scores"],
        gender_applied=effective_gender,
        frames_analyzed=1,
        tips=tips,
    )


@app.post("/analyze/finalize", response_model=schemas.AnalysisResult)
async def finalize_scan(
    payload: schemas.FinalizePayload,        # ← typed Pydantic model (was raw dict)
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_module.get_current_user),
):
    """
    Called at end of 30 s scan with aggregated metrics from all frames.
    Saves score to DB and returns final result + rank.
    """
    effective_gender = payload.gender_applied or current_user.gender or "prefer_not_to_say"

    score_result = scorer_module.compute_score(payload.feature_scores, effective_gender)

    # Async tip generation — falls back to rule-based if Ollama is unavailable
    tips = await guidance_module.generate_tips_ollama(
        score_result["feature_scores"], effective_gender
    )

    # Persist to DB
    db_score = models.Score(
        user_id=current_user.id,
        total_score=score_result["total_score"],
        details=json.dumps(score_result["feature_scores"]),
        gender_applied=effective_gender,
        frames_analyzed=payload.frames_analyzed,
    )
    db.add(db_score)
    db.commit()
    db.refresh(db_score)

    rank = _get_user_rank(db, current_user.id, score_result["total_score"])

    # Notify the scanning user via personal WebSocket
    await ws_manager.send(str(current_user.id), {
        "type":        "scan_complete",
        "total_score": score_result["total_score"],
        "rank":        rank,
    })

    # Broadcast leaderboard update to all connected leaderboard tabs
    await ws_manager.broadcast_leaderboard({
        "type":        "leaderboard_update",
        "username":    current_user.username,
        "total_score": score_result["total_score"],
        "rank":        rank,
    })

    return schemas.AnalysisResult(
        total_score=score_result["total_score"],
        details=score_result["feature_scores"],
        gender_applied=effective_gender,
        frames_analyzed=payload.frames_analyzed,
        tips=tips,
        rank=rank,
    )


# ─── Leaderboard ──────────────────────────────────────────────────────────────

def _get_user_rank(db: Session, user_id: int, score: float) -> int:
    """Return 1-based rank (number of users with a higher best score + 1)."""
    count = (
        db.query(func.count())
        .select_from(
            db.query(models.Score.user_id, func.max(models.Score.total_score).label("best"))
            .group_by(models.Score.user_id)
            .having(func.max(models.Score.total_score) > score)
            .subquery()
        )
        .scalar()
    )
    return (count or 0) + 1


@app.get("/leaderboard", response_model=schemas.LeaderboardResponse)
def leaderboard(
    gender_filter: Optional[str] = Query(None, description="Filter by 'male' or 'female'"),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_module.get_current_user),
):
    # Subquery: best score per user
    subq = (
        db.query(models.Score.user_id, func.max(models.Score.total_score).label("best_score"))
        .group_by(models.Score.user_id)
        .subquery()
    )

    query = (
        db.query(
            models.User.username,
            models.User.gender,
            subq.c.best_score,
            func.min(models.Score.created_at).label("achieved_at"),
        )
        .join(subq, models.User.id == subq.c.user_id)
        .join(
            models.Score,
            (models.Score.user_id == models.User.id) &
            (models.Score.total_score == subq.c.best_score)
        )
    )

    if gender_filter in ("male", "female"):
        query = query.filter(models.User.gender == gender_filter)

    rows = query.order_by(subq.c.best_score.desc()).limit(limit).all()

    entries = [
        schemas.LeaderboardEntry(
            rank=i + 1,
            username=row.username,
            total_score=round(float(row.best_score), 1) if row.best_score is not None else 0.0,
            gender=row.gender or "prefer_not_to_say",
            achieved_at=row.achieved_at,
        )
        for i, row in enumerate(rows)
        if row.best_score is not None
    ]

    user_best = (
        db.query(func.max(models.Score.total_score))
        .filter(models.Score.user_id == current_user.id)
        .scalar()
    )
    your_rank = _get_user_rank(db, current_user.id, user_best) if user_best is not None else None

    return schemas.LeaderboardResponse(
        entries=entries,
        total_users=len(rows),
        your_rank=your_rank,
        your_best_score=round(float(user_best), 1) if user_best is not None else None,
    )


# ─── Score History ────────────────────────────────────────────────────────────

@app.get("/scores/me", response_model=List[schemas.ScoreResponse])
def my_scores(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_module.get_current_user),
):
    scores = (
        db.query(models.Score)
        .filter(models.Score.user_id == current_user.id)
        .order_by(models.Score.created_at.desc())
        .limit(20)
        .all()
    )
    return [schemas.ScoreResponse.model_validate(s) for s in scores]


# ─── Latest scan → Roadmap data ───────────────────────────────────────────────

@app.get("/scores/me/latest")
async def my_latest_score(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth_module.get_current_user),
):
    """
    Return the user's MOST RECENT scan with generated 4-week tips for the Roadmap page.
    Uses the latest scan (created_at DESC) so the roadmap always reflects the newest data.
    """
    latest = (
        db.query(models.Score)
        .filter(models.Score.user_id == current_user.id)
        .order_by(models.Score.created_at.desc())   # most recent, not necessarily best
        .first()
    )
    if not latest:
        raise HTTPException(status_code=404, detail="No scans yet")

    gender    = current_user.gender or "prefer_not_to_say"
    feat_dict = latest.details_dict or {}

    if not feat_dict:
        raise HTTPException(status_code=422, detail="Scan data is corrupted or empty")

    rank = _get_user_rank(db, current_user.id, latest.total_score)

    # Generate 4-week tips — falls back to rule-based if Ollama is unavailable
    tips = await guidance_module.generate_tips_ollama(feat_dict, gender)

    return {
        "total_score":     round(float(latest.total_score), 1),
        "feature_scores":  {k: round(float(v), 1) for k, v in feat_dict.items()},
        "gender_applied":  gender,
        "frames_analyzed": latest.frames_analyzed or 0,
        "rank":            rank,
        "tips":            tips,
        "created_at":      latest.created_at.isoformat() if latest.created_at else None,
    }


# ─── PDF Report ───────────────────────────────────────────────────────────────

@app.post("/analyze/report")
async def download_report(
    payload: schemas.ReportPayload,          # ← typed Pydantic model (was raw dict)
    current_user: models.User = Depends(auth_module.get_current_user),
):
    """
    Generate a PDF report for the completed scan and stream it back as a download.
    Called immediately after /analyze/finalize on the frontend.
    """
    gender = payload.gender_applied or current_user.gender or "prefer_not_to_say"

    with tempfile.TemporaryDirectory() as tmpdir:
        path = generate_pdf(
            username=current_user.username,
            gender=gender,
            total_score=float(payload.total_score),
            feature_scores={k: float(v) for k, v in payload.feature_scores.items()},
            tips=payload.tips,
            frames_analyzed=int(payload.frames_analyzed),
            rank=payload.rank,
            output_dir=tmpdir,
        )
        with open(path, "rb") as f:
            pdf_bytes = f.read()

    filename = f"glowup_report_{current_user.username}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ─── WebSocket ────────────────────────────────────────────────────────────────

@app.websocket("/ws/scan/{user_id}")
async def ws_scan(websocket: WebSocket, user_id: str):
    await ws_manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id)


@app.websocket("/ws/leaderboard")
async def ws_leaderboard(websocket: WebSocket):
    """Browser tabs on the Leaderboard page connect here for live updates."""
    await ws_manager.connect_lb(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect_lb(websocket)


# ─── Health ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "glowup-coach-backend"}
