import { useState } from "react"
import Layout from "@/components/Layout"
import { logsApi } from "@/services/api"
import { useActivityLogs } from "@/hooks/useActivityLogs"
import { usePlans } from "@/hooks/usePlans"
import { useProjects } from "@/hooks/useProjects"
import type { ActivityLog } from "@/types"
import { formatDateTime, formatDuration, todayISO } from "@/utils/formatting"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { toast } from "@/components/Notifications"
import { Pencil, Trash2, Clock } from "lucide-react"
import { MAX_DURATION_MINUTES } from "@/utils/constants"

export default function ActivityLogs() {
  // Filters
  const [dateFilter, setDateFilter]       = useState(todayISO())
  const [planFilter, setPlanFilter]       = useState<number | "">("")
  const [projectFilter, setProjectFilter] = useState<number | "">("")

  // Data via hooks
  const { logs, totalHours, loading, reload } = useActivityLogs({
    date:             dateFilter || undefined,
    project_id:       projectFilter || undefined,
    biweekly_plan_id: planFilter || undefined,
  })
  const { plans }    = usePlans()
  const { projects } = useProjects()

  // Edit state
  const [editingLog, setEditingLog]     = useState<ActivityLog | null>(null)
  const [editComment, setEditComment]   = useState("")
  const [editDuration, setEditDuration] = useState(60)
  const [saving, setSaving]             = useState(false)

  // Confirm delete
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null)

  function openEdit(log: ActivityLog) {
    setEditingLog(log)
    setEditComment(log.comment)
    setEditDuration(log.duration_minutes)
  }

  async function handleSaveEdit() {
    if (!editingLog) return
    if (editDuration < 1 || editDuration > MAX_DURATION_MINUTES) {
      toast({ title: `Duration must be 1–${MAX_DURATION_MINUTES} minutes.`, variant: "destructive" })
      return
    }
    setSaving(true)
    try {
      await logsApi.update(editingLog.id, {
        comment: editComment.trim() || editingLog.comment,
        duration_minutes: editDuration,
      })
      toast({ title: "Log updated." })
      setEditingLog(null)
      reload()
    } catch {
      toast({ title: "Failed to update log.", variant: "destructive" })
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(id: number) {
    try {
      await logsApi.delete(id)
      toast({ title: "Log deleted." })
      setConfirmDeleteId(null)
      reload()
    } catch {
      toast({ title: "Failed to delete log.", variant: "destructive" })
    }
  }

  return (
    <Layout>
      <div className="p-6 max-w-5xl mx-auto">
        <div className="mb-4">
          <h1 className="text-xl font-bold">Activity Logs</h1>
          <p className="text-sm text-muted-foreground">
            {logs.length} log{logs.length !== 1 ? "s" : ""}
            {totalHours > 0 && ` · ${totalHours.toFixed(2)} hrs total`}
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-3 mb-5 items-end">
          <div>
            <Label className="text-xs text-muted-foreground">Date</Label>
            <Input
              type="date"
              value={dateFilter}
              onChange={e => setDateFilter(e.target.value)}
              className="w-40"
            />
          </div>
          <div>
            <Label className="text-xs text-muted-foreground">Plan</Label>
            <select
              value={planFilter}
              onChange={e => setPlanFilter(e.target.value ? parseInt(e.target.value) : "")}
              className="flex h-9 rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring w-48"
            >
              <option value="">All plans</option>
              {plans.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>
          {projects.length > 0 && (
            <div>
              <Label className="text-xs text-muted-foreground">Project</Label>
              <select
                value={projectFilter}
                onChange={e => setProjectFilter(e.target.value ? parseInt(e.target.value) : "")}
                className="flex h-9 rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring w-48"
              >
                <option value="">All projects</option>
                {projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </div>
          )}
          <Button
            size="sm"
            variant="outline"
            onClick={() => { setDateFilter(todayISO()); setPlanFilter(""); setProjectFilter("") }}
          >
            Reset
          </Button>
        </div>

        {/* Log table */}
        {loading ? (
          <p className="text-sm text-muted-foreground py-8 text-center">Loading…</p>
        ) : logs.length === 0 ? (
          <div className="text-center py-16 text-muted-foreground">
            <Clock className="h-8 w-8 mx-auto mb-2 opacity-30" />
            <p>No logs found for the selected filters.</p>
          </div>
        ) : (
          <div className="rounded-md border overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/50">
                <tr>
                  <th className="text-left px-4 py-2.5 font-medium whitespace-nowrap">Time</th>
                  <th className="text-left px-4 py-2.5 font-medium">Project</th>
                  <th className="text-left px-4 py-2.5 font-medium">Activity</th>
                  <th className="text-left px-4 py-2.5 font-medium">Comment</th>
                  <th className="text-right px-4 py-2.5 font-medium whitespace-nowrap">Duration</th>
                  <th className="text-right px-4 py-2.5 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {logs.map(log => (
                  <tr key={log.id} className="border-t hover:bg-muted/20">
                    <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">
                      {formatDateTime(log.timestamp)}
                    </td>
                    <td className="px-4 py-3 font-medium">
                      {log.project_name ?? `#${log.project_id}`}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {log.activity_name ?? <span className="italic">—</span>}
                    </td>
                    <td className="px-4 py-3 max-w-xs">
                      <span className="line-clamp-2">{log.comment}</span>
                    </td>
                    <td className="px-4 py-3 text-right whitespace-nowrap">
                      {formatDuration(log.duration_minutes)}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-1 justify-end">
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-7 w-7 text-muted-foreground hover:text-foreground"
                          onClick={() => openEdit(log)}
                          title="Edit log"
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </Button>
                        {confirmDeleteId === log.id ? (
                          <>
                            <Button
                              size="sm"
                              variant="destructive"
                              className="h-7 px-2 text-xs"
                              onClick={() => void handleDelete(log.id)}
                            >
                              Confirm
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              className="h-7 px-2 text-xs"
                              onClick={() => setConfirmDeleteId(null)}
                            >
                              No
                            </Button>
                          </>
                        ) : (
                          <Button
                            size="icon"
                            variant="ghost"
                            className="h-7 w-7 text-muted-foreground hover:text-destructive"
                            onClick={() => setConfirmDeleteId(log.id)}
                            title="Delete log"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Footer total */}
            <div className="px-4 py-2.5 border-t bg-muted/30 text-sm text-right font-medium">
              Total: {totalHours.toFixed(2)} hrs ({formatDuration(Math.round(totalHours * 60))})
            </div>
          </div>
        )}
      </div>

      {/* Edit dialog */}
      <Dialog open={!!editingLog} onOpenChange={() => setEditingLog(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Edit Log</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 pt-2">
            <div>
              <Label htmlFor="edit-comment">Comment</Label>
              <Textarea
                id="edit-comment"
                rows={3}
                value={editComment}
                onChange={e => setEditComment(e.target.value)}
                placeholder="What were you working on?"
              />
            </div>
            <div>
              <Label htmlFor="edit-duration">Duration (minutes)</Label>
              <Input
                id="edit-duration"
                type="number"
                min={1}
                max={MAX_DURATION_MINUTES}
                value={editDuration}
                onChange={e => setEditDuration(parseInt(e.target.value) || 60)}
              />
              <p className="text-xs text-muted-foreground mt-1">
                = {formatDuration(editDuration)}
              </p>
            </div>
            <div className="flex gap-2 pt-1">
              <Button onClick={() => void handleSaveEdit()} disabled={saving}>
                {saving ? "Saving…" : "Save"}
              </Button>
              <Button variant="outline" onClick={() => setEditingLog(null)}>
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </Layout>
  )
}
