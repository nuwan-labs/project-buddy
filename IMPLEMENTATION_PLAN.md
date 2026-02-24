# Project Buddy — Implementation Plan

**Date:** 2026-02-24
**Spec Version:** 2.0
**Current State:** Greenfield — only `PROJECT_SPECIFICATION.md` and `ollama-access.py` exist.

---

## Overview

Build a local-first web app (React 18 + FastAPI + SQLite) for Ajantha (Bioinformatics Engineer, SLIBTEC) to manage biweekly plans, log hourly activities, track project progress, and receive optional end-of-day AI analysis via DeepSeek R1 on a local workstation.

---

## Phase 1 — Backend Foundation (Python/FastAPI)

**Goal:** Runnable FastAPI server with database, models, schemas, config, and CRUD.

### Steps

1. **Create directory structure**
   - `backend/app/`, `backend/app/api/`, `backend/app/services/`
   - `frontend/` (scaffold via Vite)
   - `scripts/`, `docs/`

2. **`backend/requirements.txt`**
   ```
   fastapi>=0.104.0
   uvicorn[standard]>=0.24.0
   sqlalchemy>=2.0.0
   pydantic>=2.0.0
   apscheduler>=3.10.0
   openpyxl>=3.1.0
   requests>=2.31.0
   python-dotenv>=1.0.0
   python-multipart>=0.0.6
   pytz>=2023.3
   websockets>=12.0
   ```

3. **`backend/app/config.py`** — Load `.env` config (Ollama host/port/model, scheduler timezone, ports)

4. **`backend/app/database.py`** — SQLAlchemy engine, `SessionLocal`, `Base`, `get_db()` dependency

5. **`backend/app/models.py`** — 5 ORM models:
   - `BiweeklyPlan` (id, name UNIQUE, description, start_date, end_date, status, timestamps)
   - `Project` (id, biweekly_plan_id FK, name, description, goal, status, color_tag, timestamps)
   - `Activity` (id, project_id FK, name, description, deliverables, dependencies, status, estimated_hours, timestamps)
   - `ActivityLog` (id, biweekly_plan_id FK, project_id FK, activity_id FK nullable, comment, duration_minutes, timestamp, tags JSON)
   - `DailySummary` (id, biweekly_plan_id FK nullable, date UNIQUE, summary_text, blockers/highlights/suggestions/patterns JSON, generated_at)
   - All cascade deletes per spec

6. **`backend/app/schemas.py`** — Pydantic v2 models for Create/Update/Response for all 5 entities plus `DashboardResponse`, `ActivityLogResponse`

7. **`backend/app/crud.py`** — Database CRUD operations for all entities (create, read, update, delete, list with filters). Include computed fields: `completion_percent`, `total_hours_logged`, `days_remaining`.

8. **`backend/app/__init__.py`**, **`backend/app/api/__init__.py`**, **`backend/app/services/__init__.py`**

9. **`backend/.env.example`**
   ```
   OLLAMA_HOST=192.168.200.5
   OLLAMA_PORT=11434
   OLLAMA_MODEL=deepseek-r1:7b
   OLLAMA_TIMEOUT=300
   OLLAMA_ANALYSIS_ENABLED=True
   SCHEDULER_TIMEZONE=Asia/Colombo
   ```

---

## Phase 2 — Backend API Endpoints

**Goal:** All REST endpoints per Section 7 of the spec.

10. **`backend/app/api/biweekly_plans.py`**
    - `POST /api/biweekly-plans` — create plan
    - `GET /api/biweekly-plans` — list all (with status filter, pagination)
    - `GET /api/biweekly-plans/active` — get current active plan (**must be before `{id}` route**)
    - `GET /api/biweekly-plans/{id}` — get plan with projects + activities (full nested response)
    - `PUT /api/biweekly-plans/{id}` — update plan
    - `DELETE /api/biweekly-plans/{id}` — cascade delete
    - `GET /api/biweekly-plans/{id}/export-excel` — download XLSX (delegates to excel_exporter service)

11. **`backend/app/api/projects.py`**
    - `POST /api/biweekly-plans/{plan_id}/projects` — add project
    - `GET /api/biweekly-plans/{plan_id}/projects` — list projects with completion stats
    - `PUT /api/projects/{id}` — update project
    - `DELETE /api/projects/{id}` — delete project

