# Lab Notebook & Project Tracker - Complete Specification Document

**Project Name:** Lab Notebook & Biweekly Project Tracker  
**Version:** 2.0  
**Date:** February 24, 2026  
**User:** Ajantha (Bioinformatics Engineer, SLIBTEC)  
**Location:** Pita Kotte, Western Province, Sri Lanka

---

## TABLE OF CONTENTS

1. Executive Summary
2. System Overview & Architecture
3. User Context & Workflows
4. Technology Stack
5. Project Structure
6. Database Schema
7. API Specification
8. Frontend Specification
9. Backend Specification
10. Service Worker & Notifications
11. Excel Export
12. Ollama DeepSeek R1 Integration
13. Deployment & Startup
14. Configuration
15. Error Handling & Validation
16. Testing Strategy
17. Future Enhancements (Post-MVP)

---

## 1. EXECUTIVE SUMMARY

**Purpose:** Create a web-based lab notebook and biweekly project tracker with hourly activity logging, progress tracking, and optional AI-powered daily analysis.

**Core Problem Solved:**
- Ajantha manages 6-7 active projects (NTKP, WES, Metagenomics, Rice Genomics, Business Strategy, Infrastructure, Equipment Management)
- Works on a 2-week planning cycle with detailed project breakdowns
- Needs to track daily work activities against the biweekly plan
- Requires intelligent insights (blockers, patterns, suggestions) without cloud data leakage
- Must maintain professional documentation for team sharing

**Solution:** Local-first web application (React frontend + FastAPI backend + SQLite database) with:
- Biweekly plan creation and management (shareable Excel export)
- Hourly proactive activity logging via Service Worker notifications
- Real-time progress tracking against planned activities
- Optional end-of-day AI analysis using local DeepSeek R1 model
- Zero cloud storage or external API calls

**Key Features:**
1. ✅ Create/edit/delete biweekly plans with projects and activities
2. ✅ Hourly popup notifications (8:30 AM - 5:00 PM, Mon-Fri) for activity logging
3. ✅ Log activities with project, specific activity, comments, and duration
4. ✅ Real-time progress dashboard (% completed activities per project)
5. ✅ Download plan as Excel for boss/team sharing
6. ✅ View all daily activities and logs
7. ✅ Optional: End-of-day DeepSeek analysis (blockers, suggestions, patterns)

**Success Metrics:**
- System captures hourly activities reliably
- Progress tracking reflects actual work vs. planned activities
- User can create/manage biweekly plans in < 5 minutes
- Excel export is professional and shareable
- Zero downtime or cloud dependencies

---

