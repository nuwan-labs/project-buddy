"""
Pydantic v2 schemas for request validation and response serialization.
"""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, field_validator


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

class OrmBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# Activity schemas
# ─────────────────────────────────────────────────────────────────────────────

class ActivityCreate(BaseModel):
    name: str
    description: Optional[str] = None
    deliverables: Optional[str] = None
    dependencies: Optional[str] = None
    estimated_hours: Optional[float] = 0.0

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Activity name must not be empty")
        return v


class ActivityUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    deliverables: Optional[str] = None
    dependencies: Optional[str] = None
    status: Optional[str] = None
    estimated_hours: Optional[float] = None


class ActivityResponse(OrmBase):
    id: int
    project_id: int
    name: str
    description: Optional[str]
    deliverables: Optional[str]
    dependencies: Optional[str]
    status: str
    estimated_hours: Optional[float]
    logged_hours: float = 0.0          # computed by CRUD, not stored in DB
    created_at: datetime
    updated_at: datetime


# ─────────────────────────────────────────────────────────────────────────────
# Project schemas
# ─────────────────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    goal: Optional[str] = None
    color_tag: Optional[str] = None
    status: Optional[str] = "Active"

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Project name must not be empty")
        return v


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    goal: Optional[str] = None
    status: Optional[str] = None
    color_tag: Optional[str] = None


class ProjectSummary(OrmBase):
    """Lightweight project info used in lists / dashboard responses."""
    id: int
    name: str
    description: Optional[str]
    goal: Optional[str]
    status: str
    color_tag: Optional[str]
    activities_count: int = 0
    completed_count: int = 0
    completion_percent: float = 0.0
    hours_logged: float = 0.0
    hours_estimated: float = 0.0
    created_at: datetime
    updated_at: datetime


class ProjectDetail(ProjectSummary):
    """Full project info including activities list."""
    activities: list[ActivityResponse] = []


# ─────────────────────────────────────────────────────────────────────────────
# SprintActivity schemas
# ─────────────────────────────────────────────────────────────────────────────

class SprintActivityCreate(BaseModel):
    activity_id: int
    notes: Optional[str] = None


class SprintActivityResponse(OrmBase):
    id: int
    plan_id: int
    activity_id: int
    notes: Optional[str]
    # Enriched fields (computed from joins)
    activity_name: str = ""
    project_id: int = 0
    project_name: str = ""
    created_at: datetime


# ─────────────────────────────────────────────────────────────────────────────
# BiweeklyPlan schemas
# ─────────────────────────────────────────────────────────────────────────────

class BiweeklyPlanCreate(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: str   # YYYY-MM-DD
    end_date: str     # YYYY-MM-DD

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v or len(v) < 3:
            raise ValueError("Plan name must be at least 3 characters")
        return v

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v: str, info: Any) -> str:
        start = info.data.get("start_date")
        if start and v < start:
            raise ValueError("end_date must be on or after start_date")
        return v


class BiweeklyPlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[str] = None


class BiweeklyPlanSummary(OrmBase):
    """Lightweight plan info used in list responses."""
    id: int
    name: str
    description: Optional[str]
    start_date: str
    end_date: str
    status: str
    sprint_activity_count: int = 0
    created_at: datetime
    updated_at: datetime


class BiweeklyPlanDetail(OrmBase):
    """Full plan info including sprint activities."""
    id: int
    name: str
    description: Optional[str]
    start_date: str
    end_date: str
    status: str
    sprint_activities: list[SprintActivityResponse] = []
    created_at: datetime
    updated_at: datetime


# ─────────────────────────────────────────────────────────────────────────────
# ActivityLog schemas
# ─────────────────────────────────────────────────────────────────────────────