12. **`backend/app/api/activities.py`**
    - `POST /api/projects/{id}/activities` — add activity
    - `GET /api/projects/{id}/activities` — list activities with logged hours
    - `PUT /api/activities/{id}` — update/mark complete; auto-update project status
    - `DELETE /api/activities/{id}` — delete activity

13. **`backend/app/api/activity_logs.py`**
    - `POST /api/activity-logs` — log activity; auto-set activity status to "In Progress" if first log
    - `GET /api/activity-logs` — list logs (filter by date, project_id; join project+activity names)
    - `PUT /api/activity-logs/{id}` — edit comment/duration
    - `DELETE /api/activity-logs/{id}` — delete log

14. **`backend/app/api/dashboard.py`**
    - `GET /api/dashboard` — active plan overview + per-project stats + today's summary
    - `GET /api/dashboard/daily-summary` — daily summary for a date

15. **`backend/app/api/deepseek.py`**
    - `POST /api/deepseek/daily-analysis` — trigger analysis (called by scheduler or manually)
    - `GET /api/deepseek/daily-summary` — retrieve stored summary

16. **`backend/app/api/exports.py`**
    - `GET /api/exports/plan-excel/{plan_id}` — alias to plan export

---

## Phase 3 — Backend Services

17. **`backend/app/services/excel_exporter.py`**
    - `generate_biweekly_plan_excel(plan)` using openpyxl
    - Sheet 1: "Overview" — plan metadata, summary stats
    - Sheet 2: "Projects & Activities" — table with Project | Activity | Deliverables | Dependencies | Est Hours | Status | Week1 Mon-Fri | Week2 Mon-Fri
    - Sheet 3: "Time Tracking" — hours logged per activity
    - Styled headers (blue fill, white bold text), column widths, borders
    - Returns `BytesIO` for streaming response

18. **`backend/app/services/ollama_client.py`**
    - `analyze_daily_logs(date, activity_logs)` — formats prompt, calls Ollama `POST /api/generate`
    - `parse_deepseek_response(text)` — extracts JSON from response, handles parse errors gracefully
    - `check_ollama_health()` — test connectivity (used by settings page)
    - 5-minute timeout; returns structured dict on success, `None` on failure (not a hard error)

19. **`backend/app/services/scheduler.py`**
    - APScheduler `BackgroundScheduler`
    - `hourly_popup_job()` — sends WebSocket message to all connected clients triggering notification (Mon-Fri, 8:30–17:30 via cron `hour='8-17', minute='30'`, timezone=Asia/Colombo)
    - `daily_analysis_job()` — runs `analyze_daily_logs` at 17:00 Mon-Fri, stores `DailySummary`
    - `start_scheduler()` / `stop_scheduler()`

20. **`backend/app/services/notification.py`**
    - `WebSocketManager` class with `connect()`, `disconnect()`, `broadcast(message)`, `send_to(client, message)`
    - Singleton instance `manager` shared across app
    - Message types: `activity_logged`, `summary_ready`, `plan_updated`, `notification` (for hourly popup trigger)

21. **`backend/app/main.py`**
    - FastAPI app with CORS (localhost:3000 only)
    - Include all routers
    - WebSocket endpoint: `WS /ws/notifications`
    - Startup event: create DB tables + start scheduler
    - Shutdown event: stop scheduler

22. **`backend/run.py`** — Simple entry point: `uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload`

---

## Phase 4 — Frontend Scaffold & Foundation

**Goal:** Running React+TypeScript+Tailwind+shadcn app with routing and API client.

23. **Scaffold frontend** with `npm create vite@latest frontend -- --template react-ts`

24. **Install dependencies:**
    ```
    npm install axios react-router-dom date-fns
    npm install -D tailwindcss postcss autoprefixer
    npx tailwindcss init -p
    npx shadcn-ui@latest init
    ```
    Install shadcn components: `button, card, dialog, dropdown-menu, input, label, progress, select, textarea, badge, toast, separator, scroll-area`

25. **`frontend/src/types/index.ts`** — TypeScript interfaces for all API response shapes:
    `BiweeklyPlan`, `Project`, `Activity`, `ActivityLog`, `DailySummary`, `DashboardData`, `WebSocketMessage`

26. **`frontend/src/utils/constants.ts`** — API base URL, WS URL, status options, color palette constants

