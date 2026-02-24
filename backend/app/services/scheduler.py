"""
APScheduler background jobs:

  hourly_popup_job   — Mon–Fri, :30 past each hour from popup_start_hour to
                       popup_end_hour (Asia/Colombo).  Broadcasts a WebSocket
                       message to every connected client so the frontend can
                       show the Activity Log popup.

  daily_analysis_job — Mon–Fri at analysis_hour:analysis_minute.  Fetches
                       today's activity logs, calls Ollama DeepSeek R1, and
                       persists the result in daily_summaries.

APScheduler runs in a daemon background thread.  To broadcast WebSocket
messages from that thread we use asyncio.run_coroutine_threadsafe() with the
event loop captured at startup.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import date

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()

_scheduler: BackgroundScheduler          = BackgroundScheduler(daemon=True)
_event_loop: asyncio.AbstractEventLoop | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Sync → async bridge
# ─────────────────────────────────────────────────────────────────────────────

def _broadcast_sync(message: dict) -> None:
    """Schedule an async WebSocket broadcast from the scheduler thread."""
    from app.services.notification import manager
    if _event_loop is not None and _event_loop.is_running():
        asyncio.run_coroutine_threadsafe(manager.broadcast(message), _event_loop)
    else:
        logger.warning("WS broadcast skipped — no running event loop.")


# ─────────────────────────────────────────────────────────────────────────────
# Job: hourly popup
# ─────────────────────────────────────────────────────────────────────────────

def hourly_popup_job() -> None:
    """Tell every connected frontend client to show the Activity Log popup."""
    logger.info("⏰ Hourly popup job fired.")
    _broadcast_sync({
        "type":    "notification",
        "action":  "SHOW_ACTIVITY_POPUP",
        "message": "What are you working on right now?",
    })


# ─────────────────────────────────────────────────────────────────────────────
# Job: end-of-day DeepSeek analysis
# ─────────────────────────────────────────────────────────────────────────────

def daily_analysis_job() -> None:
    """Fetch today's logs, run Ollama analysis, persist result, notify frontend."""
    today = date.today().isoformat()
    logger.info("🔍 Daily analysis job fired for %s.", today)

    from app.database import SessionLocal
    from app import crud

    db = SessionLocal()
    try:
        logs = crud.list_activity_logs(db, log_date=today)
        if not logs:
            logger.info("No activity logs for %s — skipping Ollama analysis.", today)
            return

        try:
            from app.services.ollama_client import analyze_daily_logs
            result = analyze_daily_logs(today, logs)
        except Exception as exc:
            logger.error("Ollama analysis failed: %s", exc)
            result = {
                "summary":     f"Analysis could not be completed: {exc}",
                "blockers":    [],
                "highlights":  [],
                "suggestions": [],
                "patterns":    [],
            }

        active_plan = crud.get_active_plan(db)
        plan_id     = active_plan.id if active_plan else None

        crud.upsert_daily_summary(
            db,
            plan_id       = plan_id,
            summary_date  = today,
            summary_text  = result.get("summary", ""),
            blockers      = result.get("blockers",    []),
            highlights    = result.get("highlights",  []),
            suggestions   = result.get("suggestions", []),
            patterns      = result.get("patterns",    []),
        )

        _broadcast_sync({"type": "summary_ready", "data": {"date": today}})
        logger.info("Daily summary for %s stored and broadcast.", today)

    except Exception as exc:
        logger.error("daily_analysis_job unhandled error: %s", exc, exc_info=True)
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────────
# Start / stop
# ─────────────────────────────────────────────────────────────────────────────

def start_scheduler(loop: asyncio.AbstractEventLoop | None = None) -> None:
    """Configure and start the background scheduler.

    Args:
        loop: The running asyncio event loop (from FastAPI startup).
              Required for WebSocket broadcasts from scheduler threads.
    """
    global _event_loop
    if loop is not None:
        _event_loop = loop

    tz = settings.scheduler_timezone

    # ── Hourly popup (Mon–Fri, :30 each hour from popup_start_hour to popup_end_hour) ──
    _scheduler.add_job(
        hourly_popup_job,
        CronTrigger(
            hour         = f"{settings.popup_start_hour}-{settings.popup_end_hour}",
            minute       = str(settings.popup_start_minute),
            day_of_week  = "mon-fri",
            timezone     = tz,
        ),
        id                = "hourly_popup",
        replace_existing  = True,
        misfire_grace_time= 300,   # tolerate up to 5 min late
    )

    # ── Daily analysis (Mon–Fri at analysis_hour:analysis_minute) ─────────────
    _scheduler.add_job(
        daily_analysis_job,
        CronTrigger(
            hour         = str(settings.analysis_hour),
            minute       = str(settings.analysis_minute),
            day_of_week  = "mon-fri",
            timezone     = tz,
        ),
        id                = "daily_analysis",
        replace_existing  = True,
        misfire_grace_time= 600,
    )

    if not _scheduler.running:
        _scheduler.start()
        logger.info(
            "Scheduler started — TZ: %s | popup: %d:%02d | analysis: %d:%02d",
            tz,
            settings.popup_start_hour, settings.popup_start_minute,
            settings.analysis_hour,    settings.analysis_minute,
        )


def stop_scheduler() -> None:
    """Gracefully shut down the scheduler (called at FastAPI shutdown)."""
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")
