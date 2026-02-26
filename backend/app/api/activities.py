"""
/api/activities/{id}  — activity update and delete endpoints.
List and create are under /api/projects/{id}/activities in projects.py.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api.helpers import build_activity
from app.database import get_db

router = APIRouter(tags=["Activities"])


# ─────────────────────────────────────────────────────────────────────────────
# Update activity
# ─────────────────────────────────────────────────────────────────────────────

@router.put("/activities/{activity_id}")
def update_activity(
    activity_id: int,
    data: schemas.ActivityUpdate,
    db: Session = Depends(get_db),
):
    """Update activity details or mark it complete/in-progress.

    Automatically updates the parent project status when activity status changes.
    """
    activity = crud.update_activity(db, activity_id, data)
    if not activity:
        raise HTTPException(status_code=404, detail=f"Activity {activity_id} not found.")
    return {
        "success": True,
        "data": build_activity(activity, db),
        "message": "Activity updated successfully.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Delete activity
# ─────────────────────────────────────────────────────────────────────────────

@router.delete("/activities/{activity_id}")
def delete_activity(activity_id: int, db: Session = Depends(get_db)):
    """Delete an activity (logs referencing it will have activity_id set to NULL)."""
    deleted = crud.delete_activity(db, activity_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Activity {activity_id} not found.")
    return {"success": True, "message": "Activity deleted successfully."}
