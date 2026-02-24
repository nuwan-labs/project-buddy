import { BrowserRouter, Routes, Route } from "react-router-dom"
import { AppProvider } from "@/context/AppContext"
import { Toaster } from "@/components/ui/toaster"

// Pages (stubbed for Phase 4; full implementation in Phase 6)
import Dashboard      from "@/pages/Dashboard"
import BiweeklyPlans  from "@/pages/BiweeklyPlans"
import PlanEditor     from "@/pages/PlanEditor"
import ProjectDetail  from "@/pages/ProjectDetail"
import ActivityLogs   from "@/pages/ActivityLogs"
import Settings       from "@/pages/Settings"
import NotFound       from "@/pages/NotFound"

export default function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/"                                         element={<Dashboard />} />
          <Route path="/plans"                                    element={<BiweeklyPlans />} />
          <Route path="/plans/new"                               element={<PlanEditor />} />
          <Route path="/plans/:id/edit"                          element={<PlanEditor />} />
          <Route path="/plans/:planId/projects/:projectId"       element={<ProjectDetail />} />
          <Route path="/logs"                                    element={<ActivityLogs />} />
          <Route path="/settings"                                element={<Settings />} />
          <Route path="*"                                        element={<NotFound />} />
        </Routes>
      </BrowserRouter>
      <Toaster />
    </AppProvider>
  )
}
