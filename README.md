# Project Buddy

A local-first lab notebook and project tracker for daily research work.
Runs entirely on your machine — no cloud, no accounts.

---

## What it does

| Feature | How |
|---|---|
| **Projects** | Long-running research initiatives with activities and goals |
| **Sprints** | 1–2 week biweekly plans that select activities to focus on |
| **Hourly logging** | System tray popup every hour — "What are you working on?" |
| **Daily notes** | 5 PM popup — per-project lab notebook (what I did / blockers / next steps) |
| **AI analysis** | Optional Ollama (DeepSeek R1) — daily summary of work patterns |
| **Export** | Excel export of plans and logs |

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.11+ | [python.org](https://python.org) |
| Node.js + npm | 18+ | [nodejs.org](https://nodejs.org) |
| Ollama (optional) | any | For AI daily summaries — [ollama.ai](https://ollama.ai) |

---

## Installation (first time only)

### 1. Backend dependencies
```
cd backend
pip install -r requirements.txt
```

### 2. Frontend dependencies
```
cd frontend
npm install
```

### 3. Configure settings (optional)

Copy `.env.example` to `.env` in the `backend/` folder and edit as needed:

```
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:8b
FRONTEND_ORIGIN=http://localhost:3000
```

---

## Starting the app

### Option A — Double-click (recommended)

Double-click **`start.vbs`** in the project root.

This silently starts:
1. Backend API (port 5000)
2. Frontend UI (port 3000)
3. System tray app (opens browser automatically)

### Option B — Manual (for development)

Open three terminals:

```bash
# Terminal 1 — Backend
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 5000 --reload

# Terminal 2 — Frontend
cd frontend
npm run dev

# Terminal 3 — Tray app
cd backend
python tray.py
```

Then open [http://localhost:3000](http://localhost:3000).

---

## Auto-start on Windows login

Run **`setup-autostart.vbs`** once. It creates a shortcut in your Windows Startup folder so the app launches automatically every time you log in.

To remove auto-start: press `Win+R`, type `shell:startup`, delete the **Project Buddy** shortcut.

---

## Stopping the app

Double-click **`stop.vbs`**, or:
- Right-click the tray icon → **Quit**
- Then close the terminal windows if running manually

---

## Daily workflow

### Hourly popup (automatic)
The tray app fires a popup every hour asking what you are working on.

- Select a **project** (or "General / Admin" for emails/meetings)
- Select an **activity** (optional)
- Type a short **comment**
- Set **duration** (default 60 min)
- Click **Log Time**
- If you worked on multiple things: click **Log Another**, repeat, then **Done**
- Click **Skip** to dismiss without logging

### 5 PM daily notes (automatic)
At 5 PM the tray shows a lab notebook popup for each active project:
- **What did you do today?**
- **Blockers / issues**
- **Next steps for tomorrow**

Click **Save Notes** or **Skip**.

### Web interface
Open [http://localhost:3000](http://localhost:3000) to:

| Page | What you can do |
|---|---|
| **Dashboard** | See all active projects, today's summary, sprint banner |
| **Projects** | Create/edit projects, add activities, view lab notes |
| **Plans** | Create biweekly sprints, select activities to focus on |
| **Activity Logs** | Browse/edit/delete all time logs |
| **Settings** | Check Ollama status, trigger manual AI analysis |

---

## Debug / testing

Trigger popups manually via the API (useful for testing):

```bash
# Activity popup
curl -X POST http://localhost:5000/api/debug/trigger-popup

# Daily note popup
curl -X POST http://localhost:5000/api/debug/trigger-daily-note
```

---

## Data

All data is stored in `backend/lab_notebook.db` (SQLite).
Back up this file to preserve your logs and notes.

---

## AI Analysis (optional)

Install Ollama and pull a model:

```bash
ollama pull deepseek-r1:8b
```

The backend runs an automatic analysis at 5:00 PM daily.
To trigger it manually: go to **Settings → Run Analysis Now**.

---

## Project structure

```
Project-Buddy/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routers
│   │   ├── models.py     # SQLAlchemy models
│   │   ├── schemas.py    # Pydantic schemas
│   │   ├── crud.py       # Database operations
│   │   └── main.py       # App entry point
│   ├── tray.py           # System tray app
│   ├── requirements.txt
│   └── lab_notebook.db   # SQLite database (auto-created)
├── frontend/
│   └── src/
│       ├── pages/        # Dashboard, Projects, Plans, Logs, Settings
│       ├── components/   # Shared UI components
│       ├── hooks/        # Custom React hooks
│       ├── services/     # API + WebSocket clients
│       └── context/      # Global app state
├── start.vbs             # Start everything (double-click)
├── stop.vbs              # Stop everything (double-click)
└── setup-autostart.vbs   # Register auto-start on login (run once)
```