## 2. SYSTEM OVERVIEW & ARCHITECTURE

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│        Windows Laptop (User's Environment)          │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────────┐        ┌──────────────────┐  │
│  │  React Frontend  │◄──────►│ FastAPI Backend  │  │
│  │  (Port 3000)     │ HTTP   │  (Port 5000)     │  │
│  │                  │ WS     │                  │  │
│  │ • Dashboard      │        │ • REST APIs      │  │
│  │ • Plans UI       │        │ • Scheduler      │  │
│  │ • Activity Log   │        │ • WebSocket      │  │
│  │ • Service Worker │        │ • Excel Gen      │  │
│  └──────────────────┘        └────────┬─────────┘  │
│         │                             │            │
│         │                             ▼            │
│         │                    ┌──────────────────┐  │
│         │                    │  SQLite Database │  │
│         │                    │  lab_notebook.db │  │
│         └───────────────────►│  (Local Storage) │  │
│                              └──────────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘
         │
         │ (Network Call, Ollama API)
         │
         ▼
┌─────────────────────────────────────────────────────┐
│     Workstation (Ollama + DeepSeek R1)              │
├─────────────────────────────────────────────────────┤
│  IP: 192.168.200.5                                  │
│  Port: 11434                                        │
│  Model: deepseek-r1:7b                              │
│  (Used for end-of-day analysis only)                │
└─────────────────────────────────────────────────────┘
```

### 2.2 Data Flow

**Hourly Activity Logging:**
```
8:30 AM Monday
    │
    ▼
Service Worker checks time
    │
    ▼
Show system notification "What are you working on?"
    │
    ▼
User clicks notification
    │
    ▼
Open popup modal in browser
    │
    ├─ Project dropdown (all projects in current plan + ad-hoc)
    ├─ Activity dropdown (activities under selected project)
    ├─ Comment text area (free text)
    └─ Duration input (default 60 min)
    │
    ▼
User clicks "Submit"
    │
    ▼
POST /api/activity-logs
    │
    ▼
FastAPI stores in database
    │
    ▼
Update dashboard in real-time (WebSocket)
    │
    ▼
Close popup, wait 1 hour for next notification
```

**End-of-Day Analysis:**
```
5:00 PM (OLLAMA_ANALYSIS_HOUR = 17)
    │
    ▼
APScheduler triggers daily job
    │
    ▼
Fetch all activity_logs for today
    │
    ▼
Format prompt for DeepSeek:
  "User worked on: [list of projects/activities]
   Time logs: [detailed list]
   Provide: summary, blockers, suggestions, patterns"
    │
    ▼
POST to Ollama (192.168.200.5:11434/api/generate)
    │
    ▼
Stream response back
    │
    ▼
Store in daily_summaries table
    │
    ▼
Send WebSocket notification to frontend
    │
    ▼
User sees daily summary in dashboard
```

### 2.3 Component Breakdown

| Component | Purpose | Technology |
|-----------|---------|-----------|
| **React Frontend** | UI for plan management, activity logging, dashboard | React 18, TypeScript, Vite, Tailwind |
| **FastAPI Backend** | REST APIs, database CRUD, scheduling, Ollama integration | FastAPI, Python 3.9+, SQLAlchemy |
| **SQLite Database** | Local data storage (biweekly plans, projects, activities, logs) | SQLite3 |
| **Service Worker** | Background notifications, hourly popup triggers | JavaScript Service Worker API |
| **WebSocket** | Real-time communication (notifications, dashboard updates) | FastAPI WebSockets |
| **APScheduler** | Schedule hourly notifications and daily analysis | APScheduler (BackgroundScheduler) |
| **Ollama Client** | HTTP calls to DeepSeek R1 on workstation | Python requests library |
| **Excel Export** | Generate shareable biweekly plans as .xlsx | openpyxl library |

---

## 3. USER CONTEXT & WORKFLOWS

### 3.1 User Profile

**Name:** Ajantha  
**Role:** Bioinformatics Engineer at SLIBTEC  
**Experience:** Expert in Python, Nextflow, genomics pipelines  
**Work Pattern:** Structured 2-week planning cycles  
**Work Hours:** Monday-Friday, 8:30 AM - 5:00 PM  
**Projects:**
1. NTKP (National Traditional Knowledge Platform)
2. WES Pipeline (Whole Exome Sequencing)
3. Metagenomics Pipeline
4. Rice Genomics (Godawee salt tolerance variant analysis)
5. Business Strategy Analysis (techbio landscape research)
6. Bioinformatics Infrastructure (pipeline engineering)
7. Lab Equipment Management

**Constraints:**
- No cloud storage (local-only)
- No external API calls (privacy critical for institutional work)
- Must share plans with boss (Excel export requirement)
- Works on workstation with GPU (RTX A2000 12GB)
- Also works on separate Windows laptop (client machine)
- DeepSeek R1 only accessible on workstation (192.168.200.5:11434)

### 3.2 Workflow 1: Create Biweekly Plan (Monday, Week 1)

**Actor:** Ajantha  
**Duration:** 5-10 minutes  
**Frequency:** Every 2 weeks (start of cycle)

**Steps:**

1. **Access Application**
   - Open browser on laptop
   - Navigate to `http://localhost:3000`
   - See dashboard (empty if first plan, or previous plan summary)

2. **Create New Plan**
   - Click "New Biweekly Plan" button
   - Form opens with fields:
     - Plan Name: "Tea Genome Analysis - Week 1-2" (required, text input)
     - Start Date: "2026-02-09" (required, date picker, default = Monday of this week)
     - End Date: "2026-02-20" (required, date picker, default = Friday of week 2)
     - Description: (optional, text area)
   - Click "Create Plan"
   - System stores: `INSERT INTO biweekly_plans (name, start_date, end_date, status) VALUES (...)`
   - Redirect to Plan Editor

3. **Add Project 1**
   - Click "Add Project" button
   - Modal opens:
     - Project Name: "Tea Genome Analysis" (required)
     - Description: "Reproduce Xia et al. 2019 genome assembly paper" (optional)
     - Goal: "Complete assembly and annotation" (optional)
     - Color Tag: (optional, for UI visual organization)
   - Click "Save Project"
   - System stores: `INSERT INTO projects (biweekly_plan_id, name, description, goal) VALUES (...)`

4. **Add Activities for Project 1**
   - Under "Tea Genome Analysis", click "Add Activity"
   - Form appears:
     - Activity Name: "Illumina download SRP099527" (required)
     - Description: "Download ~2,124 Gb of raw Illumina FASTQ files" (optional)
     - Deliverables: "Directory containing raw FASTQ files" (optional)
     - Dependencies: "Availability of Data quota" (optional)
     - Estimated Hours: 4 (optional, float)
   - Click "Save Activity"
   - Repeat for all activities:
     - PacBio 20kb download SRR8334869 and SRR8334870
     - Download RNA-Seq Data SRX2748122
     - Download Validation Data SRP111069
     - Nextflow and Singularity setup
     - Filter Illumina Reads
     - (... etc, all ~30 activities from the Tea Genome example)
   - Each stored: `INSERT INTO activities (project_id, name, description, deliverables, dependencies) VALUES (...)`

5. **Add Project 2 (if any)**
   - Repeat steps 3-4 for additional projects
   - Example: "Yeast Deep Learning Project" with its activities

6. **Review and Download**
   - Click "Download as Excel"
   - System generates .xlsx file:
     - Sheet 1: Plan Overview (name, dates, project count)
     - Sheet 2: Detailed Breakdown (Project | Activity | Deliverables | Dependencies | Week 1 Mon-Fri | Week 2 Mon-Fri)
   - File saved to `Downloads/Tea_Genome_Plan_09-20-Feb-2026.xlsx`
   - User can share with boss via email

7. **Plan Ready**
   - Plan is now Active
   - System sets `biweekly_plans.status = 'Active'`
   - Dashboard now shows plan overview
   - Hourly popups will start Monday 8:30 AM

### 3.3 Workflow 2: Hourly Activity Logging (Throughout 2 Weeks)

**Actor:** Ajantha  
**Trigger:** Service Worker notification  
**Frequency:** Every hour, 8:30 AM - 5:00 PM, Monday-Friday  
**Duration:** < 1 minute per log

**Example Scenario: Tuesday 10:30 AM**

**Step-by-step:**

1. **Notification Arrives**
   - Service Worker checks current time: 10:30 AM Tuesday
   - Matches schedule (8:30 AM - 5:00 PM, Mon-Fri)
   - Shows system notification:
     ```
     🔔 Project Buddy
     What are you working on right now?
     [Click to log activity]
     ```
   - Sound/vibration (browser notification)

2. **User Clicks Notification**
   - Browser window opens/focuses
   - Popup modal appears:
     ```
     ┌─────────────────────────────────┐
     │ Log Activity - 10:30 AM          │
     ├─────────────────────────────────┤
     │                                 │
     │ Project:                        │
     │ [Dropdown: Select project...]   │
     │  • Tea Genome Analysis          │
     │  • Yeast Deep Learning          │
     │  • NTKP                         │
     │  • WES Pipeline                 │
     │  • Other/Ad-hoc                 │
     │                                 │
     │ Activity:                       │
     │ [Dropdown: Select activity...]  │
     │  (populated from selected proj) │
     │                                 │
     │ Comment:                        │
     │ [Text area]                     │
     │ "What did you do in this hour?" │
     │                                 │
     │ Duration:                       │
     │ [60] minutes                    │
     │                                 │
     │ [Submit] [Snooze 15 min] [Skip] │
     │                                 │
     └─────────────────────────────────┘
     ```

3. **User Fills Form**
   - Clicks Project dropdown → Selects "Tea Genome Analysis"
   - Activity dropdown now shows activities under Tea Genome:
     - Illumina download SRP099527
     - PacBio 20kb download
     - Nextflow and Singularity setup
     - Filter Illumina Reads
     - ... etc
   - Selects "Filter Illumina Reads"
   - Types in Comment: "Processed 500 samples, removed low-quality reads (Q < 20)"
   - Duration remains 60 minutes (can edit if needed)
   - Clicks "Submit"

4. **Data Storage**
   - Frontend POSTs to `/api/activity-logs`:
     ```json
     {
       "project_id": 1,
       "activity_id": 5,
       "comment": "Processed 500 samples, removed low-quality reads (Q < 20)",
       "duration_minutes": 60,
       "timestamp": "2026-02-24T10:30:00+05:30"
     }
     ```
   - FastAPI receives request
   - Inserts into `activity_logs` table:
     ```sql
     INSERT INTO activity_logs (
       biweekly_plan_id, project_id, activity_id, comment, 
       duration_minutes, timestamp
     ) VALUES (
       1, 1, 5, "Processed 500 samples...", 60, 
       "2026-02-24T10:30:00+05:30"
     )
     ```
   - Updates activity status if first log for this activity:
     ```sql
     UPDATE activities SET status = 'In Progress' 
     WHERE id = 5 AND status = 'Not Started'
     ```

5. **Popup Closes**
   - Modal disappears
   - User can continue working
   - Activity is logged and stored
   - Dashboard updates in real-time (WebSocket notification)
   - Next notification at 11:30 AM

6. **Ad-Hoc Activity Example**
   - 12:30 PM: Next notification arrives
   - User selects "Other/Ad-hoc"
   - Project dropdown now allows free-text input or quick-add
   - User types new project: "Troubleshooting SLURM Queue"
   - System auto-creates project if doesn't exist
   - User logs activity without specific activity_id
   - Comment: "Debugged SLURM scheduler errors, restarted service"

### 3.4 Workflow 3: View Progress Dashboard

**Actor:** Ajantha  
**Trigger:** Manual (anytime during or after work day)  
**Frequency:** Multiple times per day

**Steps:**

1. **Open Dashboard**
   - Navigate to `http://localhost:3000` (if not already open)
   - See "Dashboard" page (default landing page)

2. **View Current Plan Overview**
   - Header shows:
     ```
     Active Biweekly Plan
     Tea Genome Analysis - Week 1-2
     Start: Feb 9, 2026 | End: Feb 20, 2026
     Days Remaining: 12 days
     ```

3. **View Project Progress Cards**
   - For each project, see card:
     ```
     ┌──────────────────────────────┐
     │ Tea Genome Analysis          │
     │ Status: In Progress          │
     │                              │
     │ Activities: 8/30 Complete    │ (Progress bar: 27%)
     │ Hours Logged: 24/120         │ (Progress bar: 20%)
     │ Pending: 22                  │
     │                              │
     │ [View Details] [Log Time]    │
     └──────────────────────────────┘
     ```

4. **View Project Details** (Click "View Details")
   - See detailed activity list:
     ```
     Activity                           Status    Hours    Comments
     ─────────────────────────────────────────────────────────────
     ✓ Illumina download               Complete   4h      Downloaded SRP...
     ✓ PacBio 20kb download            Complete   3h      SRR8334869/8334870
     ◯ Download RNA-Seq Data           Pending    -       (0/2h est)
     ◯ Nextflow and Singularity setup  Pending    -       (0/8h est)
     ◯ Filter Illumina Reads           In Prog    2h      Processed 500 samples
     ◯ Filter PacBio Reads             Pending    -       (0/3h est)
     ... (24 more)
     ```

5. **View Daily Summary**
   - If it's after 5:00 PM and DeepSeek analysis is enabled:
     ```
     Today's Summary (Feb 24, 2026)
     ──────────────────────────────
     
     Projects Worked On:
     • Tea Genome Analysis (4 hours)
     • WES Pipeline (2 hours)
     • Ad-hoc: Troubleshooting SLURM (1 hour)
     
     Blockers Identified:
     ⚠️  Data Download Slow
         Issue: SRP099527 download stuck at 60% (recurring issue)
         Last occurrence: Feb 22, 2026
         Suggestion: Check network quota, consider parallel download
     
     Tomorrow's Suggestions:
     • Resume PacBio gap closing (blocked on assembly completion)
     • Start Nextflow environment setup
     • Check SLURM scheduler status
     
     Patterns Detected:
     • Tuesday mornings: 80% spent on Tea Genome
     • Afternoon blocks: Infrastructure maintenance (avg 1h/day)
     • End-of-week: More ad-hoc work (unplanned tasks)
     ```

### 3.5 Workflow 4: End-of-Day Analysis (5:00 PM)

**Actor:** System (automated)  
**Trigger:** APScheduler daily job at 5:00 PM  
**Frequency:** Every business day (Mon-Fri)

**Steps:**

1. **Job Triggered**
   - APScheduler fires at 5:00 PM (OLLAMA_ANALYSIS_HOUR = 17)
   - Calls FastAPI endpoint: `GET /api/deepseek/daily-analysis?date=2026-02-24`

2. **Data Aggregation**
   - FastAPI queries all activity_logs for today:
     ```sql
     SELECT * FROM activity_logs 
     WHERE DATE(timestamp) = '2026-02-24'
     ORDER BY timestamp ASC
     ```
   - Formats activities for DeepSeek prompt:
     ```
     Today's Work Log (Feb 24, 2026):
     
     8:30 AM: Tea Genome Analysis → Illumina download SRP099527
             Comment: Downloaded SRP... (60 min)
     
     9:30 AM: Tea Genome Analysis → Filter Illumina Reads
             Comment: Processed 500 samples, removed low-quality reads (60 min)
     
     10:30 AM: Tea Genome Analysis → Filter Illumina Reads
              Comment: Continued filtering, 3000/5000 samples done (60 min)
     
     ...
     
     4:30 PM: Troubleshooting SLURM Queue (ad-hoc)
             Comment: Debugged SLURM errors, restarted service (60 min)
     ```

3. **DeepSeek Analysis**
   - FastAPI sends HTTP POST to Ollama:
     ```
     POST http://192.168.200.5:11434/api/generate
     
     {
       "model": "deepseek-r1:7b",
       "prompt": "Analyze this work log and provide: 1) Summary of accomplishments, 2) Blockers or issues, 3) Recommendations for tomorrow, 4) Patterns observed. Format as JSON.",
       "stream": true
     }
     ```
   - Receives streaming response, aggregates into text
   - Parses for key sections (blockers, suggestions, patterns)

4. **Storage**
   - Creates daily_summary record:
     ```sql
     INSERT INTO daily_summaries (
       biweekly_plan_id, date, summary_text, blockers, 
       highlights, suggestions
     ) VALUES (
       1, '2026-02-24', 
       'Today you worked on Tea Genome...',
       '[{"issue": "Data download slow", "frequency": 2, ...}]',
       '[{"achievement": "Filtered 5000 samples", ...}]',
       '[{"project": "Tea Genome", "next_step": "Resume gap closing", ...}]'
     )
     ```

5. **Notification to User**
   - Sends WebSocket message to frontend
   - Dashboard updates with new daily summary
   - Optional: System notification alert
   - User can view summary immediately or later

---

## 4. TECHNOLOGY STACK

### 4.1 Frontend Stack

| Technology | Version | Purpose |
|-----------|---------|---------|
| **React** | 18.x | UI framework, component-based architecture |
| **TypeScript** | 5.x | Type safety, better IDE support |
| **Vite** | 5.x | Fast build tool, hot module replacement |
| **Tailwind CSS** | 3.x | Utility-first CSS framework |
| **shadcn/ui** | Latest | Pre-built, accessible UI components |
| **Axios** or **Fetch** | - | HTTP client for API calls |
| **Zustand** or **Context API** | - | State management (lightweight) |
| **date-fns** | 3.x | Date/time manipulation |
| **xlsx** | 0.18.x | Excel file generation |
| **React Router** | 6.x | Page routing |

### 4.2 Backend Stack

| Technology | Version | Purpose |
|-----------|---------|---------|
| **Python** | 3.9+ | Backend language |
| **FastAPI** | 0.104+ | REST API framework, async support |
| **SQLAlchemy** | 2.x | ORM for database |
| **SQLite** | 3.x | Local database |
| **APScheduler** | 3.x | Job scheduling (hourly popups, daily analysis) |
| **python-multipart** | - | File upload support |
| **openpyxl** | 3.x | Excel file generation |
| **requests** | 2.x | HTTP client for Ollama API |
| **pydantic** | 2.x | Data validation, serialization |
| **uvicorn** | 0.24+ | ASGI server |
| **python-dotenv** | - | Environment variable management |
| **websockets** | - | WebSocket support |

### 4.3 Database

| Component | Details |
|-----------|---------|
| **Type** | SQLite 3 |
| **File** | `lab_notebook.db` |
| **Location** | Project root directory (local) |
| **Connection** | SQLAlchemy + sqlite3 |
| **Backup Strategy** | User-initiated (no auto-backup in MVP) |

### 4.4 Deployment Platforms

| Environment | Specification |
|-------------|-----------|
| **Development** | Windows laptop, localhost:3000 (React) + localhost:5000 (FastAPI) |
| **Production** | Same Windows laptop (single-machine deployment) |
| **External Integration** | Ollama on workstation (192.168.200.5:11434) |

### 4.5 Browser Requirements

| Feature | Requirement |
|---------|-------------|
| **JavaScript** | ES2020+ (React 18 target) |
| **Service Worker** | Required for notifications |
| **WebSocket** | Required for real-time updates |
| **Supported Browsers** | Chrome, Edge, Firefox (latest versions) |

---

## 5. PROJECT STRUCTURE

### 5.1 Directory Layout

```
project-buddy/
├── backend/                          # FastAPI server
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app initialization, routes
│   │   ├── database.py               # SQLAlchemy setup, session management
│   │   ├── models.py                 # SQLAlchemy ORM models
│   │   ├── schemas.py                # Pydantic schemas (request/response)
│   │   ├── crud.py                   # Database CRUD operations
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── biweekly_plans.py     # /api/biweekly-plans endpoints
│   │   │   ├── projects.py           # /api/projects endpoints
│   │   │   ├── activities.py         # /api/activities endpoints
│   │   │   ├── activity_logs.py      # /api/activity-logs endpoints
│   │   │   ├── dashboard.py          # /api/dashboard endpoints
│   │   │   ├── deepseek.py           # /api/deepseek endpoints
│   │   │   └── exports.py            # /api/exports endpoints
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── scheduler.py          # APScheduler setup
│   │   │   ├── ollama_client.py      # Ollama HTTP client
│   │   │   ├── excel_exporter.py     # Excel file generation
│   │   │   └── notification.py       # WebSocket notifications
│   │   └── config.py                 # Configuration settings
│   ├── requirements.txt              # Python dependencies
│   ├── .env.example                  # Environment variables template
│   └── run.py                        # Startup script for backend
│
├── frontend/                         # React application
│   ├── src/
│   │   ├── index.tsx                 # Entry point
│   │   ├── App.tsx                   # Root component
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx         # Main dashboard page
│   │   │   ├── BiweeklyPlans.tsx     # Plan management page
│   │   │   ├── PlanEditor.tsx        # Create/edit plan page
│   │   │   ├── ProjectDetail.tsx     # Project detail page
│   │   │   ├── ActivityLogs.tsx      # Activity log view page
│   │   │   ├── Settings.tsx          # Settings/configuration page
│   │   │   └── NotFound.tsx          # 404 page
│   │   ├── components/
│   │   │   ├── ActivityPopup.tsx     # Hourly activity modal
│   │   │   ├── ProjectCard.tsx       # Project progress card
│   │   │   ├── ActivityList.tsx      # Activity list component
│   │   │   ├── DailySummary.tsx      # Daily summary display
│   │   │   ├── ProgressBar.tsx       # Progress visualization
│   │   │   ├── Header.tsx            # App header/navbar
│   │   │   ├── Sidebar.tsx           # Navigation sidebar
│   │   │   └── Notifications.tsx     # Toast notifications
│   │   ├── services/
│   │   │   ├── api.ts                # API client wrapper
│   │   │   ├── websocket.ts          # WebSocket client
│   │   │   ├── serviceWorker.ts      # Service Worker registration
│   │   │   └── storage.ts            # Local storage utilities
│   │   ├── hooks/
│   │   │   ├── usePlans.ts           # Custom hook for plans
│   │   │   ├── useActivities.ts      # Custom hook for activities
│   │   │   ├── useNotifications.ts   # Custom hook for notifications
│   │   │   └── useWebSocket.ts       # Custom hook for WebSocket
│   │   ├── context/
│   │   │   └── AppContext.tsx        # Global app state (Context API)
│   │   ├── types/
│   │   │   └── index.ts              # TypeScript type definitions
│   │   ├── utils/
│   │   │   ├── formatting.ts         # Date/time formatting
│   │   │   ├── calculations.ts       # Progress calculations
│   │   │   └── constants.ts          # App constants
│   │   └── styles/
│   │       └── globals.css           # Global styles
│   ├── public/
│   │   ├── service-worker.js         # Service Worker script
│   │   └── manifest.json             # PWA manifest
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── index.html
│
├── scripts/                          # Startup scripts
│   ├── start.bat                     # Windows startup script
│   ├── start.sh                      # Linux/Mac startup script
│   └── config.example.json           # Configuration template
│
├── docs/                             # Documentation
│   ├── SETUP.md                      # Installation & setup guide
│   ├── API.md                        # API documentation
│   ├── USER_GUIDE.md                 # User manual
│   └── TROUBLESHOOTING.md            # Common issues & solutions
│
├── README.md                         # Project overview
├── .gitignore
└── docker-compose.yml                # (Optional) Docker setup

```

### 5.2 Key File Descriptions

**Backend Files:**

- **main.py**: FastAPI app definition, route mounting, startup/shutdown events
- **database.py**: SQLAlchemy engine, session management, database initialization
- **models.py**: SQLAlchemy ORM models (BiweeklyPlan, Project, Activity, ActivityLog, DailySummary)
- **schemas.py**: Pydantic models for request/response validation
- **crud.py**: Create, Read, Update, Delete operations for all entities
- **scheduler.py**: APScheduler setup, hourly job and daily analysis job definitions
- **ollama_client.py**: HTTP wrapper for DeepSeek R1 API calls

**Frontend Files:**

- **App.tsx**: Main React component, routing setup
- **Dashboard.tsx**: Main dashboard, project cards, daily summary
- **ActivityPopup.tsx**: Modal for logging activities during hourly popups
- **serviceWorker.ts**: Service Worker registration, notification handling
- **api.ts**: Axios/Fetch wrapper for all API calls

---

## 6. DATABASE SCHEMA

### 6.1 Complete SQLite Schema

```sql
-- Biweekly Plans Table
CREATE TABLE biweekly_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    start_date TEXT NOT NULL,      -- ISO 8601 format (YYYY-MM-DD)
    end_date TEXT NOT NULL,        -- ISO 8601 format (YYYY-MM-DD)
    status TEXT DEFAULT 'Active',  -- Active | Completed | Paused | Archived
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Projects Table
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    biweekly_plan_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    goal TEXT,
    status TEXT DEFAULT 'Not Started',  -- Not Started | In Progress | Blocked | Complete
    color_tag TEXT,                     -- Optional: for UI organization (#FF5733, etc.)
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(biweekly_plan_id) REFERENCES biweekly_plans(id) ON DELETE CASCADE,
    UNIQUE(biweekly_plan_id, name)  -- Project name unique within a plan
);

-- Activities Table (tasks within projects)
CREATE TABLE activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    deliverables TEXT,
    dependencies TEXT,
    status TEXT DEFAULT 'Not Started',  -- Not Started | In Progress | Complete
    estimated_hours REAL DEFAULT 0.0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Activity Logs Table (hourly activity captures)
CREATE TABLE activity_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    biweekly_plan_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    activity_id INTEGER,                -- NULL for ad-hoc activities
    comment TEXT NOT NULL,              -- User's description of work done
    duration_minutes INTEGER DEFAULT 60,
    timestamp TEXT NOT NULL,            -- ISO 8601 with timezone (YYYY-MM-DDTHH:MM:SS+05:30)
    tags TEXT,                          -- JSON array of tags (auto-generated by DeepSeek)
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(biweekly_plan_id) REFERENCES biweekly_plans(id) ON DELETE CASCADE,
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY(activity_id) REFERENCES activities(id) ON DELETE SET NULL
);

-- Daily Summaries Table (end-of-day analysis results)
CREATE TABLE daily_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    biweekly_plan_id INTEGER,           -- NULL if summary spans multiple plans
    date TEXT NOT NULL,                 -- ISO 8601 date (YYYY-MM-DD)
    summary_text TEXT,                  -- Free-form summary from DeepSeek
    blockers TEXT,                      -- JSON array of blocker objects
    highlights TEXT,                    -- JSON array of accomplishments
    suggestions TEXT,                   -- JSON array of recommendations
    patterns TEXT,                      -- JSON array of observed patterns
    generated_at TEXT NOT NULL,         -- When the summary was generated
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date)                        -- One summary per day
);

-- Indexes for Performance
CREATE INDEX idx_biweekly_plans_status ON biweekly_plans(status);
CREATE INDEX idx_projects_plan_id ON projects(biweekly_plan_id);
CREATE INDEX idx_activities_project_id ON activities(project_id);
CREATE INDEX idx_activity_logs_plan_id ON activity_logs(biweekly_plan_id);
CREATE INDEX idx_activity_logs_project_id ON activity_logs(project_id);
CREATE INDEX idx_activity_logs_timestamp ON activity_logs(timestamp);
CREATE INDEX idx_daily_summaries_date ON daily_summaries(date);
```

### 6.2 Data Type & Constraint Explanations

| Table | Field | Type | Constraints | Notes |
|-------|-------|------|-------------|-------|
| biweekly_plans | id | INTEGER | PK, AUTO | System-generated ID |
| | name | TEXT | UNIQUE, NOT NULL | E.g., "Tea Genome - Week 1-2" |
| | start_date | TEXT | NOT NULL | ISO 8601 format for cross-platform compatibility |
| | end_date | TEXT | NOT NULL | Always >= start_date |
| | status | TEXT | DEFAULT 'Active' | Controls which plan is "current" |
| projects | id | INTEGER | PK, AUTO | - |
| | biweekly_plan_id | INTEGER | FK, NOT NULL | Links to owning plan |
| | name | TEXT | NOT NULL, UNIQUE in plan | Can't have duplicate project names in same plan |
| activities | id | INTEGER | PK, AUTO | - |
| | activity_id | INTEGER | FK, nullable | NULL for ad-hoc activities |
| activity_logs | timestamp | TEXT | NOT NULL | Stored as ISO 8601 (YYYY-MM-DDTHH:MM:SS+05:30) for timezone accuracy |
| | tags | TEXT | nullable | JSON array: `["analysis", "debugging", "documentation"]` |
| daily_summaries | blockers | TEXT | nullable | JSON array of blocker objects with issue, frequency, suggestions |

### 6.3 Sample Data

**BiweeklyPlan:**
```
id=1, name="Tea Genome Analysis - Week 1-2", start_date="2026-02-09", 
end_date="2026-02-20", status="Active"
```

**Project:**
```
id=1, biweekly_plan_id=1, name="Tea Genome Analysis", 
status="In Progress", goal="Complete assembly and annotation"
```

**Activity:**
```
id=5, project_id=1, name="Filter Illumina Reads", 
deliverables="QC reports", estimated_hours=3.0, status="In Progress"
```

**ActivityLog:**
```
id=1, biweekly_plan_id=1, project_id=1, activity_id=5,
comment="Processed 500 samples, removed low-quality reads (Q < 20)",
duration_minutes=60, timestamp="2026-02-24T10:30:00+05:30"
```

**DailySummary:**
```
id=1, biweekly_plan_id=1, date="2026-02-24",
summary_text="Worked on Tea Genome filtering and PacBio download...",
blockers='[{"issue": "Slow download", "frequency": 2}]',
suggestions='[{"next_step": "Resume gap closing"}]'
```

---

## 7. API SPECIFICATION

### 7.1 API Base Configuration

- **Base URL (Development):** `http://localhost:5000`
- **Base URL (Production):** `http://localhost:5000` (same machine)
- **Authentication:** None (local-only application)
- **Content-Type:** `application/json`
- **Response Format:** Consistent JSON structure

### 7.2 Global Response Format

**Success Response (2xx):**
```json
{
  "success": true,
  "data": { /* endpoint-specific data */ },
  "message": "Operation completed successfully"
}
```

**Error Response (4xx/5xx):**
```json
{
  "success": false,
  "error": "Error code or message",
  "details": "Detailed error description",
  "timestamp": "2026-02-24T10:30:00Z"
}
```

### 7.3 Endpoints

---

## BIWEEKLY PLANS ENDPOINTS

### `POST /api/biweekly-plans`
**Create a new biweekly plan**

**Request:**
```json
{
  "name": "Tea Genome Analysis - Week 1-2",
  "description": "Genome assembly and annotation for tea plant",
  "start_date": "2026-02-09",
  "end_date": "2026-02-20"
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Tea Genome Analysis - Week 1-2",
    "start_date": "2026-02-09",
    "end_date": "2026-02-20",
    "status": "Active",
    "created_at": "2026-02-09T08:30:00Z",
    "updated_at": "2026-02-09T08:30:00Z"
  }
}
```

**Validation:**
- `name`: Required, unique, 3-200 characters
- `start_date`, `end_date`: Valid ISO 8601 dates, end >= start
- `description`: Optional, max 1000 characters

---

### `GET /api/biweekly-plans`
**List all biweekly plans**

**Query Parameters:**
- `status`: Filter by status (Active | Completed | Paused | Archived)
- `sort`: Sort by (created_at | updated_at | name), default: created_at DESC
- `limit`: Records per page (default: 20)
- `offset`: Pagination offset (default: 0)

**Response (200):**
```json
{
  "success": true,
  "data": {
    "plans": [
      {
        "id": 1,
        "name": "Tea Genome - Week 1-2",
        "start_date": "2026-02-09",
        "end_date": "2026-02-20",
        "status": "Active",
        "project_count": 2,
        "activity_count": 35,
        "created_at": "2026-02-09T08:30:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "pages": 1
  }
}
```

---

### `GET /api/biweekly-plans/{id}`
**Get plan details with all projects and activities**

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Tea Genome Analysis - Week 1-2",
    "description": "...",
    "start_date": "2026-02-09",
    "end_date": "2026-02-20",
    "status": "Active",
    "projects": [
      {
        "id": 1,
        "name": "Tea Genome Analysis",
        "status": "In Progress",
        "activities_count": 30,
        "completed_count": 5,
        "completion_percent": 16.7,
        "total_hours_logged": 24,
        "estimated_total_hours": 120,
        "activities": [
          {
            "id": 1,
            "name": "Illumina download SRP099527",
            "status": "Complete",
            "estimated_hours": 4,
            "logged_hours": 4.5,
            "deliverables": "Directory containing raw FASTQ files"
          }
        ]
      }
    ],
    "created_at": "2026-02-09T08:30:00Z",
    "updated_at": "2026-02-09T08:30:00Z"
  }
}
```

---

### `PUT /api/biweekly-plans/{id}`
**Update plan details**

**Request:**
```json
{
  "name": "Tea Genome - Week 1-2 (Updated)",
  "status": "Active",
  "description": "Updated description"
}
```

**Response (200):** Updated plan object

---

### `DELETE /api/biweekly-plans/{id}`
**Delete a plan and all associated data**

**Response (200):**
```json
{
  "success": true,
  "message": "Plan deleted successfully"
}
```

**Note:** Cascading delete removes all projects, activities, activity_logs

---

### `GET /api/biweekly-plans/active`
**Get the currently active biweekly plan**

**Response (200):**
```json
{
  "success": true,
  "data": { /* full plan object */ }
}
```

**Note:** Returns the plan with `status='Active'`. Only one should exist at a time.

---

### `GET /api/biweekly-plans/{id}/export-excel`
**Download plan as Excel file**

**Response (200):** Binary XLSX file with headers:
```
Content-Disposition: attachment; filename=Tea_Genome_Plan_09-20-Feb-2026.xlsx
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
```

**Excel Structure:**
- Sheet 1: "Overview" - Plan metadata, project summary
- Sheet 2: "Projects & Activities" - Detailed breakdown
- Sheet 3: "Time Tracking" - Hours logged per activity
- Columns: Project | Activity | Deliverables | Dependencies | Week1 Mon-Fri | Week2 Mon-Fri

---

## PROJECTS ENDPOINTS

### `POST /api/biweekly-plans/{plan_id}/projects`
**Add a project to a biweekly plan**

**Request:**
```json
{
  "name": "Tea Genome Analysis",
  "description": "Reproduce Xia et al. 2019 genome assembly",
  "goal": "Complete assembly and annotation",
  "color_tag": "#FF5733"
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "biweekly_plan_id": 1,
    "name": "Tea Genome Analysis",
    "status": "Not Started",
    "activities": [],
    "created_at": "2026-02-09T09:00:00Z"
  }
}
```

---

### `GET /api/biweekly-plans/{plan_id}/projects`
**List all projects in a plan**

**Response (200):**
```json
{
  "success": true,
  "data": {
    "projects": [
      {
        "id": 1,
        "name": "Tea Genome Analysis",
        "status": "In Progress",
        "activities_count": 30,
        "completed_count": 5,
        "completion_percent": 16.7
      }
    ]
  }
}
```

---

### `PUT /api/projects/{id}`
**Update project details**

**Request:**
```json
{
  "name": "Tea Genome - Updated",
  "status": "In Progress",
  "goal": "Updated goal"
}
```

**Response (200):** Updated project object

---

### `DELETE /api/projects/{id}`
**Delete a project**

**Response (200):**
```json
{
  "success": true,
  "message": "Project deleted successfully"
}
```

---

### `POST /api/projects/{id}/activities`
**Add an activity to a project**

**Request:**
```json
{
  "name": "Illumina download SRP099527",
  "description": "Download ~2,124 Gb of raw Illumina FASTQ files",
  "deliverables": "Directory containing raw FASTQ files",
  "dependencies": "Availability of Data quota",
  "estimated_hours": 4.0
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "project_id": 1,
    "name": "Illumina download SRP099527",
    "status": "Not Started",
    "estimated_hours": 4.0,
    "logged_hours": 0,
    "created_at": "2026-02-09T09:15:00Z"
  }
}
```

---

### `GET /api/projects/{id}/activities`
**List all activities in a project**

**Response (200):**
```json
{
  "success": true,
  "data": {
    "activities": [
      {
        "id": 1,
        "name": "Illumina download SRP099527",
        "status": "Not Started",
        "estimated_hours": 4.0,
        "logged_hours": 0,
        "deliverables": "..."
      }
    ]
  }
}
```

---

### `PUT /api/activities/{id}`
**Update activity details or mark as complete**

**Request:**
```json
{
  "name": "Illumina download SRP099527",
  "status": "Complete"
}
```

**Response (200):** Updated activity object

---

### `DELETE /api/activities/{id}`
**Delete an activity**

**Response (200):**
```json
{
  "success": true,
  "message": "Activity deleted successfully"
}
```

---

## ACTIVITY LOGS ENDPOINTS

### `POST /api/activity-logs`
**Log an activity (hourly capture)**

**Request:**
```json
{
  "biweekly_plan_id": 1,
  "project_id": 1,
  "activity_id": 5,
  "comment": "Processed 500 samples, removed low-quality reads (Q < 20)",
  "duration_minutes": 60,
  "timestamp": "2026-02-24T10:30:00+05:30"
}
```

**Note:** `activity_id` is optional (null for ad-hoc projects)

**Response (201):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "project_id": 1,
    "activity_id": 5,
    "comment": "Processed 500 samples...",
    "duration_minutes": 60,
    "timestamp": "2026-02-24T10:30:00+05:30",
    "created_at": "2026-02-24T10:30:05Z"
  }
}
```

