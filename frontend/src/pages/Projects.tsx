import { useState } from "react"
import { useNavigate } from "react-router-dom"
import Layout from "@/components/Layout"
import { projectsApi } from "@/services/api"
import { useProjects } from "@/hooks/useProjects"
import { PROJECT_STATUS_COLORS, PROJECT_STATUSES } from "@/utils/constants"
import { formatHours } from "@/utils/formatting"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { toast } from "@/components/Notifications"

export default function Projects() {
  const navigate = useNavigate()
  const [filter, setFilter]       = useState("all")
  const [confirmId, setConfirmId] = useState<number | null>(null)

  const { projects, loading, reload } = useProjects(filter !== "all" ? filter : undefined)

  async function handleDelete(id: number) {
    try {
      await projectsApi.delete(id)
      toast({ title: "Project deleted." })
      setConfirmId(null)
      reload()
    } catch {
      toast({ title: "Delete failed.", variant: "destructive" })
    }
  }

  async function handleArchive(id: number) {
    try {
      await projectsApi.update(id, { status: "Archived" })
      toast({ title: "Project archived." })
      reload()
    } catch {
      toast({ title: "Archive failed.", variant: "destructive" })
    }
  }

  return (
    <Layout>
      <div className="p-6 max-w-5xl mx-auto">

        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-xl font-bold">Projects</h1>
            <p className="text-sm text-muted-foreground">
              {projects.length} project{projects.length !== 1 ? "s" : ""}
            </p>
          </div>
          <Button onClick={() => navigate("/projects/new")}>+ New Project</Button>
        </div>

        {/* Status filter pills */}
        <div className="flex gap-2 mb-4 flex-wrap">
          {(["all", ...PROJECT_STATUSES] as string[]).map(s => (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                filter === s
                  ? "bg-blue-600 text-white border-blue-600"
                  : "border-gray-300 text-gray-600 hover:border-blue-400"
              }`}
            >
              {s === "all" ? "All" : s}
            </button>
          ))}
        </div>

        {/* Content */}
        {loading ? (
          <p className="text-sm text-muted-foreground py-8 text-center">Loading…</p>
        ) : projects.length === 0 ? (
          <div className="text-center py-16 text-muted-foreground">
            <p className="mb-3">No projects found.</p>
            <Button variant="outline" onClick={() => navigate("/projects/new")}>
              Create your first project
            </Button>
          </div>
        ) : (
          <div className="rounded-md border overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/50">
                <tr>
                  <th className="text-left px-4 py-2.5 font-medium">Name</th>
                  <th className="text-left px-4 py-2.5 font-medium">Status</th>
                  <th className="text-right px-4 py-2.5 font-medium">Activities</th>
                  <th className="text-right px-4 py-2.5 font-medium">Done</th>
                  <th className="text-right px-4 py-2.5 font-medium">Hours</th>
                  <th className="text-right px-4 py-2.5 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {projects.map(project => (
                  <tr key={project.id} className="border-t hover:bg-muted/20">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        {project.color_tag && (
                          <div
                            className="h-3 w-3 rounded-full flex-shrink-0"
                            style={{ backgroundColor: project.color_tag }}
                          />
                        )}
                        <div>
                          <span className="font-medium">{project.name}</span>
                          {project.goal && (
                            <p className="text-xs text-muted-foreground truncate max-w-xs mt-0.5">
                              {project.goal}
                            </p>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <Badge className={PROJECT_STATUS_COLORS[project.status]}>
                        {project.status}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-right">
                      {project.activities_count ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {project.completion_percent != null
                        ? `${Math.round(project.completion_percent)}%`
                        : "—"}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {project.hours_logged != null
                        ? formatHours(project.hours_logged)
                        : "—"}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-1 justify-end flex-wrap">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => navigate(`/projects/${project.id}`)}
                        >
                          View
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => navigate(`/projects/${project.id}/edit`)}
                        >
                          Edit
                        </Button>
                        {project.status !== "Archived" && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => void handleArchive(project.id)}
                          >
                            Archive
                          </Button>
                        )}
                        {confirmId === project.id ? (
                          <>
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => void handleDelete(project.id)}
                            >
                              Confirm
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => setConfirmId(null)}
                            >
                              Cancel
                            </Button>
                          </>
                        ) : (
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-red-600 hover:text-red-700"
                            onClick={() => setConfirmId(project.id)}
                          >
                            Delete
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Layout>
  )
}
