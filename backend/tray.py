#!/usr/bin/env python3
"""
Project Buddy — System Tray App  (v2 – modern notification cards)

Architecture:
  Main thread  →  tkinter event loop (hidden root + popup Toplevels)
  Thread 2     →  pystray icon (run_detached)
  Thread 3     →  WebSocket listener (auto-reconnects)
"""
from __future__ import annotations

import json
import queue
import sys
import threading
import time
import tkinter as tk
import webbrowser
from datetime import date, datetime
from tkinter import ttk

import requests

try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError:
    sys.exit("Run: pip install pystray pillow")

try:
    import websocket as _websocket
except ImportError:
    sys.exit("Run: pip install websocket-client")

# ─── Config ───────────────────────────────────────────────────────────────────

API_BASE = "http://127.0.0.1:5000/api"
APP_URL  = "http://localhost:3000"
WS_URL   = "ws://127.0.0.1:5000/ws/notifications"

_popup_queue           = queue.Queue()
_activity_popup_open   = False
_daily_note_popup_open = False

# ─── Design tokens ────────────────────────────────────────────────────────────

A_HDR    = "#2563EB"    # activity header (blue)
A_HDR_DK = "#1D4ED8"
N_HDR    = "#059669"    # notes header (green)
N_HDR_DK = "#047857"

BG      = "#FFFFFF"
BG_FOOT = "#F8FAFF"
TXT     = "#111827"
LBL_C   = "#6B7280"
BRD     = "#E5E7EB"

PRI   = "#2563EB";  PRI_H  = "#1D4ED8"
SEC   = "#F3F4F6";  SEC_H  = "#E5E7EB"

F    = ("Segoe UI", 9)
FB   = ("Segoe UI", 10, "bold")
FH   = ("Segoe UI", 11, "bold")
FS   = ("Segoe UI", 8)
FBTN = ("Segoe UI", 9)

# ─── API helpers ──────────────────────────────────────────────────────────────

def _get(path: str) -> dict:
    try:
        return requests.get(f"{API_BASE}{path}", timeout=5).json().get("data", {})
    except Exception:
        return {}

def _post(path: str, payload: dict) -> dict:
    try:
        return requests.post(f"{API_BASE}{path}", json=payload, timeout=10).json()
    except Exception:
        return {}

# ─── Widget helpers ───────────────────────────────────────────────────────────

def _flat_btn(parent, text: str, cmd, primary: bool = True) -> tk.Label:
    """Flat label-button with hover colour change."""
    bg, bgh = (PRI, PRI_H) if primary else (SEC, SEC_H)
    fg      = "white" if primary else "#374151"
    b = tk.Label(parent, text=text, bg=bg, fg=fg, font=FBTN,
                 padx=16, pady=7, cursor="hand2")
    b.bind("<Button-1>", lambda e: cmd())
    b.bind("<Enter>",    lambda e: b.config(bg=bgh))
    b.bind("<Leave>",    lambda e: b.config(bg=bg))
    return b

def _entry(parent, **kw) -> tk.Entry:
    return tk.Entry(parent, bg=BG, fg=TXT, font=F, relief="flat",
                    highlightthickness=1, highlightbackground=BRD,
                    highlightcolor=A_HDR, insertbackground=TXT, **kw)

def _textbox(parent, height: int = 2, **kw) -> tk.Text:
    return tk.Text(parent, bg=BG, fg=TXT, font=F, relief="flat",
                   highlightthickness=1, highlightbackground=BRD,
                   highlightcolor=A_HDR, insertbackground=TXT,
                   height=height, wrap="word", **kw)

def _pos(win: tk.Toplevel, w: int, h: int) -> None:
    """Position window at bottom-right corner (near system tray)."""
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    win.geometry(f"{w}x{h}+{sw - w - 24}+{sh - h - 60}")

def _sep(parent) -> None:
    tk.Frame(parent, bg=BRD, height=1).pack(fill="x")

# ─── Activity Popup ───────────────────────────────────────────────────────────

