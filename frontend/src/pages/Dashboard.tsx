import { useState, useEffect } from "react"
import Layout from "@/components/Layout"
import { useApp } from "@/context/AppContext"
import { formatDate, formatHours } from "@/utils/formatting"
import { calcDaysRemaining } from "@/utils/calculations"
import ProjectCard from "@/components/ProjectCard"
import DailySummaryCard from "@/components/DailySummaryCard"
import { dashboardApi } from "@/services/api"
import type { TodaySummary } from "@/types"

export default function Dashboard() {
  const { state, openActivityPopup } = useApp()
  const { activePlan, projects, sprintActivities, dailySummary, dashboardLoading, dashboardError } = state

  const [todaySummary, setTodaySummary] = useState<TodaySummary | null>(null)

  // Fetch full dashboard to get today_summary (AppContext only stores plan/projects/summary)
  useEffect(() => {
    void dashboardApi.get().then(({ data }) => {
      setTodaySummary(data.data.today_summary)
    }).catch(() => {/* ignore */})
  }, [])

  return (
    <Layout>
      <div className="p-6 max-w-5xl mx-auto space-y-6">
        {dashboardLoading && (
          <p className="text-muted-foreground text-sm">Loading dashboard…</p>
        )}
        {dashboardError && (
          <p className="text-destructive text-sm">{dashboardError}</p>
        )}

        {/* Sprint banner */}
        {activePlan ? (
          <div className="bg-white rounded-lg border p-5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-medium text-blue-600 uppercase tracking-wide mb-1">
                  Active Sprint
                </p>
                <h1 className="text-xl font-bold">{activePlan.name}</h1>
                <p className="text-sm text-muted-foreground mt-0.5">
                  {formatDate(activePlan.start_date)} – {formatDate(activePlan.end_date)}
                  <span className="mx-2 text-gray-300">|</span>
                  {calcDaysRemaining(activePlan.end_date)} days remaining
                </p>
              </div>
              <div className="text-right shrink-0">
                <p className="text-2xl font-bold text-blue-600">
                  {activePlan.overall_completion ?? 0}%
                </p>
                <p className="text-xs text-muted-foreground">sprint complete</p>
              </div>
            </div>
            <div className="flex gap-4 mt-3 text-xs text-muted-foreground">
              <span>{activePlan.sprint_activity_count ?? 0} sprint activities</span>
              {sprintActivities.length > 0 && (
                <span>
                  {sprintActivities
                    .map((sa) => sa.project_name)
                    .filter((v, i, a) => a.indexOf(v) === i)
                    .join(", ")}
                </span>
              )}
            </div>
          </div>
        ) : !dashboardLoading ? (
          <div className="bg-white rounded-lg border p-4 text-sm text-muted-foreground flex items-center gap-3">
            <span>No active sprint.</span>
            <a href="/plans/new" className="text-blue-600 hover:underline">
              Create a sprint →
            </a>
          </div>
        ) : null}

        {/* Projects grid — all Active projects */}
        {projects.length > 0 ? (
          <div>
            <h2 className="text-base font-semibold mb-3">
              Active Projects ({projects.length})
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {projects.map((p) => (
                <ProjectCard
                  key={p.id}
                  project={p}
                  onLogTime={(id) => openActivityPopup(id)}
                />
              ))}
            </div>
          </div>
        ) : !dashboardLoading ? (
          <div className="bg-white rounded-lg border p-8 text-center">
            <p className="text-muted-foreground">No active projects.</p>
            <p className="text-sm text-muted-foreground mt-1">
              Create a project to get started.
            </p>
          </div>
        ) : null}

        {/* Today summary row */}
        {todaySummary && (
          <div className="bg-white rounded-lg border p-4 flex gap-6 text-sm flex-wrap">
            <div>
              <span className="text-muted-foreground">Today </span>
              <span className="font-medium">{formatHours(todaySummary.total_hours_logged)} logged</span>
            </div>
            <div>
              <span className="text-muted-foreground">Entries </span>
              <span className="font-medium">{todaySummary.activities_logged}</span>
            </div>
            {todaySummary.projects_worked_on.length > 0 && (
              <div>
                <span className="text-muted-foreground">Projects </span>
                <span className="font-medium">
                  {todaySummary.projects_worked_on.join(", ")}
                </span>
              </div>
            )}
          </div>
        )}

        {/* AI Daily Summary */}
        {dailySummary && (
          <DailySummaryCard summary={dailySummary} />
        )}
      </div>
    </Layout>
  )
}
