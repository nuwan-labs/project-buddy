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

from app.models import (
    Activity, ActivityLog, BiweeklyPlan, DailySummary,
    Project, ProjectDailyNote, SprintActivity,
)
from app.schemas import (
    ActivityCreate,
    ActivityLogCreate,
    ActivityLogUpdate,
    ActivityUpdate,
    BiweeklyPlanCreate,
    BiweeklyPlanUpdate,
    ProjectCreate,
    ProjectDailyNoteCreate,
    ProjectDailyNoteUpdate,
    ProjectUpdate,
    SprintActivityCreate,
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


def _overall_completion_from_sprint(db: Session, plan_id: int) -> float:
    """Compute completion % based on sprint activities."""
    sprint_acts = list_sprint_activities(db, plan_id)
    if not sprint_acts:
        return 0.0
    total = len(sprint_acts)
    done = sum(1 for sa in sprint_acts if sa.activity and sa.activity.status == "Complete")
    return round((done / total * 100) if total else 0.0, 1)


def _auto_update_project_status(db: Session, project: Project) -> None:
    """Nudge project to Active when work has started; never auto-complete it."""
    if not project.activities:
        return
    statuses = {a.status for a in project.activities}
    if "In Progress" in statuses or "Complete" in statuses:
        if project.status not in ("Complete", "On Hold", "Archived"):
            project.status = "Active"
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
            joinedload(BiweeklyPlan.sprint_activities)
            .joinedload(SprintActivity.activity)
            .joinedload(Activity.project)
        )
        .filter(BiweeklyPlan.id == plan_id)
        .first()
    )


