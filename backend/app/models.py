"""
SQLAlchemy ORM models for all database tables.
"""
from datetime import datetime, timezone

from sqlalchemy import (
    Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class BiweeklyPlan(Base):
    __tablename__ = "biweekly_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    start_date = Column(String(10), nullable=False)   # ISO 8601 YYYY-MM-DD
    end_date = Column(String(10), nullable=False)     # ISO 8601 YYYY-MM-DD
    status = Column(String(20), nullable=False, default="Active")
    # Allowed: Active | Completed | Paused | Archived
    created_at = Column(DateTime(timezone=True), default=_now)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    # Relationships
    sprint_activities = relationship(
        "SprintActivity",
        back_populates="plan",
        cascade="all, delete-orphan",
    )
    activity_logs = relationship(
        "ActivityLog",
        back_populates="biweekly_plan",
        cascade="all, delete-orphan",
    )
    daily_summaries = relationship(
        "DailySummary",
        back_populates="biweekly_plan",
    )
    project_daily_notes = relationship(
        "ProjectDailyNote",
        back_populates="plan",
    )


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    goal = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="Active")
    # Allowed: Active | On Hold | Complete | Archived
    color_tag = Column(String(20), nullable=True)   # e.g. "#FF5733"
    created_at = Column(DateTime(timezone=True), default=_now)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    # Relationships
    activities = relationship(
        "Activity",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="Activity.id",
    )
    activity_logs = relationship(
        "ActivityLog",
        back_populates="project",
        passive_deletes=True,
    )
    daily_notes = relationship(
        "ProjectDailyNote",
        back_populates="project",
        cascade="all, delete-orphan",
    )


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    deliverables = Column(Text, nullable=True)
    dependencies = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="Not Started")
    # Allowed: Not Started | In Progress | Complete
    estimated_hours = Column(Float, nullable=True, default=0.0)
    created_at = Column(DateTime(timezone=True), default=_now)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    # Relationships
    project = relationship("Project", back_populates="activities")
    activity_logs = relationship(
        "ActivityLog",
        back_populates="activity",
        foreign_keys="ActivityLog.activity_id",
    )
    sprint_activities = relationship(
        "SprintActivity",
        back_populates="activity",
        cascade="all, delete-orphan",
    )


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    biweekly_plan_id = Column(
        Integer, ForeignKey("biweekly_plans.id", ondelete="CASCADE"), nullable=True
    )
    project_id = Column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True
    )
    activity_id = Column(
        Integer, ForeignKey("activities.id", ondelete="SET NULL"), nullable=True
    )
    comment = Column(Text, nullable=False)
    duration_minutes = Column(Integer, nullable=False, default=60)
    timestamp = Column(String(35), nullable=False)  # ISO 8601 with timezone
    tags = Column(Text, nullable=True)              # JSON array string
    created_at = Column(DateTime(timezone=True), default=_now)

    # Relationships
    biweekly_plan = relationship("BiweeklyPlan", back_populates="activity_logs")
    project = relationship("Project", back_populates="activity_logs")
    activity = relationship(
        "Activity",
        back_populates="activity_logs",
        foreign_keys=[activity_id],
    )


class DailySummary(Base):
    __tablename__ = "daily_summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    biweekly_plan_id = Column(
        Integer, ForeignKey("biweekly_plans.id", ondelete="SET NULL"), nullable=True
    )
    date = Column(String(10), unique=True, nullable=False, index=True)  # YYYY-MM-DD
    summary_text = Column(Text, nullable=True)
    blockers = Column(Text, nullable=True)      # JSON array
    highlights = Column(Text, nullable=True)    # JSON array
    suggestions = Column(Text, nullable=True)   # JSON array
    patterns = Column(Text, nullable=True)      # JSON array
    generated_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=_now)

    # Relationships
    biweekly_plan = relationship("BiweeklyPlan", back_populates="daily_summaries")


class SprintActivity(Base):
    """Junction table: a sprint selects specific activities to focus on."""
    __tablename__ = "sprint_activities"
    __table_args__ = (
        UniqueConstraint("plan_id", "activity_id", name="uq_sprint_activity"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(
        Integer, ForeignKey("biweekly_plans.id", ondelete="CASCADE"), nullable=False
    )
    activity_id = Column(
        Integer, ForeignKey("activities.id", ondelete="CASCADE"), nullable=False
    )
    notes = Column(Text, nullable=True)   # sprint-specific notes for this activity
    created_at = Column(DateTime(timezone=True), default=_now)

    # Relationships
    plan = relationship("BiweeklyPlan", back_populates="sprint_activities")
    activity = relationship("Activity", back_populates="sprint_activities")


class ProjectDailyNote(Base):
    """Per-project structured lab-notebook entry (what I did / blockers / next steps)."""
    __tablename__ = "project_daily_notes"
    __table_args__ = (
        UniqueConstraint("project_id", "date", name="uq_project_daily_note"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    plan_id = Column(
        Integer, ForeignKey("biweekly_plans.id", ondelete="SET NULL"), nullable=True
    )
    date = Column(String(10), nullable=False)   # YYYY-MM-DD
    what_i_did = Column(Text, nullable=True)
    blockers = Column(Text, nullable=True)
    next_steps = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    # Relationships
    project = relationship("Project", back_populates="daily_notes")
    plan = relationship("BiweeklyPlan", back_populates="project_daily_notes")
