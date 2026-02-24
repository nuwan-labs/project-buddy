"""
Database CRUD operations for all entities.
All functions receive a SQLAlchemy Session and return ORM model instances
(or None / list thereof). The API layer converts to Pydantic schemas.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models import Activity, ActivityLog, BiweeklyPlan, DailySummary, Project
from app.schemas import (
    ActivityCreate,
    ActivityLogCreate,
    ActivityLogUpdate,
    ActivityUpdate,
    BiweeklyPlanCreate,
    BiweeklyPlanUpdate,
    ProjectCreate,
    ProjectUpdate,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _logged_hours_for_activity(db: Session, activity_id: int) -> float:
    result = db.query(func.sum(ActivityLog.duration_minutes)).filter(
        ActivityLog.activity_id == activity_id
    ).scalar()
    return round((result or 0) / 60, 2)


def _logged_hours_for_project(db: Session, project_id: int) -> float:
    result = db.query(func.sum(ActivityLog.duration_minutes)).filter(
        ActivityLog.project_id == project_id
    ).scalar()
    return round((result or 0) / 60, 2)


def _days_remaining(end_date_str: str) -> int:
    try:
        end = date.fromisoformat(end_date_str)
        delta = end - date.today()
        return max(delta.days, 0)
    except ValueError:
        return 0


def _overall_completion(projects: list[Project]) -> float:
    total = sum(len(p.activities) for p in projects)
    done = sum(1 for p in projects for a in p.activities if a.status == "Complete")
    return round((done / total * 100) if total else 0.0, 1)


def _auto_update_project_status(db: Session, project: Project) -> None:
    """Mark project In Progress / Complete based on its activities."""
    if not project.activities:
        return
    statuses = {a.status for a in project.activities}
    if statuses == {"Complete"}:
        project.status = "Complete"
    elif "In Progress" in statuses or "Complete" in statuses:
        project.status = "In Progress"
    db.flush()


# ─────────────────────────────────────────────────────────────────────────────
# BiweeklyPlan CRUD
# ─────────────────────────────────────────────────────────────────────────────

def create_plan(db: Session, data: BiweeklyPlanCreate) -> BiweeklyPlan:
    plan = BiweeklyPlan(**data.model_dump())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def get_plan(db: Session, plan_id: int) -> Optional[BiweeklyPlan]:
    return (
        db.query(BiweeklyPlan)
        .options(
            joinedload(BiweeklyPlan.projects).joinedload(Project.activities)
        )
        .filter(BiweeklyPlan.id == plan_id)
        .first()
    )


def get_active_plan(db: Session) -> Optional[BiweeklyPlan]:
    return (
        db.query(BiweeklyPlan)
        .options(
            joinedload(BiweeklyPlan.projects).joinedload(Project.activities)
        )
        .filter(BiweeklyPlan.status == "Active")
        .first()
    )


def list_plans(
    db: Session,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[BiweeklyPlan], int]:
    q = db.query(BiweeklyPlan)
    if status:
        q = q.filter(BiweeklyPlan.status == status)
    total = q.count()
    plans = q.order_by(BiweeklyPlan.created_at.desc()).offset(offset).limit(limit).all()
    return plans, total


def update_plan(db: Session, plan_id: int, data: BiweeklyPlanUpdate) -> Optional[BiweeklyPlan]:
    plan = db.query(BiweeklyPlan).filter(BiweeklyPlan.id == plan_id).first()
    if not plan:
        return None
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(plan, field, value)
    plan.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(plan)
    return plan


def delete_plan(db: Session, plan_id: int) -> bool:
    plan = db.query(BiweeklyPlan).filter(BiweeklyPlan.id == plan_id).first()
    if not plan:
        return False
    db.delete(plan)
    db.commit()
    return True


def get_plan_summary_stats(db: Session, plan: BiweeklyPlan) -> dict:
    """Return project_count and activity_count for a plan."""
    project_count = len(plan.projects)
    activity_count = sum(len(p.activities) for p in plan.projects)
    return {"project_count": project_count, "activity_count": activity_count}


# ─────────────────────────────────────────────────────────────────────────────
# Project CRUD
# ─────────────────────────────────────────────────────────────────────────────

def create_project(db: Session, plan_id: int, data: ProjectCreate) -> Project:
    project = Project(biweekly_plan_id=plan_id, **data.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_project(db: Session, project_id: int) -> Optional[Project]:
    return (
        db.query(Project)
        .options(joinedload(Project.activities))
        .filter(Project.id == project_id)
        .first()
    )


def list_projects(db: Session, plan_id: int) -> list[Project]:
    return (
        db.query(Project)
        .options(joinedload(Project.activities))
        .filter(Project.biweekly_plan_id == plan_id)
        .order_by(Project.id)
        .all()
    )


def update_project(db: Session, project_id: int, data: ProjectUpdate) -> Optional[Project]:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return None
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(project, field, value)
    project.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: int) -> bool:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return False
    db.delete(project)
    db.commit()
    return True


def enrich_project(db: Session, project: Project) -> dict:
    """Compute derived stats for a project to attach to its schema response."""
    activities = project.activities
    total = len(activities)
    completed = sum(1 for a in activities if a.status == "Complete")
    hours_estimated = sum(a.estimated_hours or 0 for a in activities)
    hours_logged = _logged_hours_for_project(db, project.id)
    return {
        "activities_count": total,
        "completed_count": completed,
        "completion_percent": round((completed / total * 100) if total else 0.0, 1),
        "hours_logged": hours_logged,
        "hours_estimated": round(hours_estimated, 2),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Activity CRUD
# ─────────────────────────────────────────────────────────────────────────────

def create_activity(db: Session, project_id: int, data: ActivityCreate) -> Activity:
    activity = Activity(project_id=project_id, **data.model_dump())
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def get_activity(db: Session, activity_id: int) -> Optional[Activity]:
    return db.query(Activity).filter(Activity.id == activity_id).first()


def list_activities(db: Session, project_id: int) -> list[Activity]:
    return (
        db.query(Activity)
        .filter(Activity.project_id == project_id)
        .order_by(Activity.id)
        .all()
    )


def update_activity(db: Session, activity_id: int, data: ActivityUpdate) -> Optional[Activity]:
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        return None
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(activity, field, value)
    activity.updated_at = datetime.now(timezone.utc)
    db.flush()
    # Auto-update parent project status
    project = db.query(Project).options(joinedload(Project.activities)).filter(
        Project.id == activity.project_id
    ).first()
    if project:
        _auto_update_project_status(db, project)
    db.commit()
    db.refresh(activity)
    return activity


def delete_activity(db: Session, activity_id: int) -> bool:
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        return False
    project_id = activity.project_id
    db.delete(activity)
    db.flush()
    project = db.query(Project).options(joinedload(Project.activities)).filter(
        Project.id == project_id
    ).first()
    if project:
        _auto_update_project_status(db, project)
    db.commit()
    return True


def get_activity_logged_hours(db: Session, activity_id: int) -> float:
    return _logged_hours_for_activity(db, activity_id)


# ─────────────────────────────────────────────────────────────────────────────
# ActivityLog CRUD
# ─────────────────────────────────────────────────────────────────────────────

def create_activity_log(db: Session, data: ActivityLogCreate) -> ActivityLog:
    log = ActivityLog(**data.model_dump())
    db.add(log)
    db.flush()

    # Auto-set activity status to "In Progress" on first log
    if data.activity_id:
        activity = db.query(Activity).filter(Activity.id == data.activity_id).first()
        if activity and activity.status == "Not Started":
            activity.status = "In Progress"
            activity.updated_at = datetime.now(timezone.utc)
            # Cascade project status
            project = db.query(Project).options(joinedload(Project.activities)).filter(
                Project.id == activity.project_id
            ).first()
            if project:
                _auto_update_project_status(db, project)

    db.commit()
    db.refresh(log)
    return log


def get_activity_log(db: Session, log_id: int) -> Optional[ActivityLog]:
    return db.query(ActivityLog).filter(ActivityLog.id == log_id).first()


def list_activity_logs(
    db: Session,
    log_date: Optional[str] = None,
    project_id: Optional[int] = None,
    plan_id: Optional[int] = None,
    sort_asc: bool = True,
) -> list[ActivityLog]:
    q = db.query(ActivityLog).options(
        joinedload(ActivityLog.project),
        joinedload(ActivityLog.activity),
    )
    if log_date:
        # timestamp stored as "YYYY-MM-DDTHH:MM:SS+05:30" — filter on date prefix
        q = q.filter(ActivityLog.timestamp.like(f"{log_date}%"))
    if project_id:
        q = q.filter(ActivityLog.project_id == project_id)
    if plan_id:
        q = q.filter(ActivityLog.biweekly_plan_id == plan_id)
    order_col = ActivityLog.timestamp.asc() if sort_asc else ActivityLog.timestamp.desc()
    return q.order_by(order_col).all()


def update_activity_log(
    db: Session, log_id: int, data: ActivityLogUpdate
) -> Optional[ActivityLog]:
    log = db.query(ActivityLog).filter(ActivityLog.id == log_id).first()
    if not log:
        return None
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(log, field, value)
    db.commit()
    db.refresh(log)
    return log


def delete_activity_log(db: Session, log_id: int) -> bool:
    log = db.query(ActivityLog).filter(ActivityLog.id == log_id).first()
    if not log:
        return False
    db.delete(log)
    db.commit()
    return True


def total_hours_from_logs(logs: list[ActivityLog]) -> float:
    return round(sum(l.duration_minutes for l in logs) / 60, 2)


# ─────────────────────────────────────────────────────────────────────────────
# DailySummary CRUD
# ─────────────────────────────────────────────────────────────────────────────

def get_daily_summary(db: Session, summary_date: str) -> Optional[DailySummary]:
    return db.query(DailySummary).filter(DailySummary.date == summary_date).first()


def upsert_daily_summary(
    db: Session,
    plan_id: Optional[int],
    summary_date: str,
    summary_text: str,
    blockers: list,
    highlights: list,
    suggestions: list,
    patterns: list,
) -> DailySummary:
    existing = get_daily_summary(db, summary_date)
    now = datetime.now(timezone.utc)
    if existing:
        existing.summary_text = summary_text
        existing.blockers = json.dumps(blockers)
        existing.highlights = json.dumps(highlights)
        existing.suggestions = json.dumps(suggestions)
        existing.patterns = json.dumps(patterns)
        existing.generated_at = now
        db.commit()
        db.refresh(existing)
        return existing

    summary = DailySummary(
        biweekly_plan_id=plan_id,
        date=summary_date,
        summary_text=summary_text,
        blockers=json.dumps(blockers),
        highlights=json.dumps(highlights),
        suggestions=json.dumps(suggestions),
        patterns=json.dumps(patterns),
        generated_at=now,
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return summary


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard aggregation
# ─────────────────────────────────────────────────────────────────────────────

def get_dashboard_data(db: Session) -> dict:
    """Build the complete dashboard payload."""
    active_plan = get_active_plan(db)

    active_plan_overview = None
    projects_data = []

    if active_plan:
        stats = _overall_completion(active_plan.projects)
        active_plan_overview = {
            "id": active_plan.id,
            "name": active_plan.name,
            "start_date": active_plan.start_date,
            "end_date": active_plan.end_date,
            "days_remaining": _days_remaining(active_plan.end_date),
            "projects_count": len(active_plan.projects),
            "overall_completion": stats,
        }

        for project in active_plan.projects:
            enriched = enrich_project(db, project)
            projects_data.append({
                "id": project.id,
                "biweekly_plan_id": project.biweekly_plan_id,
                "name": project.name,
                "description": project.description,
                "goal": project.goal,
                "status": project.status,
                "color_tag": project.color_tag,
                "created_at": project.created_at,
                "updated_at": project.updated_at,
                **enriched,
            })

    # Today's activity summary
    today_str = date.today().isoformat()
    today_logs = list_activity_logs(db, log_date=today_str)
    today_summary = {
        "date": today_str,
        "total_hours_logged": total_hours_from_logs(today_logs),
        "activities_logged": len(today_logs),
        "projects_worked_on": list({
            l.project.name for l in today_logs if l.project
        }),
    }

    daily_summary = get_daily_summary(db, today_str)

    return {
        "active_plan": active_plan_overview,
        "projects": projects_data,
        "today_summary": today_summary,
        "daily_summary": daily_summary,
    }
