"""
Shared response-builder helpers used by multiple API routers.
Each function takes an ORM model instance + db session and returns a plain dict
that matches the corresponding Pydantic response schema.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app import crud
from app.models import Activity, ActivityLog, BiweeklyPlan, Project


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
        "biweekly_plan_id": project.biweekly_plan_id,
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
        "biweekly_plan_id": project.biweekly_plan_id,
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
        "project_count": stats["project_count"],
        "activity_count": stats["activity_count"],
        "created_at": plan.created_at,
        "updated_at": plan.updated_at,
    }


def build_plan_detail(plan: BiweeklyPlan, db: Session) -> dict:
    return {
        "id": plan.id,
        "name": plan.name,
        "description": plan.description,
        "start_date": plan.start_date,
        "end_date": plan.end_date,
        "status": plan.status,
        "projects": [build_project_detail(p, db) for p in plan.projects],
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
    return {
        "id": summary.id,
        "biweekly_plan_id": summary.biweekly_plan_id,
        "date": summary.date,
        "summary_text": summary.summary_text,
        "blockers": summary.blockers,
        "highlights": summary.highlights,
        "suggestions": summary.suggestions,
        "patterns": summary.patterns,
        "generated_at": summary.generated_at,
        "created_at": summary.created_at,
    }
