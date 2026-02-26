import { useState, useEffect } from "react"
import { logsApi } from "@/services/api"
import type { ActivityLog } from "@/types"
import { toast } from "@/components/Notifications"

interface LogFilters {
  date?:             string
  project_id?:       number | ""
  biweekly_plan_id?: number | ""
}

export function useActivityLogs(filters: LogFilters) {
  const [logs, setLogs]           = useState<ActivityLog[]>([])
  const [totalHours, setTotalHours] = useState(0)
  const [loading, setLoading]     = useState(false)
  const [ver, setVer]             = useState(0)

  useEffect(() => {
    setLoading(true)
    const params: Record<string, string | number> = {}
    if (filters.date)             params.date             = filters.date
    if (filters.project_id)       params.project_id       = filters.project_id
    if (filters.biweekly_plan_id) params.biweekly_plan_id = filters.biweekly_plan_id
    void logsApi.list(params)
      .then(({ data: res }) => {
        setLogs(res.data.logs)
        setTotalHours(res.data.total_hours)
      })
      .catch(() => toast({ title: "Failed to load logs.", variant: "destructive" }))
      .finally(() => setLoading(false))
  }, [filters.date, filters.project_id, filters.biweekly_plan_id, ver])

  return { logs, totalHours, loading, reload: () => setVer(v => v + 1) }
}
