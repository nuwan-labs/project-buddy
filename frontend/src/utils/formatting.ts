import { format, parseISO, isValid } from "date-fns"

/** Format a YYYY-MM-DD date string to a human-readable form, e.g. "09 Feb 2026" */
export function formatDate(dateStr: string): string {
  try {
    const d = parseISO(dateStr)
    return isValid(d) ? format(d, "dd MMM yyyy") : dateStr
  } catch {
    return dateStr
  }
}

/** Format a full ISO 8601 timestamp to "HH:mm" */
export function formatTime(isoStr: string): string {
  try {
    const d = parseISO(isoStr)
    return isValid(d) ? format(d, "HH:mm") : isoStr
  } catch {
    return isoStr
  }
}

/** Format a full ISO 8601 timestamp to "dd MMM, HH:mm" */
export function formatDateTime(isoStr: string): string {
  try {
    const d = parseISO(isoStr)
    return isValid(d) ? format(d, "dd MMM, HH:mm") : isoStr
  } catch {
    return isoStr
  }
}

/** Convert minutes to a readable duration string: "1h 30m", "45m", "2h" */
export function formatDuration(minutes: number): string {
  if (minutes <= 0) return "0m"
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  if (h === 0) return `${m}m`
  if (m === 0) return `${h}h`
  return `${h}h ${m}m`
}

/** Convert decimal hours to readable string: "1.75 hrs" */
export function formatHours(hours: number): string {
  return `${hours.toFixed(2)} hrs`
}

/** Return today's date as YYYY-MM-DD */
export function todayISO(): string {
  return format(new Date(), "yyyy-MM-dd")
}

/** Return current timestamp as ISO 8601 with local TZ offset, e.g. "2026-02-09T10:30:00+05:30" */
export function nowWithOffset(): string {
  const d   = new Date()
  const pad = (n: number) => String(n).padStart(2, "0")
  const off = -d.getTimezoneOffset()
  const sign = off >= 0 ? "+" : "-"
  const hh   = pad(Math.floor(Math.abs(off) / 60))
  const mm   = pad(Math.abs(off) % 60)
  return (
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}` +
    `T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}` +
    `${sign}${hh}:${mm}`
  )
}
