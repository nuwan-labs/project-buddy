import { useState, useEffect } from "react"
import { plansApi } from "@/services/api"
import type { BiweeklyPlan } from "@/types"
import { toast } from "@/components/Notifications"

export function usePlans(statusFilter?: string) {
  const [plans, setPlans]   = useState<BiweeklyPlan[]>([])
  const [loading, setLoading] = useState(false)
  const [ver, setVer]         = useState(0)

  useEffect(() => {
    setLoading(true)
    const params = statusFilter ? { status_filter: statusFilter } : undefined
    void plansApi.list(params)
      .then(({ data: res }) => setPlans(res.data.plans))
      .catch(() => toast({ title: "Failed to load plans.", variant: "destructive" }))
      .finally(() => setLoading(false))
  }, [statusFilter, ver])

  return { plans, loading, reload: () => setVer(v => v + 1) }
}
