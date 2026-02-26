' Project Buddy — Stop All Services
' Double-click this file to cleanly shut down everything.

Option Explicit

Dim shell
Set shell = WScript.CreateObject("WScript.Shell")

' Kill process listening on port 5000 (backend)
shell.Run "powershell -Command ""$p = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -First 1; if ($p) { Stop-Process -Id $p -Force }""", 0, True

' Kill process listening on port 3000 (frontend)
shell.Run "powershell -Command ""$p = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -First 1; if ($p) { Stop-Process -Id $p -Force }""", 0, True

' Kill tray (any python.exe not on port 5000 — i.e. tray.py)
shell.Run "powershell -Command ""Get-Process python -ErrorAction SilentlyContinue | Where-Object { (Get-NetTCPConnection -OwningProcess $_.Id -LocalPort 5000 -ErrorAction SilentlyContinue) -eq $null } | Stop-Process -Force""", 0, True

MsgBox "Project Buddy stopped.", 64, "Project Buddy"
