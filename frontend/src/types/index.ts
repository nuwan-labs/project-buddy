// ─── Core domain types ────────────────────────────────────────────────────────

export type PlanStatus = "Active" | "Completed" | "Paused" | "Archived"
export type ProjectStatus = "Not Started" | "In Progress" | "Blocked" | "Complete"
export type ActivityStatus = "Not Started" | "In Progress" | "Complete"

export interface BiweeklyPlan {
  id: number
  name: string
  description: string | null
  start_date: string        // YYYY-MM-DD
  end_date: string          // YYYY-MM-DD
  status: PlanStatus
  created_at: string
  updated_at: string
  // summary-level extras (returned by list & active endpoints)
  days_remaining?: number
  overall_completion?: number
  total_hours_logged?: number
  project_count?: number
  // detail-level extras (returned by /biweekly-plans/{id})
  projects?: Project[]
}

export interface Project {
  id: number
  biweekly_plan_id: number
  name: string
  description: string | null
  goal: string | null
  status: ProjectStatus
  color_tag: string | null
  created_at: string
  updated_at: string
  // computed
  completion_percent?: number
  hours_logged?: number
  activity_count?: number
  completed_activities?: number
  // detail-level
  activities?: Activity[]
}

export interface Activity {
  id: number
  project_id: number
  name: string
  description: string | null
  deliverables: string | null
  dependencies: string | null
  status: ActivityStatus
  estimated_hours: number
  logged_hours: number
  created_at: string
  updated_at: string
}

export interface ActivityLog {
  id: number
  biweekly_plan_id: number
  project_id: number
  activity_id: number | null
  comment: string
  duration_minutes: number
  timestamp: string           // ISO 8601 with TZ offset
  tags: string[] | null
  project_name?: string
  activity_name?: string | null
  created_at: string
}

export interface DailySummary {
  id: number
  biweekly_plan_id: number | null
  date: string               // YYYY-MM-DD
  summary_text: string | null
  blockers: string[]
  highlights: string[]
  suggestions: string[]
  patterns: string[]
  generated_at: string
}

// ─── Dashboard ────────────────────────────────────────────────────────────────

export interface TodaySummary {
  date: string
  total_hours_logged: number
  log_count: number
  projects_active: number
}

export interface DashboardData {
  active_plan: BiweeklyPlan | null
  projects: Project[]
  today_summary: TodaySummary | null
  daily_summary: DailySummary | null
}

// ─── API response wrappers ────────────────────────────────────────────────────

export interface ApiResponse<T> {
  success: boolean
  data: T
  message?: string
}

export interface PaginatedPlans {
  plans: BiweeklyPlan[]
  total: number
  page: number
  pages: number
}

export interface ProjectsResponse {
  projects: Project[]
}

export interface ActivitiesResponse {
  activities: Activity[]
}

export interface LogsResponse {
  logs: ActivityLog[]
  total_hours: number
  log_count: number
}

// ─── WebSocket ────────────────────────────────────────────────────────────────

export type WsMessageType =
  | "activity_logged"
  | "summary_ready"
  | "plan_updated"
  | "notification"

export interface WebSocketMessage {
  type: WsMessageType
  action?: string
  message?: string
  data?: Record<string, unknown>
}

// ─── Form payloads ────────────────────────────────────────────────────────────

export interface PlanFormData {
  name: string
  description: string
  start_date: string
  end_date: string
  status?: PlanStatus
}

export interface ProjectFormData {
  name: string
  description: string
  goal: string
  color_tag: string
  status?: ProjectStatus
}

export interface ActivityFormData {
  name: string
  description: string
  deliverables: string
  dependencies: string
  estimated_hours: number
  status?: ActivityStatus
}

export interface LogFormData {
  biweekly_plan_id: number
  project_id: number
  activity_id: number | null
  comment: string
  duration_minutes: number
  timestamp: string
}
