"""
/api/projects  — standalone project CRUD (projects are no longer owned by plans).
/api/projects/{id}/activities  — activity sub-resource.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api.helpers import build_activity, build_project_detail, build_project_summary
from app.database import get_db

router = APIRouter(prefix="/projects", tags=["Projects"])


# ─────────────────────────────────────────────────────────────────────────────
# List all projects
# ─────────────────────────────────────────────────────────────────────────────

@router.get("")
def list_projects(
    status: str | None = Query(None, description="Filter by status: Active | On Hold | Complete | Archived"),
    db: Session = Depends(get_db),
):
    """List all projects, optionally filtered by status."""
    projects = crud.list_projects(db, status=status)
    return {
        "success": True,
        "data": {
            "projects": [build_project_summary(p, db) for p in projects]
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Create project
# ─────────────────────────────────────────────────────────────────────────────

@router.post("", status_code=status.HTTP_201_CREATED)
def create_project(
    data: schemas.ProjectCreate,
    db: Session = Depends(get_db),
):
    """Create a new standalone project."""
    try:
        project = crud.create_project(db, data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    project = crud.get_project(db, project.id)
    return {
        "success": True,
        "data": build_project_detail(project, db),
        "message": "Project created successfully.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Get project by ID
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db)):
    """Return a project with all its activities and stats."""
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")
    return {"success": True, "data": build_project_detail(project, db)}


# ─────────────────────────────────────────────────────────────────────────────
# Update project
# ─────────────────────────────────────────────────────────────────────────────

@router.put("/{project_id}")
def update_project(
    project_id: int,
    data: schemas.ProjectUpdate,
    db: Session = Depends(get_db),
):
    """Update project name, goal, status, or color."""
    project = crud.update_project(db, project_id, data)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")

    project = crud.get_project(db, project_id)
    return {
        "success": True,
        "data": build_project_detail(project, db),
        "message": "Project updated successfully.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Delete project
# ─────────────────────────────────────────────────────────────────────────────

@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """Delete a project and all its activities and logs."""
    deleted = crud.delete_project(db, project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")
    return {"success": True, "message": "Project deleted successfully."}


# ─────────────────────────────────────────────────────────────────────────────
# Activities sub-resource
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{project_id}/activities")
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


@router.post("/{project_id}/activities", status_code=status.HTTP_201_CREATED)
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
