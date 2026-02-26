"""
/api/deepseek endpoints — trigger and retrieve DeepSeek R1 daily analysis.
"""
from __future__ import annotations

from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud
from app.api.helpers import build_daily_summary
from app.database import get_db
from app.services.notification import manager

router = APIRouter(prefix="/deepseek", tags=["DeepSeek"])


# ─────────────────────────────────────────────────────────────────────────────
# Trigger daily analysis
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/daily-analysis")
async def trigger_daily_analysis(
    payload: dict = None,
    db: Session = Depends(get_db),
):
    """Trigger end-of-day DeepSeek R1 analysis for a given date.

    Called automatically by APScheduler at 5:00 PM, or manually via the
    Settings page. Requires Ollama to be reachable at the configured host.

    Request body (optional): `{"date": "YYYY-MM-DD"}` — defaults to today.
    """
    try:
        from app.services.ollama_client import analyze_daily_logs
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DeepSeek analysis service is not available.",
        )

    analysis_date = (payload or {}).get("date") or date_type.today().isoformat()

    # Fetch today's logs
    logs = crud.list_activity_logs(db, log_date=analysis_date)
    if not logs:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"No activity logs found for {analysis_date}. Nothing to analyze.",
        )

    # Get active plan id (may be None)
    active_plan = crud.get_active_plan(db)
    plan_id = active_plan.id if active_plan else None

    # Call Ollama
    try:
        result = analyze_daily_logs(analysis_date, logs)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ollama analysis failed: {exc}",
        )

    # Persist summary
    summary = crud.upsert_daily_summary(
        db,
        plan_id=plan_id,
        summary_date=analysis_date,
        summary_text=result.get("summary", ""),
        blockers=result.get("blockers", []),
        highlights=result.get("highlights", []),
        suggestions=result.get("suggestions", []),
        patterns=result.get("patterns", []),
    )

    # Notify frontend
    await manager.broadcast({"type": "summary_ready", "data": {"date": analysis_date}})

    return {
        "success": True,
        "data": build_daily_summary(summary),
        "message": "Daily analysis completed successfully.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Retrieve stored summary
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/status")
def get_ollama_status():
    """Check whether the Ollama server is reachable and the model is loaded."""
    try:
        from app.services.ollama_client import check_ollama_health
        result = check_ollama_health()
        return {"success": True, "data": result}
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ollama client is not available.",
        )


@router.get("/daily-summary")
def get_daily_summary(date: str = None, db: Session = Depends(get_db)):
    """Retrieve a stored DeepSeek daily summary for a given date."""
    query_date = date or date_type.today().isoformat()
    summary = crud.get_daily_summary(db, query_date)
    if not summary:
        raise HTTPException(
            status_code=404,
            detail=f"No summary found for {query_date}.",
        )
    return {"success": True, "data": build_daily_summary(summary)}
