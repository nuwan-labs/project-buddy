"""
/api/project-notes  — per-project structured daily lab-notebook entries.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api.helpers import build_project_daily_note
from app.database import get_db

router = APIRouter(prefix="/project-notes", tags=["Daily Notes"])


# ─────────────────────────────────────────────────────────────────────────────
# List
# ─────────────────────────────────────────────────────────────────────────────

@router.get("")
def list_notes(
    project_id: int | None = Query(None),
    date: str | None = Query(None, description="YYYY-MM-DD"),
    plan_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    """List project daily notes with optional filters."""
    notes = crud.list_project_daily_notes(
        db, project_id=project_id, note_date=date, plan_id=plan_id
    )
    return {
        "success": True,
        "data": {
            "notes": [build_project_daily_note(n) for n in notes]
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Create / upsert
# ─────────────────────────────────────────────────────────────────────────────

@router.post("", status_code=status.HTTP_201_CREATED)
def upsert_note(
    data: schemas.ProjectDailyNoteCreate,
    db: Session = Depends(get_db),
):
    """Create or update a daily note for a project on a specific date."""
    # Verify project exists
    project = crud.get_project(db, data.project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {data.project_id} not found.")

    try:
        note = crud.upsert_project_daily_note(db, data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    # Reload with joins for project_name
    note = crud.get_project_daily_note(db, note.id)
    return {
        "success": True,
        "data": build_project_daily_note(note),
        "message": "Daily note saved.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Update
# ─────────────────────────────────────────────────────────────────────────────

@router.put("/{note_id}")
def update_note(
    note_id: int,
    data: schemas.ProjectDailyNoteUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing daily note."""
    note = crud.update_project_daily_note(db, note_id, data)
    if not note:
        raise HTTPException(status_code=404, detail=f"Note {note_id} not found.")

    note = crud.get_project_daily_note(db, note_id)
    return {
        "success": True,
        "data": build_project_daily_note(note),
        "message": "Note updated.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Delete
# ─────────────────────────────────────────────────────────────────────────────

@router.delete("/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    """Delete a daily note."""
    deleted = crud.delete_project_daily_note(db, note_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Note {note_id} not found.")
    return {"success": True, "message": "Note deleted."}
