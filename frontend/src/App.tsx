import { BrowserRouter, Routes, Route } from "react-router-dom"
import { AppProvider } from "@/context/AppContext"
import { Toaster } from "@/components/ui/toaster"

import Dashboard      from "@/pages/Dashboard"
import BiweeklyPlans  from "@/pages/BiweeklyPlans"
import PlanEditor     from "@/pages/PlanEditor"
import Projects       from "@/pages/Projects"
import ProjectEditor  from "@/pages/ProjectEditor"
import ProjectDetail  from "@/pages/ProjectDetail"
import ActivityLogs   from "@/pages/ActivityLogs"
import Settings       from "@/pages/Settings"
import NotFound       from "@/pages/NotFound"

export default function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/"                          element={<Dashboard />} />
          <Route path="/plans"                     element={<BiweeklyPlans />} />
          <Route path="/plans/new"                 element={<PlanEditor />} />
          <Route path="/plans/:id/edit"            element={<PlanEditor />} />
          <Route path="/projects"                    element={<Projects />} />
          <Route path="/projects/new"              element={<ProjectEditor />} />
          <Route path="/projects/:projectId"       element={<ProjectDetail />} />
          <Route path="/projects/:projectId/edit"  element={<ProjectEditor />} />
          <Route path="/logs"                      element={<ActivityLogs />} />
          <Route path="/settings"                  element={<Settings />} />
          <Route path="*"                          element={<NotFound />} />
        </Routes>
      </BrowserRouter>
      <Toaster />
    </AppProvider>
  )
}
