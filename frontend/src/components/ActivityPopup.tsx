import { useState, useEffect } from "react"
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from "@/components/ui/dialog"
import { Button }   from "@/components/ui/button"
import { Label }    from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Input }    from "@/components/ui/input"
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select"
import { useApp }            from "@/context/AppContext"
import { activitiesApi, logsApi, projectsApi } from "@/services/api"
import { useToast }          from "@/components/ui/use-toast"
import { nowWithOffset }     from "@/utils/formatting"
import { DEFAULT_DURATION, MAX_DURATION_MINUTES } from "@/utils/constants"
import type { Activity }     from "@/types"

// ─── Form state ───────────────────────────────────────────────────────────────

interface FormState {
  projectId:  string   // numeric id as string, or "adhoc", or ""
  adhocName:  string
  activityId: string   // numeric id as string, or "none", or ""
  comment:    string
  duration:   number
}

const EMPTY: FormState = {
  projectId:  "",
  adhocName:  "",
  activityId: "",
  comment:    "",
  duration:   DEFAULT_DURATION,
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function ActivityPopup() {
  const { state, closeActivityPopup, snoozePopup, refreshDashboard } = useApp()
  const { toast } = useToast()

  const [form, setForm]             = useState<FormState>(EMPTY)
  const [activities, setActivities] = useState<Activity[]>([])
  const [loadingActs, setLoadingActs] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  // Pre-select project when popup opens with a preselected project
  useEffect(() => {
    if (state.showActivityPopup && state.preselectedProjectId !== null) {
      setForm((f) => ({ ...f, projectId: String(state.preselectedProjectId) }))
    }
    if (!state.showActivityPopup) {
      setForm(EMPTY)
      setActivities([])
    }
  }, [state.showActivityPopup, state.preselectedProjectId])

  // Fetch activities when project selection changes
  useEffect(() => {
    const pid = form.projectId
    if (!pid || pid === "adhoc") {
      setActivities([])
      setForm((f) => ({ ...f, activityId: "" }))
      return
    }
    setLoadingActs(true)
    activitiesApi
      .list(Number(pid))
      .then(({ data }) => {
        setActivities(data.data.activities)
        setForm((f) => ({ ...f, activityId: "" }))
      })
      .catch(() => setActivities([]))
      .finally(() => setLoadingActs(false))
  }, [form.projectId])

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setForm((f) => ({ ...f, [key]: value }))

  const handleClose = () => {
    closeActivityPopup()
    setForm(EMPTY)
    setActivities([])
  }

  const handleSubmit = async () => {
    if (!form.comment.trim()) {
      toast({ title: "Comment is required", variant: "destructive" })
      return
    }
    if (form.duration < 1 || form.duration > MAX_DURATION_MINUTES) {
      toast({ title: `Duration must be 1–${MAX_DURATION_MINUTES} minutes`, variant: "destructive" })
      return
    }
    if (!state.activePlan) {
      toast({ title: "No active plan — create one first", variant: "destructive" })
      return
    }
    if (!form.projectId) {
      toast({ title: "Please select a project", variant: "destructive" })
      return
    }

    setSubmitting(true)
    try {
      let resolvedProjectId = Number(form.projectId)

      // Create ad-hoc project on the fly
      if (form.projectId === "adhoc") {
        if (!form.adhocName.trim()) {
          toast({ title: "Please enter a project name", variant: "destructive" })
          return
        }
        const { data: pr } = await projectsApi.create(state.activePlan.id, {
          name:        `Ad-hoc: ${form.adhocName.trim()}`,
          description: "",
          goal:        "",
          color_tag:   "#888888",
          status:      "In Progress",
        })
        resolvedProjectId = pr.data.id
      }

      await logsApi.create({
        biweekly_plan_id: state.activePlan.id,
        project_id:       resolvedProjectId,
        activity_id:      form.activityId && form.activityId !== "none"
          ? Number(form.activityId)
          : null,
        comment:          form.comment.trim(),
        duration_minutes: form.duration,
        timestamp:        nowWithOffset(),
      })

      toast({ title: "Activity logged!" })
      await refreshDashboard()
      handleClose()
    } catch {
      toast({ title: "Failed to log activity", variant: "destructive" })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={state.showActivityPopup} onOpenChange={(open) => { if (!open) handleClose() }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>What are you working on?</DialogTitle>
        </DialogHeader>

        <div className="grid gap-4 py-2">
          {/* Project */}
          <div className="grid gap-1.5">
            <Label htmlFor="pp-project">Project</Label>
            <Select
              value={form.projectId}
              onValueChange={(v) => set("projectId", v)}
            >
              <SelectTrigger id="pp-project">
                <SelectValue placeholder="Select a project…" />
              </SelectTrigger>
              <SelectContent>
                {state.projects.map((p) => (
                  <SelectItem key={p.id} value={String(p.id)}>
                    {p.name}
                  </SelectItem>
                ))}
                <SelectItem value="adhoc">Ad-hoc / Other…</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Ad-hoc name input */}
          {form.projectId === "adhoc" && (
            <div className="grid gap-1.5">
              <Label htmlFor="pp-adhoc">Project name</Label>
              <Input
                id="pp-adhoc"
                placeholder="e.g. Team meeting, Paper review…"
                value={form.adhocName}
                onChange={(e) => set("adhocName", e.target.value)}
              />
            </div>
          )}

          {/* Activity (only when a real project is selected) */}
          {form.projectId && form.projectId !== "adhoc" && (
            <div className="grid gap-1.5">
              <Label htmlFor="pp-activity">
                Activity{" "}
                <span className="text-muted-foreground font-normal">(optional)</span>
              </Label>
              <Select
                value={form.activityId}
                onValueChange={(v) => set("activityId", v)}
                disabled={loadingActs}
              >
                <SelectTrigger id="pp-activity">
                  <SelectValue placeholder={loadingActs ? "Loading…" : "Select an activity…"} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">— General / No specific activity —</SelectItem>
                  {activities.map((a) => (
                    <SelectItem key={a.id} value={String(a.id)}>
                      {a.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Comment */}
          <div className="grid gap-1.5">
            <Label htmlFor="pp-comment">What did you do?</Label>
            <Textarea
              id="pp-comment"
              placeholder="Describe what you worked on…"
              rows={3}
              value={form.comment}
              onChange={(e) => set("comment", e.target.value)}
            />
          </div>

          {/* Duration */}
          <div className="grid gap-1.5">
            <Label htmlFor="pp-duration">
              Duration{" "}
              <span className="text-muted-foreground font-normal">(minutes)</span>
            </Label>
            <Input
              id="pp-duration"
              type="number"
              min={1}
              max={MAX_DURATION_MINUTES}
              value={form.duration}
              onChange={(e) => set("duration", Number(e.target.value))}
            />
          </div>
        </div>

        <DialogFooter className="gap-2 flex-col sm:flex-row">
          <Button variant="ghost" size="sm" onClick={() => snoozePopup(15)} className="sm:mr-auto">
            Snooze 15 min
          </Button>
          <Button variant="outline" size="sm" onClick={handleClose}>
            Skip
          </Button>
          <Button
            size="sm"
            disabled={submitting || !form.projectId}
            onClick={() => void handleSubmit()}
          >
            {submitting ? "Saving…" : "Log Activity"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