class ActivityLogCreate(BaseModel):
    biweekly_plan_id: Optional[int] = None
    project_id: Optional[int] = None
    activity_id: Optional[int] = None
    comment: str
    duration_minutes: int = 60
    timestamp: str   # ISO 8601 with timezone

    @field_validator("comment")
    @classmethod
    def comment_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Comment must not be empty")
        if len(v) > 500:
            raise ValueError("Comment must be 500 characters or fewer")
        return v

    @field_validator("duration_minutes")
    @classmethod
    def valid_duration(cls, v: int) -> int:
        if not (1 <= v <= 480):
            raise ValueError("Duration must be between 1 and 480 minutes")
        return v


class ActivityLogUpdate(BaseModel):
    comment: Optional[str] = None
    duration_minutes: Optional[int] = None
    activity_id: Optional[int] = None


class ActivityLogResponse(OrmBase):
    id: int
    biweekly_plan_id: Optional[int]
    project_id: int
    activity_id: Optional[int]
    comment: str
    duration_minutes: int
    timestamp: str
    tags: Optional[str]
    project_name: str = ""      # joined from Project
    activity_name: Optional[str] = None   # joined from Activity
    created_at: datetime


# ─────────────────────────────────────────────────────────────────────────────
# ProjectDailyNote schemas
# ─────────────────────────────────────────────────────────────────────────────

class ProjectDailyNoteCreate(BaseModel):
    project_id: int
    date: str          # YYYY-MM-DD
    what_i_did: Optional[str] = None
    blockers: Optional[str] = None
    next_steps: Optional[str] = None
    plan_id: Optional[int] = None

    @field_validator("date")
    @classmethod
    def valid_date(cls, v: str) -> str:
        v = v.strip()
        if len(v) != 10 or v[4] != "-" or v[7] != "-":
            raise ValueError("date must be YYYY-MM-DD")
        return v


class ProjectDailyNoteUpdate(BaseModel):
    what_i_did: Optional[str] = None
    blockers: Optional[str] = None
    next_steps: Optional[str] = None


class ProjectDailyNoteResponse(OrmBase):
    id: int
    project_id: int
    plan_id: Optional[int]
    date: str
    what_i_did: Optional[str]
    blockers: Optional[str]
    next_steps: Optional[str]
    project_name: str = ""
    created_at: datetime
    updated_at: datetime


# ─────────────────────────────────────────────────────────────────────────────
# DailySummary schemas
# ─────────────────────────────────────────────────────────────────────────────

class DailySummaryResponse(OrmBase):
    id: int
    biweekly_plan_id: Optional[int]
    date: str
    summary_text: Optional[str]
    blockers: Optional[str]     # raw JSON string
    highlights: Optional[str]   # raw JSON string
    suggestions: Optional[str]  # raw JSON string
    patterns: Optional[str]     # raw JSON string
    generated_at: datetime
    created_at: datetime


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard schemas
# ─────────────────────────────────────────────────────────────────────────────

class TodaySummary(BaseModel):
    date: str
    total_hours_logged: float
    activities_logged: int
    projects_worked_on: list[str]


class ActivePlanOverview(BaseModel):
    id: int
    name: str
    start_date: str
    end_date: str
    days_remaining: int
    sprint_activity_count: int
    overall_completion: float


class DashboardResponse(BaseModel):
    active_plan: Optional[ActivePlanOverview]
    projects: list[ProjectSummary]           # all Active projects
    sprint_activities: list[SprintActivityResponse]  # activities in current sprint
    today_summary: Optional[TodaySummary]
    daily_summary: Optional[DailySummaryResponse]


# ─────────────────────────────────────────────────────────────────────────────
# Generic API response wrapper
# ─────────────────────────────────────────────────────────────────────────────

class ApiResponse(BaseModel):
    success: bool = True
    data: Optional[Any] = None
    message: Optional[str] = None


class ApiError(BaseModel):
    success: bool = False
    error: str
    details: Optional[str] = None
    timestamp: Optional[str] = None


class PaginatedPlans(BaseModel):
    plans: list[BiweeklyPlanSummary]
    total: int
    page: int
    pages: int


class ActivityLogsPage(BaseModel):
    date: str
    total_hours: float
    logs: list[ActivityLogResponse]
