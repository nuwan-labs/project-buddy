import { useNavigate } from "react-router-dom"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import ProgressBar from "@/components/ProgressBar"
import type { Project } from "@/types"
import { PROJECT_STATUS_COLORS } from "@/utils/constants"
import { formatHours } from "@/utils/formatting"

interface ProjectCardProps {
  project:    Project
  planId:     number
  onLogTime:  (projectId: number) => void
}

function variantFor(status: Project["status"]): "blue" | "green" | "red" | "yellow" {
  if (status === "Complete")    return "green"
  if (status === "Blocked")     return "red"
  if (status === "In Progress") return "blue"
  return "blue"
}

export default function ProjectCard({ project, planId, onLogTime }: ProjectCardProps) {
  const navigate   = useNavigate()
  const completion = project.completion_percent ?? 0
  const hours      = project.hours_logged ?? 0
  const total      = project.activity_count ?? 0
  const done       = project.completed_activities ?? 0
  const badgeClass = PROJECT_STATUS_COLORS[project.status] ?? ""

  return (
    <Card className="relative overflow-hidden hover:shadow-md transition-shadow">
      {/* Left colour stripe */}
      {project.color_tag && (
        <div
          className="absolute left-0 top-0 h-full w-1.5 rounded-l-lg"
          style={{ backgroundColor: project.color_tag }}
        />
      )}

      <CardHeader className="pb-2 pl-6">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-sm font-semibold leading-snug">
            {project.name}
          </CardTitle>
          <Badge className={`${badgeClass} shrink-0 text-xs`}>
            {project.status}
          </Badge>
        </div>
        {project.goal && (
          <p className="text-xs text-muted-foreground line-clamp-2 mt-0.5">
            {project.goal}
          </p>
        )}
      </CardHeader>

      <CardContent className="pl-6 space-y-3">
        <ProgressBar
          label="Activities complete"
          value={completion}
          variant={variantFor(project.status)}
        />

        <div className="flex justify-between text-xs text-muted-foreground">
          <span>{done}/{total} activities</span>
          <span>{formatHours(hours)} logged</span>
        </div>

        <div className="flex gap-2 pt-1">
          <Button
            size="sm"
            variant="outline"
            className="flex-1 text-xs h-8"
            onClick={() => navigate(`/plans/${planId}/projects/${project.id}`)}
          >
            View Details
          </Button>
          <Button
            size="sm"
            className="flex-1 text-xs h-8"
            onClick={() => onLogTime(project.id)}
          >
            Log Time
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
