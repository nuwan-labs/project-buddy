"""
/api/biweekly-plans endpoints.

Route order matters: /active MUST be declared before /{plan_id} so FastAPI
does not try to cast the literal string "active" to an integer.
"""
from __future__ import annotations

import math

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api.helpers import build_plan_detail, build_plan_summary
from app.database import get_db

router = APIRouter(prefix="/biweekly-plans", tags=["Plans"])


# ─────────────────────────────────────────────────────────────────────────────
# Create
# ─────────────────────────────────────────────────────────────────────────────

@router.post("", status_code=status.HTTP_201_CREATED)
def create_plan(data: schemas.BiweeklyPlanCreate, db: Session = Depends(get_db)):
    """Create a new biweekly plan."""
    try:
        plan = crud.create_plan(db, data)
    except Exception as exc:
        if "UNIQUE constraint" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A plan named '{data.name}' already exists.",
            )
        raise HTTPException(status_code=500, detail=str(exc))

    return {
        "success": True,
        "data": build_plan_summary(plan, db),
        "message": "Plan created successfully.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# List
# ─────────────────────────────────────────────────────────────────────────────

@router.get("")
def list_plans(
    status_filter: str | None = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List all biweekly plans with optional status filter and pagination."""
    plans, total = crud.list_plans(db, status=status_filter, limit=limit, offset=offset)
    pages = math.ceil(total / limit) if limit else 1
    return {
        "success": True,
        "data": {
            "plans": [build_plan_summary(p, db) for p in plans],
            "total": total,
            "page": (offset // limit) + 1 if limit else 1,
            "pages": pages,
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Get active plan  ← MUST be before /{plan_id}
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/active")
def get_active_plan(db: Session = Depends(get_db)):
    """Return the current active biweekly plan with full detail."""
    plan = crud.get_active_plan(db)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active plan found.",
        )
    return {"success": True, "data": build_plan_detail(plan, db)}


# ─────────────────────────────────────────────────────────────────────────────
# Get by ID
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{plan_id}")
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    """Return a plan with all projects and activities."""
    plan = crud.get_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found.")
    return {"success": True, "data": build_plan_detail(plan, db)}


# ─────────────────────────────────────────────────────────────────────────────
# Update
# ─────────────────────────────────────────────────────────────────────────────

@router.put("/{plan_id}")
def update_plan(
    plan_id: int,
    data: schemas.BiweeklyPlanUpdate,
    db: Session = Depends(get_db),
):
    """Update plan name, dates, status, or description."""
    plan = crud.update_plan(db, plan_id, data)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found.")
    return {
        "success": True,
        "data": build_plan_summary(plan, db),
        "message": "Plan updated successfully.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Delete
# ─────────────────────────────────────────────────────────────────────────────

@router.delete("/{plan_id}")
def delete_plan(plan_id: int, db: Session = Depends(get_db)):
    """Delete a plan and all its projects, activities, and logs."""
    deleted = crud.delete_plan(db, plan_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found.")
    return {"success": True, "message": "Plan deleted successfully."}


# ─────────────────────────────────────────────────────────────────────────────
# Excel export
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{plan_id}/export-excel")
def export_excel(plan_id: int, db: Session = Depends(get_db)):
    """Download the biweekly plan as a formatted Excel (.xlsx) file."""
    plan = crud.get_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found.")

    try:
        from app.services.excel_exporter import generate_biweekly_plan_excel
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Excel export service is not available.",
        )

    excel_bytes = generate_biweekly_plan_excel(plan, db)

    # Build a safe filename: e.g. Tea_Genome_Plan_2026-02-09_2026-02-20.xlsx
    safe_name = plan.name.replace(" ", "_").replace("/", "-")[:60]
    filename = f"{safe_name}_{plan.start_date}_{plan.end_date}.xlsx"

    return StreamingResponse(
        excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
