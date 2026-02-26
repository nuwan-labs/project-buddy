// ─── Backend URLs ─────────────────────────────────────────────────────────────
// In dev, Vite proxies /api → http://localhost:5000
export const API_BASE = "/api"
export const WS_URL   = `ws://${window.location.host}/ws/notifications`

// ─── Status options ───────────────────────────────────────────────────────────
export const PLAN_STATUSES     = ["Active", "Completed", "Paused", "Archived"] as const
export const PROJECT_STATUSES  = ["Active", "On Hold", "Complete", "Archived"] as const
export const ACTIVITY_STATUSES = ["Not Started", "In Progress", "Complete"] as const

// ─── Status colours (Tailwind classes) ───────────────────────────────────────
export const PLAN_STATUS_COLORS: Record<string, string> = {
  Active:    "bg-green-100 text-green-800",
  Completed: "bg-blue-100 text-blue-800",
  Paused:    "bg-yellow-100 text-yellow-800",
  Archived:  "bg-gray-100 text-gray-600",
}

export const PROJECT_STATUS_COLORS: Record<string, string> = {
  "Active":   "bg-blue-100 text-blue-800",
  "On Hold":  "bg-yellow-100 text-yellow-800",
  "Complete": "bg-green-100 text-green-800",
  "Archived": "bg-gray-100 text-gray-600",
}

export const ACTIVITY_STATUS_COLORS: Record<string, string> = {
  "Not Started": "bg-gray-100 text-gray-600",
  "In Progress": "bg-yellow-100 text-yellow-800",
  "Complete":    "bg-green-100 text-green-800",
}

// ─── Project colour palette ───────────────────────────────────────────────────
export const COLOR_PALETTE = [
  "#4472C4", "#ED7D31", "#A9D18E", "#FF5733",
  "#FFC000", "#5B9BD5", "#70AD47", "#7030A0",
  "#C00000", "#00B0F0",
]

// ─── Activity log limits ──────────────────────────────────────────────────────
export const MAX_DURATION_MINUTES = 480   // 8 hours
export const DEFAULT_DURATION     = 60    // 1 hour
