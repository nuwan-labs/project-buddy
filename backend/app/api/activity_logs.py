"""
/api/activity-logs endpoints — hourly activity capture.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api.helpers import build_log
from app.database import get_db
from app.services.notification import manager

router = APIRouter(prefix="/activity-logs", tags=["Logs"])


# ─────────────────────────────────────────────────────────────────────────────
# Log an activity
# ─────────────────────────────────────────────────────────────────────────────

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_log(data: schemas.ActivityLogCreate, db: Session = Depends(get_db)):
    """Log an activity (the core hourly capture action).

    - Stores the log in activity_logs.
    - Auto-transitions the activity from Not Started → In Progress on first log.
    - Broadcasts an 'activity_logged' WebSocket event to update the dashboard.
    """
    # Validate project exists; plan is optional
    if data.biweekly_plan_id is not None:
        plan = crud.get_plan(db, data.biweekly_plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail=f"Plan {data.biweekly_plan_id} not found.")
    if data.project_id is not None:
        project = crud.get_project(db, data.project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Project {data.project_id} not found.")

    log = crud.create_activity_log(db, data)

    # Reload with joined relationships for the response
    from sqlalchemy.orm import joinedload
    from app.models import ActivityLog
    log = (
        db.query(ActivityLog)
        .options(joinedload(ActivityLog.project), joinedload(ActivityLog.activity))
        .filter(ActivityLog.id == log.id)
        .first()
    )

    log_dict = build_log(log)

    # Real-time dashboard update
    await manager.broadcast({
        "type": "activity_logged",
        "data": {k: str(v) if hasattr(v, "isoformat") else v for k, v in log_dict.items()},
    })

    return {
        "success": True,
        "data": log_dict,
        "message": "Activity logged successfully.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# List logs
# ─────────────────────────────────────────────────────────────────────────────

@router.get("")
def list_logs(
    date: str | None = None,
    project_id: int | None = None,
    plan_id: int | None = None,
    sort: str = "timestamp_asc",
    db: Session = Depends(get_db),
):
    """Get activity logs filtered by date, project, or plan.

    - `date`: ISO 8601 date string (YYYY-MM-DD)
    - `sort`: timestamp_asc (default) | timestamp_desc
    """
    sort_asc = sort != "timestamp_desc"
    logs = crud.list_activity_logs(
        db,
        log_date=date,
        project_id=project_id,
        plan_id=plan_id,
        sort_asc=sort_asc,
    )
    total_hours = crud.total_hours_from_logs(logs)
    return {
        "success": True,
        "data": {
            "date": date,
            "total_hours": total_hours,
            "logs": [build_log(l) for l in logs],
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Edit a log
# ─────────────────────────────────────────────────────────────────────────────

@router.put("/{log_id}")
def update_log(
    log_id: int,
    data: schemas.ActivityLogUpdate,
    db: Session = Depends(get_db),
):
    """Edit a previously logged activity's comment, duration, or linked activity."""
    log = crud.update_activity_log(db, log_id, data)
    if not log:
        raise HTTPException(status_code=404, detail=f"Log {log_id} not found.")

    # Reload with relationships
    from sqlalchemy.orm import joinedload
    from app.models import ActivityLog
    log = (
        db.query(ActivityLog)
        .options(joinedload(ActivityLog.project), joinedload(ActivityLog.activity))
        .filter(ActivityLog.id == log_id)
        .first()
    )
    return {
        "success": True,
        "data": build_log(log),
        "message": "Log updated successfully.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Delete a log
# ─────────────────────────────────────────────────────────────────────────────

@router.delete("/{log_id}")
def delete_log(log_id: int, db: Session = Depends(get_db)):
    """Delete an activity log entry."""
    deleted = crud.delete_activity_log(db, log_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Log {log_id} not found.")
    return {"success": True, "message": "Log deleted successfully."}