class ActivityPopup(tk.Toplevel):
    W, H = 390, 355

    def __init__(self, master: tk.Tk) -> None:
        global _activity_popup_open
        _activity_popup_open = True
        super().__init__(master)

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg=BRD)
        self.withdraw()                     # hide while building (prevents blank-white flash)

        self._projects: list[dict]       = []
        self._act_map:  dict[int, list]  = {}
        self._dx = self._dy = 0

        self._build()
        self.update_idletasks()             # let geometry manager calculate sizes
        _pos(self, self.W, self.H)          # position after layout is ready
        self.deiconify()                    # show
        self.attributes("-alpha", 0.99)     # trigger DWM compositing (Windows rendering fix)
        self.update()
        self._load_projects()
        self.lift()
        self.focus_force()
        self.bell()
        self.after(100, self.grab_set)      # delay grab so render completes first

    # ── layout ────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="both", expand=True, padx=1, pady=1)

        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(outer, bg=A_HDR)
        hdr.pack(fill="x")

        tk.Frame(hdr, bg=A_HDR, height=10).pack(fill="x")   # top spacer
        app_lbl = tk.Label(hdr, text="Project Buddy",
                           bg=A_HDR, fg="#BAD5FF", font=FS, padx=14, pady=0)
        app_lbl.pack(anchor="w")

        tit_lbl = tk.Label(hdr, text="⏰  What are you working on?",
                           bg=A_HDR, fg="white", font=FH, padx=14, pady=3)
        tit_lbl.pack(anchor="w")

        sub_lbl = tk.Label(hdr,
                           text=datetime.now().strftime("%H:%M  ·  %A %d %B"),
                           bg=A_HDR, fg="#93C5FD", font=FS, padx=14, pady=0)
        sub_lbl.pack(anchor="w")
        tk.Frame(hdr, bg=A_HDR, height=10).pack(fill="x")   # bottom spacer

        # bind drag to header + all labels
        for w in (hdr, app_lbl, tit_lbl, sub_lbl):
            w.bind("<ButtonPress-1>", self._ds)
            w.bind("<B1-Motion>",     self._dm)

        # close button (placed over header, top-right)
        close = tk.Label(hdr, text="×", bg=A_HDR, fg="white",
                         font=("Segoe UI", 15, "bold"), cursor="hand2",
                         padx=10, pady=6)
        close.place(relx=1.0, y=6, anchor="ne", x=-4)
        close.bind("<Button-1>", lambda e: self._skip())

        # ── Body ──────────────────────────────────────────────────────────────
        body = tk.Frame(outer, bg=BG, padx=16, pady=10)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)

        row = 0
        for label_text, v_attr, cb_attr in [
            ("Project",  "_proj_var", "_proj_cb"),
            ("Activity", "_act_var",  "_act_cb"),
        ]:
            tk.Label(body, text=label_text, bg=BG, fg=LBL_C, font=FS).grid(
                row=row, column=0, sticky="w", pady=(4 if row else 0, 2))
            var = tk.StringVar()
            cb  = ttk.Combobox(body, textvariable=var, state="readonly", font=F)
            cb.grid(row=row + 1, column=0, sticky="ew", pady=(0, 2))
            setattr(self, v_attr, var)
            setattr(self, cb_attr, cb)
            row += 2

        self._proj_cb.bind("<<ComboboxSelected>>", self._on_proj)

        tk.Label(body, text="Comment *", bg=BG, fg=LBL_C, font=FS).grid(
            row=row, column=0, sticky="w", pady=(4, 2))
        self._comment = _textbox(body, height=2)
        self._comment.grid(row=row + 1, column=0, sticky="ew")

        dur_row = tk.Frame(body, bg=BG)
        dur_row.grid(row=row + 2, column=0, sticky="w", pady=(8, 0))
        tk.Label(dur_row, text="Duration:", bg=BG, fg=LBL_C, font=FS).pack(side="left")
        self._dur = tk.StringVar(value="60")
        _entry(dur_row, textvariable=self._dur, width=5).pack(side="left", padx=(6, 4))
        tk.Label(dur_row, text="min", bg=BG, fg=LBL_C, font=FS).pack(side="left")

        self._err = tk.Label(body, text="", fg="#EF4444", bg=BG, font=FS)
        self._err.grid(row=row + 3, column=0, sticky="w", pady=(3, 0))

        # ── Footer ────────────────────────────────────────────────────────────
        _sep(outer)
        self._foot = tk.Frame(outer, bg=BG_FOOT, padx=16, pady=10)
        self._foot.pack(fill="x")
        self._log_btn = _flat_btn(self._foot, "Log Time", self._submit)
        self._log_btn.pack(side="right", padx=(8, 0))
        _flat_btn(self._foot, "Skip", self._skip, primary=False).pack(side="right")

    # ── drag ──────────────────────────────────────────────────────────────────

    def _ds(self, e) -> None:
        self._dx = e.x_root - self.winfo_x()
        self._dy = e.y_root - self.winfo_y()

    def _dm(self, e) -> None:
        self.geometry(f"+{e.x_root - self._dx}+{e.y_root - self._dy}")

    # ── data ──────────────────────────────────────────────────────────────────

    def _load_projects(self) -> None:
        def _fetch():
            d = _get("/projects?status=Active")
            self._projects = d.get("projects", [])
            # "General / Admin" is always first — maps to project_id=None
            names = ["— General / Admin —"] + [p["name"] for p in self._projects]
            self.after(0, lambda: self._proj_cb.config(values=names))
        threading.Thread(target=_fetch, daemon=True).start()

    def _on_proj(self, _=None) -> None:
        name = self._proj_var.get()
        if name == "— General / Admin —":
            self._act_cb.config(values=[])
            self._act_var.set("")
            return
        proj = next((p for p in self._projects if p["name"] == name), None)
        if not proj:
            return
        pid = proj["id"]
        if pid in self._act_map:
            self._fill_acts(pid)
        else:
            def _fetch():
                d = _get(f"/projects/{pid}/activities")
                self._act_map[pid] = d.get("activities", [])
                self.after(0, lambda: self._fill_acts(pid))
            threading.Thread(target=_fetch, daemon=True).start()

    def _fill_acts(self, pid: int) -> None:
        self._act_cb.config(values=[a["name"] for a in self._act_map.get(pid, [])])
        self._act_var.set("")

    # ── submit ────────────────────────────────────────────────────────────────

    def _submit(self) -> None:
        comment = self._comment.get("1.0", "end").strip()
        if not comment:
            self._err.config(text="Comment is required.")
            return

        try:
            dur = max(1, min(480, int(self._dur.get())))
        except ValueError:
            self._err.config(text="Duration must be a number.")
            return

        proj_name = self._proj_var.get()
        proj = next((p for p in self._projects if p["name"] == proj_name), None)
        an   = self._act_var.get()
        act  = (next((a for a in self._act_map.get(proj["id"], [])
                      if a["name"] == an), None) if proj and an else None)

        self._log_btn.config(text="Saving…")
        self._err.config(text="")
        payload = {
            "project_id":       proj["id"] if proj else None,
            "activity_id":      act["id"]  if act  else None,
            "comment":          comment,
            "duration_minutes": dur,
            "timestamp":        datetime.now().astimezone().isoformat(),
        }
        threading.Thread(target=self._do_post, args=(payload,),
                         daemon=True).start()

    def _do_post(self, payload: dict) -> None:
        res = _post("/activity-logs", payload)
        if res.get("success"):
            self.after(0, self._show_saved)
        else:
            self.after(0, lambda: (
                self._err.config(text="Save failed — check backend."),
                self._log_btn.config(text="Log Time"),
            ))

    def _show_saved(self) -> None:
        """Replace footer with Saved ✓ + Log Another / Done buttons."""
        self._err.config(text="✓ Saved!", fg="#16A34A")
        self._log_btn.config(text="Log Time")

        # clear footer and replace buttons
        for w in self._foot.winfo_children():
            w.destroy()
        _flat_btn(self._foot, "Done",        self.destroy,      primary=False).pack(side="right", padx=(8, 0))
        _flat_btn(self._foot, "Log Another", self._reset_form,  primary=True ).pack(side="right")

    def _reset_form(self) -> None:
        """Clear the form for another entry without closing the window."""
        self._proj_var.set("")
        self._act_var.set("")
        self._act_cb.config(values=[])
        self._comment.delete("1.0", "end")
        self._dur.set("60")
        self._err.config(text="", fg="#EF4444")

        # restore original footer buttons
        for w in self._foot.winfo_children():
            w.destroy()
        self._log_btn = _flat_btn(self._foot, "Log Time", self._submit)
        self._log_btn.pack(side="right", padx=(8, 0))
        _flat_btn(self._foot, "Skip", self._skip, primary=False).pack(side="right")

        self._comment.focus_set()

    def _skip(self) -> None:
        self.destroy()

    def destroy(self) -> None:
        global _activity_popup_open
        _activity_popup_open = False
        super().destroy()