---

### `GET /api/activity-logs?date={YYYY-MM-DD}`
**Get all logs for a specific date**

**Query Parameters:**
- `date`: ISO 8601 date (required)
- `project_id`: Filter by project (optional)
- `sort`: (timestamp_asc | timestamp_desc), default: timestamp_asc

**Response (200):**
```json
{
  "success": true,
  "data": {
    "date": "2026-02-24",
    "total_hours": 7.5,
    "logs": [
      {
        "id": 1,
        "timestamp": "2026-02-24T08:30:00+05:30",
        "project_name": "Tea Genome Analysis",
        "activity_name": "Illumina download",
        "comment": "Started download...",
        "duration_minutes": 60
      }
    ]
  }
}
```

---

### `PUT /api/activity-logs/{id}`
**Edit a logged activity**

**Request:**
```json
{
  "comment": "Updated comment",
  "duration_minutes": 75
}
```

**Response (200):** Updated log object

---

### `DELETE /api/activity-logs/{id}`
**Delete a logged activity**

**Response (200):**
```json
{
  "success": true,
  "message": "Log deleted successfully"
}
```

---

## DASHBOARD ENDPOINTS

### `GET /api/dashboard`
**Get current plan overview and progress summary**

**Response (200):**
```json
{
  "success": true,
  "data": {
    "active_plan": {
      "id": 1,
      "name": "Tea Genome Analysis - Week 1-2",
      "start_date": "2026-02-09",
      "end_date": "2026-02-20",
      "days_remaining": 12,
      "projects_count": 2,
      "overall_completion": 22.5
    },
    "projects": [
      {
        "id": 1,
        "name": "Tea Genome Analysis",
        "status": "In Progress",
        "completion_percent": 16.7,
        "activities_total": 30,
        "activities_completed": 5,
        "hours_logged": 24,
        "hours_estimated": 120
      }
    ],
    "today_summary": {
      "date": "2026-02-24",
      "total_hours_logged": 7.5,
      "activities_logged": 8,
      "projects_worked_on": ["Tea Genome Analysis", "WES Pipeline", "Troubleshooting"]
    }
  }
}
```

