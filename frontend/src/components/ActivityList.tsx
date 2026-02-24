import { useState } from "react"
import { Check, ChevronDown, ChevronUp, Trash2, Clock } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import type { Activity, ActivityStatus } from "@/types"
import { ACTIVITY_STATUS_COLORS } from "@/utils/constants"
import { formatHours } from "@/utils/formatting"
import { activitiesApi } from "@/services/api"
import { useToast } from "@/components/ui/use-toast"

interface ActivityListProps {
  activities: Activity[]
  onRefresh:  () => void
}

const STATUS_CYCLE: ActivityStatus[] = ["Not Started", "In Progress", "Complete"]

function variantFor(status: ActivityStatus): string {
  const base = ACTIVITY_STATUS_COLORS[status] ?? "bg-gray-100 text-gray-600"
  return base
}

export default function ActivityList({ activities, onRefresh }: ActivityListProps) {
  const { toast }                           = useToast()
  const [expanded, setExpanded]             = useState<Set<number>>(new Set())
  const [processing, setProcessing]         = useState<Set<number>>(new Set())

  const toggleExpand = (id: number) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const cycleStatus = async (act: Activity) => {
    const idx        = STATUS_CYCLE.indexOf(act.status)
    const nextStatus = STATUS_CYCLE[(idx + 1) % STATUS_CYCLE.length]
    setProcessing((p) => new Set(p).add(act.id))
    try {
      await activitiesApi.update(act.id, { status: nextStatus })
      onRefresh()
    } catch {
      toast({ title: "Status update failed", variant: "destructive" })
    } finally {
      setProcessing((p) => { const s = new Set(p); s.delete(act.id); return s })
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this activity and all its logs?")) return
    try {
      await activitiesApi.delete(id)
      onRefresh()
      toast({ title: "Activity deleted" })
    } catch {
      toast({ title: "Delete failed", variant: "destructive" })
    }
  }

  if (activities.length === 0) {
    return (
      <p className="text-sm text-muted-foreground text-center py-8">
        No activities yet. Add one to get started.
      </p>
    )
  }

  return (
    <div className="space-y-2">
      {activities.map((act) => {
        const isOpen       = expanded.has(act.id)
        const isBusy       = processing.has(act.id)
        const badgeClass   = variantFor(act.status)
        const hoursPct     = act.estimated_hours > 0
          ? Math.min(100, Math.round((act.logged_hours / act.estimated_hours) * 100))
          : 0

        return (
          <div key={act.id} className="border rounded-lg overflow-hidden bg-white">
            {/* Row */}
            <div className="flex items-center gap-3 px-4 py-3">
              {/* Status circle button */}
              <button
                title={`Status: ${act.status} — click to advance`}
                disabled={isBusy}
                onClick={() => void cycleStatus(act)}
                className={[
                  "flex-shrink-0 h-5 w-5 rounded-full border-2 flex items-center justify-center transition-colors",
                  act.status === "Complete"
                    ? "border-green-500 bg-green-500"
                    : act.status === "In Progress"
                    ? "border-blue-400 bg-transparent"
                    : "border-gray-300 bg-transparent",
                  isBusy ? "opacity-50 cursor-not-allowed" : "cursor-pointer hover:border-blue-500",
                ].join(" ")}
              >
                {act.status === "Complete" && <Check className="h-3 w-3 text-white" />}
              </button>

              {/* Name */}
              <span
                className={`flex-1 text-sm min-w-0 truncate ${
                  act.status === "Complete" ? "line-through text-muted-foreground" : "font-medium"
                }`}
              >
                {act.name}
              </span>

              {/* Hours */}
              <div className="flex items-center gap-1 text-xs text-muted-foreground shrink-0">
                <Clock className="h-3 w-3" />
                <span>{formatHours(act.logged_hours)}</span>
                {act.estimated_hours > 0 && (
                  <span>/ {formatHours(act.estimated_hours)} ({hoursPct}%)</span>
                )}
              </div>

              {/* Status badge */}
              <Badge className={`${badgeClass} shrink-0 text-xs`}>{act.status}</Badge>

              {/* Expand toggle */}
              <button
                onClick={() => toggleExpand(act.id)}
                className="text-muted-foreground hover:text-foreground ml-1"
                aria-label={isOpen ? "Collapse" : "Expand"}
              >
                {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </button>

              {/* Delete */}
              <Button
                size="icon"
                variant="ghost"
                className="h-7 w-7 text-muted-foreground hover:text-destructive"
                onClick={() => void handleDelete(act.id)}
                aria-label="Delete activity"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </Button>
            </div>

            {/* Expanded detail panel */}
            {isOpen && (
              <div className="px-4 pb-4 pt-2 border-t bg-gray-50 space-y-2.5">
                {act.estimated_hours > 0 && (
                  <div>
                    <div className="flex justify-between text-xs text-muted-foreground mb-1">
                      <span>Hours progress</span>
                      <span>{hoursPct}%</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-secondary overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full transition-all"
                        style={{ width: `${hoursPct}%` }}
                      />
                    </div>
                  </div>
                )}
                {act.description && (
                  <p className="text-xs">
                    <span className="font-medium text-gray-700">Description: </span>
                    {act.description}
                  </p>
                )}
                {act.deliverables && (
                  <p className="text-xs">
                    <span className="font-medium text-gray-700">Deliverables: </span>
                    {act.deliverables}
                  </p>
                )}
                {act.dependencies && (
                  <p className="text-xs">
                    <span className="font-medium text-gray-700">Dependencies: </span>
                    {act.dependencies}
                  </p>
                )}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
