import axios from "axios"
import type {
  ApiResponse,
  PaginatedPlans,
  BiweeklyPlan,
  Project,
  Activity,
  ActivityLog,
  DailySummary,
  DashboardData,
  ProjectsResponse,
  ActivitiesResponse,
  LogsResponse,
  SprintActivitiesResponse,
  SprintActivity,
  DailyNotesResponse,
  ProjectDailyNote,
  PlanFormData,
  ProjectFormData,
  ActivityFormData,
  LogFormData,
  DailyNoteFormData,
} from "@/types"

const http = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
})

// ─── Biweekly Plans ───────────────────────────────────────────────────────────

export const plansApi = {
  list: (params?: { status_filter?: string; limit?: number; offset?: number }) =>
    http.get<ApiResponse<PaginatedPlans>>("/biweekly-plans", { params }),

  get: (id: number) =>
    http.get<ApiResponse<BiweeklyPlan>>(`/biweekly-plans/${id}`),

  getActive: () =>
    http.get<ApiResponse<BiweeklyPlan>>("/biweekly-plans/active"),

  create: (data: PlanFormData) =>
    http.post<ApiResponse<BiweeklyPlan>>("/biweekly-plans", data),

  update: (id: number, data: Partial<PlanFormData>) =>
    http.put<ApiResponse<BiweeklyPlan>>(`/biweekly-plans/${id}`, data),

  delete: (id: number) =>
    http.delete<ApiResponse<null>>(`/biweekly-plans/${id}`),

  exportExcel: (id: number) =>
    http.get(`/biweekly-plans/${id}/export-excel`, { responseType: "blob" }),
}

// ─── Projects (standalone — no plan ownership) ────────────────────────────────

export const projectsApi = {
  list: (params?: { status?: string }) =>
    http.get<ApiResponse<ProjectsResponse>>("/projects", { params }),

  get: (id: number) =>
    http.get<ApiResponse<Project>>(`/projects/${id}`),

  create: (data: ProjectFormData) =>
    http.post<ApiResponse<Project>>("/projects", data),

  update: (id: number, data: Partial<ProjectFormData>) =>
    http.put<ApiResponse<Project>>(`/projects/${id}`, data),

  delete: (id: number) =>
    http.delete<ApiResponse<null>>(`/projects/${id}`),
}

// ─── Activities ───────────────────────────────────────────────────────────────

export const activitiesApi = {
  list: (projectId: number) =>
    http.get<ApiResponse<ActivitiesResponse>>(`/projects/${projectId}/activities`),

  create: (projectId: number, data: ActivityFormData) =>
    http.post<ApiResponse<Activity>>(`/projects/${projectId}/activities`, data),

  update: (id: number, data: Partial<ActivityFormData & { status: string }>) =>
    http.put<ApiResponse<Activity>>(`/activities/${id}`, data),

  delete: (id: number) =>
    http.delete<ApiResponse<null>>(`/activities/${id}`),
}

// ─── Sprint Activities ────────────────────────────────────────────────────────

export const sprintActivitiesApi = {
  list: (planId: number) =>
    http.get<ApiResponse<SprintActivitiesResponse>>(`/biweekly-plans/${planId}/sprint-activities`),

  add: (planId: number, data: { activity_id: number; notes?: string }) =>
    http.post<ApiResponse<SprintActivity>>(`/biweekly-plans/${planId}/sprint-activities`, data),

  remove: (planId: number, activityId: number) =>
    http.delete<ApiResponse<null>>(`/biweekly-plans/${planId}/sprint-activities/${activityId}`),
}

// ─── Activity Logs ────────────────────────────────────────────────────────────

export const logsApi = {
  list: (params?: {
    date?: string
    project_id?: number
    plan_id?: number
    sort?: string
  }) => http.get<ApiResponse<LogsResponse>>("/activity-logs", { params }),

  create: (data: LogFormData) =>
    http.post<ApiResponse<ActivityLog>>("/activity-logs", data),

  update: (id: number, data: { comment?: string; duration_minutes?: number }) =>
    http.put<ApiResponse<ActivityLog>>(`/activity-logs/${id}`, data),

  delete: (id: number) =>
    http.delete<ApiResponse<null>>(`/activity-logs/${id}`),
}

// ─── Project Daily Notes ──────────────────────────────────────────────────────

export const dailyNotesApi = {
  list: (params?: { project_id?: number; date?: string; plan_id?: number }) =>
    http.get<ApiResponse<DailyNotesResponse>>("/project-notes", { params }),

  upsert: (data: DailyNoteFormData) =>
    http.post<ApiResponse<ProjectDailyNote>>("/project-notes", data),

  update: (id: number, data: { what_i_did?: string; blockers?: string; next_steps?: string }) =>
    http.put<ApiResponse<ProjectDailyNote>>(`/project-notes/${id}`, data),

  delete: (id: number) =>
    http.delete<ApiResponse<null>>(`/project-notes/${id}`),
}

// ─── Dashboard ────────────────────────────────────────────────────────────────

export const dashboardApi = {
  get: () =>
    http.get<ApiResponse<DashboardData>>("/dashboard"),

  getDailySummary: (date: string) =>
    http.get<ApiResponse<DailySummary>>("/dashboard/daily-summary", { params: { date } }),
}

// ─── DeepSeek / AI ────────────────────────────────────────────────────────────

export const deepseekApi = {
  triggerAnalysis: (date: string) =>
    http.post<ApiResponse<DailySummary>>("/deepseek/daily-analysis", { date }),

  getSummary: (date: string) =>
    http.get<ApiResponse<DailySummary>>("/deepseek/daily-summary", { params: { date } }),

  status: () =>
    http.get<ApiResponse<{ reachable: boolean; model: string | null; message: string | null }>>(
      "/deepseek/status"
    ),
}

// ─── Health ───────────────────────────────────────────────────────────────────

export const healthApi = {
  check: () =>
    http.get<{ status: string; version: string }>("/health".replace("/api", "")),
}

// Re-export the raw axios instance for edge cases
export { http }