---

### `GET /api/dashboard/daily-summary?date={YYYY-MM-DD}`
**Get daily summary and stats**

**Response (200):**
```json
{
  "success": true,
  "data": {
    "date": "2026-02-24",
    "generated_summary": {
      "id": 1,
      "summary_text": "Today you worked on Tea Genome filtering...",
      "blockers": [
        {
          "issue": "Slow data download",
          "frequency": 2,
          "last_occurred": "2026-02-22",
          "suggestion": "Check network quota"
        }
      ],
      "highlights": [
        {
          "achievement": "Filtered 5000 samples",
          "project": "Tea Genome"
        }
      ],
      "suggestions": [
        {
          "project": "Tea Genome",
          "next_step": "Resume PacBio gap closing",
          "rationale": "Assembly phase is next"
        }
      ],
      "patterns": [
        {
          "observation": "Tuesday mornings: 80% Tea Genome"
        }
      ],
      "generated_at": "2026-02-24T17:00:00Z"
    }
  }
}
```

---

## DEEPSEEK INTEGRATION ENDPOINTS

### `POST /api/deepseek/daily-analysis`
**Trigger end-of-day analysis (normally called by scheduler)**

**Request:**
```json
{
  "date": "2026-02-24"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "summary_id": 1,
    "analysis_completed_at": "2026-02-24T17:02:00Z",
    "summary": { /* full summary object */ }
  }
}
```

