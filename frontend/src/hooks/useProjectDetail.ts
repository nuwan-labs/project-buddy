import { useState, useEffect, useCallback } from "react"
import { projectsApi, activitiesApi, dailyNotesApi } from "@/services/api"
import type { Project, Activity, ProjectDailyNote } from "@/types"
import { toast } from "@/components/Notifications"

export function useProjectDetail(projectId: number) {
  const [project, setProject]       = useState<Project | null>(null)
  const [activities, setActivities] = useState<Activity[]>([])
  const [notes, setNotes]           = useState<ProjectDailyNote[]>([])
  const [loading, setLoading]       = useState(true)

  const loadProject = useCallback(async () => {
    try {
      const { data: res } = await projectsApi.get(projectId)
      setProject(res.data)
    } catch {
      toast({ title: "Failed to load project.", variant: "destructive" })
    }
  }, [projectId])

  const loadActivities = useCallback(async () => {
    try {
      const { data: res } = await activitiesApi.list(projectId)
      setActivities(res.data.activities)
    } catch {
      toast({ title: "Failed to load activities.", variant: "destructive" })
    }
  }, [projectId])

  const loadNotes = useCallback(async () => {
    try {
      const { data: res } = await dailyNotesApi.list({ project_id: projectId })
      setNotes(res.data.notes)
    } catch {
      // notes are optional — silently ignore
    }
  }, [projectId])

  useEffect(() => {
    setLoading(true)
    Promise.all([loadProject(), loadActivities(), loadNotes()])
      .finally(() => setLoading(false))
  }, [loadProject, loadActivities, loadNotes])

  return {
    project,
    activities,
    notes,
    loading,
    loadProject,
    loadActivities,
    loadNotes,
  }
}