# ─── Daily Note Popup ─────────────────────────────────────────────────────────

class DailyNotePopup(tk.Toplevel):
    W, H = 460, 480

    def __init__(self, master: tk.Tk, date_str: str) -> None:
        global _daily_note_popup_open
        _daily_note_popup_open = True
        super().__init__(master)

        self.date_str = date_str
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg=BRD)
        self.withdraw()                     # hide while building

        self._projects: list[dict]         = []
        self._fields:   dict[int, dict]    = {}
        self._dx = self._dy = 0

        self._build_shell()
        self.update_idletasks()
        _pos(self, self.W, self.H)
        self.deiconify()
        self.attributes("-alpha", 0.99)     # trigger DWM compositing
        self.update()
        self._load_projects()
        self.lift()
        self.focus_force()
        self.bell()
        self.after(100, self.grab_set)

    # ── layout ────────────────────────────────────────────────────────────────

    def _build_shell(self) -> None:
        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="both", expand=True, padx=1, pady=1)

        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(outer, bg=N_HDR)
        hdr.pack(fill="x")

        tk.Frame(hdr, bg=N_HDR, height=10).pack(fill="x")   # top spacer
        app_lbl = tk.Label(hdr, text="Project Buddy",
                           bg=N_HDR, fg="#A7F3D0", font=FS, padx=14, pady=0)
        app_lbl.pack(anchor="w")

        tit_lbl = tk.Label(hdr, text=f"📓  Lab Notes — {self.date_str}",
                           bg=N_HDR, fg="white", font=FH, padx=14, pady=3)
        tit_lbl.pack(anchor="w")

        sub_lbl = tk.Label(hdr, text="Record what you did, blockers, and next steps",
                           bg=N_HDR, fg="#6EE7B7", font=FS, padx=14, pady=0)
        sub_lbl.pack(anchor="w")
        tk.Frame(hdr, bg=N_HDR, height=10).pack(fill="x")   # bottom spacer

        for w in (hdr, app_lbl, tit_lbl, sub_lbl):
            w.bind("<ButtonPress-1>", self._ds)
            w.bind("<B1-Motion>",     self._dm)

        close = tk.Label(hdr, text="×", bg=N_HDR, fg="white",
                         font=("Segoe UI", 15, "bold"), cursor="hand2",
                         padx=10, pady=6)
        close.place(relx=1.0, y=6, anchor="ne", x=-4)
        close.bind("<Button-1>", lambda e: self._skip())

        # ── Scrollable body ───────────────────────────────────────────────────
        mid = tk.Frame(outer, bg=BG)
        mid.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(mid, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(mid, orient="vertical", command=self._canvas.yview)
        self._sf = tk.Frame(self._canvas, bg=BG, padx=14, pady=8)
        self._sf.bind(
            "<Configure>",
            lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas.create_window((0, 0), window=self._sf, anchor="nw")
        self._canvas.configure(yscrollcommand=sb.set)
        self._canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self._canvas.bind_all(
            "<MouseWheel>",
            lambda e: self._canvas.yview_scroll(-1 * (e.delta // 120), "units"))

        # ── Footer ────────────────────────────────────────────────────────────
        _sep(outer)
        foot = tk.Frame(outer, bg=BG_FOOT, padx=16, pady=10)
        foot.pack(fill="x")
        self._save_btn = _flat_btn(foot, "Save Notes", self._submit)
        self._save_btn.pack(side="right", padx=(8, 0))
        _flat_btn(foot, "Skip", self._skip, primary=False).pack(side="right")

    # ── drag ──────────────────────────────────────────────────────────────────

    def _ds(self, e) -> None:
        self._dx = e.x_root - self.winfo_x()
        self._dy = e.y_root - self.winfo_y()

    def _dm(self, e) -> None:
        self.geometry(f"+{e.x_root - self._dx}+{e.y_root - self._dy}")

    # ── data ──────────────────────────────────────────────────────────────────

    def _load_projects(self) -> None:
        def _fetch():
            d = _get("/projects?status=Active")
            projects = d.get("projects", [])
            self.after(0, lambda: self._build_sections(projects))
        threading.Thread(target=_fetch, daemon=True).start()

    def _build_sections(self, projects: list[dict]) -> None:
        self._projects = projects
        if not projects:
            tk.Label(self._sf, text="No active projects found.",
                     fg=LBL_C, bg=BG, font=F).pack(pady=20)
            return

        for proj in projects:
            color  = proj.get("color_tag") or A_HDR
            fields: dict[str, tk.Text] = {}

            # project title row
            ph = tk.Frame(self._sf, bg=BG)
            ph.pack(fill="x", pady=(12, 4))
            dot = tk.Canvas(ph, width=10, height=10, bg=BG, highlightthickness=0)
            dot.create_oval(1, 1, 9, 9, fill=color, outline="")
            dot.pack(side="left")
            tk.Label(ph, text=f"  {proj['name']}", bg=BG, font=FB).pack(side="left")

            tk.Frame(self._sf, bg=BRD, height=1).pack(fill="x", pady=(0, 6))

            for key, label in [
                ("what_i_did", "What did you do today?"),
                ("blockers",   "Blockers / issues"),
                ("next_steps", "Next steps for tomorrow"),
            ]:
                tk.Label(self._sf, text=label, bg=BG,
                         fg=LBL_C, font=FS).pack(anchor="w", pady=(2, 1))
                t = _textbox(self._sf, height=2)
                t.pack(fill="x", pady=(0, 4))
                fields[key] = t

            self._fields[proj["id"]] = fields

    # ── submit ────────────────────────────────────────────────────────────────

    def _submit(self) -> None:
        self._save_btn.config(text="Saving…")
        threading.Thread(target=self._do_save, daemon=True).start()

    def _do_save(self) -> None:
        for pid, fields in self._fields.items():
            what  = fields["what_i_did"].get("1.0", "end").strip()
            blks  = fields["blockers"].get("1.0", "end").strip()
            nxt   = fields["next_steps"].get("1.0", "end").strip()
            if what or blks or nxt:
                _post("/project-notes", {
                    "project_id": pid,
                    "date":       self.date_str,
                    "what_i_did": what,
                    "blockers":   blks,
                    "next_steps": nxt,
                })
        self.after(0, self.destroy)

    def _skip(self) -> None:
        self.destroy()

    def destroy(self) -> None:
        global _daily_note_popup_open
        _daily_note_popup_open = False
        super().destroy()


# ─── Tray icon ────────────────────────────────────────────────────────────────

def _make_icon() -> Image.Image:
    img  = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([2, 2, 62, 62], fill="#2563EB")
    # stylised "P" dots
    for x0, y0, x1, y1 in [
        (16, 14, 28, 26), (16, 28, 28, 40), (16, 42, 28, 54),
        (30, 14, 42, 26), (30, 28, 42, 40),
    ]:
        draw.ellipse([x0, y0, x1, y1], fill="white")
    return img

def _open_app(*_) -> None:
    webbrowser.open(APP_URL)

# ─── WebSocket listener ───────────────────────────────────────────────────────

def _ws_listener() -> None:
    def on_message(_ws, raw: str) -> None:
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            return
        if msg.get("type") != "notification":
            return
        action = msg.get("action", "")
        if action == "SHOW_ACTIVITY_POPUP":
            _popup_queue.put(("activity", {}))
        elif action == "SHOW_DAILY_NOTE_PROMPT":
            d = (msg.get("data") or {}).get("date") or date.today().isoformat()
            _popup_queue.put(("daily_note", {"date": d}))

    while True:
        try:
            _websocket.WebSocketApp(
                WS_URL,
                on_message=on_message,
                on_error=lambda _ws, _err: None,
            ).run_forever()
        except Exception:
            pass
        time.sleep(5)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    root = tk.Tk()
    root.withdraw()     # invisible root — just owns the popup windows

    # use Windows Vista theme for nicer ttk Combobox
    style = ttk.Style(root)
    try:
        style.theme_use("vista")
    except Exception:
        pass

    icon = pystray.Icon(
        name  = "project_buddy",
        icon  = _make_icon(),
        title = "Project Buddy",
        menu  = pystray.Menu(
            pystray.MenuItem("Open Project Buddy", _open_app, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", lambda ic, _: (ic.stop(), root.quit())),
        ),
    )
    icon.run_detached()

    threading.Thread(target=_ws_listener, daemon=True, name="ws-listener").start()

    def poll() -> None:
        global _activity_popup_open, _daily_note_popup_open
        try:
            while True:
                kind, data = _popup_queue.get_nowait()
                print(f"[poll] got: {kind}", flush=True)
                if kind == "activity" and not _activity_popup_open:
                    try:
                        ActivityPopup(root)
                        print("[poll] ActivityPopup created OK", flush=True)
                    except Exception as exc:
                        import traceback
                        print(f"[poll] ActivityPopup ERROR: {exc}", flush=True)
                        traceback.print_exc()
                        _activity_popup_open = False
                elif kind == "daily_note" and not _daily_note_popup_open:
                    try:
                        DailyNotePopup(root, data.get("date", date.today().isoformat()))
                    except Exception as exc:
                        import traceback
                        print(f"[poll] DailyNotePopup ERROR: {exc}", flush=True)
                        traceback.print_exc()
                        _daily_note_popup_open = False
        except queue.Empty:
            pass
        root.after(300, poll)

    root.after(300, poll)
    root.after(800, _open_app)
    root.mainloop()
    icon.stop()


if __name__ == "__main__":
    main()