---

### `GET /api/deepseek/daily-summary?date={YYYY-MM-DD}`
**Retrieve stored daily summary (same as /api/dashboard/daily-summary)**

---

## FILE EXPORT ENDPOINTS

### `GET /api/exports/plan-excel/{plan_id}`
**Generate and download Excel for a specific plan**

**Response (200):** Binary XLSX file

---

## WEBSOCKET ENDPOINTS

### `WS /ws/notifications`
**Real-time notification stream**

**Message Format (from server to client):**
```json
{
  "type": "activity_logged",
  "timestamp": "2026-02-24T10:30:05Z",
  "data": { /* activity log object */ }
}
```

Message types:
- `activity_logged`: New activity logged
- `summary_ready`: Daily summary generated
- `plan_updated`: Plan modified
- `notification`: Alert for user

---

## 7.4 Error Codes

| HTTP Code | Scenario |
|-----------|----------|
| 400 | Bad request (validation error) |
| 404 | Resource not found |
| 409 | Conflict (e.g., duplicate name) |
| 500 | Server error |
| 503 | Service unavailable (Ollama unreachable) |

---

## 8. FRONTEND SPECIFICATION

### 8.1 Technology & Tools

- **React Version:** 18.x
- **TypeScript:** Full type coverage
- **Build Tool:** Vite
- **CSS Framework:** Tailwind CSS 3.x
- **UI Components:** shadcn/ui (or Radix UI primitives)
- **State Management:** React Context API + useReducer
- **HTTP Client:** Axios or Fetch API
- **Routing:** React Router v6
- **Date/Time:** date-fns or dayjs

### 8.2 Page Structure & Navigation

```
App (Root)
├── Header (Logo, Plan name, Quick stats)
├── Sidebar (Navigation)
│   ├── Dashboard
│   ├── Biweekly Plans
│   ├── Activity Logs
│   ├── Settings
│   └── Help
└── Main Content Area
    ├── Dashboard Page
    ├── Biweekly Plans List Page
    ├── Plan Editor Page
    ├── Project Detail Page
    ├── Activity Logs Page
    └── Settings Page
```

### 8.3 Detailed Page Specifications