27. **`frontend/src/utils/formatting.ts`** — date formatting helpers (e.g. `formatDate`, `formatTime`, `formatDuration`)

28. **`frontend/src/utils/calculations.ts`** — `calcCompletionPercent`, `calcHoursLogged`, `calcDaysRemaining`

29. **`frontend/src/services/api.ts`** — Axios instance with base URL, typed functions for every API endpoint

30. **`frontend/src/services/websocket.ts`** — `WebSocketClient` class with auto-reconnect, typed message handler

31. **`frontend/src/services/serviceWorker.ts`** — SW registration + message listener to open `ActivityPopup` on `SHOW_ACTIVITY_POPUP`

32. **`frontend/src/context/AppContext.tsx`** — Global state with `useReducer`:
    - `activePlan`, `projects`, `todayLogs`, `dailySummary`, `showActivityPopup`, `notifications`
    - Actions: `SET_ACTIVE_PLAN`, `LOG_ACTIVITY`, `TOGGLE_POPUP`, `SET_SUMMARY`, etc.

---

## Phase 5 — Frontend Components

33. **`src/components/Header.tsx`** — Logo, current plan name, live clock, Settings link

34. **`src/components/Sidebar.tsx`** — Nav links: Dashboard, Plans, Activity Logs, Settings, Help

35. **`src/components/ProgressBar.tsx`** — Reusable bar with percent label and color variants (blue/green/red)

36. **`src/components/ProjectCard.tsx`** — Card with project name, status badge, activities progress bar, hours bar, "View Details" + "Log Time" buttons

37. **`src/components/ActivityList.tsx`** — Sortable list of activities with status checkboxes, logged hours, deliverables, recent logs inline, edit/delete actions

38. **`src/components/ActivityPopup.tsx`** (critical component)
    - Modal triggered by: WebSocket `notification` message, "Log Time Now" button click
    - Form: Project dropdown → Activity dropdown (populated from selected project) → Comment textarea → Duration input
    - Buttons: Submit (POST `/api/activity-logs`) | Snooze 15min (sends message to backend) | Skip (dismiss)
    - Shows toast on success; closes modal

39. **`src/components/DailySummary.tsx`** — Displays summary_text, blockers (with icons), highlights, suggestions, patterns from DeepSeek

40. **`src/components/Notifications.tsx`** — Toast notification stack (success/error/info)

---

## Phase 6 — Frontend Pages

41. **`src/pages/Dashboard.tsx`**
    - Fetches `GET /api/dashboard` on mount
    - Sections: Plan header (name, dates, days remaining, overall %), Project cards grid, Today's activity timeline, Daily summary (if available)
    - Real-time updates via WebSocket

42. **`src/pages/BiweeklyPlans.tsx`**
    - Fetches `GET /api/biweekly-plans`
    - Table with columns: Name, Status, Projects, Date range, Actions (Edit, Download, Archive, Delete)
    - "+ New Plan" button → navigates to `/plans/new`

43. **`src/pages/PlanEditor.tsx`** (create + edit)
    - Plan details form (name, description, start/end dates)
    - Dynamic project list: add/edit/remove projects inline
    - Per-project activity list: add/edit/remove activities inline
    - Buttons: Save Plan | Download Excel | Cancel
    - On save: POST (create) or PUT (edit) to API; redirect to dashboard

44. **`src/pages/ProjectDetail.tsx`**
    - Route: `/plans/:planId/projects/:projectId`
    - Shows project header (status, completion bars)
    - Full activity list (ActivityList component)
    - Buttons: Log Time Now (opens ActivityPopup), Add Activity, Edit Project

45. **`src/pages/ActivityLogs.tsx`**
    - Date range picker + project filter + search
    - Table of all logs (time, project, activity, comment, duration)
    - Edit/delete per row (inline)
    - Export CSV button

46. **`src/pages/Settings.tsx`**
    - Ollama connection test button (calls health check endpoint)
    - Notification preferences (enable/disable, sound)
    - Timezone display (informational)

47. **`src/pages/NotFound.tsx`** — 404 fallback

48. **`src/App.tsx`** — React Router v6 routes + AppContext provider + WebSocket initialization + service worker registration

49. **`frontend/index.html`** — HTML entry point with PWA meta tags

---

## Phase 7 — Custom Hooks

