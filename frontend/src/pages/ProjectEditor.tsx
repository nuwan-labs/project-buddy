import { useState, useEffect } from "react"
import { useParams, useNavigate, Link } from "react-router-dom"
import Layout from "@/components/Layout"
import { projectsApi } from "@/services/api"
import type { ProjectStatus } from "@/types"
import { PROJECT_STATUSES, COLOR_PALETTE } from "@/utils/constants"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { toast } from "@/components/Notifications"

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

// ─── Form type ────────────────────────────────────────────────────────────────

interface ProjectForm {
  name: string
  description: string
  goal: string
  color_tag: string
  status: ProjectStatus
}

const BLANK: ProjectForm = {
  name: "", description: "", goal: "", color_tag: COLOR_PALETTE[0], status: "Active",
}

// ─── Main component ────────────────────────────────────────────────────────────

export default function ProjectEditor() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate      = useNavigate()
  const isNew         = !projectId
  const prId          = projectId ? parseInt(projectId) : null

  const [form, setForm]       = useState<ProjectForm>(BLANK)
  const [loading, setLoading] = useState(!isNew)
  const [saving, setSaving]   = useState(false)

  useEffect(() => {
    if (!prId) return
    void projectsApi.get(prId)
      .then(({ data: res }) => {
        const p = res.data
        setForm({
          name:        p.name,
          description: p.description ?? "",
          goal:        p.goal ?? "",
          color_tag:   p.color_tag ?? COLOR_PALETTE[0],
          status:      p.status,
        })
      })
      .catch(() => toast({ title: "Failed to load project.", variant: "destructive" }))
      .finally(() => setLoading(false))
  }, [prId])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!form.name.trim()) {
      toast({ title: "Name is required.", variant: "destructive" }); return
    }
    setSaving(true)
    try {
      if (isNew) {
        const { data: res } = await projectsApi.create({
          name:        form.name.trim(),
          description: form.description,
          goal:        form.goal,
          color_tag:   form.color_tag,
          status:      form.status,
        })
        toast({ title: "Project created." })
        navigate(`/projects/${res.data.id}`)
      } else if (prId) {
        await projectsApi.update(prId, {
          name:        form.name.trim(),
          description: form.description,
          goal:        form.goal,
          color_tag:   form.color_tag,
          status:      form.status,
        })
        toast({ title: "Project updated." })
        navigate(`/projects/${prId}`)
      }
    } catch {
      toast({ title: "Save failed.", variant: "destructive" })
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <Layout><div className="p-6 text-sm text-muted-foreground">Loading…</div></Layout>
  }

  return (
    <Layout>
      <div className="p-6 max-w-xl mx-auto">

        {/* Breadcrumb */}
        <p className="text-sm text-muted-foreground mb-6">
          <Link to="/projects" className="hover:underline">Projects</Link>
          {" / "}
          <span>{isNew ? "New Project" : "Edit Project"}</span>
        </p>

        <h1 className="text-xl font-bold mb-6">
          {isNew ? "Create Project" : "Edit Project"}
        </h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="name">Name *</Label>
            <Input
              id="name"
              value={form.name}
              onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
              placeholder="e.g. CRISPR Off-target Analysis"
              required
            />
          </div>

          <div>
            <Label htmlFor="goal">Goal</Label>
            <Input
              id="goal"
              value={form.goal}
              onChange={e => setForm(f => ({ ...f, goal: e.target.value }))}
              placeholder="One-line goal or hypothesis"
            />
          </div>

          <div>
            <Label htmlFor="desc">Description</Label>
            <Textarea
              id="desc"
              rows={3}
              value={form.description}
              onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
              placeholder="Background, scope, notes…"
            />
          </div>

          <div>
            <Label>Color tag</Label>
            <ColorPicker value={form.color_tag} onChange={c => setForm(f => ({ ...f, color_tag: c }))} />
          </div>

          {!isNew && (
            <div>
              <Label htmlFor="status">Status</Label>
              <select
                id="status"
                value={form.status}
                onChange={e => setForm(f => ({ ...f, status: e.target.value as ProjectStatus }))}
                className={selectCls}
              >
                {PROJECT_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <Button type="submit" disabled={saving}>
              {saving ? "Saving…" : isNew ? "Create Project" : "Save Changes"}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate(isNew ? "/projects" : `/projects/${prId}`)}
            >
              Cancel
            </Button>
          </div>
        </form>
      </div>
    </Layout>
  )
}
