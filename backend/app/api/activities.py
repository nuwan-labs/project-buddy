"""
/api/projects/{id}/activities  and  /api/activities/{id} endpoints.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api.helpers import build_activity
from app.database import get_db

router = APIRouter(tags=["Activities"])


# ─────────────────────────────────────────────────────────────────────────────
# Add activity to a project
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/projects/{project_id}/activities", status_code=status.HTTP_201_CREATED)
def create_activity(
    project_id: int,
    data: schemas.ActivityCreate,
    db: Session = Depends(get_db),
):
    """Add a new activity (task) to a project."""
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")

    activity = crud.create_activity(db, project_id, data)
    return {
        "success": True,
        "data": build_activity(activity, db),
        "message": "Activity created successfully.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# List activities in a project
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/activities")
def list_activities(project_id: int, db: Session = Depends(get_db)):
    """List all activities in a project with logged hours."""
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")

    activities = crud.list_activities(db, project_id)
    return {
        "success": True,
        "data": {
            "activities": [build_activity(a, db) for a in activities]
        },
    }


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
