import { useState } from "react"
import { useParams, Link } from "react-router-dom"
import Layout from "@/components/Layout"
import ActivityList from "@/components/ActivityList"
import { activitiesApi, dailyNotesApi } from "@/services/api"
import { useProjectDetail } from "@/hooks/useProjectDetail"
import { PROJECT_STATUS_COLORS } from "@/utils/constants"
import { formatHours } from "@/utils/formatting"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { toast } from "@/components/Notifications"
import { useApp } from "@/context/AppContext"
import { Clock, Plus, ChevronUp, BookOpen, Trash2 } from "lucide-react"

export default function ProjectDetail() {
  const { projectId }          = useParams<{ projectId: string }>()
  const { openActivityPopup }  = useApp()

  const prId = projectId ? parseInt(projectId) : 0

  const { project, activities, notes, loading, loadProject, loadActivities, loadNotes } =
    useProjectDetail(prId)

  // Add activity form
  const [showAddForm, setShowAddForm] = useState(false)
  const [addingAct, setAddingAct]     = useState(false)
  const [newAct, setNewAct] = useState({
    name: "", description: "", deliverables: "", dependencies: "", estimated_hours: 1,
  })

  // Daily notes
  const [showNoteForm, setShowNoteForm] = useState(false)
  const [savingNote, setSavingNote]     = useState(false)
  const [noteForm, setNoteForm] = useState({ what_i_did: "", blockers: "", next_steps: "" })
  const todayStr = new Date().toISOString().slice(0, 10)

  async function handleAddActivity() {
    if (!newAct.name.trim()) return
    setAddingAct(true)
    try {
      await activitiesApi.create(prId, {
        name:            newAct.name,
        description:     newAct.description,
        deliverables:    newAct.deliverables,
        dependencies:    newAct.dependencies,
        estimated_hours: newAct.estimated_hours,
      })
      setNewAct({ name: "", description: "", deliverables: "", dependencies: "", estimated_hours: 1 })
      setShowAddForm(false)
      await loadActivities()
      await loadProject()
      toast({ title: "Activity added." })
    } catch {
      toast({ title: "Failed to add activity.", variant: "destructive" })
    } finally {
      setAddingAct(false)
    }
  }

  async function handleSaveNote() {
    if (!noteForm.what_i_did.trim() && !noteForm.blockers.trim() && !noteForm.next_steps.trim()) {
      toast({ title: "Please fill at least one field.", variant: "destructive" })
      return
    }
    setSavingNote(true)
    try {
      await dailyNotesApi.upsert({
        project_id: prId,
        date:       todayStr,
        what_i_did: noteForm.what_i_did.trim(),
        blockers:   noteForm.blockers.trim(),
        next_steps: noteForm.next_steps.trim(),
      })
      setNoteForm({ what_i_did: "", blockers: "", next_steps: "" })
      setShowNoteForm(false)
      await loadNotes()
      toast({ title: "Daily note saved." })
    } catch {
      toast({ title: "Failed to save note.", variant: "destructive" })
    } finally {
      setSavingNote(false)
    }
  }

  async function handleDeleteNote(noteId: number) {
    if (!confirm("Delete this daily note?")) return
    try {
      await dailyNotesApi.delete(noteId)
      await loadNotes()
      toast({ title: "Note deleted." })
    } catch {
      toast({ title: "Failed to delete note.", variant: "destructive" })
    }
  }

  if (loading) {
    return <Layout><div className="p-6 text-sm text-muted-foreground">Loading…</div></Layout>
  }

  if (!project) {
    return (
      <Layout>
        <div className="p-6 text-center mt-16 text-muted-foreground">
          <p>Project not found.</p>
          <Link to="/" className="text-blue-600 text-sm mt-2 inline-block hover:underline">
            ← Back to Dashboard
          </Link>
        </div>
      </Layout>
    )
  }

  const completedCount = activities.filter(a => a.status === "Complete").length
  const totalCount     = activities.length

  return (
    <Layout>
      <div className="p-6 max-w-3xl mx-auto space-y-6">

        {/* Breadcrumb */}
        <p className="text-sm text-muted-foreground">
          <Link to="/" className="hover:underline">Dashboard</Link>
          {" / "}
          <span>{project.name}</span>
        </p>

        {/* Project header */}
        <div className="border rounded-xl overflow-hidden">
          <div
            className="h-2"
            style={{ backgroundColor: project.color_tag ?? "#4472C4" }}
          />
          <div className="p-5">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <h1 className="text-xl font-bold truncate">{project.name}</h1>
                {project.goal && (
                  <p className="text-sm text-muted-foreground mt-1">{project.goal}</p>
                )}
                {project.description && (
                  <p className="text-xs text-muted-foreground mt-1">{project.description}</p>
                )}
              </div>
              <div className="flex flex-col items-end gap-2 shrink-0">
                <Badge className={PROJECT_STATUS_COLORS[project.status]}>{project.status}</Badge>
                <Button
                  size="sm"
                  onClick={() => openActivityPopup(project.id)}
                >
                  <Clock className="h-4 w-4 mr-1.5" /> Log Time
                </Button>
              </div>
            </div>

            {/* Stats row */}
            <div className="flex gap-6 mt-4 text-sm">
              <div>
                <span className="text-muted-foreground">Activities </span>
                <span className="font-medium">{completedCount}/{totalCount}</span>
              </div>
              {project.completion_percent != null && (
                <div>
                  <span className="text-muted-foreground">Complete </span>
                  <span className="font-medium">{Math.round(project.completion_percent)}%</span>
                </div>
              )}
              {project.hours_logged != null && (
                <div>
                  <span className="text-muted-foreground">Logged </span>
                  <span className="font-medium">{formatHours(project.hours_logged)}</span>
                </div>
              )}
            </div>

            {/* Progress bar */}
            {totalCount > 0 && (
              <div className="mt-3">
                <div className="h-1.5 rounded-full bg-secondary overflow-hidden">
                  <div
                    className="h-full bg-green-500 rounded-full transition-all"
                    style={{ width: `${Math.round((completedCount / totalCount) * 100)}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Activities section */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-base font-semibold">Activities ({totalCount})</h2>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setShowAddForm(v => !v)}
            >
              {showAddForm
                ? <><ChevronUp className="h-4 w-4 mr-1" /> Close</>
                : <><Plus className="h-4 w-4 mr-1" /> Add Activity</>}
            </Button>
          </div>

          {/* Add activity form */}
          {showAddForm && (
            <div className="border rounded-lg p-4 mb-4 bg-blue-50/40 space-y-3">
              <p className="text-sm font-medium">New Activity</p>
              <Input
                placeholder="Activity name *"
                value={newAct.name}
                onChange={e => setNewAct(a => ({ ...a, name: e.target.value }))}
              />
              <Textarea
                rows={2}
                placeholder="Description (optional)"
                value={newAct.description}
                onChange={e => setNewAct(a => ({ ...a, description: e.target.value }))}
              />
              <Input
                placeholder="Deliverables"
                value={newAct.deliverables}
                onChange={e => setNewAct(a => ({ ...a, deliverables: e.target.value }))}
              />
              <div className="flex items-center gap-3">
                <Label className="text-xs shrink-0">Estimated hours</Label>
                <Input
                  type="number"
                  min="0.5"
                  step="0.5"
                  value={newAct.estimated_hours}
                  onChange={e => setNewAct(a => ({ ...a, estimated_hours: parseFloat(e.target.value) || 1 }))}
                  className="w-24"
                />
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  disabled={addingAct || !newAct.name.trim()}
                  onClick={() => void handleAddActivity()}
                >
                  {addingAct ? "Adding…" : "Add Activity"}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setShowAddForm(false)
                    setNewAct({ name: "", description: "", deliverables: "", dependencies: "", estimated_hours: 1 })
                  }}
                >
                  Cancel
                </Button>
              </div>
            </div>
          )}

          <ActivityList
            activities={activities}
            onRefresh={() => {
              void loadActivities()
              void loadProject()
            }}
          />
        </section>

        {/* Daily Notes section */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-base font-semibold flex items-center gap-2">
              <BookOpen className="h-4 w-4" />
              Lab Notes ({notes.length})
            </h2>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setShowNoteForm(v => !v)}
            >
              {showNoteForm
                ? <><ChevronUp className="h-4 w-4 mr-1" /> Close</>
                : <><Plus className="h-4 w-4 mr-1" /> Today's Note</>}
            </Button>
          </div>

          {/* Add note form */}
          {showNoteForm && (
            <div className="border rounded-lg p-4 mb-4 bg-green-50/40 space-y-3">
              <p className="text-sm font-medium">Note for {todayStr}</p>
              <div>
                <Label className="text-xs text-muted-foreground">What did I do?</Label>
                <Textarea
                  rows={2}
                  placeholder="Describe your progress today…"
                  value={noteForm.what_i_did}
                  onChange={e => setNoteForm(n => ({ ...n, what_i_did: e.target.value }))}
                />
              </div>
              <div>
                <Label className="text-xs text-muted-foreground">Blockers</Label>
                <Textarea
                  rows={2}
                  placeholder="Any blockers or issues?"
                  value={noteForm.blockers}
                  onChange={e => setNoteForm(n => ({ ...n, blockers: e.target.value }))}
                />
              </div>
              <div>
                <Label className="text-xs text-muted-foreground">Next Steps</Label>
                <Textarea
                  rows={2}
                  placeholder="What will you do tomorrow?"
                  value={noteForm.next_steps}
                  onChange={e => setNoteForm(n => ({ ...n, next_steps: e.target.value }))}
                />
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  disabled={savingNote}
                  onClick={() => void handleSaveNote()}
                >
                  {savingNote ? "Saving…" : "Save Note"}
                </Button>
                <Button size="sm" variant="outline" onClick={() => setShowNoteForm(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          )}

          {/* Notes list */}
          {notes.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-6">
              No lab notes yet.
            </p>
          ) : (
            <div className="space-y-3">
              {notes.map(note => (
                <div key={note.id} className="border rounded-lg p-4 bg-white text-sm">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-xs text-muted-foreground">{note.date}</span>
                    <button
                      className="text-muted-foreground hover:text-red-600"
                      onClick={() => void handleDeleteNote(note.id)}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                  {note.what_i_did && (
                    <div className="mb-2">
                      <p className="text-xs font-medium text-muted-foreground mb-0.5">What I did</p>
                      <p className="text-sm">{note.what_i_did}</p>
                    </div>
                  )}
                  {note.blockers && (
                    <div className="mb-2">
                      <p className="text-xs font-medium text-amber-600 mb-0.5">Blockers</p>
                      <p className="text-sm">{note.blockers}</p>
                    </div>
                  )}
                  {note.next_steps && (
                    <div>
                      <p className="text-xs font-medium text-blue-600 mb-0.5">Next Steps</p>
                      <p className="text-sm">{note.next_steps}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </Layout>
  )
}
