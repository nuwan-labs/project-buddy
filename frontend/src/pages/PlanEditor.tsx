import { useState, useEffect } from "react"
import { useParams, useNavigate, Link } from "react-router-dom"
import Layout from "@/components/Layout"
import { plansApi, projectsApi, activitiesApi, sprintActivitiesApi } from "@/services/api"
import type { PlanStatus, Project, Activity, SprintActivity } from "@/types"
import {
  PLAN_STATUSES,
  COLOR_PALETTE,
} from "@/utils/constants"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { toast } from "@/components/Notifications"
import { ChevronDown, ChevronRight, Plus, Check } from "lucide-react"

// ─── Local form types ──────────────────────────────────────────────────────────

interface PlanForm {
  name: string
  description: string
  start_date: string
  end_date: string
  status: PlanStatus
}

const BLANK_PLAN: PlanForm = {
  name: "", description: "", start_date: "", end_date: "", status: "Active",
}

// ─── Styled select ─────────────────────────────────────────────────────────────

const selectCls =
  "flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring mt-1"

// ─── Color swatch picker ───────────────────────────────────────────────────────

function ColorPicker({ value, onChange }: { value: string; onChange: (c: string) => void }) {
  return (
    <div className="flex gap-1 flex-wrap mt-1">
      {COLOR_PALETTE.map(c => (
        <button
          key={c}
          type="button"
          onClick={() => onChange(c)}
          style={{ backgroundColor: c }}
          className={`h-6 w-6 rounded-full border-2 transition-transform ${
            value === c ? "border-gray-800 scale-125" : "border-transparent hover:border-gray-400"
          }`}
        />
      ))}
    </div>
  )
}

// ─── Main component ────────────────────────────────────────────────────────────

