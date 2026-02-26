"""
Shared response-builder helpers used by multiple API routers.
Each function takes an ORM model instance + db session and returns a plain dict
that matches the corresponding Pydantic response schema.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app import crud
from app.models import Activity, ActivityLog, BiweeklyPlan, Project, ProjectDailyNote, SprintActivity


# ─────────────────────────────────────────────────────────────────────────────
# Activity
# ─────────────────────────────────────────────────────────────────────────────

def build_activity(activity: Activity, db: Session) -> dict:
    return {
        "id": activity.id,
        "project_id": activity.project_id,
        "name": activity.name,
        "description": activity.description,
        "deliverables": activity.deliverables,
        "dependencies": activity.dependencies,
        "status": activity.status,
        "estimated_hours": activity.estimated_hours or 0.0,
        "logged_hours": crud.get_activity_logged_hours(db, activity.id),
        "created_at": activity.created_at,
        "updated_at": activity.updated_at,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Project
# ─────────────────────────────────────────────────────────────────────────────

def build_project_summary(project: Project, db: Session) -> dict:
    enriched = crud.enrich_project(db, project)
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "goal": project.goal,
        "status": project.status,
        "color_tag": project.color_tag,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        **enriched,
    }


def build_project_detail(project: Project, db: Session) -> dict:
    enriched = crud.enrich_project(db, project)
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "goal": project.goal,
        "status": project.status,
        "color_tag": project.color_tag,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "activities": [build_activity(a, db) for a in project.activities],
        **enriched,
    }


# ─────────────────────────────────────────────────────────────────────────────
# SprintActivity
# ─────────────────────────────────────────────────────────────────────────────

def build_sprint_activity(sa: SprintActivity) -> dict:
    activity = sa.activity
    project = activity.project if activity else None
    return {
        "id": sa.id,
        "plan_id": sa.plan_id,
        "activity_id": sa.activity_id,
        "notes": sa.notes,
        "activity_name": activity.name if activity else "",
        "project_id": activity.project_id if activity else 0,
        "project_name": project.name if project else "",
        "created_at": sa.created_at,
    }


# ─────────────────────────────────────────────────────────────────────────────
# BiweeklyPlan
# ─────────────────────────────────────────────────────────────────────────────

def build_plan_summary(plan: BiweeklyPlan, db: Session) -> dict:
    stats = crud.get_plan_summary_stats(db, plan)
    return {
        "id": plan.id,
        "name": plan.name,
        "description": plan.description,
        "start_date": plan.start_date,
        "end_date": plan.end_date,
        "status": plan.status,
        "sprint_activity_count": stats["sprint_activity_count"],
        "created_at": plan.created_at,
        "updated_at": plan.updated_at,
    }


def build_plan_detail(plan: BiweeklyPlan, db: Session) -> dict:
    sprint_acts = crud.list_sprint_activities(db, plan.id)
    return {
        "id": plan.id,
        "name": plan.name,
        "description": plan.description,
        "start_date": plan.start_date,
        "end_date": plan.end_date,
        "status": plan.status,
        "sprint_activities": [build_sprint_activity(sa) for sa in sprint_acts],
        "created_at": plan.created_at,
        "updated_at": plan.updated_at,
    }


# ─────────────────────────────────────────────────────────────────────────────
# ActivityLog
# ─────────────────────────────────────────────────────────────────────────────

def build_log(log: ActivityLog) -> dict:
    return {
        "id": log.id,
        "biweekly_plan_id": log.biweekly_plan_id,
        "project_id": log.project_id,
        "activity_id": log.activity_id,
        "comment": log.comment,
        "duration_minutes": log.duration_minutes,
        "timestamp": log.timestamp,
        "tags": log.tags,
        "project_name": log.project.name if log.project else "",
        "activity_name": log.activity.name if log.activity else None,
        "created_at": log.created_at,
    }


# ─────────────────────────────────────────────────────────────────────────────
# DailySummary
# ─────────────────────────────────────────────────────────────────────────────

def build_daily_summary(summary) -> dict:
    if summary is None:
        return None

    def _parse_list(val) -> list:
        if val is None:
            return []
        if isinstance(val, list):
            return val
        try:
            import json
            parsed = json.loads(val)
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []

    return {
        "id": summary.id,
        "biweekly_plan_id": summary.biweekly_plan_id,
        "date": summary.date,
        "summary_text": summary.summary_text,
        "blockers":    _parse_list(summary.blockers),
        "highlights":  _parse_list(summary.highlights),
        "suggestions": _parse_list(summary.suggestions),
        "patterns":    _parse_list(summary.patterns),
        "generated_at": summary.generated_at,
        "created_at": summary.created_at,
    }


# ─────────────────────────────────────────────────────────────────────────────
# ProjectDailyNote
# ─────────────────────────────────────────────────────────────────────────────

def build_project_daily_note(note: ProjectDailyNote) -> dict:
    return {
        "id": note.id,
        "project_id": note.project_id,
        "plan_id": note.plan_id,
        "date": note.date,
        "what_i_did": note.what_i_did,
        "blockers": note.blockers,
        "next_steps": note.next_steps,
        "project_name": note.project.name if note.project else "",
        "created_at": note.created_at,
        "updated_at": note.updated_at,
    }
