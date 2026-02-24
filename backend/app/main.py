"""
FastAPI application — entry point for the Project Buddy backend.

Startup sequence:
  1. Create all SQLite tables (if not already existing).
  2. Start APScheduler (hourly popup + daily DeepSeek analysis).

Shutdown sequence:
  1. Stop the scheduler gracefully.
"""
from __future__ import annotations

import asyncio
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    activities,
    activity_logs,
    biweekly_plans,
    dashboard,
    deepseek,
    exports,
    projects,
)
from app.config import get_settings
from app.database import Base, engine
from app.services.notification import manager

logger = logging.getLogger(__name__)
settings = get_settings()

# ─────────────────────────────────────────────────────────────────────────────
# App instance
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Project Buddy API",
    description="Lab Notebook & Biweekly Project Tracker — local-first backend",
    version="2.0.0",
)

# ─────────────────────────────────────────────────────────────────────────────
# CORS — allow React dev server only
# ─────────────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
# Routers
# ─────────────────────────────────────────────────────────────────────────────

app.include_router(biweekly_plans.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(activities.router, prefix="/api")
app.include_router(activity_logs.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(deepseek.router, prefix="/api")
app.include_router(exports.router, prefix="/api")

# ─────────────────────────────────────────────────────────────────────────────
# WebSocket endpoint
# ─────────────────────────────────────────────────────────────────────────────

@app.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time notification stream.

    The frontend connects here on startup and receives push messages:
      - activity_logged  → refresh dashboard counts
      - summary_ready    → show DeepSeek daily summary
      - plan_updated     → refetch plan data
      - notification     → show hourly activity popup
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; client messages are ignored for now
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ─────────────────────────────────────────────────────────────────────────────
# Lifecycle events
# ─────────────────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def on_startup() -> None:
    # 1. Ensure all DB tables exist
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready.")

    # 2. Start the background job scheduler, passing the running event loop
    #    so it can bridge sync scheduler threads → async WebSocket broadcasts.
    try:
        from app.services.scheduler import start_scheduler
        loop = asyncio.get_event_loop()
        start_scheduler(loop)
        logger.info("Scheduler started.")
    except Exception as exc:
        logger.warning("Scheduler could not start: %s", exc)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    try:
        from app.services.scheduler import stop_scheduler
        stop_scheduler()
        logger.info("Scheduler stopped.")
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "version": "2.0.0"}
