"""
/api/exports endpoints — alternative Excel export path.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db

router = APIRouter(prefix="/exports", tags=["Exports"])


@router.get("/plan-excel/{plan_id}")
def export_plan_excel(plan_id: int, db: Session = Depends(get_db)):
    """Generate and download a biweekly plan as a formatted Excel (.xlsx) file.

    This is an alias for GET /api/biweekly-plans/{id}/export-excel.
    """
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

    safe_name = plan.name.replace(" ", "_").replace("/", "-")[:60]
    filename = f"{safe_name}_{plan.start_date}_{plan.end_date}.xlsx"

    return StreamingResponse(
        excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