export default function PlanEditor() {
  const { id }   = useParams<{ id: string }>()
  const navigate = useNavigate()
  const isNew    = !id
  const planId   = id ? parseInt(id) : null

  // Plan form
  const [form, setForm]           = useState<PlanForm>(BLANK_PLAN)
  const [saving, setSaving]       = useState(false)
  const [loadingPlan, setLoadingPlan] = useState(!isNew)

  // Sprint activity selection (edit mode only)
  const [allProjects, setAllProjects]           = useState<Project[]>([])
  const [expandedProjId, setExpandedProjId]     = useState<number | null>(null)
  const [activityCache, setActivityCache]       = useState<Record<number, Activity[]>>({})
  const [sprintActivities, setSprintActivities] = useState<SprintActivity[]>([])
  const [togglingId, setTogglingId]             = useState<number | null>(null)

  // Add project inline
  const [showAddProject, setShowAddProject] = useState(false)
  const [newProjName, setNewProjName]       = useState("")
  const [newProjColor, setNewProjColor]     = useState(COLOR_PALETTE[0])
  const [addingProject, setAddingProject]   = useState(false)

  // Load plan for edit mode
  useEffect(() => {
    if (!planId) return
    void plansApi.get(planId)
      .then(({ data: res }) => {
        const p = res.data
        setForm({ name: p.name, description: p.description ?? "", start_date: p.start_date, end_date: p.end_date, status: p.status })
        setSprintActivities(p.sprint_activities ?? [])
      })
      .catch(() => toast({ title: "Failed to load plan.", variant: "destructive" }))
      .finally(() => setLoadingPlan(false))
  }, [planId])

  // Load all projects for sprint activity selection
  useEffect(() => {
    if (!planId) return
    void projectsApi.list()
      .then(({ data: res }) => setAllProjects(res.data.projects))
      .catch(() => toast({ title: "Failed to load projects.", variant: "destructive" }))
  }, [planId])

  // Lazy-load activities for expanded project
  useEffect(() => {
    if (expandedProjId == null || activityCache[expandedProjId] !== undefined) return
    void activitiesApi.list(expandedProjId)
      .then(({ data: res }) =>
        setActivityCache(c => ({ ...c, [expandedProjId]: res.data.activities }))
      )
      .catch(() => toast({ title: "Failed to load activities.", variant: "destructive" }))
  }, [expandedProjId, activityCache])

  // ─── Sprint activity toggle ─────────────────────────────────────────────────

  function isInSprint(activityId: number): boolean {
    return sprintActivities.some(sa => sa.activity_id === activityId)
  }

  async function toggleSprintActivity(activityId: number) {
    if (!planId) return
    setTogglingId(activityId)
    try {
      if (isInSprint(activityId)) {
        await sprintActivitiesApi.remove(planId, activityId)
        setSprintActivities(prev => prev.filter(sa => sa.activity_id !== activityId))
        toast({ title: "Removed from sprint." })
      } else {
        const { data: res } = await sprintActivitiesApi.add(planId, { activity_id: activityId })
        setSprintActivities(prev => [...prev, res.data])
        toast({ title: "Added to sprint." })
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Operation failed."
      toast({ title: msg, variant: "destructive" })
    } finally {
      setTogglingId(null)
    }
  }

  // ─── Add project ────────────────────────────────────────────────────────────

  async function handleAddProject() {
    if (!newProjName.trim()) return
    setAddingProject(true)
    try {
      const { data: res } = await projectsApi.create({
        name:     newProjName.trim(),
        description: "",
        goal:     "",
        color_tag: newProjColor,
        status:   "Active",
      })
      setAllProjects(p => [...p, res.data])
      setNewProjName("")
      setNewProjColor(COLOR_PALETTE[0])
      setShowAddProject(false)
      toast({ title: "Project created." })
    } catch {
      toast({ title: "Failed to create project.", variant: "destructive" })
    } finally {
      setAddingProject(false)
    }
  }

  // ─── Plan handlers ──────────────────────────────────────────────────────────

  async function handleSavePlan(e: React.FormEvent) {
    e.preventDefault()
    if (!form.name.trim()) {
      toast({ title: "Name is required.", variant: "destructive" }); return
    }
    if (!form.start_date || !form.end_date) {
      toast({ title: "Both dates are required.", variant: "destructive" }); return
    }
    if (form.start_date >= form.end_date) {
      toast({ title: "End date must be after start date.", variant: "destructive" }); return
    }
    setSaving(true)
    try {
      if (isNew) {
        await plansApi.create(form)
        toast({ title: "Plan created." })
      } else if (planId) {
        await plansApi.update(planId, form)
        toast({ title: "Plan updated." })
      }
      navigate("/plans")
    } catch {
      toast({ title: "Save failed.", variant: "destructive" })
    } finally {
      setSaving(false)
    }
  }

  // ─── Render ────────────────────────────────────────────────────────────────

  if (loadingPlan) {
    return <Layout><div className="p-6 text-sm text-muted-foreground">Loading…</div></Layout>
  }

  return (
    <Layout>
      <div className="p-6 max-w-3xl mx-auto space-y-8">

        {/* Breadcrumb */}
        <p className="text-sm text-muted-foreground">
          <Link to="/plans" className="hover:underline">Plans</Link>
          {" / "}
          <span>{isNew ? "New Plan" : "Edit Plan"}</span>
        </p>

        {/* ─── Plan form ─────────────────────────────────────────────────── */}
        <section>
          <h1 className="text-xl font-bold mb-4">{isNew ? "Create Plan" : "Edit Plan"}</h1>
          <form onSubmit={handleSavePlan} className="space-y-4">
            <div>
              <Label htmlFor="name">Name *</Label>
              <Input
                id="name"
                value={form.name}
                onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                placeholder="e.g. Sprint 1 — Feb 2026"
                required
              />
            </div>
            <div>
              <Label htmlFor="desc">Description</Label>
              <Textarea
                id="desc"
                rows={2}
                value={form.description}
                onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                placeholder="Optional notes about this sprint"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="start">Start Date *</Label>
                <Input
                  id="start"
                  type="date"
                  value={form.start_date}
                  onChange={e => setForm(f => ({ ...f, start_date: e.target.value }))}
                  required
                />
              </div>
              <div>
                <Label htmlFor="end">End Date *</Label>
                <Input
                  id="end"
                  type="date"
                  value={form.end_date}
                  onChange={e => setForm(f => ({ ...f, end_date: e.target.value }))}
                  required
                />
              </div>
            </div>
            {!isNew && (
              <div>
                <Label htmlFor="pstatus">Status</Label>
                <select
                  id="pstatus"
                  value={form.status}
                  onChange={e => setForm(f => ({ ...f, status: e.target.value as PlanStatus }))}
                  className={selectCls}
                >
                  {PLAN_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
            )}
            <div className="flex gap-3 pt-1">
              <Button type="submit" disabled={saving}>
                {saving ? "Saving…" : "Save Plan"}
              </Button>
              <Button type="button" variant="outline" onClick={() => navigate("/plans")}>
                Cancel
              </Button>
            </div>
          </form>
        </section>

        {/* ─── Sprint Activities section (edit mode only) ─────────────────── */}
        {!isNew && (
          <section className="border-t pt-6">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h2 className="text-base font-semibold">
                  Sprint Activities ({sprintActivities.length})
                </h2>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Select activities from your projects to focus on this sprint.
                </p>
              </div>
              <Button
                size="sm"
                variant="outline"
                onClick={() => { setShowAddProject(v => !v) }}
              >
                <Plus className="h-4 w-4 mr-1" /> New Project
              </Button>
            </div>

            {/* Quick create project form */}
            {showAddProject && (
              <div className="border rounded-lg p-4 mb-4 bg-blue-50/40 space-y-3">
                <p className="text-sm font-medium">New Project</p>
                <Input
                  placeholder="Project name *"
                  value={newProjName}
                  onChange={e => setNewProjName(e.target.value)}
                />
                <div>
                  <Label className="text-xs text-muted-foreground">Color tag</Label>
                  <ColorPicker value={newProjColor} onChange={setNewProjColor} />
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    disabled={addingProject || !newProjName.trim()}
                    onClick={() => void handleAddProject()}
                  >
                    {addingProject ? "Creating…" : "Create Project"}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => { setShowAddProject(false); setNewProjName("") }}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            )}

            {/* Project list with expandable activities */}
            {allProjects.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-6">
                No projects yet. Create one above.
              </p>
            ) : (
              <div className="space-y-2">
                {allProjects.map(project => {
                  const isExpanded = expandedProjId === project.id
                  const acts = activityCache[project.id] ?? []
                  const inSprintCount = acts.filter(a => isInSprint(a.id)).length
                  return (
                    <div key={project.id} className="border rounded-lg overflow-hidden">
                      {/* Project row */}
                      <div
                        className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-gray-50"
                        onClick={() => setExpandedProjId(isExpanded ? null : project.id)}
                      >
                        <div
                          className="h-4 w-4 rounded-full flex-shrink-0"
                          style={{ backgroundColor: project.color_tag ?? "#4472C4" }}
                        />
                        <span className="flex-1 font-medium text-sm truncate">{project.name}</span>
                        {inSprintCount > 0 && (
                          <span className="text-xs text-blue-600 font-medium">
                            {inSprintCount} in sprint
                          </span>
                        )}
                        {isExpanded
                          ? <ChevronDown className="h-4 w-4 text-muted-foreground" />
                          : <ChevronRight className="h-4 w-4 text-muted-foreground" />}
                      </div>

                      {/* Activities panel */}
                      {isExpanded && (
                        <div className="border-t px-4 pb-4 pt-3 bg-gray-50">
                          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
                            Activities — check to add to sprint
                          </p>
                          {acts.length === 0 ? (
                            <p className="text-xs text-muted-foreground py-2">
                              No activities in this project.
                            </p>
                          ) : (
                            <div className="space-y-1.5">
                              {acts.map(act => {
                                const checked  = isInSprint(act.id)
                                const toggling = togglingId === act.id
                                return (
                                  <label
                                    key={act.id}
                                    className="flex items-center gap-3 p-2 rounded border bg-white hover:bg-blue-50/30 cursor-pointer"
                                  >
                                    <input
                                      type="checkbox"
                                      checked={checked}
                                      disabled={toggling}
                                      onChange={() => void toggleSprintActivity(act.id)}
                                      className="h-4 w-4 rounded border-gray-300 text-blue-600"
                                    />
                                    <span className="flex-1 text-sm">{act.name}</span>
                                    <span className="text-xs text-muted-foreground">{act.status}</span>
                                    <span className="text-xs text-muted-foreground">{act.estimated_hours}h est</span>
                                    {checked && (
                                      <Check className="h-3.5 w-3.5 text-blue-600" />
                                    )}
                                  </label>
                                )
                              })}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </section>
        )}
      </div>
    </Layout>
  )
}
