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
  PlanFormData,
  ProjectFormData,
  ActivityFormData,
  LogFormData,
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

// ─── Projects ─────────────────────────────────────────────────────────────────

export const projectsApi = {
  list: (planId: number) =>
    http.get<ApiResponse<ProjectsResponse>>(`/biweekly-plans/${planId}/projects`),

  create: (planId: number, data: ProjectFormData) =>
    http.post<ApiResponse<Project>>(`/biweekly-plans/${planId}/projects`, data),

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

// ─── Activity Logs ────────────────────────────────────────────────────────────

export const logsApi = {
  list: (params?: {
    date?: string
    project_id?: number
    biweekly_plan_id?: number
    sort?: string
  }) => http.get<ApiResponse<LogsResponse>>("/activity-logs", { params }),

  create: (data: LogFormData) =>
    http.post<ApiResponse<ActivityLog>>("/activity-logs", data),

  update: (id: number, data: { comment?: string; duration_minutes?: number }) =>
    http.put<ApiResponse<ActivityLog>>(`/activity-logs/${id}`, data),

  delete: (id: number) =>
    http.delete<ApiResponse<null>>(`/activity-logs/${id}`),
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
}

// ─── Health ───────────────────────────────────────────────────────────────────

export const healthApi = {
  check: () =>
    http.get<{ status: string; version: string }>("/health".replace("/api", "")),
}

// Re-export the raw axios instance for edge cases
export { http }
