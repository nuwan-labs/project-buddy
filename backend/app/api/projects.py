"""
/api/biweekly-plans/{plan_id}/projects  and  /api/projects/{id} endpoints.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api.helpers import build_project_detail, build_project_summary
from app.database import get_db

router = APIRouter(tags=["Projects"])


# ─────────────────────────────────────────────────────────────────────────────
# Add project to a plan
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/biweekly-plans/{plan_id}/projects", status_code=status.HTTP_201_CREATED)
def create_project(
    plan_id: int,
    data: schemas.ProjectCreate,
    db: Session = Depends(get_db),
):
    """Add a new project to a biweekly plan."""
    plan = crud.get_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found.")

    try:
        project = crud.create_project(db, plan_id, data)
    except Exception as exc:
        if "UNIQUE constraint" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Project '{data.name}' already exists in this plan.",
            )
        raise HTTPException(status_code=500, detail=str(exc))

    # Reload with activities relationship
    project = crud.get_project(db, project.id)
    return {
        "success": True,
        "data": build_project_detail(project, db),
        "message": "Project created successfully.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# List projects in a plan
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/biweekly-plans/{plan_id}/projects")
def list_projects(plan_id: int, db: Session = Depends(get_db)):
    """List all projects in a plan with completion statistics."""
    plan = crud.get_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found.")

    projects = crud.list_projects(db, plan_id)
    return {
        "success": True,
        "data": {
            "projects": [build_project_summary(p, db) for p in projects]
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Update project
# ─────────────────────────────────────────────────────────────────────────────

@router.put("/projects/{project_id}")
def update_project(
    project_id: int,
    data: schemas.ProjectUpdate,
    db: Session = Depends(get_db),
):
    """Update project name, goal, status, or color."""
    project = crud.update_project(db, project_id, data)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")

    project = crud.get_project(db, project_id)  # reload with activities
    return {
        "success": True,
        "data": build_project_detail(project, db),
        "message": "Project updated successfully.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Delete project
# ─────────────────────────────────────────────────────────────────────────────

@router.delete("/projects/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """Delete a project and all its activities and logs."""
    deleted = crud.delete_project(db, project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found.")
    return {"success": True, "message": "Project deleted successfully."}