def get_active_plan(db: Session) -> Optional[BiweeklyPlan]:
    return (
        db.query(BiweeklyPlan)
        .options(
            joinedload(BiweeklyPlan.sprint_activities)
            .joinedload(SprintActivity.activity)
            .joinedload(Activity.project)
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
    """Return sprint_activity_count for a plan."""
    sprint_activity_count = (
        db.query(func.count(SprintActivity.id))
        .filter(SprintActivity.plan_id == plan.id)
        .scalar()
    ) or 0
    return {"sprint_activity_count": sprint_activity_count}


# ─────────────────────────────────────────────────────────────────────────────
# SprintActivity CRUD
# ─────────────────────────────────────────────────────────────────────────────

def add_sprint_activity(
    db: Session, plan_id: int, data: SprintActivityCreate
) -> SprintActivity:
    sa = SprintActivity(
        plan_id=plan_id,
        activity_id=data.activity_id,
        notes=data.notes,
    )
    db.add(sa)
    db.commit()
    db.refresh(sa)
    return sa


def remove_sprint_activity(db: Session, plan_id: int, activity_id: int) -> bool:
    sa = (
        db.query(SprintActivity)
        .filter(SprintActivity.plan_id == plan_id, SprintActivity.activity_id == activity_id)
        .first()
    )
    if not sa:
        return False
    db.delete(sa)
    db.commit()
    return True


def list_sprint_activities(db: Session, plan_id: int) -> list[SprintActivity]:
    return (
        db.query(SprintActivity)
        .options(
            joinedload(SprintActivity.activity).joinedload(Activity.project)
        )
        .filter(SprintActivity.plan_id == plan_id)
        .order_by(SprintActivity.id)
        .all()
    )


def get_sprint_activity(db: Session, plan_id: int, activity_id: int) -> Optional[SprintActivity]:
    return (
        db.query(SprintActivity)
        .filter(SprintActivity.plan_id == plan_id, SprintActivity.activity_id == activity_id)
        .first()
    )


# ─────────────────────────────────────────────────────────────────────────────
# Project CRUD
# ─────────────────────────────────────────────────────────────────────────────

def create_project(db: Session, data: ProjectCreate) -> Project:
    project = Project(**data.model_dump())
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


def list_projects(
    db: Session,
    status: Optional[str] = None,
) -> list[Project]:
    q = (
        db.query(Project)
        .options(joinedload(Project.activities))
    )
    if status:
        q = q.filter(Project.status == status)
    return q.order_by(Project.id).all()


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
# ProjectDailyNote CRUD
# ─────────────────────────────────────────────────────────────────────────────

def upsert_project_daily_note(
    db: Session, data: ProjectDailyNoteCreate
) -> ProjectDailyNote:
    """Create or update a project daily note (upsert by project_id + date)."""
    existing = (
        db.query(ProjectDailyNote)
        .filter(
            ProjectDailyNote.project_id == data.project_id,
            ProjectDailyNote.date == data.date,
        )
        .first()
    )
    now = datetime.now(timezone.utc)
    if existing:
        existing.what_i_did = data.what_i_did
        existing.blockers = data.blockers
        existing.next_steps = data.next_steps
        if data.plan_id is not None:
            existing.plan_id = data.plan_id
        existing.updated_at = now
        db.commit()
        db.refresh(existing)
        return existing

    note = ProjectDailyNote(**data.model_dump())
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def get_project_daily_note(db: Session, note_id: int) -> Optional[ProjectDailyNote]:
    return (
        db.query(ProjectDailyNote)
        .options(joinedload(ProjectDailyNote.project))
        .filter(ProjectDailyNote.id == note_id)
        .first()
    )


def list_project_daily_notes(
    db: Session,
    project_id: Optional[int] = None,
    note_date: Optional[str] = None,
    plan_id: Optional[int] = None,
) -> list[ProjectDailyNote]:
    q = db.query(ProjectDailyNote).options(joinedload(ProjectDailyNote.project))
    if project_id:
        q = q.filter(ProjectDailyNote.project_id == project_id)
    if note_date:
        q = q.filter(ProjectDailyNote.date == note_date)
    if plan_id:
        q = q.filter(ProjectDailyNote.plan_id == plan_id)
    return q.order_by(ProjectDailyNote.date.desc(), ProjectDailyNote.project_id).all()


def update_project_daily_note(
    db: Session, note_id: int, data: ProjectDailyNoteUpdate
) -> Optional[ProjectDailyNote]:
    note = db.query(ProjectDailyNote).filter(ProjectDailyNote.id == note_id).first()
    if not note:
        return None
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(note, field, value)
    note.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(note)
    return note


def delete_project_daily_note(db: Session, note_id: int) -> bool:
    note = db.query(ProjectDailyNote).filter(ProjectDailyNote.id == note_id).first()
    if not note:
        return False
    db.delete(note)
    db.commit()
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard aggregation
# ─────────────────────────────────────────────────────────────────────────────

def get_dashboard_data(db: Session) -> dict:
    """Build the complete dashboard payload."""
    active_plan = get_active_plan(db)

    active_plan_overview = None
    sprint_activities_data = []

    if active_plan:
        sprint_acts = active_plan.sprint_activities
        sprint_activity_count = len(sprint_acts)
        sprint_activities_data = [
            {
                "id": sa.id,
                "plan_id": sa.plan_id,
                "activity_id": sa.activity_id,
                "notes": sa.notes,
                "activity_name": sa.activity.name if sa.activity else "",
                "project_id": sa.activity.project_id if sa.activity else 0,
                "project_name": sa.activity.project.name if (sa.activity and sa.activity.project) else "",
                "created_at": sa.created_at,
            }
            for sa in sprint_acts
        ]

        # Completion = based on sprint activities
        total_sa = len(sprint_acts)
        done_sa = sum(1 for sa in sprint_acts if sa.activity and sa.activity.status == "Complete")
        overall_completion = round((done_sa / total_sa * 100) if total_sa else 0.0, 1)

        active_plan_overview = {
            "id": active_plan.id,
            "name": active_plan.name,
            "start_date": active_plan.start_date,
            "end_date": active_plan.end_date,
            "days_remaining": _days_remaining(active_plan.end_date),
            "sprint_activity_count": sprint_activity_count,
            "overall_completion": overall_completion,
        }

    # All active projects
    active_projects = list_projects(db, status="Active")
    projects_data = []
    for project in active_projects:
        enriched = enrich_project(db, project)
        projects_data.append({
            "id": project.id,
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
        "sprint_activities": sprint_activities_data,
        "today_summary": today_summary,
        "daily_summary": daily_summary,
    }