50. **`src/hooks/usePlans.ts`** — `usePlans()`: fetch/create/update/delete plans, loading/error state
51. **`src/hooks/useActivities.ts`** — `useActivities(projectId)`: fetch/add/toggle activities
52. **`src/hooks/useNotifications.ts`** — manage toast queue, request browser notification permission on mount
53. **`src/hooks/useWebSocket.ts`** — connect WS, expose typed message stream, auto-reconnect on disconnect

---

## Phase 8 — Service Worker & PWA

54. **`frontend/public/service-worker.js`**
    - install/activate lifecycle (skip waiting, claim clients)
    - Listen for `SHOW_NOTIFICATION` message → `showNotification()` with `requireInteraction: true` and action buttons (Log, Snooze, Skip)
    - `notificationclick` handler: focus/open app window, `postMessage({ type: 'SHOW_ACTIVITY_POPUP' })` to client

55. **`frontend/public/manifest.json`** — PWA manifest (name, icons, theme color, display: standalone)

---

## Phase 9 — Scripts, Config & Documentation

56. **`scripts/start.bat`** — Launch backend (uvicorn) + frontend (npm run dev) in separate terminals, then open browser

57. **`scripts/start.sh`** — Linux/macOS equivalent

58. **`config.json`** — Root-level config (app, backend, frontend, ollama, scheduler, notifications settings)

59. **`README.md`** — Quick start, prerequisites, setup steps, usage guide

60. **`.gitignore`** — node_modules, __pycache__, *.pyc, lab_notebook.db, .env, dist, .vite

---

## Implementation Order & Dependencies

```
Phase 1 (Backend Foundation)
  → Phase 2 (API Endpoints)       [requires models/schemas/crud]
  → Phase 3 (Backend Services)    [requires models; scheduler requires notification service]
  → main.py                       [requires all routers + services]

Phase 4 (Frontend Scaffold)       [parallel with Phase 1-3]
  → Phase 5 (Components)          [requires types/api service]
  → Phase 6 (Pages)               [requires components + hooks]
  → Phase 7 (Hooks)               [parallel with Phase 5-6]
  → Phase 8 (Service Worker)      [standalone]

Phase 9 (Scripts/Docs)            [last, after all code]
```

---

## Key Design Decisions

1. **Route ordering:** `GET /api/biweekly-plans/active` must be registered before `GET /api/biweekly-plans/{id}` to avoid FastAPI treating "active" as an integer ID.

2. **Activity status auto-update:** When a first `ActivityLog` is created for an activity, automatically set `activity.status = "In Progress"`. When all activities in a project are complete, auto-set `project.status = "Complete"`.

3. **WebSocket for notifications:** The APScheduler job does NOT use browser push API — it broadcasts a WebSocket message to all connected frontend clients, which then trigger the Service Worker to show the OS notification.

4. **Snooze handling:** Frontend sets a timer (15 min) using `setTimeout`, then re-triggers the `ActivityPopup` without involving the backend scheduler.

5. **Ad-hoc projects:** When user selects "Other/Ad-hoc" in the ActivityPopup, allow free-text project name. Backend auto-creates a project with `name="Ad-hoc: {user_text}"` under the current active plan.

6. **Ollama is optional:** If Ollama is unreachable or disabled, the backend scheduler job silently skips — no hard failure. The DeepSeek section of the dashboard simply shows "Analysis not available."

7. **Timezone:** All scheduled jobs run in `Asia/Colombo` timezone (Sri Lanka, UTC+5:30). Activity log timestamps stored as ISO 8601 with timezone offset.

8. **Excel filename:** Auto-generated as `{plan_name_slug}_{start_date}_{end_date}.xlsx` (e.g., `Tea_Genome_Plan_09-20-Feb-2026.xlsx`).

---

## File Count Summary

| Area | Files |
|------|-------|
| Backend core | 6 (main, database, models, schemas, crud, config) |
| Backend API routers | 7 |
| Backend services | 4 |
| Backend misc | 3 (requirements.txt, .env.example, run.py) |
| Frontend pages | 7 |
| Frontend components | 8 |
| Frontend hooks | 4 |
| Frontend services | 4 |
| Frontend types/utils | 4 |
| Frontend config | 4 (vite.config, tsconfig, package.json, index.html) |
| Public (SW + manifest) | 2 |
| Scripts + root config | 4 |
| **Total** | **~57 files** |

---

*This plan is ready to implement. Each phase should be built and tested before moving to the next.*
