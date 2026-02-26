"""
/api/dashboard endpoints — overview and daily summary.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.api.helpers import build_daily_summary, build_project_summary
from app.database import get_db

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# ─────────────────────────────────────────────────────────────────────────────
# Main dashboard
# ─────────────────────────────────────────────────────────────────────────────

@router.get("")
def get_dashboard(db: Session = Depends(get_db)):
    """Return the full dashboard payload:
    - Active plan overview (name, dates, days remaining, completion %)
    - Per-project statistics cards
    - Today's activity summary (hours, projects worked)
    - Daily DeepSeek summary (if generated for today)
    """
    data = crud.get_dashboard_data(db)
    if data.get("daily_summary") is not None:
        data["daily_summary"] = build_daily_summary(data["daily_summary"])
    return {"success": True, "data": data}


# ─────────────────────────────────────────────────────────────────────────────
# Daily summary
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/daily-summary")
def get_daily_summary(date: str, db: Session = Depends(get_db)):
    """Return the stored DeepSeek daily summary for a given date (YYYY-MM-DD)."""
    summary = crud.get_daily_summary(db, date)
    if not summary:
        raise HTTPException(
            status_code=404,
            detail=f"No daily summary found for {date}.",
        )
    return {"success": True, "data": build_daily_summary(summary)}
