import Layout from "@/components/Layout"
import { useApp } from "@/context/AppContext"
import { formatDate, formatHours } from "@/utils/formatting"
import { calcDaysRemaining } from "@/utils/calculations"
import ProjectCard from "@/components/ProjectCard"
import DailySummaryCard from "@/components/DailySummaryCard"

export default function Dashboard() {
  const { state, openActivityPopup } = useApp()
  const { activePlan, projects, dailySummary, dashboardLoading, dashboardError } = state

  return (
    <Layout>
      <div className="p-6 max-w-5xl mx-auto space-y-6">
        {dashboardLoading && (
          <p className="text-muted-foreground text-sm">Loading dashboard…</p>
        )}
        {dashboardError && (
          <p className="text-destructive text-sm">{dashboardError}</p>
        )}

        {/* Plan header */}
        {activePlan ? (
          <div className="bg-white rounded-lg border p-5">
            <div className="flex items-start justify-between gap-4">
              <div>
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
                <p className="text-xs text-muted-foreground">overall complete</p>
              </div>
            </div>
            {activePlan.description && (
              <p className="text-sm text-muted-foreground mt-2">{activePlan.description}</p>
            )}
            <div className="flex gap-4 mt-3 text-xs text-muted-foreground">
              <span>{formatHours(activePlan.total_hours_logged ?? 0)} logged this period</span>
              <span>{activePlan.project_count ?? 0} projects</span>
            </div>
          </div>
        ) : !dashboardLoading ? (
          <div className="bg-white rounded-lg border p-8 text-center">
            <p className="text-muted-foreground">No active plan found.</p>
            <a href="/plans/new" className="text-blue-600 text-sm mt-2 inline-block hover:underline">
              Create your first biweekly plan →
            </a>
          </div>
        ) : null}

        {/* Projects grid */}
        {projects.length > 0 && (
          <div>
            <h2 className="text-base font-semibold mb-3">Projects</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {projects.map((p) => (
                <ProjectCard
                  key={p.id}
                  project={p}
                  planId={activePlan?.id ?? 0}
                  onLogTime={(id) => openActivityPopup(id)}
                />
              ))}
            </div>
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
