from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
import json


# ─── Auth Schemas ─────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    gender: str = "prefer_not_to_say"

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v):
        allowed = {"male", "female", "prefer_not_to_say"}
        if v.lower() not in allowed:
            raise ValueError(f"gender must be one of {allowed}")
        return v.lower()

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        v = v.strip()
        if len(v) < 3 or len(v) > 30:
            raise ValueError("username must be 3–30 characters")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError("password must be at least 6 characters")
        return v


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    gender: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ─── Score Schemas ─────────────────────────────────────────────────────────────

class ScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    total_score: float
    details: Dict[str, float]   # deserialized for the frontend
    gender_applied: str
    frames_analyzed: int
    created_at: datetime

    @field_validator("details", mode="before")
    @classmethod
    def parse_details(cls, v):
        """DB stores details as a JSON string — deserialize it."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, ValueError):
                return {}
        return v or {}


class AnalysisResult(BaseModel):
    total_score: float
    details: Dict[str, float]
    gender_applied: str
    frames_analyzed: int
    tips: List[Dict[str, Any]]
    rank: Optional[int] = None


# ─── Request body models for finalize + report ────────────────────────────────

class FinalizePayload(BaseModel):
    """Body for POST /analyze/finalize"""
    feature_scores: Dict[str, float]
    frames_analyzed: int = 0
    gender_applied: Optional[str] = None

    @field_validator("feature_scores")
    @classmethod
    def check_scores(cls, v):
        if not v:
            raise ValueError("feature_scores must not be empty")
        return v


class ReportPayload(BaseModel):
    """Body for POST /analyze/report"""
    feature_scores: Dict[str, float]
    total_score: float
    gender_applied: Optional[str] = None
    frames_analyzed: int = 0
    rank: Optional[int] = None
    tips: List[Dict[str, Any]] = []

    @field_validator("feature_scores")
    @classmethod
    def check_scores(cls, v):
        if not v:
            raise ValueError("feature_scores must not be empty")
        return v


# ─── Leaderboard Schemas ───────────────────────────────────────────────────────

class LeaderboardEntry(BaseModel):
    rank: int
    username: str
    total_score: float
    gender: str
    achieved_at: datetime


class LeaderboardResponse(BaseModel):
    entries: List[LeaderboardEntry]
    total_users: int
    your_rank: Optional[int] = None
    your_best_score: Optional[float] = None


# ─── Gender Update ─────────────────────────────────────────────────────────────

class GenderUpdate(BaseModel):
    gender: str

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v):
        v = v.strip().lower()
        allowed = {"male", "female", "prefer_not_to_say"}
        if v not in allowed:
            raise ValueError(f"gender must be one of {allowed}")
        return v