#### **Page 1: Dashboard (Default Landing)**

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  Project Buddy          [Time: 10:30 AM]    [⚙️ Settings]│
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────┐  Active Biweekly Plan            │
│  │                  │  ─────────────────────────────    │
│  │ [Sidebar]        │  Tea Genome Analysis - Week 1-2  │
│  │ Dashboard    ✓   │  Start: Feb 9 | End: Feb 20      │
│  │ Plans            │  Days Remaining: 12               │
│  │ Activity Log     │  Overall Completion: 22.5%       │
│  │ Settings         │                                   │
│  │                  │  Quick Stats:                     │
│  │                  │  ├─ Active Projects: 2           │
│  │                  │  ├─ Activities Done: 5/30        │
│  │                  │  ├─ Hours Logged Today: 3.5h     │
│  │                  │  └─ Total Hours This Week: 15h   │
│  │                  │                                   │
│  └──────────────────┘  ┌────────────────────────────┐  │
│                        │ Project: Tea Genome        │  │
│                        │ Status: In Progress        │  │
│                        │ Completion: 16.7% (5/30)   │  │
│                        │ Hours: 24h/120h            │  │
│                        │ [View Details] [Log Time]  │  │
│                        └────────────────────────────┘  │
│                        ┌────────────────────────────┐  │
│                        │ Project: Yeast Deep Learn  │  │
│                        │ Status: Not Started        │  │
│                        │ Completion: 0% (0/5)       │  │
│                        │ Hours: 0h/20h              │  │
│                        │ [View Details] [Log Time]  │  │
│                        └────────────────────────────┘  │
│                                                         │
│  ──────────────────────────────────────────────────────│
│  Today's Activity Timeline                             │
│  8:30 [████] Tea Genome (60 min)                       │
│  9:30 [████] Tea Genome (60 min)                       │
│  10:30 [████] Tea Genome (60 min)                      │
│  11:30 [████] WES Pipeline (60 min)                    │
│  12:30 [███] Lunch/Break (30 min)                      │
│  1:30  [████] Tea Genome (60 min)                      │
│  ──────────────────────────────────────────────────────│
│  Daily Summary (Generated 5:00 PM)                     │
│  Summary: Focused on Tea Genome...                     │
│  Blockers: Download stuck at 60% (recurring)           │
│  Next Steps: Resume gap closing, setup Nextflow       │
└─────────────────────────────────────────────────────────┘
```

**Components:**
- Project cards (name, status badge, progress bar, stats)
- Daily timeline (visual bar chart of hours by time)
- Quick action buttons ("View Details", "Log Time Now")
- Daily summary section (if available from DeepSeek)

**Interactions:**
- Clicking "View Details" → ProjectDetail page
- Clicking "Log Time Now" → ActivityPopup modal
- Clicking project card → Project detail page

---

#### **Page 2: Biweekly Plans**

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  Biweekly Plans                      [+ New Plan]       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Filters: [All ▼] [Sort by: Created ▼]                │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Plan Name              | Status    | Projects | Actions
│  ├───────────────────────────────────────────────────┤ │
│  │ Tea Genome - Week 1-2  │ Active    │ 2        │ [Edit][Download][Archive][Delete] │
│  │ Yeast Deep Learning    │ Completed │ 1        │ [View][Download][Delete]         │
│  │ Previous Plan 2        │ Archived  │ 3        │ [View][Download][Delete]         │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Actions:**
- **New Plan**: Opens PlanEditor page
- **Edit**: Opens PlanEditor with plan data prefilled
- **Download**: Downloads Excel file immediately
- **Archive**: Moves plan to Archived status
- **Delete**: Asks confirmation, deletes plan and all data

---

#### **Page 3: Plan Editor (Create/Edit)**

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  [◄ Back] Create Biweekly Plan                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Plan Details:                                          │
│  ┌─────────────────────────────────────────────────┐  │
│  │ Plan Name: [Tea Genome Analysis - Week 1-2____]│  │
│  │ Description: [Large text area for description] │  │
│  │ Start Date: [Feb 9, 2026] | End Date: [Feb 20]│  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  Projects:                                              │
│  ┌─────────────────────────────────────────────────┐  │
│  │ Project 1: Tea Genome Analysis                  │  │
│  │ Description: Reproduce Xia et al. 2019         │  │
│  │ Goal: Complete assembly and annotation          │  │
│  │ Color: [#FF5733 ▼]                              │  │
│  │                                                 │  │
│  │ Activities:                                      │  │
│  │ ├─ Illumina download SRP099527 (4h)            │  │
│  │ ├─ PacBio 20kb download (3h)                   │  │
│  │ ├─ Download RNA-Seq Data (2h)                  │  │
│  │ ├─ Nextflow and Singularity setup (8h)         │  │
│  │ ├─ Filter Illumina Reads (3h)                  │  │
│  │ └─ [+ Add Activity]                             │  │
│  │                                                 │  │
│  │ [Delete Project]                                │  │
│  └─────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────┐  │
│  │ [+ Add Project]                                 │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  [Save Plan] [Download Excel] [Cancel]                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Interactions:**
- Add/edit/delete projects dynamically
- Add/edit/delete activities within each project
- Inline edit fields with validation
- Real-time character count for descriptions
- Save triggers POST to `/api/biweekly-plans` or PUT if editing
- Download Excel triggers GET to `/api/biweekly-plans/{id}/export-excel`

---

#### **Page 4: Project Detail**

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  [◄ Back] Tea Genome Analysis                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Status: In Progress | Completion: 16.7% (5/30)        │
│  [████░░░░░░░░░░░░░░░░░░] Progress Bar                │
│  Hours: 24h logged / 120h estimated (20% of estimate)  │
│                                                         │
│  Activities List:                                       │
│  ┌──────────────────────────────────────────────────┐ │
│  │ [✓] Illumina download SRP099527 (4/4h)         │ │
│  │     Deliverables: Directory with raw FASTQ     │ │
│  │     [Edit] [Mark Incomplete]                   │ │
│  │                                                  │ │
│  │ [✓] PacBio 20kb download (3/3h)                │ │
│  │     Deliverables: SRR8334869, SRR8334870       │ │
│  │     [Edit] [Mark Incomplete]                   │ │
│  │                                                  │ │
│  │ [◯] Download RNA-Seq Data (0/2h)              │ │
│  │     Deliverables: SRX2748122 directory        │ │
│  │     [Edit] [Mark Complete]                    │ │
│  │                                                  │ │
│  │ [◯] Nextflow and Singularity setup (0/8h)     │ │
│  │     Deliverables: Working Nextflow env        │ │
│  │     Dependencies: Server access                │ │
│  │     [Edit] [Mark Complete]                    │ │
│  │                                                  │ │
│  │ [□] Filter Illumina Reads (2.5/3h)            │ │
│  │     Status: In Progress                        │ │
│  │     Deliverables: QC reports                   │ │
│  │     [Edit] [Mark Complete]                    │ │
│  │     Recent logs:                               │ │
│  │     • 10:30 AM: Processed 500 samples...      │ │
│  │     • 9:30 AM: Started filtering (2.5h total) │ │
│  │     [View All Logs]                           │ │
│  │                                                  │ │
│  │ ... (24 more activities)                       │ │
│  └──────────────────────────────────────────────────┘ │
│                                                         │
│  [Log Time Now] [Add Activity] [Edit Project]         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Components:**
- Activity list with checkboxes (click to toggle complete)
- Progress bars (completed activities, estimated hours)
- Recent activity logs for each activity (last 3 logs shown)
- Inline editing for activity details
- Time tracking display

---

#### **Page 5: Activity Logs**

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  Activity Logs                                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Filters:                                               │
│  Date Range: [Feb 24, 2026] to [Feb 24, 2026]         │
│  Project: [All Projects ▼]                            │
│  Search: [________________]                            │
│  [Apply Filters] [Export CSV]                          │
│                                                         │
│  ┌──────────────────────────────────────────────────┐ │
│  │ Time       │ Project       │ Activity  │ Comment │ │
│  ├──────────────────────────────────────────────────┤ │
│  │ 8:30 AM    │ Tea Genome    │ Illumina  │ Started│ │
│  │            │               │ download  │ DL...  │ │
│  │ 9:30 AM    │ Tea Genome    │ Filter IL │ Proces│ │
│  │            │               │           │ sed... │ │
│  │ 10:30 AM   │ Tea Genome    │ Filter IL │ Cont. │ │
│  │            │               │           │ filtering
│  │ 11:30 AM   │ WES Pipeline  │ Variant   │ Called│ │
│  │            │               │ calling   │ var... │ │
│  │ 12:30 PM   │ Ad-hoc        │ (none)    │ Lunch  │ │
│  │ 1:30 PM    │ Tea Genome    │ Filter IL │ Resume│ │
│  │            │               │           │ filtering
│  └──────────────────────────────────────────────────┘ │
│                                                         │
│  [Edit] [Delete]  (hover over entries)                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

### 8.4 Hourly Activity Popup

**Appearance:**
- Service Worker notification (Windows system notification)
- Clicking notification opens popup modal in browser
- Modal is always-on-top, centers on screen
- Cannot be minimized, only dismissed (submit/snooze/skip)

**Modal Content:**
```
┌──────────────────────────────────────────┐
│  📝 Log Activity                          │
│  10:30 AM - What are you working on?     │
│  [×] Close                               │
├──────────────────────────────────────────┤
│                                          │
│  Project:                                │
│  [Dropdown ▼]                            │
│   • Tea Genome Analysis                  │
│   • WES Pipeline                         │
│   • NTKP                                 │
│   • Metagenomics                         │
│   • Other/Ad-hoc                         │
│                                          │
│  Activity:                               │
│  [Dropdown ▼] (populated from project)  │
│   • Filter Illumina Reads                │
│   • PacBio gap closing                   │
│   • (none for ad-hoc projects)           │
│                                          │
│  Comment:                                │
│  [Large text area]                       │
│  "What specifically did you work on?"    │
│  (Max 500 chars)                         │
│                                          │
│  Duration:                               │
│  [60▼] minutes                           │
│                                          │
│  [Submit] [Snooze 15 min] [Skip]        │
│                                          │
└──────────────────────────────────────────┘
```

**State Management:**
- Uses React state (useState) for form data
- POST to `/api/activity-logs` on Submit
- Close popup after successful submit
- Show toast notification: "Activity logged ✓"
- WebSocket updates dashboard in real-time

---

### 8.5 Service Worker Implementation

**File:** `public/service-worker.js`

**Functionality:**
1. Register on app load
2. Listen for messages from FastAPI backend
3. Show system notification when message received
4. Click notification → focus app window + open popup modal
5. Background notifications (works even if browser minimized)

**Code Structure:**
```javascript
// Register on page load
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/service-worker.js');
}

// Service Worker handler for push messages
self.addEventListener('message', (event) => {
  const { type, data } = event.data;
  if (type === 'SHOW_NOTIFICATION') {
    self.registration.showNotification('Project Buddy', {
      body: 'What are you working on right now?',
      icon: '/icon.png',
      badge: '/badge.png',
      tag: 'activity-popup',
      requireInteraction: true
    });
  }
});

// Click notification
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    clients.matchAll({ type: 'window' }).then((clientList) => {
      // Focus existing window or open new one
      // Send message to show ActivityPopup
    })
  );
});
```

---

### 8.6 Styling & Design System

**Color Palette:**
- Primary: #3B82F6 (Blue - actions, focus)
- Secondary: #10B981 (Green - success, complete)
- Danger: #EF4444 (Red - delete, warning)
- Neutral: #6B7280 (Gray - borders, disabled)
- Background: #F9FAFB (Off-white)
- Text: #1F2937 (Dark gray)

**Typography:**
- Headers: Inter Bold, 18-28px
- Body: Inter Regular, 14-16px
- Mono: Fira Code, 12-14px (for code snippets)

**Components (shadcn/ui):**
- Buttons, inputs, dropdowns, modals, progress bars, cards
- Pre-built, accessible, minimal styling needed

---

## 9. BACKEND SPECIFICATION

### 9.1 Directory & File Breakdown

**main.py** - FastAPI Application
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base, get_db
from app.api import biweekly_plans, projects, activities, activity_logs, dashboard, deepseek
from app.services.scheduler import start_scheduler

app = FastAPI(title="Project Buddy API")

# CORS middleware (localhost only)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"])

# Create tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(biweekly_plans.router, prefix="/api", tags=["Plans"])
app.include_router(projects.router, prefix="/api", tags=["Projects"])
app.include_router(activities.router, prefix="/api", tags=["Activities"])
app.include_router(activity_logs.router, prefix="/api", tags=["Logs"])
app.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])
app.include_router(deepseek.router, prefix="/api", tags=["DeepSeek"])

@app.on_event("startup")
async def startup():
    start_scheduler()

@app.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket):
    # WebSocket handler for real-time notifications
    pass
```

