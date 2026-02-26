import { useState, useEffect } from "react"
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from "@/components/ui/dialog"
import { Button }   from "@/components/ui/button"
import { Label }    from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { useApp }   from "@/context/AppContext"
import { projectsApi, dailyNotesApi } from "@/services/api"
import { useToast } from "@/components/ui/use-toast"
import type { Project } from "@/types"

// ─── Per-project note form state ──────────────────────────────────────────────

interface NoteEntry {
  projectId:  number
  projectName: string
  whatIDid:   string
  blockers:   string
  nextSteps:  string
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function DailyNotePopup() {
  const { state, closeDailyNotePopup } = useApp()
  const { toast } = useToast()

  const [notes, setNotes]         = useState<NoteEntry[]>([])
  const [loading, setLoading]     = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const open = state.showDailyNotePopup
  const date = state.dailyNoteDate ?? new Date().toISOString().slice(0, 10)

  // Load active projects when popup opens
  useEffect(() => {
    if (!open) {
      setNotes([])
      return
    }

    setLoading(true)
    projectsApi
      .list({ status: "Active" })
      .then(({ data }) => {
        const initial: NoteEntry[] = data.data.projects.map((p: Project) => ({
          projectId:   p.id,
          projectName: p.name,
          whatIDid:    "",
          blockers:    "",
          nextSteps:   "",
        }))
        setNotes(initial)
      })
      .catch(() => setNotes([]))
      .finally(() => setLoading(false))
  }, [open])

  function updateNote(projectId: number, field: keyof Omit<NoteEntry, "projectId" | "projectName">, value: string) {
    setNotes((prev) => prev.map((n) =>
      n.projectId === projectId ? { ...n, [field]: value } : n
    ))
  }

  async function handleSubmit() {
    const filled = notes.filter((n) => n.whatIDid.trim() || n.blockers.trim() || n.nextSteps.trim())
    if (filled.length === 0) {
      closeDailyNotePopup()
      return
    }

    setSubmitting(true)
    try {
      await Promise.all(
        filled.map((n) =>
          dailyNotesApi.upsert({
            project_id: n.projectId,
            date,
            what_i_did: n.whatIDid.trim(),
            blockers:   n.blockers.trim(),
            next_steps: n.nextSteps.trim(),
            plan_id:    state.activePlan?.id ?? null,
          })
        )
      )
      toast({ title: `Daily notes saved for ${filled.length} project${filled.length > 1 ? "s" : ""}.` })
      closeDailyNotePopup()
    } catch {
      toast({ title: "Failed to save notes", variant: "destructive" })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) closeDailyNotePopup() }}>
      <DialogContent className="sm:max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>End-of-Day Lab Notes — {date}</DialogTitle>
          <p className="text-sm text-muted-foreground mt-1">
            Record what you did, any blockers, and next steps for each project.
          </p>
        </DialogHeader>

        {loading ? (
          <p className="text-sm text-muted-foreground py-4 text-center">Loading projects…</p>
        ) : notes.length === 0 ? (
          <p className="text-sm text-muted-foreground py-4 text-center">
            No active projects found.
          </p>
        ) : (
          <div className="space-y-6 py-2">
            {notes.map((n) => (
              <div key={n.projectId} className="border rounded-lg p-4 space-y-3">
                <h3 className="font-semibold text-sm">{n.projectName}</h3>

                <div className="space-y-1.5">
                  <Label className="text-xs text-muted-foreground">What did I do?</Label>
                  <Textarea
                    rows={2}
                    placeholder="Describe your progress today…"
                    value={n.whatIDid}
                    onChange={(e) => updateNote(n.projectId, "whatIDid", e.target.value)}
                  />
                </div>

                <div className="space-y-1.5">
                  <Label className="text-xs text-muted-foreground">Blockers / Issues</Label>
                  <Textarea
                    rows={2}
                    placeholder="Any blockers or problems encountered?"
                    value={n.blockers}
                    onChange={(e) => updateNote(n.projectId, "blockers", e.target.value)}
                  />
                </div>

                <div className="space-y-1.5">
                  <Label className="text-xs text-muted-foreground">Next Steps</Label>
                  <Textarea
                    rows={2}
                    placeholder="What will you do tomorrow?"
                    value={n.nextSteps}
                    onChange={(e) => updateNote(n.projectId, "nextSteps", e.target.value)}
                  />
                </div>
              </div>
            ))}
          </div>
        )}

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={closeDailyNotePopup}>
            Skip
          </Button>
          <Button
            disabled={submitting || loading}
            onClick={() => void handleSubmit()}
          >
            {submitting ? "Saving…" : "Save Notes"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
