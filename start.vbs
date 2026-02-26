' Project Buddy — Start All Services
' Double-click this file to launch backend, frontend, and system tray.
' Windows will run everything silently (no console windows).

Option Explicit

Dim shell, root
Set shell = WScript.CreateObject("WScript.Shell")

root = "D:\Nuwan\Concept_Papers\Project-Buddy"

' ── 1. Backend (FastAPI / uvicorn on port 5000) ───────────────────────────────
shell.Run "cmd /c cd /d """ & root & "\backend"" && python -m uvicorn app.main:app --host 127.0.0.1 --port 5000", 0, False

' Wait for backend to bind the port
WScript.Sleep 3000

' ── 2. Frontend (Vite dev server on port 3000) ────────────────────────────────
shell.Run "cmd /c cd /d """ & root & "\frontend"" && npm run dev", 0, False

' Wait for Vite to compile
WScript.Sleep 4000

' ── 3. System tray app (opens browser automatically) ─────────────────────────
shell.Run "python """ & root & "\backend\tray.py""", 0, False