**database.py** - SQLAlchemy Setup
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./lab_notebook.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**models.py** - ORM Models
```python
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class BiweeklyPlan(Base):
    __tablename__ = "biweekly_plans"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    start_date = Column(String)  # ISO 8601
    end_date = Column(String)
    status = Column(String, default="Active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    projects = relationship("Project", back_populates="biweekly_plan", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="biweekly_plan", cascade="all, delete-orphan")

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    biweekly_plan_id = Column(Integer, ForeignKey("biweekly_plans.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    goal = Column(Text, nullable=True)
    status = Column(String, default="Not Started")
    color_tag = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    biweekly_plan = relationship("BiweeklyPlan", back_populates="projects")
    activities = relationship("Activity", back_populates="project", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="project")

class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    deliverables = Column(Text, nullable=True)
    dependencies = Column(Text, nullable=True)
    status = Column(String, default="Not Started")
    estimated_hours = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    project = relationship("Project", back_populates="activities")
    activity_logs = relationship("ActivityLog", back_populates="activity")

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id = Column(Integer, primary_key=True)
    biweekly_plan_id = Column(Integer, ForeignKey("biweekly_plans.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=True)
    comment = Column(Text, nullable=False)
    duration_minutes = Column(Integer, default=60)
    timestamp = Column(String, nullable=False)  # ISO 8601 with timezone
    tags = Column(Text, nullable=True)  # JSON array
    created_at = Column(DateTime, default=datetime.utcnow)
    
    biweekly_plan = relationship("BiweeklyPlan", back_populates="activity_logs")
    project = relationship("Project", back_populates="activity_logs")
    activity = relationship("Activity", back_populates="activity_logs")

class DailySummary(Base):
    __tablename__ = "daily_summaries"
    id = Column(Integer, primary_key=True)
    biweekly_plan_id = Column(Integer, ForeignKey("biweekly_plans.id"), nullable=True)
    date = Column(String, unique=True, index=True)  # ISO 8601 date
    summary_text = Column(Text, nullable=True)
    blockers = Column(Text, nullable=True)  # JSON
    highlights = Column(Text, nullable=True)  # JSON
    suggestions = Column(Text, nullable=True)  # JSON
    patterns = Column(Text, nullable=True)  # JSON
    generated_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

**schemas.py** - Pydantic Models
```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class BiweeklyPlanCreate(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: str  # ISO 8601
    end_date: str
    
class BiweeklyPlanResponse(BiweeklyPlanCreate):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    
class ActivityLogCreate(BaseModel):
    biweekly_plan_id: int
    project_id: int
    activity_id: Optional[int] = None
    comment: str
    duration_minutes: int = 60
    timestamp: str  # ISO 8601 with timezone
    
class ActivityLogResponse(ActivityLogCreate):
    id: int
    created_at: datetime
```

**scheduler.py** - Job Scheduling
```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.services.ollama_client import analyze_daily_logs
from app.services.notification import send_notification
import pytz

scheduler = BackgroundScheduler()

def hourly_popup_job():
    """Trigger hourly activity popup (Mon-Fri 8:30-17:30)"""
    send_notification(type="activity_popup", message="What are you working on?")

def daily_analysis_job():
    """Trigger end-of-day DeepSeek analysis at 5:00 PM"""
    analyze_daily_logs(date=datetime.today())

def start_scheduler():
    # Hourly popup every hour from 8:30 AM to 5:30 PM, Mon-Fri
    scheduler.add_job(
        hourly_popup_job,
        CronTrigger(hour='8-17', minute='30', day_of_week='0-4'),
        timezone=pytz.timezone('Asia/Colombo')
    )
    
    # Daily analysis at 5:00 PM, Mon-Fri
    scheduler.add_job(
        daily_analysis_job,
        CronTrigger(hour='17', minute='0', day_of_week='0-4'),
        timezone=pytz.timezone('Asia/Colombo')
    )
    
    scheduler.start()
```

**ollama_client.py** - Ollama Integration
```python
import requests
import json
from datetime import datetime

OLLAMA_BASE_URL = "http://192.168.200.5:11434"
MODEL = "deepseek-r1:7b"

def analyze_daily_logs(date: str, activity_logs: List[ActivityLog]) -> dict:
    """Send activity logs to DeepSeek for analysis"""
    
    # Format logs into prompt
    logs_text = "\n".join([
        f"{log.timestamp}: {log.project.name} → {log.activity.name if log.activity else 'Ad-hoc'}\n"
        f"  Comment: {log.comment}\n"
        f"  Duration: {log.duration_minutes} minutes"
        for log in activity_logs
    ])
    
    prompt = f"""Analyze this work log from {date} and provide structured feedback:

{logs_text}

Please provide in JSON format:
{{
  "summary": "Overall summary of the day's work",
  "blockers": [
    {{"issue": "...", "frequency": 1, "suggestion": "..."}}
  ],
  "highlights": ["achievement 1", "achievement 2"],
  "suggestions": [
    {{"project": "...", "next_step": "...", "rationale": "..."}}
  ],
  "patterns": ["pattern 1", "pattern 2"]
}}"""
    
    # Call Ollama API
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=300  # 5-minute timeout
    )
    
    if response.status_code == 200:
        result = response.json()
        return json.loads(result.get("response", "{}"))
    else:
        raise Exception(f"Ollama API error: {response.status_code}")
```

---

## 10. SERVICE WORKER & NOTIFICATIONS

### 10.1 Service Worker Registration (React)

**File:** `src/services/serviceWorker.ts`

```typescript
export function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/service-worker.js')
      .then((registration) => {
        console.log('Service Worker registered:', registration);
        // Listen for messages from service worker
        navigator.serviceWorker.addEventListener('message', handleServiceWorkerMessage);
      })
      .catch((error) => {
        console.error('Service Worker registration failed:', error);
      });
  }
}

function handleServiceWorkerMessage(event: MessageEvent) {
  const { type, data } = event.data;
  if (type === 'ACTIVITY_POPUP') {
    // Open activity popup modal
    showActivityPopup();
  }
}
```

### 10.2 Service Worker Script

**File:** `public/service-worker.js`

```javascript
const CACHE_NAME = 'project-buddy-v1';

self.addEventListener('install', (event) => {
  event.waitUntil(self.skipWaiting());
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

// Listen for messages from backend (via WebSocket)
self.addEventListener('message', (event) => {
  const { type, data } = event.data;
  
  if (type === 'SHOW_NOTIFICATION') {
    self.registration.showNotification('Project Buddy - Activity Log', {
      body: 'What are you working on right now?',
      icon: '/icon-192.png',
      badge: '/badge-72.png',
      tag: 'activity-popup-' + Date.now(),
      requireInteraction: true,
      actions: [
        { action: 'open', title: 'Log Activity' },
        { action: 'snooze', title: 'Snooze 15 min' },
        { action: 'skip', title: 'Skip' }
      ]
    });
  }
});

// Handle notification click
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  const action = event.action;
  
  if (action === 'open' || action === '') {
    event.waitUntil(
      clients.matchAll({ type: 'window', includeUncontrolled: true })
        .then((clientList) => {
          // Focus existing window or open new one
          let client = clientList.find(c => c.type === 'window');
          
          if (client) {
            client.focus();
            client.postMessage({ type: 'SHOW_ACTIVITY_POPUP' });
            return client;
          } else {
            return clients.openWindow('/');
          }
        })
    );
  } else if (action === 'snooze') {
    // Schedule next notification in 15 minutes
    // This would be handled by backend scheduler
  }
});
```

### 10.3 WebSocket Real-Time Updates

**File:** `src/services/websocket.ts`

```typescript
export class WebSocketClient {
  private ws: WebSocket;
  private url: string;
  
  constructor(url: string = 'ws://localhost:5000/ws/notifications') {
    this.url = url;
  }
  
  connect(onMessage: (data: any) => void) {
    this.ws = new WebSocket(this.url);
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
      
      // Handle different message types
      if (data.type === 'NOTIFICATION') {
        this.showBrowserNotification(data);
      } else if (data.type === 'ACTIVITY_LOGGED') {
        // Update dashboard in real-time
      } else if (data.type === 'SUMMARY_READY') {
        // Show daily summary
      }
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }
  
  private showBrowserNotification(data: any) {
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification('Project Buddy', {
        body: data.message,
        icon: '/icon.png'
      });
    }
  }
  
  send(data: any) {
    if (this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }
  
  close() {
    if (this.ws) {
      this.ws.close();
    }
  }
}
```

---

## 11. EXCEL EXPORT

### 11.1 Excel File Structure

**File Format:** XLSX (openpyxl)

**Sheets:**

**Sheet 1: Overview**
```
Biweekly Plan: Tea Genome Analysis - Week 1-2
Period: Feb 9 - Feb 20, 2026
Generated: Feb 24, 2026 at 10:30 AM

Summary:
- Total Projects: 2
- Total Activities: 35
- Activities Completed: 5
- Overall Completion: 14.3%

Projects:
1. Tea Genome Analysis (30 activities, 5 complete)
2. Yeast Deep Learning (5 activities, 0 complete)
```

**Sheet 2: Projects & Activities**
```
Project Name | Activity | Deliverables | Dependencies | Week 1 Mon | ... | Week 2 Fri
─────────────┼──────────┼──────────────┼──────────────┼───────────┼─────┼──────────
Tea Genome   | Illumina | Directory    | Data quota   | [   ]     | ... | [   ]
             | download |              |              |           |     |
             | SRP...   |              |              |           |     |
             │          │              │              │           │     │
             | PacBio   | SRR8334869   | None         | [   ]     | ... | [   ]
             | 20kb dl  | SRR8334870   |              |           |     |
             │          │              │              │           |     │
