// ─── Core domain types ────────────────────────────────────────────────────────

export type PlanStatus = "Active" | "Completed" | "Paused" | "Archived"
export type ProjectStatus = "Active" | "On Hold" | "Complete" | "Archived"
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
  // summary-level extras
  days_remaining?: number
  overall_completion?: number
  sprint_activity_count?: number
  // detail-level extras
  sprint_activities?: SprintActivity[]
}

export interface Project {
  id: number
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
  activities_count?: number
  completed_count?: number
  hours_estimated?: number
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

export interface SprintActivity {
  id: number
  plan_id: number
  activity_id: number
  notes: string | null
  activity_name: string
  project_id: number
  project_name: string
  created_at: string
}

export interface ProjectDailyNote {
  id: number
  project_id: number
  plan_id: number | null
  date: string              // YYYY-MM-DD
  what_i_did: string | null
  blockers: string | null
  next_steps: string | null
  project_name: string
  created_at: string
  updated_at: string
}

export interface ActivityLog {
  id: number
  biweekly_plan_id: number | null
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
  activities_logged: number
  projects_worked_on: string[]
}

export interface ActivePlanOverview {
  id: number
  name: string
  start_date: string
  end_date: string
  days_remaining: number
  sprint_activity_count: number
  overall_completion: number
}

export interface DashboardData {
  active_plan: ActivePlanOverview | null
  projects: Project[]              // all Active projects
  sprint_activities: SprintActivity[]
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

export interface SprintActivitiesResponse {
  sprint_activities: SprintActivity[]
}

export interface DailyNotesResponse {
  notes: ProjectDailyNote[]
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
  biweekly_plan_id?: number | null
  project_id: number
  activity_id: number | null
  comment: string
  duration_minutes: number
  timestamp: string
}

export interface DailyNoteFormData {
  project_id: number
  date: string
  what_i_did: string
  blockers: string
  next_steps: string
  plan_id?: number | null
}
