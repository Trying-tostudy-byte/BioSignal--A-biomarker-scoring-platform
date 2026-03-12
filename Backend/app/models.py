"""
SQLAlchemy models for SQLite. Internal storage only.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer, String, Float, Boolean, DateTime, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class BiomarkerRecord(Base):
    """Stored biomarker result (internal). API exposes only 6 fields via schemas."""

    __tablename__ = "biomarker_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    biomarker: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String(128), nullable=False)
    summary: Mapped[str] = mapped_column(String(512), nullable=False)
    therapeutic_area: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def to_response_dict(self, sno: int) -> dict:
        """Map to strict 6-field dict for API response."""
        return {
            "sno": sno,
            "biomarker": self.biomarker,
            "type": self.type,
            "score": self.score,
            "source": self.source,
            "summary": self.summary,
        }


# Default SQLite URL (override via env if needed)
SQLITE_URL = "sqlite:///./biomarker.db"
engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create tables if they do not exist."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency: yield a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