... (all activities)
```

---

### 11.2 Excel Generation Code

**File:** `app/services/excel_exporter.py`

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border
from datetime import datetime

def generate_biweekly_plan_excel(plan: BiweeklyPlan) -> BytesIO:
    """Generate Excel file for biweekly plan"""
    
    wb = Workbook()
    
    # Sheet 1: Overview
    ws_overview = wb.active
    ws_overview.title = "Overview"
    
    ws_overview['A1'] = f"Biweekly Plan: {plan.name}"
    ws_overview['A2'] = f"Period: {plan.start_date} to {plan.end_date}"
    ws_overview['A3'] = f"Generated: {datetime.now().strftime('%b %d, %Y at %H:%M %p')}"
    
    # Style headers
    for cell in ['A1', 'A2', 'A3']:
        ws_overview[cell].font = Font(bold=True, size=12)
    
    # Summary section
    ws_overview['A5'] = "Summary:"
    total_projects = len(plan.projects)
    total_activities = sum(len(p.activities) for p in plan.projects)
    completed = sum(1 for p in plan.projects for a in p.activities if a.status == 'Complete')
    
    ws_overview['A6'] = f"Total Projects: {total_projects}"
    ws_overview['A7'] = f"Total Activities: {total_activities}"
    ws_overview['A8'] = f"Completed: {completed}"
    ws_overview['A9'] = f"Completion: {(completed/total_activities*100):.1f}%" if total_activities > 0 else "0%"
    
    # Sheet 2: Detailed Breakdown
    ws_detail = wb.create_sheet("Projects & Activities")
    
    headers = [
        'Project Name', 'Activity', 'Deliverables', 'Dependencies', 
        'Est. Hours', 'Status', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri',
        'Mon', 'Tue', 'Wed', 'Thu', 'Fri'
    ]
    
    ws_detail.append(headers)
    
    # Style header row
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    
    for cell in ws_detail[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
    
    # Add data rows
    row_num = 2
    for project in plan.projects:
        for idx, activity in enumerate(project.activities):
            if idx == 0:
                ws_detail[f'A{row_num}'] = project.name
            else:
                ws_detail[f'A{row_num}'] = ''
            
            ws_detail[f'B{row_num}'] = activity.name
            ws_detail[f'C{row_num}'] = activity.deliverables or ''
            ws_detail[f'D{row_num}'] = activity.dependencies or ''
            ws_detail[f'E{row_num}'] = activity.estimated_hours or 0
            ws_detail[f'F{row_num}'] = activity.status
            
            row_num += 1
    
    # Set column widths
    ws_detail.column_dimensions['A'].width = 20
    ws_detail.column_dimensions['B'].width = 25
    ws_detail.column_dimensions['C'].width = 20
    ws_detail.column_dimensions['D'].width = 15
    
    # Save to bytes
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    return output
```

---

## 12. OLLAMA DEEPSEEK R1 INTEGRATION

### 12.1 Configuration

**Environment Variables (.env):**
```
OLLAMA_HOST=192.168.200.5
OLLAMA_PORT=11434
OLLAMA_MODEL=deepseek-r1:7b
OLLAMA_TIMEOUT=300
OLLAMA_ANALYSIS_ENABLED=True
OLLAMA_ANALYSIS_HOUR=17
OLLAMA_ANALYSIS_MINUTE=0
```

### 12.2 Analysis Workflow

**Triggered:** Daily at 5:00 PM (17:00)

**Input:** All ActivityLog entries for the day

**Prompt Template:**
```
User's Work Log for {DATE}:

{FORMATTED_LOGS}

Please analyze this work log and provide:

1. SUMMARY: Brief overview of today's work (2-3 sentences)
2. BLOCKERS: Issues, blockers, or recurring problems
   Format as JSON: [{"issue": "...", "frequency": X, "last_occurred": "...", "suggestion": "..."}]
3. HIGHLIGHTS: Key accomplishments
   Format as JSON array of strings
4. SUGGESTIONS: Recommendations for next steps
   Format as JSON: [{"project": "...", "next_step": "...", "rationale": "..."}]
5. PATTERNS: Observed patterns in work habits
   Format as JSON array of strings

Return ONLY valid JSON with these fields.
```

### 12.3 Response Parsing

```python
def parse_deepseek_response(response_text: str) -> dict:
    """Parse JSON response from DeepSeek"""
    try:
        # Extract JSON from response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        json_text = response_text[json_start:json_end]
        
        return json.loads(json_text)
    except (json.JSONDecodeError, ValueError):
        # If parsing fails, return empty structure
        return {
            "summary": "Unable to parse response",
            "blockers": [],
            "highlights": [],
            "suggestions": [],
            "patterns": []
        }
```

---

## 13. DEPLOYMENT & STARTUP

### 13.1 Windows Startup Script

**File:** `scripts/start.bat`

```batch
@echo off
echo Starting Project Buddy...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo Node.js is not installed or not in PATH
    exit /b 1
)

REM Start FastAPI backend in new terminal
echo Starting FastAPI Backend...
start "Project Buddy Backend" cmd /k "cd backend && python -m uvicorn app.main:app --reload --port 5000"

REM Wait for backend to start
timeout /t 3 /nobreak

REM Start React frontend in new terminal
echo Starting React Frontend...
start "Project Buddy Frontend" cmd /k "cd frontend && npm run dev"

REM Wait for frontend to start
timeout /t 5 /nobreak

REM Open browser
echo Opening browser...
start http://localhost:3000

echo Project Buddy is starting. Frontend will open in your default browser.
echo Backend: http://localhost:5000
echo Frontend: http://localhost:3000
pause
```

### 13.2 Installation Guide

**Prerequisites:**
- Python 3.9+
- Node.js 16+
- SQLite 3
- Windows 10+ (for Service Worker & notifications)

**Steps:**

1. **Clone/download project**
   ```bash
   cd project-buddy
   ```

2. **Backend setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Frontend setup**
   ```bash
   cd ../frontend
   npm install
   ```

4. **Verify Ollama connectivity**
   ```bash
   python ../test_ollama_access.py --host 192.168.200.5 --model deepseek-r1:7b
   ```

5. **Launch application**
   ```bash
   ../scripts/start.bat
   ```

---

## 14. CONFIGURATION

**File:** `config.json` (in project root)

```json
{
  "app": {
    "name": "Project Buddy",
    "version": "2.0.0",
    "debug": false
  },
  "backend": {
    "host": "127.0.0.1",
    "port": 5000,
    "database_url": "sqlite:///lab_notebook.db"
  },
  "frontend": {
    "host": "127.0.0.1",
    "port": 3000
  },
  "ollama": {
    "enabled": true,
    "host": "192.168.200.5",
    "port": 11434,
    "model": "deepseek-r1:7b",
    "timeout": 300
  },
  "scheduler": {
    "enabled": true,
    "timezone": "Asia/Colombo",
    "hourly_popup": {
      "start_hour": 8,
      "start_minute": 30,
      "end_hour": 17,
      "end_minute": 0,
      "interval_minutes": 60,
      "days_of_week": "0-4"
    },
    "daily_analysis": {
      "hour": 17,
      "minute": 0,
      "days_of_week": "0-4"
    }
  },
  "notifications": {
    "enabled": true,
    "sound": true,
    "vibration": true
  }
}
```

---

## 15. ERROR HANDLING & VALIDATION

### 15.1 Input Validation

- **Plan name:** Required, 3-200 chars, unique
- **Dates:** Valid ISO 8601, end >= start
- **Project name:** Required, 1-100 chars, unique per plan
- **Activity name:** Required, 1-150 chars
- **Comment:** Required, 1-500 chars
- **Duration:** 1-480 minutes (1 minute to 8 hours)
- **Estimated hours:** 0.5-1000 (optional)

### 15.2 Error Codes & Messages

| Scenario | Status | Message |
|----------|--------|---------|
| Missing required field | 400 | "Field {name} is required" |
| Invalid date format | 400 | "Date must be ISO 8601 format (YYYY-MM-DD)" |
| Duplicate name | 409 | "Plan with this name already exists" |
| Resource not found | 404 | "{Resource} with ID {id} not found" |
| Ollama unreachable | 503 | "DeepSeek analysis service unavailable" |
| Database error | 500 | "Database operation failed" |

---

## 16. TESTING STRATEGY

### 16.1 Unit Tests

- Database CRUD operations
- Calculation functions (progress %, estimated vs. logged hours)
- Excel generation
- Date/time utilities

### 16.2 Integration Tests

- API endpoints (create plan → add projects → log activities → view dashboard)
- WebSocket messaging
- File download generation
- Ollama connectivity

### 16.3 Manual Testing Checklist

- [ ] Create biweekly plan with multiple projects
- [ ] Add activities to projects
- [ ] Download plan as Excel
- [ ] Receive hourly notification
- [ ] Log activity via popup
- [ ] View dashboard with progress
- [ ] Edit/delete activities
- [ ] Verify progress calculations
- [ ] Test daily analysis (if Ollama available)
- [ ] Cross-browser testing (Chrome, Edge, Firefox)

---

## 17. FUTURE ENHANCEMENTS (Post-MVP)

1. **Smart Suggestions:** Auto-suggest project based on day/time patterns
2. **Historical Analysis:** Compare weeks, identify productivity trends
3. **Time Estimation:** Auto-learn typical duration for activity types
4. **Team Sharing:** Export plan for team collaboration
5. **Mobile App:** React Native version for phone access
6. **Cloud Sync:** Optional cloud backup (user-controlled)
7. **Integration:** Slack/Teams notifications for hourly popups
8. **Analytics Dashboard:** Charts, burndown graphs, velocity tracking
9. **Custom Reports:** Generate PDF reports of accomplishments
10. **Recurring Activities:** Template-based plans from previous cycles

---

**END OF SPECIFICATION DOCUMENT**

This comprehensive specification provides complete implementation guidance for all components of the Lab Notebook & Project Tracker system.
