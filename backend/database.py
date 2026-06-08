import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ── Supports SQLite (local dev) and PostgreSQL (production) ───────────────────
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./data/glowup.db")

# Render/Supabase give postgres:// but SQLAlchemy needs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if DATABASE_URL.startswith("sqlite"):
    # SQLite — local dev only
    connect_args = {"check_same_thread": False}
    engine = create_engine(DATABASE_URL, connect_args=connect_args)
else:
    # PostgreSQL (Render DB or Supabase pooler)
    # - pool_pre_ping: drops stale connections automatically
    # - connect_args sslmode: required by Supabase; safe for Render DB too
    # - pool_size / max_overflow: tuned for free tier (512 MB RAM, 2 workers)
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_recycle=300,          # recycle connections every 5 min
        connect_args={
            "sslmode": "require",  # Supabase requires SSL; Render DB supports it
            "connect_timeout": 10, # fail fast if DB is unreachable
        },
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
