import { parseISO, differenceInCalendarDays } from "date-fns"
import type { Activity } from "@/types"

/** % of activities marked Complete, 0–100 */
export function calcCompletionPercent(activities: Activity[]): number {
  if (activities.length === 0) return 0
  const done = activities.filter((a) => a.status === "Complete").length
  return Math.round((done / activities.length) * 100)
}

/** Sum of (duration_minutes / 60) for a list of logs */
export function calcHoursLogged(totalMinutes: number): number {
  return Math.round((totalMinutes / 60) * 100) / 100
}

/** Calendar days remaining from today to end_date (inclusive). Min 0. */
export function calcDaysRemaining(endDate: string): number {
  const end   = parseISO(endDate)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const diff = differenceInCalendarDays(end, today)
  return Math.max(0, diff)
}

/** Clamp a value between min and max */
export function clamp(value: number, min = 0, max = 100): number {
  return Math.min(max, Math.max(min, value))
}
