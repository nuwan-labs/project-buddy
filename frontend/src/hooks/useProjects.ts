import { useState, useEffect } from "react"
import { projectsApi } from "@/services/api"
import type { Project } from "@/types"
import { toast } from "@/components/Notifications"

export function useProjects(status?: string) {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading]   = useState(false)
  const [ver, setVer]           = useState(0)

  useEffect(() => {
    setLoading(true)
    const params = status ? { status } : undefined
    void projectsApi.list(params)
      .then(({ data: res }) => setProjects(res.data.projects))
      .catch(() => toast({ title: "Failed to load projects.", variant: "destructive" }))
      .finally(() => setLoading(false))
  }, [status, ver])

  return { projects, loading, reload: () => setVer(v => v + 1) }
}
