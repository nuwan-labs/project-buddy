' Project Buddy — Setup Windows Auto-start
' Run this ONCE to make Project Buddy launch automatically on login.
' It creates a shortcut to start.vbs in your Windows Startup folder.

Option Explicit

Dim shell, fso, startupFolder, shortcutPath, shortcut, scriptDir

Set shell  = WScript.CreateObject("WScript.Shell")
Set fso    = WScript.CreateObject("Scripting.FileSystemObject")

startupFolder = shell.SpecialFolders("Startup")
scriptDir     = fso.GetParentFolderName(WScript.ScriptFullName)
shortcutPath  = startupFolder & "\Project Buddy.lnk"

Set shortcut             = shell.CreateShortcut(shortcutPath)
shortcut.TargetPath      = scriptDir & "\start.vbs"
shortcut.WorkingDirectory = scriptDir
shortcut.Description     = "Start Project Buddy (backend + frontend + tray)"
shortcut.IconLocation    = "shell32.dll,13"   ' calendar/notebook icon
shortcut.Save

MsgBox "Done! Project Buddy will now start automatically on login." & Chr(13) & Chr(13) & _
       "Shortcut created at:" & Chr(13) & shortcutPath & Chr(13) & Chr(13) & _
       "To remove auto-start, delete that shortcut.", _
       64, "Project Buddy — Auto-start Setup"
