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
    projects = relationship(
        "Project",
        back_populates="biweekly_plan",
        cascade="all, delete-orphan",
        order_by="Project.id",
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


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("biweekly_plan_id", "name", name="uq_project_name_per_plan"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    biweekly_plan_id = Column(
        Integer, ForeignKey("biweekly_plans.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    goal = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="Not Started")
    # Allowed: Not Started | In Progress | Blocked | Complete
    color_tag = Column(String(20), nullable=True)   # e.g. "#FF5733"
    created_at = Column(DateTime(timezone=True), default=_now)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    # Relationships
    biweekly_plan = relationship("BiweeklyPlan", back_populates="projects")
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


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    biweekly_plan_id = Column(
        Integer, ForeignKey("biweekly_plans.id", ondelete="CASCADE"), nullable=False
    )
    project_id = Column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    activity_id = Column(
        Integer, ForeignKey("activities.id", ondelete="SET NULL"), nullable=True
    )
    comment = Column(Text, nullable=False)
    duration_minutes = Column(Integer, nullable=False, default=60)
    timestamp = Column(String(35), nullable=False)  # ISO 8601 with timezone e.g. 2026-02-24T10:30:00+05:30
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
